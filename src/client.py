"""
NetProbe Client

UDP tabanlı dosya gönderim istemcisi
Dosyayı paketlere bölerek gönder, ACK bekle, timeout yönetimi
"""

import socket
import argparse
import os
import hashlib
import time
from pathlib import Path
from typing import Dict

from protocol import DataPacket, AckPacket, PacketType, StartPacket, EndPacket, Constants
from logger import get_logger, EventType
from metrics import MetricsCalculator, MetricsWriter


class NetProbeClient:
    """UDP tabanlı dosya gönderim istemcisi"""
    
    def __init__(self,
                 host: str = "localhost",
                 port: int = 5000,
                 packet_size: int = 1024,
                 timeout: float = 2.0,
                 max_retries: int = 5,
                 window_size: int = 10,
                 compress: bool = False,
                 encrypt: bool = False,
                 pcap_file: str = None):
        """
        İstemciyi başlat
        
        Args:
            host: Sunucu adresi
            port: Sunucu portu
            packet_size: Paket boyutu (bayt)
            timeout: Timeout süresi (saniye)
            max_retries: Maksimum retry sayısı
            window_size: Sliding window boyutu
            compress: Sıkıştırma aktif mi?
            encrypt: Şifreleme aktif mi?
            pcap_file: PCAP dosyası (opsiyonel)
        """
        self.host = host
        self.port = port
        self.packet_size = packet_size
        self.timeout = timeout
        self.max_retries = max_retries
        self.window_size = window_size
        self.compress = compress
        self.encrypt = encrypt
        
        self.logger = get_logger()
        self.pcap_writer = PcapWriter(pcap_file) if pcap_file else None
        self.socket = None
        
        # Metrikleri hesapla
        self.metrics = MetricsCalculator()
        self.pending_acks: Dict[int, float] = {}  # seq_num -> gönderme zamanı
    
    def transfer_file(self, filepath: str) -> bool:
        """
        Dosyayı sunucuya gönder
        
        Args:
            filepath: Gönderilecek dosya yolu
            
        Returns:
            True eğer transfer başarılı, False aksi halde
        """
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"[ERR] Dosya bulunamadı: {filepath}")
            return False
        
        file_size = filepath.stat().st_size
        print(f"[OK] Dosya: {filepath.name} ({file_size:,} bytes)")
        
        # Socket oluştur
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(self.timeout)
        
        self.metrics = MetricsCalculator()
        
        try:
            # Dosya hash'ini hesapla
            file_hash = self._calculate_file_hash(str(filepath))
            
            # Dosyayı paketkara böl
            packets = self._split_file(filepath)
            total_packets = len(packets)
            
            print(f"[OK] Dosya bölündü: {total_packets} paket ({self.packet_size} bytes/paket)")
            
            # START paketini gönder
            self.logger.log_transfer_start(filepath.name, file_size)
            self._send_start_packet(total_packets, file_hash)
            
            # Her paketi gönder
            failed_packets = []
            for seq_num, payload in packets:
                success = self._send_packet_with_retry(seq_num, total_packets, payload)
                if not success:
                    failed_packets.append(seq_num)
            
            # END paketini gönder
            self._send_end_packet(total_packets)
            
            # Metrikleri hesapla
            self.metrics.end_transfer()
            metrics = self.metrics.calculate_metrics(
                filename=filepath.name,
                file_size_bytes=file_size,
                packet_size=self.packet_size,
                total_packets=total_packets
            )
            
            # Metrikleri kaydet ve yazdır
            MetricsWriter.print_metrics(metrics)
            MetricsWriter.save_json(metrics, "results/metrics.json")
            
            if failed_packets:
                print(f"\n[ERR] Başarısız paketler: {failed_packets}")
                self.logger.log_event(
                    EventType.FAILED,
                    status="WARNING",
                    details=f"Başarısız paketler: {failed_packets}"
                )
                return False
            
            print(f"\n[OK] Transfer başarılı!")
            self.logger.log_transfer_end(total_packets, len(packets) - len(failed_packets))
            
            return True
            
        except Exception as e:
            print(f"[ERR] Transfer hatası: {e}")
            self.logger.log_error(-1, str(e))
            return False
        
        finally:
            self.socket.close()
            self.logger.print_summary()
    
    def _send_start_packet(self, total_packets: int, file_hash: bytes):
        """Başlama paketini gönder"""
        start_pkt = StartPacket(total_packets=total_packets, file_hash=file_hash)
        data = start_pkt.serialize()
        self.socket.sendto(data, (self.host, self.port))
        print(f"[OK] START paketi gönderildi ({total_packets} paket)")
    
    def _send_end_packet(self, total_packets: int):
        """Bitiş paketini gönder"""
        end_pkt = EndPacket(total_packets=total_packets)
        data = end_pkt.serialize()
        self.socket.sendto(data, (self.host, self.port))
        print(f"[OK] END paketi gönderildi")
    
    def _send_packet_with_retry(self, seq_num: int, total_packets: int, payload: bytes) -> bool:
        """
        Paketi retry ile gönder
        
        Args:
            seq_num: Sequence numarası
            total_packets: Toplam paket sayısı
            payload: Veri
            
        Returns:
            True eğer başarılı, False aksi halde
        """
        current_timeout = self.timeout
        
        for retry_count in range(self.max_retries):
            # Paketi gönder
            pkt = DataPacket(
                seq_num=seq_num,
                total_packets=total_packets,
                payload=payload
            )
            data = pkt.serialize()
            
            self.socket.sendto(data, (self.host, self.port))
            self.metrics.record_send(seq_num)
            
            if retry_count == 0:
                self.logger.log_send(seq_num, len(payload))
            else:
                self.logger.log_timeout(seq_num, retry_count)
                self.metrics.record_retry(seq_num)
            
            # ACK bekleme
            try:
                self.socket.settimeout(current_timeout)
                ack_data, _ = self.socket.recvfrom(256)
                
                # ACK paketini kontrol et
                if ack_data[0] == PacketType.ACK:
                    ack_pkt = AckPacket.deserialize(ack_data)
                    if ack_pkt.ack_num == seq_num:
                        self.metrics.record_ack(seq_num)
                        self.logger.log_ack_received(seq_num)
                        return True
                
            except socket.timeout:
                # Timeout oluştu, retry et
                if retry_count < self.max_retries - 1:
                    current_timeout += 1.0  # Timeout'u arttır
                    continue
                else:
                    # Max retry'a ulaştı
                    self.metrics.record_failed_packet(seq_num)
                    self.logger.log_packet_failed(seq_num, self.max_retries)
                    return False
        
        return False
    
    def _split_file(self, filepath: Path) -> list:
        """
        Dosyayı paketkara böl
        
        Args:
            filepath: Dosya yolu
            
        Returns:
            (seq_num, payload) tuple'larının listesi
        """
        packets = []
        seq_num = 0
        max_payload = Constants.MAX_PAYLOAD
        
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(max_payload)
                if not chunk:
                    break
                packets.append((seq_num, chunk))
                seq_num += 1
        
        return packets
    
    def _calculate_file_hash(self, filepath: str) -> bytes:
        """Dosya SHA-256 hash'ini hesapla"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.digest()


def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description="NetProbe UDP Dosya Gönderim İstemcisi")
    parser.add_argument("--host", default="localhost", help="Sunucu adresi (varsayılan: localhost)")
    parser.add_argument("--port", type=int, default=5000, help="Sunucu portu (varsayılan: 5000)")
    parser.add_argument("--file", required=True, help="Gönderilecek dosya yolu")
    parser.add_argument("--packet-size", type=int, default=1024, help="Paket boyutu (varsayılan: 1024)")
    parser.add_argument("--timeout", type=float, default=2.0, help="Timeout süresi (varsayılan: 2.0)")
    parser.add_argument("--max-retries", type=int, default=5, help="Maksimum retry sayısı (varsayılan: 5)")
    parser.add_argument("--window-size", type=int, default=10, help="Sliding window boyutu (varsayılan: 10)")
    parser.add_argument("--compress", action="store_true", help="Zlib sıkıştırmayı etkinleştir")
    parser.add_argument("--encrypt", action="store_true", help="XOR şifrelemeyi etkinleştir")
    parser.add_argument("--pcap", type=str, help="Trafiği PCAP dosyasına kaydet")
    
    args = parser.parse_args()
    
    client = NetProbeClient(
        host=args.host,
        port=args.port,
        packet_size=args.packet_size,
        timeout=args.timeout,
        max_retries=args.max_retries,
        window_size=args.window_size,
        compress=args.compress,
        encrypt=args.encrypt,
        pcap_file=args.pcap
    )
    
    success = client.transfer_file(args.file)
    exit(0 if success else 1)


if __name__ == "__main__":
    main()

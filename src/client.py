"""
NetProbe Client

UDP tabanlı dosya gönderim istemcisi
Selective Repeat Sliding Window, Compression, Encryption, Dashboard
"""

import socket
import argparse
import os
import hashlib
import time
import threading
import zlib
from pathlib import Path
from typing import Dict, Tuple

from protocol import DataPacket, AckPacket, PacketType, StartPacket, EndPacket, Constants, NackPacket
from logger import get_logger, EventType, PcapWriter
from metrics import MetricsCalculator, MetricsWriter
try:
    from dashboard import TransferDashboard
except ImportError:
    TransferDashboard = None


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
        
        self.metrics = MetricsCalculator()
        
        # Sliding Window State
        self.window_base = 0
        self.unacked_packets: Dict[int, Tuple[bytes, float, int]] = {}  # seq_num -> (payload, send_time, retries)
        self.acked_packets = set()
        self.lock = threading.Lock()
        self.is_transferring = False
        self.dashboard = None
        self.failed_packets = []

    def transfer_file(self, filepath: str) -> bool:
        """Dosyayı sunucuya gönder"""
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"[ERR] Dosya bulunamadı: {filepath}")
            return False
        
        file_size = filepath.stat().st_size
        print(f"[OK] Dosya: {filepath.name} ({file_size:,} bytes)")
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Timeout on socket receive for the listener thread
        self.socket.settimeout(1.0)
        
        self.metrics = MetricsCalculator()
        
        try:
            # 1. Orijinal dosya hash'i
            file_hash = self._calculate_file_hash(str(filepath))
            
            # 2. Dosyayı belleğe al
            with open(filepath, 'rb') as f:
                full_data = f.read()
                
            # 3. Sıkıştırma
            if self.compress:
                print("[*] Veri sıkıştırılıyor (zlib)...")
                full_data = zlib.compress(full_data)
                
            # 4. Şifreleme
            if self.encrypt:
                print("[*] Veri şifreleniyor (XOR)...")
                key = b"NETPROBE_SECRET_KEY"
                encrypted = bytearray(len(full_data))
                for i in range(len(full_data)):
                    encrypted[i] = full_data[i] ^ key[i % len(key)]
                full_data = encrypted
                
            # 5. Paketlere böl
            packets_payload = []
            max_payload = Constants.MAX_PAYLOAD
            for i in range(0, len(full_data), max_payload):
                packets_payload.append(full_data[i:i+max_payload])
                
            total_packets = len(packets_payload)
            print(f"[OK] İşlem tamam, gönderilecek paket: {total_packets}")
            
            # 6. START paketini gönder
            self.logger.log_transfer_start(filepath.name, file_size)
            flags = 0
            if self.compress: flags |= 1
            if self.encrypt: flags |= 2
            
            self._send_start_packet(total_packets, flags, file_hash)
            
            # 7. Dashboard'u başlat
            if TransferDashboard:
                self.dashboard = TransferDashboard(filepath.name, total_packets, file_size)
                self.dashboard.start()
            
            self.is_transferring = True
            
            # 8. ACK Listener Thread başlat
            listener_thread = threading.Thread(target=self._ack_listener)
            listener_thread.daemon = True
            listener_thread.start()
            
            # 9. Ana Gönderim Döngüsü (Selective Repeat)
            next_seq_num = 0
            
            while self.window_base < total_packets and self.is_transferring:
                with self.lock:
                    # Pencere içinde gönderilmemiş yeni paket varsa gönder
                    while next_seq_num < self.window_base + self.window_size and next_seq_num < total_packets:
                        payload = packets_payload[next_seq_num]
                        self._send_data_packet(next_seq_num, total_packets, payload, 0)
                        self.unacked_packets[next_seq_num] = (payload, time.time(), 0)
                        next_seq_num += 1
                        
                    # Timeout kontrolü (Retransmission)
                    current_time = time.time()
                    for seq, (payload, send_time, retries) in list(self.unacked_packets.items()):
                        # Exponential backoff veya artan timeout (current_timeout = self.timeout + retries)
                        current_timeout = self.timeout + retries
                        
                        if current_time - send_time > current_timeout:
                            if retries >= self.max_retries:
                                self.failed_packets.append(seq)
                                self.metrics.record_failed_packet(seq)
                                self.logger.log_packet_failed(seq, self.max_retries)
                                del self.unacked_packets[seq]
                                
                                # Eger başarısız olan window_base ise, pencereyi ilerletmek zorundayız 
                                # yoksa deadlock olur.
                                if seq == self.window_base:
                                    self._advance_window(total_packets)
                            else:
                                # Tekrar gönder
                                self.logger.log_timeout(seq, retries + 1)
                                self.metrics.record_retry(seq)
                                self._send_data_packet(seq, total_packets, payload, retries + 1)
                                self.unacked_packets[seq] = (payload, current_time, retries + 1)
                                
                if self.dashboard:
                    with self.lock:
                        retransmissions = sum(self.metrics.retry_counts.values())
                        # Ortalama RTT hesabı
                        rtt_times = []
                        for seq_num in self.metrics.ack_times:
                            if seq_num in self.metrics.send_times:
                                rtt = (self.metrics.ack_times[seq_num] - self.metrics.send_times[seq_num]) * 1000
                                rtt_times.append(rtt)
                        avg_rtt = sum(rtt_times)/len(rtt_times) if rtt_times else 0.0
                        
                        self.dashboard.update(next_seq_num, len(self.acked_packets), retransmissions, avg_rtt)
                
                time.sleep(0.01)  # CPU yormamak için kısa uyku
            
            # Transfer döngüsü bitti
            self.is_transferring = False
            listener_thread.join(timeout=1.0)
            
            # 10. END paketini gönder
            self._send_end_packet(total_packets)
            
            if self.dashboard:
                self.dashboard.stop()
            
            # 11. Metrikler
            self.metrics.end_transfer()
            metrics = self.metrics.calculate_metrics(
                filename=filepath.name,
                file_size_bytes=file_size,
                packet_size=self.packet_size,
                total_packets=total_packets
            )
            
            MetricsWriter.print_metrics(metrics)
            MetricsWriter.save_json(metrics, "results/metrics.json")
            
            if self.failed_packets:
                print(f"\n[ERR] Başarısız paketler: {self.failed_packets}")
                self.logger.log_event(EventType.FAILED, status="WARNING", details=f"Başarısız paketler: {self.failed_packets}")
                return False
            
            print(f"\n[OK] Transfer başarılı!")
            self.logger.log_transfer_end(total_packets, len(self.acked_packets))
            return True
            
        except Exception as e:
            print(f"[ERR] Transfer hatası: {e}")
            import traceback
            traceback.print_exc()
            self.logger.log_error(-1, str(e))
            if self.dashboard:
                self.dashboard.stop()
            return False
        
        finally:
            self.is_transferring = False
            self.socket.close()
            self.logger.print_summary()

    def _ack_listener(self):
        """Asenkron olarak ACK ve NACK paketlerini dinleyen thread"""
        while self.is_transferring:
            try:
                data, _ = self.socket.recvfrom(256)
                packet_type = data[0]
                
                if packet_type == PacketType.ACK:
                    ack_pkt = AckPacket.deserialize(data)
                    seq_num = ack_pkt.ack_num
                    
                    with self.lock:
                        if seq_num in self.unacked_packets:
                            del self.unacked_packets[seq_num]
                            self.acked_packets.add(seq_num)
                            self.metrics.record_ack(seq_num)
                            self.logger.log_ack_received(seq_num)
                            
                            if seq_num == self.window_base:
                                self._advance_window(-1)
                                
                elif packet_type == PacketType.NACK:
                    nack_pkt = NackPacket.deserialize(data)
                    seq_num = nack_pkt.nack_num
                    
                    with self.lock:
                        if seq_num in self.unacked_packets:
                            # NACK geldi, hemen fast retransmit yap
                            payload, _, retries = self.unacked_packets[seq_num]
                            self.logger.log_error(seq_num, "NACK alındı, hızlı yeniden iletim")
                            self.metrics.record_retry(seq_num)
                            # total_packets bilgisini fonksiyona yollamiyoruz ama deserialize'da lazım.
                            # Hacky çözüm: StartPacket üzerinden zaten biliyoruz ama DataPacket'e lazım.
                            # Tuple'da tuttuğumuz sadece payload.
                            pass # Bir sonraki loop iteration'da timeout'a düşmesini beklemeden gönderebiliriz.
                            # Fakat total_packets'i listener thread bilmiyor. 
                            # Basitlik açısından NACK geldiğinde send_time'ı 0 yapalım, main thread timeout'a düşüp göndersin.
                            self.unacked_packets[seq_num] = (payload, 0, retries)
                            
            except socket.timeout:
                continue
            except Exception as e:
                # Bazen soket kapandığında hata fırlatır, sessizce devam et
                continue
                
    def _advance_window(self, total_packets):
        """Window_base'i ilerletebildiği kadar ilerletir"""
        while self.window_base in self.acked_packets or self.window_base in self.failed_packets:
            self.window_base += 1

    def _send_data_packet(self, seq_num: int, total_packets: int, payload: bytes, retries: int):
        """Tek bir veri paketini ağa gönderir"""
        pkt = DataPacket(seq_num=seq_num, total_packets=total_packets, payload=payload)
        data = pkt.serialize()
        self.socket.sendto(data, (self.host, self.port))
        
        if retries == 0:
            self.metrics.record_send(seq_num)
            self.logger.log_send(seq_num, len(payload))
            
    def _send_start_packet(self, total_packets: int, flags: int, file_hash: bytes):
        """Başlama paketini gönder"""
        start_pkt = StartPacket(total_packets=total_packets, flags=flags, file_hash=file_hash)
        data = start_pkt.serialize()
        self.socket.sendto(data, (self.host, self.port))
        print(f"[OK] START paketi gönderildi ({total_packets} paket)")
    
    def _send_end_packet(self, total_packets: int):
        """Bitiş paketini gönder"""
        end_pkt = EndPacket(total_packets=total_packets)
        data = end_pkt.serialize()
        self.socket.sendto(data, (self.host, self.port))
        print(f"[OK] END paketi gönderildi")
    
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

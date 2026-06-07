"""
NetProbe Lossy Server

Senaryo 3 için paket kaybı simülasyonu yapan sunucu versiyonu.
--loss-rate argümanı ile kayıp oranı ayarlanabilir.
"""

import socket
import argparse
import threading
import os
import hashlib
import sys
from pathlib import Path
from typing import Dict, Set

# Proje kök dizinini path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

from protocol import DataPacket, AckPacket, PacketType, StartPacket, EndPacket
from logger import get_logger, EventType
from metrics import MetricsCalculator, MetricsWriter
from loss_simulator import LossSimulator


class LossyNetProbeServer:
    """
    Paket kaybı simülasyonu yapan UDP dosya alım sunucusu.
    ACK'leri belirtilen olasılıkla düşürerek istemcinin retransmission mekanizmasını test eder.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5002,
                 output_dir: str = "received_files", loss_rate: float = 0.0):
        self.host = host
        self.port = port
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = get_logger()
        self.socket = None
        self.running = False
        self.loss_sim = LossSimulator(loss_rate=loss_rate, seed=42)
        
        # Transfer durumu
        self.current_seq_num = 0
        self.total_packets = 0
        self.received_packets: Set[int] = set()
        self.output_file = None
        self.output_filename = ""
        self.file_hash = b''
        
        self.metrics = MetricsCalculator()
        
        print(f"[OK] Lossy Server: kayıp oranı = %{loss_rate*100:.0f}")
    
    def start(self):
        """Sunucuyu başlat"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        
        self.running = True
        print(f"[OK] Lossy Sunucu başlatıldı: {self.host}:{self.port}")
        
        try:
            while self.running:
                try:
                    self.socket.settimeout(5.0)
                    data, client_addr = self.socket.recvfrom(2048)
                    
                    packet_type = data[0]
                    
                    if packet_type == PacketType.START:
                        self._handle_start_packet(data, client_addr)
                    elif packet_type == PacketType.DATA:
                        self._handle_data_packet(data, client_addr)
                    elif packet_type == PacketType.END:
                        self._handle_end_packet(data, client_addr)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.log_error(-1, str(e))
                    print(f"[ERR] Hata: {e}")
        
        except KeyboardInterrupt:
            print("\n[OK] Lossy Sunucu durduruldu")
        finally:
            self._print_loss_stats()
            self.stop()
    
    def _handle_start_packet(self, data: bytes, client_addr: tuple):
        """Başlama paketini işle"""
        try:
            start_pkt = StartPacket.deserialize(data)
            self.total_packets = start_pkt.total_packets
            self.file_hash = start_pkt.file_hash
            self.received_packets.clear()
            self.current_seq_num = 0
            self.loss_sim.reset()
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_filename = self.output_dir / f"lossy_transfer_{timestamp}.bin"
            self.output_file = open(self.output_filename, 'wb')
            
            print(f"[OK] Transfer başlandı: {self.total_packets} paket bekleniyor")
            
        except Exception as e:
            self.logger.log_error(-1, f"START paketi hatası: {e}")
    
    def _handle_data_packet(self, data: bytes, client_addr: tuple):
        """Veri paketini işle"""
        try:
            data_pkt = DataPacket.deserialize(data)
            seq_num = data_pkt.seq_num
            
            self.metrics.record_ack(seq_num)
            
            # Duplicate kontrol
            if seq_num in self.received_packets:
                self._send_ack_maybe(client_addr, seq_num)
                return
            
            # Yeni paket al
            self.received_packets.add(seq_num)
            self.output_file.write(data_pkt.payload)
            
            # ACK'i kayıp simülasyonuyla gönder
            self._send_ack_maybe(client_addr, seq_num)
            
        except Exception as e:
            self.logger.log_error(-1, f"DATA paketi hatası: {e}")
    
    def _send_ack_maybe(self, client_addr: tuple, ack_num: int):
        """
        ACK gönder veya kaybı simüle et.
        loss_sim.should_drop_ack() True dönerse ACK gönderilmez (paket kaybı).
        """
        if self.loss_sim.should_drop_ack(ack_num):
            # ACK düşürüldü - istemci timeout alacak ve retry yapacak
            print(f"  [LOSS SIM] ACK {ack_num} düşürüldü (kayıp simülasyonu)")
            return
        
        # Normal ACK gönder
        ack_pkt = AckPacket(ack_num=ack_num)
        ack_data = ack_pkt.serialize()
        self.socket.sendto(ack_data, client_addr)
    
    def _handle_end_packet(self, data: bytes, client_addr: tuple):
        """Bitiş paketini işle"""
        try:
            end_pkt = EndPacket.deserialize(data)
            total_packets = end_pkt.total_packets
            
            if self.output_file:
                self.output_file.close()
            
            # Hash doğrulaması
            file_hash = self._calculate_file_hash(str(self.output_filename))
            if file_hash == self.file_hash:
                print(f"[OK] Hash doğrulandı")
            else:
                print(f"[WARN] Hash uyuşmazlığı (kayıp paketler nedeniyle beklenen)")
            
            success_rate = (len(self.received_packets) / total_packets * 100) if total_packets > 0 else 0
            print(f"[OK] Transfer tamamlandı: {len(self.received_packets)}/{total_packets} paket (%{success_rate:.2f})")
            
            self.metrics.end_transfer()
            
        except Exception as e:
            self.logger.log_error(-1, f"END paketi hatası: {e}")
    
    def _calculate_file_hash(self, filepath: str) -> bytes:
        """Dosya SHA-256 hash'ini hesapla"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.digest()
    
    def _print_loss_stats(self):
        """Kayıp simülasyon istatistiklerini yazdır"""
        stats = self.loss_sim.get_stats()
        print(f"\n📊 Loss Simülasyon İstatistikleri:")
        print(f"  - Hedef Kayıp: %{stats['configured_loss_rate']:.0f}")
        print(f"  - Gerçek Kayıp: %{stats['actual_loss_rate']:.1f}")
        print(f"  - Düşürülen ACK: {stats['dropped_packets']}/{stats['total_packets']}")
    
    def stop(self):
        """Sunucuyu durdur"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.output_file and not self.output_file.closed:
            self.output_file.close()


def main():
    parser = argparse.ArgumentParser(description="NetProbe Lossy UDP Sunucu (Senaryo 3)")
    parser.add_argument("--host", default="0.0.0.0", help="Host adresi")
    parser.add_argument("--port", type=int, default=5002, help="Port")
    parser.add_argument("--output-dir", default="received_files", help="Çıkış dizini")
    parser.add_argument("--loss-rate", type=float, default=0.0,
                        help="Kayıp oranı (0.0-1.0, örn: 0.1 = %%10)")
    
    args = parser.parse_args()
    
    server = LossyNetProbeServer(
        host=args.host,
        port=args.port,
        output_dir=args.output_dir,
        loss_rate=args.loss_rate
    )
    server.start()


if __name__ == "__main__":
    main()

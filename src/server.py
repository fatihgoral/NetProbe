"""
NetProbe Server

UDP tabanlı dosya alım sunucusu
Gelen paketleri alır, doğrular ve dosyaya yazıyor
"""

import socket
import argparse
import threading
import os
import hashlib
from pathlib import Path
from typing import Dict, Set

from protocol import DataPacket, AckPacket, PacketType, StartPacket, EndPacket
from logger import get_logger, EventType
from metrics import MetricsCalculator, MetricsWriter
try:
    from loss_simulator import get_loss_simulator
except ImportError:
    get_loss_simulator = None


class NetProbeServer:
    """UDP tabanlı dosya alım sunucusu"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5000, output_dir: str = "received_files"):
        """
        Sunucuyu başlat
        
        Args:
            host: Dinlenecek host adresi
            port: Dinlenecek port
            output_dir: Alınan dosyaların kaydedileceği dizin
        """
        self.host = host
        self.port = port
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = get_logger()
        self.socket = None
        self.running = False
        
        # Transfer durumunu takip et
        self.current_seq_num = 0
        self.total_packets = 0
        self.received_packets: Set[int] = set()  # Alınan paket seq numaraları
        self.output_file = None
        self.output_filename = ""
        self.file_hash = b''
        
        # Metrikleri hesapla
        self.metrics = MetricsCalculator()
    
    def start(self):
        """Sunucuyu başlat"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        
        self.running = True
        print(f"✓ Sunucu başlatıldı: {self.host}:{self.port}")
        self.logger.log_event(EventType.START, status="OK", details=f"Sunucu açıldı: {self.host}:{self.port}")
        
        try:
            while self.running:
                try:
                    # Paket al (timeout: 5 saniye)
                    self.socket.settimeout(5.0)
                    data, client_addr = self.socket.recvfrom(2048)
                    
                    # Paket tipini belirle
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
                    print(f"✗ Hata: {e}")
        
        except KeyboardInterrupt:
            print("\n✓ Sunucu durduruldu")
        finally:
            self.stop()
    
    def _handle_start_packet(self, data: bytes, client_addr: tuple):
        """Başlama paketini işle"""
        try:
            start_pkt = StartPacket.deserialize(data)
            self.total_packets = start_pkt.total_packets
            self.file_hash = start_pkt.file_hash
            self.received_packets.clear()
            self.current_seq_num = 0
            
            # Dosya adını oluştur (timestamp'li)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_filename = self.output_dir / f"transfer_{timestamp}.bin"
            self.output_file = open(self.output_filename, 'wb')
            
            self.logger.log_event(
                EventType.START,
                status="OK",
                details=f"Transfer başlandı: {self.total_packets} paket bekleniyor"
            )
            print(f"✓ Transfer başlandı: {self.total_packets} paket bekleniyor")
            
        except Exception as e:
            self.logger.log_error(-1, f"START paketi hatası: {e}")
    
    def _handle_data_packet(self, data: bytes, client_addr: tuple):
        """Veri paketini işle"""
        try:
            data_pkt = DataPacket.deserialize(data)
            seq_num = data_pkt.seq_num
            
            # Metrics'e kaydet
            self.metrics.record_ack(seq_num)
            
            # Duplicate kontrol
            if seq_num in self.received_packets:
                self.logger.log_duplicate(seq_num)
                # ACK'i tekrar gönder (duplicate'i yok say)
                self._send_ack(client_addr, seq_num)
                return
            
            # Paket al
            self.received_packets.add(seq_num)
            self.output_file.write(data_pkt.payload)
            
            self.logger.log_event(
                EventType.ACK_RECEIVED,
                seq_num=seq_num,
                status="OK",
                details=f"Paket alındı: {len(data_pkt.payload)} bytes"
            )
            
            # ACK gönder
            self._send_ack(client_addr, seq_num)
            
        except Exception as e:
            self.logger.log_error(-1, f"DATA paketi hatası: {e}")
    
    def _handle_end_packet(self, data: bytes, client_addr: tuple):
        """Bitiş paketini işle"""
        try:
            end_pkt = EndPacket.deserialize(data)
            total_packets = end_pkt.total_packets
            
            # Dosyayı kapat
            if self.output_file:
                self.output_file.close()
            
            # Dosya hash'ini doğrula
            file_hash = self._calculate_file_hash(str(self.output_filename))
            if file_hash == self.file_hash:
                status = "OK"
                details = "Dosya hash'i doğrulandı"
            else:
                status = "WARNING"
                details = f"Hash uyuşmazlığı! Beklenen: {self.file_hash.hex()[:16]}..., Alınan: {file_hash.hex()[:16]}..."
            
            success_rate = (len(self.received_packets) / total_packets * 100) if total_packets > 0 else 0
            
            self.logger.log_event(
                EventType.END,
                status=status,
                details=f"Transfer tamamlandı: {len(self.received_packets)}/{total_packets} paket (%{success_rate:.2f})"
            )
            
            print(f"✓ Transfer tamamlandı")
            print(f"  Dosya: {self.output_filename}")
            print(f"  Paket: {len(self.received_packets)}/{total_packets} (%{success_rate:.2f})")
            
            self.metrics.end_transfer()
            
        except Exception as e:
            self.logger.log_error(-1, f"END paketi hatası: {e}")
    
    def _send_ack(self, client_addr: tuple, ack_num: int):
        """ACK paketi gönder (loss simulator aktifse paket kaybı simüle edilir)"""
        # Loss simulator kontrolü (Senaryo 3)
        if get_loss_simulator is not None:
            sim = get_loss_simulator()
            if sim.loss_rate > 0 and sim.should_drop_ack(ack_num):
                # ACK'i düşür (paket kaybı simülasyonu)
                self.logger.log_event(
                    EventType.DUPLICATE,
                    seq_num=ack_num,
                    status="DROPPED",
                    details=f"ACK {ack_num} simüle kayıp ile düşürüldü"
                )
                return
        
        ack_pkt = AckPacket(ack_num=ack_num)
        ack_data = ack_pkt.serialize()
        self.socket.sendto(ack_data, client_addr)
    
    def _calculate_file_hash(self, filepath: str) -> bytes:
        """Dosya SHA-256 hash'ini hesapla"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.digest()
    
    def stop(self):
        """Sunucuyu durdur"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.output_file and not self.output_file.closed:
            self.output_file.close()
        
        self.logger.print_summary()


def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description="NetProbe UDP Dosya Alım Sunucusu")
    parser.add_argument("--host", default="0.0.0.0", help="Dinlenecek host (varsayılan: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Dinlenecek port (varsayılan: 5000)")
    parser.add_argument("--output-dir", default="received_files", help="Çıkış dizini (varsayılan: received_files)")
    
    args = parser.parse_args()
    
    server = NetProbeServer(host=args.host, port=args.port, output_dir=args.output_dir)
    server.start()


if __name__ == "__main__":
    main()

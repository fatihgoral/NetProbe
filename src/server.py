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

from protocol import DataPacket, AckPacket, PacketType, StartPacket, EndPacket, NackPacket
from logger import get_logger, EventType, PcapWriter
from metrics import MetricsCalculator, MetricsWriter
try:
    from loss_simulator import get_loss_simulator
except ImportError:
    get_loss_simulator = None


class ClientSession:
    """Tek bir istemci oturumunun durumu"""
    def __init__(self, client_addr: tuple, output_dir: Path):
        self.addr = client_addr
        self.output_dir = output_dir
        self.expected_seq = 0
        self.received_packets: Dict[int, bytes] = {}
        self.total_expected_packets = 0
        self.file_hash = b""
        self.output_file = None
        self.metrics = MetricsCalculator()


class NetProbeServer:
    """UDP tabanlı dosya alım sunucusu"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5000, output_dir: str = "received_files", pcap_file: str = None):
        """
        Sunucuyu başlat
        
        Args:
            host: Dinlenecek host adresi
            port: Dinlenecek port
            output_dir: Alınan dosyaların kaydedileceği dizin
            pcap_file: Trafiği kaydetmek için PCAP dosyası (opsiyonel)
        """
        self.host = host
        self.port = port
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = get_logger()
        self.pcap_writer = PcapWriter(pcap_file) if pcap_file else None
        self.socket = None
        self.running = False
        
        # Her istemci için ayrı session state tutuyoruz
        self.sessions: Dict[tuple, ClientSession] = {}
        
        # Metrikleri hesapla
        self.metrics = MetricsCalculator()
    
    def start(self):
        """Sunucuyu başlat"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        
        self.running = True
        print(f"[OK] Sunucu başlatıldı: {self.host}:{self.port}")
        self.logger.log_event(EventType.START, status="OK", details=f"Sunucu açıldı: {self.host}:{self.port}")
        
        try:
            while self.running:
                try:
                    # Paket al (timeout: 5 saniye)
                    self.socket.settimeout(5.0)
                    data, client_addr = self.socket.recvfrom(2048)
                    
                    if self.pcap_writer:
                        self.pcap_writer.write_packet(client_addr[0], self.host, client_addr[1], self.port, data)
                    
                    # Session kontrolü/oluşturma
                    if client_addr not in self.sessions:
                        self.sessions[client_addr] = ClientSession(client_addr, self.output_dir)
                        
                    session = self.sessions[client_addr]
                    
                    # Paket tipini belirle
                    packet_type = data[0]
                    
                    if packet_type == PacketType.START:
                        self._handle_start_packet(data, session)
                    elif packet_type == PacketType.DATA:
                        self._handle_data_packet(data, session)
                    elif packet_type == PacketType.END:
                        self._handle_end_packet(data, session)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.log_error(-1, str(e))
                    print(f"[ERR] Hata: {e}")
        
        except KeyboardInterrupt:
            print("\n[OK] Sunucu durduruldu")
        finally:
            self.stop()
    
    def _handle_start_packet(self, data: bytes, session: ClientSession):
        """Başlangıç paketini işle"""
        start_pkt = StartPacket.deserialize(data)
        session.total_expected_packets = start_pkt.total_packets
        session.file_hash = start_pkt.file_hash
        session.expected_seq = 0
        session.received_packets.clear()
        
        print(f"\n[OK] Transfer başlıyor: {session.total_expected_packets} paket bekleniyor. İstemci: {session.addr}")
        self.logger.log_event(EventType.START, status="OK", details=f"Transfer başlandı: {session.total_expected_packets} paket bekleniyor")
        
    def _handle_data_packet(self, data: bytes, session: ClientSession):
        """Veri paketini işle"""
        try:
            data_pkt = DataPacket.deserialize(data)
        except ValueError as e:
            # Checksum hatası durumunda NACK gönder
            self.logger.log_error(-1, f"Paket hatası: {e}")
            self._send_nack(session.addr, session.expected_seq)
            return
            
        seq_num = data_pkt.seq_num
        payload = data_pkt.payload
        
        # Metrikleri kaydet
        session.metrics.record_ack(seq_num)
        
        # Paketi buffer'a kaydet
        if seq_num not in session.received_packets:
            session.received_packets[seq_num] = payload
            print(f"[OK] Paket alındı: {seq_num}/{session.total_expected_packets}")
        
        # ACK gönder
        self._send_ack(session.addr, seq_num)
        
    def _send_nack(self, client_addr: tuple, nack_num: int):
        """NACK paketi gönder"""
        nack_pkt = NackPacket(nack_num=nack_num)
        nack_data = nack_pkt.serialize()
        self.socket.sendto(nack_data, client_addr)
        if self.pcap_writer:
            self.pcap_writer.write_packet(self.host, client_addr[0], self.port, client_addr[1], nack_data)
    
    def _handle_end_packet(self, data: bytes, session: ClientSession):
        """Bitiş paketini işle"""
        end_pkt = EndPacket.deserialize(data)
        
        if end_pkt.total_packets == len(session.received_packets):
            print(f"\n[OK] Tüm paketler başarıyla alındı!")
            
            # Dosyayı kaydet
            filename = f"received_file_{session.addr[0]}_{session.addr[1]}.bin"
            session.output_file = session.output_dir / filename
            self._save_file(session)
            
            # Metrikleri hesapla
            session.metrics.end_transfer()
            
            self.logger.log_event(EventType.END, status="OK", details="Transfer başarıyla tamamlandı")
            
            # Session'ı temizle
            del self.sessions[session.addr]
        else:
            print(f"\n[ERR] Eksik paketler var! Alınan: {len(session.received_packets)}, Beklenen: {end_pkt.total_packets}")

    def _save_file(self, session: ClientSession):
        """Alınan paketleri dosyaya kaydet"""
        try:
            with open(session.output_file, 'wb') as f:
                for i in range(session.total_expected_packets):
                    f.write(session.received_packets[i])
                    
            print(f"[OK] Dosya kaydedildi: {session.output_file}")
            
            # Hash kontrolü
            calculated_hash = self._calculate_file_hash(str(session.output_file))
            if calculated_hash == session.file_hash:
                print("[OK] Dosya bütünlüğü doğrulandı (Hash eşleşiyor)")
            else:
                print("[ERR] Dosya bütünlüğü hatalı! Hash eşleşmiyor.")
                
        except Exception as e:
            print(f"[ERR] Dosya kaydetme hatası: {e}")

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
        if self.pcap_writer:
            self.pcap_writer.write_packet(self.host, client_addr[0], self.port, client_addr[1], ack_data)
    
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
    parser.add_argument("--pcap", type=str, help="Trafiği PCAP dosyasına kaydet")
    
    args = parser.parse_args()
    
    server = NetProbeServer(host=args.host, port=args.port, output_dir=args.output_dir, pcap_file=args.pcap)
    server.start()


if __name__ == "__main__":
    main()

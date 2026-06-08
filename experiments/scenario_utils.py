"""
NetProbe - Senaryo Yardimci Modulu

Tum senaryolar icin ortak altyapi:
- Sunucuyu ayni process'te thread olarak baslatir (port hazirlik garantisi)
- Her test icin temiz metrik toplar
- Basarili/basarisiz transferleri dogru ayirt eder
"""

import sys
import socket
import threading
import time
import json
import hashlib
import struct
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from protocol import DataPacket, AckPacket, PacketType, StartPacket, EndPacket
from loss_simulator import LossSimulator


class InProcessServer:
    """
    Senaryo testleri icin ayni process'te thread olarak calisan sunucu.
    - Port hazirligini garantiler (socket bind sonrasi thread baslatilinmaz)
    - Her test icin sifirlabilir
    - Loss simulator entegre
    """

    def __init__(self, port: int = 5000, loss_rate: float = 0.0):
        self.port = port
        self.loss_sim = LossSimulator(loss_rate=loss_rate)  # seed=None: her test bagimsiz rastgelelik
        self.socket = None
        self.thread = None
        self.running = False
        self.received_packets = set()
        self.total_packets = 0
        self.output_file = None
        self.output_path = None
        self.file_hash = b''
        self._ready = threading.Event()
        Path("received_files").mkdir(exist_ok=True)

    def _server_loop(self):
        """Sunucu dongusu (thread icerisinde)"""
        self._ready.set()  # Socket bind sonrasi hazir
        while self.running:
            try:
                self.socket.settimeout(0.5)
                data, addr = self.socket.recvfrom(2048)
                ptype = data[0]
                if ptype == PacketType.START:
                    self._on_start(data)
                elif ptype == PacketType.DATA:
                    self._on_data(data, addr)
                elif ptype == PacketType.END:
                    self._on_end(data)
            except socket.timeout:
                continue
            except Exception:
                if self.running:
                    pass  # Hatalari yut, test devam etsin

    def _on_start(self, data):
        pkt = StartPacket.deserialize(data)
        self.total_packets = pkt.total_packets
        self.file_hash = pkt.file_hash
        self.received_packets.clear()
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.output_path = Path("received_files") / f"test_{ts}.bin"
        self.output_file = open(self.output_path, 'wb')

    def _on_data(self, data, addr):
        try:
            pkt = DataPacket.deserialize(data)
            seq = pkt.seq_num
            if seq not in self.received_packets:
                self.received_packets.add(seq)
                if self.output_file and not self.output_file.closed:
                    self.output_file.write(pkt.payload)
            # Loss simulation: ACK'i dusurecek miyiz?
            if self.loss_sim.loss_rate > 0 and self.loss_sim.should_drop_ack(seq):
                return  # ACK gonderme, istemci timeout alacak
            ack = AckPacket(ack_num=seq)
            self.socket.sendto(ack.serialize(), addr)
        except Exception:
            pass

    def _on_end(self, data):
        if self.output_file and not self.output_file.closed:
            self.output_file.close()

    def start(self):
        """Sunucuyu baslat ve hazir olana kadar bekle"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)  # 4MB buffer
        self.socket.bind(("0.0.0.0", self.port))
        self.running = True
        self._ready.clear()
        self.thread = threading.Thread(target=self._server_loop, daemon=True)
        self.thread.start()
        self._ready.wait(timeout=2.0)  # Hazir olana kadar bekle

    def reset(self, loss_rate: float = None):
        """Bir sonraki test icin sifirla"""
        self.received_packets.clear()
        self.total_packets = 0
        if self.output_file and not self.output_file.closed:
            self.output_file.close()
        self.output_file = None
        self.output_path = None
        self.file_hash = b''
        if loss_rate is not None:
            self.loss_sim.set_loss_rate(loss_rate)
            self.loss_sim.reset()

    def stop(self):
        """Sunucuyu durdur"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        if self.thread:
            self.thread.join(timeout=3)


def run_single_transfer(host: str, port: int, filepath: Path,
                        packet_size: int = 1024,
                        timeout: float = 2.0,
                        max_retries: int = 5) -> dict:
    """
    Tek bir dosya transferi calistir ve metrikleri dondur.

    Returns:
        dict: Metrik sozlugu, veya None (basarisiz)
    """
    from logger import reset_logger
    from client import NetProbeClient

    reset_logger()

    client = NetProbeClient(
        host=host, port=port,
        packet_size=packet_size,
        timeout=timeout,
        max_retries=max_retries
    )

    success = client.transfer_file(str(filepath))

    # Metrikleri oku (sadece basariliysa)
    if success:
        try:
            with open("results/metrics.json", 'r') as f:
                return json.load(f)
        except Exception:
            return None
    return None


def avg_metrics(results: list) -> dict:
    """Metrik listesinin ortalamasini al"""
    if not results:
        return None
    keys = ['throughput_kbps', 'goodput_kbps', 'completion_time_seconds',
            'packet_loss_rate', 'retransmission_rate', 'avg_rtt_ms']
    out = {}
    for k in keys:
        vals = [r[k] for r in results if k in r]
        out[k] = sum(vals) / len(vals) if vals else 0.0
    out['tests'] = len(results)
    return out

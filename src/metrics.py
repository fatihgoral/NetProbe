"""
NetProbe Metrics Module

Performans metrikleri hesaplama ve raporlama
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


@dataclass
class TransferMetrics:
    """Transfer performans metrikleri"""
    filename: str = ""
    file_size_bytes: int = 0
    packet_size: int = 1024
    total_packets: int = 0
    transfer_time_seconds: float = 0.0
    throughput_kbps: float = 0.0
    goodput_kbps: float = 0.0
    packet_loss_rate: float = 0.0
    retransmission_rate: float = 0.0
    completion_time_seconds: float = 0.0
    avg_rtt_ms: float = 0.0
    successful_packets: int = 0
    failed_packets: int = 0
    timeout_count: int = 0
    retransmission_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Sözlüğe dönüştür"""
        return {
            'filename': self.filename,
            'file_size_bytes': self.file_size_bytes,
            'packet_size': self.packet_size,
            'total_packets': self.total_packets,
            'transfer_time_seconds': round(self.transfer_time_seconds, 2),
            'throughput_kbps': round(self.throughput_kbps, 2),
            'goodput_kbps': round(self.goodput_kbps, 2),
            'packet_loss_rate': round(self.packet_loss_rate, 2),
            'retransmission_rate': round(self.retransmission_rate, 2),
            'completion_time_seconds': round(self.completion_time_seconds, 2),
            'avg_rtt_ms': round(self.avg_rtt_ms, 2),
            'successful_packets': self.successful_packets,
            'failed_packets': self.failed_packets,
            'timeout_count': self.timeout_count,
            'retransmission_count': self.retransmission_count
        }


class MetricsCalculator:
    """Performans metrikleri hesapla"""
    
    def __init__(self):
        """Hesaplamacı başlat"""
        self.start_time: float = time.time()
        self.end_time: float = None
        self.send_times: Dict[int, float] = {}  # seq_num -> gönderme zamanı
        self.ack_times: Dict[int, float] = {}   # seq_num -> ACK alış zamanı
        self.retry_counts: Dict[int, int] = {}  # seq_num -> deneme sayısı
        self.failed_packets: List[int] = []     # Başarısız paket seq numaraları
    
    def record_send(self, seq_num: int):
        """Paket gönderişini kaydet"""
        self.send_times[seq_num] = time.time()
        if seq_num not in self.retry_counts:
            self.retry_counts[seq_num] = 0
    
    def record_ack(self, ack_num: int):
        """ACK alışını kaydet"""
        self.ack_times[ack_num] = time.time()
    
    def record_retry(self, seq_num: int):
        """Retry'ı kaydet"""
        if seq_num in self.retry_counts:
            self.retry_counts[seq_num] += 1
        else:
            self.retry_counts[seq_num] = 1
    
    def record_failed_packet(self, seq_num: int):
        """Başarısız paket kaydet"""
        self.failed_packets.append(seq_num)
    
    def end_transfer(self):
        """Transfer bitiş zamanını kaydet"""
        self.end_time = time.time()
    
    def calculate_metrics(self,
                         filename: str,
                         file_size_bytes: int,
                         packet_size: int,
                         total_packets: int) -> TransferMetrics:
        """
        Tüm metrikleri hesapla
        
        Args:
            filename: Dosya adı
            file_size_bytes: Dosya boyutu (bayt)
            packet_size: Paket boyutu (bayt)
            total_packets: Toplam paket sayısı
            
        Returns:
            TransferMetrics objesi
        """
        if self.end_time is None:
            self.end_transfer()
        
        transfer_time = self.end_time - self.start_time
        successful_packets = len(self.ack_times)
        failed_packets = len(self.failed_packets)
        
        # Throughput: Tüm gönderilen baytlar / zaman
        total_bytes_sent = total_packets * packet_size
        throughput_kbps = (total_bytes_sent * 8) / (transfer_time * 1000) if transfer_time > 0 else 0
        
        # Goodput: Sadece başarılı baytlar / zaman
        successful_bytes = successful_packets * packet_size
        goodput_kbps = (successful_bytes * 8) / (transfer_time * 1000) if transfer_time > 0 else 0
        
        # Packet Loss Rate
        packet_loss_rate = (failed_packets / total_packets * 100) if total_packets > 0 else 0
        
        # Retransmission Rate
        retransmission_count = sum(self.retry_counts.values())
        retransmission_rate = (retransmission_count / total_packets * 100) if total_packets > 0 else 0
        
        # Average RTT
        rtt_times = []
        for seq_num in self.ack_times:
            if seq_num in self.send_times:
                rtt = (self.ack_times[seq_num] - self.send_times[seq_num]) * 1000  # ms
                rtt_times.append(rtt)
        avg_rtt_ms = sum(rtt_times) / len(rtt_times) if rtt_times else 0
        
        # Timeout count (max retry'a ulaşan paketler)
        timeout_count = len(self.failed_packets)
        
        metrics = TransferMetrics(
            filename=filename,
            file_size_bytes=file_size_bytes,
            packet_size=packet_size,
            total_packets=total_packets,
            transfer_time_seconds=transfer_time,
            throughput_kbps=throughput_kbps,
            goodput_kbps=goodput_kbps,
            packet_loss_rate=packet_loss_rate,
            retransmission_rate=retransmission_rate,
            completion_time_seconds=transfer_time,
            avg_rtt_ms=avg_rtt_ms,
            successful_packets=successful_packets,
            failed_packets=failed_packets,
            timeout_count=timeout_count,
            retransmission_count=retransmission_count
        )
        
        return metrics


class MetricsWriter:
    """Metrikleri dosyaya yaz"""
    
    @staticmethod
    def save_json(metrics: TransferMetrics, filepath: str = "results/metrics.json"):
        """Metrikleri JSON'a kaydet"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(metrics.to_dict(), f, indent=2)
        
        print(f"✓ Metrikler kaydedildi: {filepath}")
    
    @staticmethod
    def save_csv(metrics_list: List[TransferMetrics], filepath: str = "results/metrics.csv"):
        """Birden fazla test'in metriklerini CSV'ye kaydet"""
        import csv
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        if not metrics_list:
            print("Kaydedilecek metrik yok!")
            return
        
        # CSV başlıkları
        headers = list(metrics_list[0].to_dict().keys())
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for metrics in metrics_list:
                writer.writerow(metrics.to_dict())
        
        print(f"✓ Metrikler kaydedildi: {filepath}")
    
    @staticmethod
    def print_metrics(metrics: TransferMetrics):
        """Metrikleri konsolda yazdır"""
        print("\n" + "="*60)
        print("TRANSFER PERFORMANSİ METRİKLERİ")
        print("="*60)
        print(f"Dosya: {metrics.filename}")
        print(f"Dosya Boyutu: {metrics.file_size_bytes:,} bytes ({metrics.file_size_bytes/1024/1024:.2f} MB)")
        print(f"Paket Boyutu: {metrics.packet_size} bytes")
        print(f"Toplam Paket: {metrics.total_packets}")
        print(f"\nHızlar:")
        print(f"  - Throughput: {metrics.throughput_kbps:.2f} Kbps ({metrics.throughput_kbps/1000:.2f} Mbps)")
        print(f"  - Goodput: {metrics.goodput_kbps:.2f} Kbps ({metrics.goodput_kbps/1000:.2f} Mbps)")
        print(f"\nZamanlama:")
        print(f"  - Transfer Süresi: {metrics.transfer_time_seconds:.2f} saniye")
        print(f"  - Ortalama RTT: {metrics.avg_rtt_ms:.2f} ms")
        print(f"\nGüvenilirlik:")
        print(f"  - Başarılı Paketler: {metrics.successful_packets}")
        print(f"  - Başarısız Paketler: {metrics.failed_packets}")
        print(f"  - Paket Kaybı: {metrics.packet_loss_rate:.2f}%")
        print(f"\nRetransmission:")
        print(f"  - Yeniden Gönderilen Paketler: {metrics.retransmission_count}")
        print(f"  - Retransmission Oranı: {metrics.retransmission_rate:.2f}%")
        print(f"  - Timeout Sayısı: {metrics.timeout_count}")
        print("="*60 + "\n")


def create_metrics_summary(metrics_list: List[TransferMetrics]) -> Dict[str, Any]:
    """
    Birden fazla test'in özet istatistiklerini oluştur
    
    Args:
        metrics_list: TransferMetrics listesi
        
    Returns:
        Özet istatistikleri içeren sözlük
    """
    if not metrics_list:
        return {}
    
    throughputs = [m.throughput_kbps for m in metrics_list]
    goodputs = [m.goodput_kbps for m in metrics_list]
    completion_times = [m.completion_time_seconds for m in metrics_list]
    packet_losses = [m.packet_loss_rate for m in metrics_list]
    
    summary = {
        'test_count': len(metrics_list),
        'avg_throughput_kbps': sum(throughputs) / len(throughputs),
        'avg_goodput_kbps': sum(goodputs) / len(goodputs),
        'avg_completion_time': sum(completion_times) / len(completion_times),
        'avg_packet_loss_rate': sum(packet_losses) / len(packet_losses),
        'min_throughput_kbps': min(throughputs),
        'max_throughput_kbps': max(throughputs),
        'min_completion_time': min(completion_times),
        'max_completion_time': max(completion_times),
    }
    
    return summary

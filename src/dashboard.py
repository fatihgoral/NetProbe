"""
NetProbe Real-time Dashboard

Transfer süresince hız, kayıp oranı ve ilerleme çubuğu gibi metriklerin 
konsolda canlı olarak gösterilmesini sağlayan rich tabanlı panel.
"""

from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.layout import Layout
from rich import box
import time

class TransferDashboard:
    def __init__(self, filename: str, total_packets: int, file_size: int):
        """
        Dashboard nesnesini oluşturur.

        Args:
            filename: Aktarılan dosyanın adı.
            total_packets: Toplam gönderilecek paket sayısı.
            file_size: Dosya boyutu (byte cinsinden).
        """
        self.filename = filename
        self.total_packets = total_packets
        self.file_size = file_size
        self.start_time = time.time()
        
        self.progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            TimeRemainingColumn()
        )
        self.task_id = self.progress.add_task("Transfer", total=self.total_packets)
        
        self.layout = Layout()
        self.live = Live(self._generate_layout(0, 0, 0, 0, 0.0), refresh_per_second=4)
        
    def _generate_layout(self, sent, acked, throughput, retransmissions, rtt):
        """Anlık metriklerle rich layout nesnesini oluşturur ve döner."""
        table = Table(box=box.ROUNDED, expand=True)
        table.add_column("Metrik", style="cyan")
        table.add_column("Değer", style="magenta")
        
        table.add_row("Dosya", self.filename)
        table.add_row("Boyut", f"{self.file_size / 1024 / 1024:.2f} MB")
        table.add_row("Gönderilen / Toplam", f"{sent} / {self.total_packets}")
        table.add_row("Onaylanan (ACK)", f"{acked}")
        table.add_row("Hız (Throughput)", f"{throughput:.2f} Mbps")
        table.add_row("Yeniden İletim (Retrans)", f"{retransmissions}")
        table.add_row("Ortalama RTT", f"{rtt:.2f} ms")
        
        panel = Panel(table, title="[bold green]NetProbe Transfer Durumu")
        
        self.layout.split_column(
            Layout(panel, size=12),
            Layout(Panel(self.progress, title="İlerleme", border_style="blue"))
        )
        return self.layout
        
    def start(self):
        """Canlı güncelleme panelini başlatır; transfer öncesi çağrılmalıdır."""
        self.live.start()
        
    def update(self, sent_packets: int, acked_packets: int, retransmissions: int, rtt_ms: float):
        """
        Transfer istatistiklerini günceller ve paneli yeniler.

        Args:
            sent_packets: Şimdiye kadar gönderilmiş toplam paket sayısı.
            acked_packets: ACK alınmış (onaylanmış) paket sayısı.
            retransmissions: Toplam yeniden gönderim sayısı.
            rtt_ms: Anlık ortalama RTT (milisaniye).
        """
        elapsed = time.time() - self.start_time
        throughput = 0.0
        if elapsed > 0:
            # packet_size ~1024 bytes
            throughput = (sent_packets * 1024 * 8) / (elapsed * 1000000)
            
        self.progress.update(self.task_id, completed=acked_packets)
        self.live.update(self._generate_layout(sent_packets, acked_packets, throughput, retransmissions, rtt_ms))
        
    def stop(self):
        """Canlı güncelleme panelini durdurur; transfer tamamlanınca çağrılmalıdır."""
        self.live.stop()

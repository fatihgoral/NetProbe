"""
NetProbe - Grafik Oluşturma Scripti

4 senaryonun sonuçlarından profesyonel grafikler oluşturur.
Çıktılar: reports/ klasörüne PNG formatında kaydedilir.
"""

import sys
import csv
import json
from pathlib import Path
from typing import List, Dict, Any

try:
    import matplotlib
    matplotlib.use('Agg')  # GUI olmadan çalış
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠ matplotlib veya numpy yüklü değil!")
    print("  Kurulum: pip install matplotlib numpy")


# ─── RENK PALETİ ────────────────────────────────────────────
COLORS = {
    'blue': '#2196F3',
    'green': '#4CAF50',
    'orange': '#FF9800',
    'red': '#F44336',
    'purple': '#9C27B0',
    'teal': '#009688',
    'bg_dark': '#1E1E2E',
    'bg_card': '#2A2A3E',
    'text': '#E0E0E0',
    'grid': '#3A3A4E'
}

ACCENT_COLORS = ['#4FC3F7', '#81C784', '#FFB74D', '#E57373', '#CE93D8']


def setup_style():
    """Grafik stilini ayarla"""
    plt.style.use('dark_background')
    plt.rcParams.update({
        'figure.facecolor': COLORS['bg_dark'],
        'axes.facecolor': COLORS['bg_card'],
        'axes.edgecolor': COLORS['grid'],
        'axes.labelcolor': COLORS['text'],
        'text.color': COLORS['text'],
        'xtick.color': COLORS['text'],
        'ytick.color': COLORS['text'],
        'grid.color': COLORS['grid'],
        'grid.alpha': 0.4,
        'font.family': 'DejaVu Sans',
        'font.size': 11,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'figure.dpi': 150,
        'savefig.dpi': 150,
        'savefig.bbox': 'tight',
        'savefig.facecolor': COLORS['bg_dark'],
    })


def read_csv(filepath: str) -> List[Dict[str, Any]]:
    """CSV dosyasını oku"""
    rows = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            converted = {}
            for k, v in row.items():
                try:
                    converted[k] = float(v)
                except ValueError:
                    converted[k] = v
            rows.append(converted)
    return rows


def add_value_labels(ax, bars, fmt='{:.1f}', color='white', fontsize=9):
    """Bar üzerine değer etiketleri ekle"""
    for bar in bars:
        height = bar.get_height()
        ax.annotate(fmt.format(height),
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    color=color, fontsize=fontsize, fontweight='bold')


def plot_scenario1(data_dir: str = "data", output_dir: str = "reports"):
    """Senaryo 1: Paket Boyutu vs Throughput/Goodput/Completion Time"""
    filepath = Path(data_dir) / "scenario1_results.csv"
    if not filepath.exists():
        print(f"⚠ Senaryo 1 verisi bulunamadı, atlanıyor.")
        return
    
    rows = read_csv(str(filepath))
    
    packet_sizes = [int(r['packet_size']) for r in rows]
    throughputs = [r['throughput_kbps'] for r in rows]
    goodputs = [r['goodput_kbps'] for r in rows]
    completion_times = [r['completion_time_seconds'] for r in rows]
    
    x = np.arange(len(packet_sizes))
    width = 0.35
    labels = [f"{s}B" for s in packet_sizes]
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Senaryo 1: Paket Boyutu Etkisi', fontsize=16, fontweight='bold',
                 color=COLORS['text'], y=1.02)
    
    # Grafik 1: Throughput vs Goodput
    ax1 = axes[0]
    bars1 = ax1.bar(x - width/2, throughputs, width, label='Throughput', 
                    color=COLORS['blue'], alpha=0.85, edgecolor='white', linewidth=0.5)
    bars2 = ax1.bar(x + width/2, goodputs, width, label='Goodput',
                    color=COLORS['green'], alpha=0.85, edgecolor='white', linewidth=0.5)
    
    add_value_labels(ax1, bars1, '{:.0f}')
    add_value_labels(ax1, bars2, '{:.0f}')
    
    ax1.set_xlabel('Paket Boyutu', fontweight='bold')
    ax1.set_ylabel('Bant Genişliği (Kbps)', fontweight='bold')
    ax1.set_title('Throughput ve Goodput', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.legend(loc='upper left')
    ax1.grid(axis='y', alpha=0.4)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # Grafik 2: Completion Time
    ax2 = axes[1]
    bars3 = ax2.bar(x, completion_times, color=COLORS['orange'], alpha=0.85,
                    edgecolor='white', linewidth=0.5)
    
    # Trend çizgisi
    if len(packet_sizes) > 1:
        z = np.polyfit(packet_sizes, completion_times, 1)
        p = np.poly1d(z)
        ax2.plot(x, p(packet_sizes), '--', color=COLORS['red'], linewidth=2,
                 label='Trend', alpha=0.8)
    
    add_value_labels(ax2, bars3, '{:.1f}s')
    
    ax2.set_xlabel('Paket Boyutu', fontweight='bold')
    ax2.set_ylabel('Tamamlanma Süresi (saniye)', fontweight='bold')
    ax2.set_title('Tamamlanma Süresi', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.4)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    plt.tight_layout()
    output_path = Path(output_dir) / "scenario1_paket_boyutu.png"
    plt.savefig(output_path)
    plt.close()
    print(f"✓ Grafik kaydedildi: {output_path}")


def plot_scenario2(data_dir: str = "data", output_dir: str = "reports"):
    """Senaryo 2: Timeout vs Retransmission Rate / Completion Time"""
    filepath = Path(data_dir) / "scenario2_results.csv"
    if not filepath.exists():
        print(f"⚠ Senaryo 2 verisi bulunamadı, atlanıyor.")
        return
    
    rows = read_csv(str(filepath))
    
    timeouts = [r['timeout_seconds'] for r in rows]
    retrans_rates = [r['retransmission_rate'] for r in rows]
    completion_times = [r['completion_time_seconds'] for r in rows]
    throughputs = [r['throughput_kbps'] for r in rows]
    
    x = np.arange(len(timeouts))
    labels = [f"{t:.1f}s" for t in timeouts]
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Senaryo 2: Timeout Değeri Etkisi', fontsize=16, fontweight='bold',
                 color=COLORS['text'], y=1.02)
    
    # Grafik 1: Retransmission Rate
    ax1 = axes[0]
    bars1 = ax1.bar(x, retrans_rates, color=COLORS['red'], alpha=0.85,
                    edgecolor='white', linewidth=0.5)
    add_value_labels(ax1, bars1, '{:.1f}%')
    
    ax1.set_xlabel('Timeout Değeri (saniye)', fontweight='bold')
    ax1.set_ylabel('Retransmission Oranı (%)', fontweight='bold')
    ax1.set_title('Timeout vs Retransmission Oranı', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.grid(axis='y', alpha=0.4)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # Açıklama notu
    ax1.annotate('Düşük timeout →\nyüksek gereksiz\nretransmission',
                 xy=(0, retrans_rates[0] if retrans_rates else 0),
                 xytext=(0.5, max(retrans_rates)*0.7 if retrans_rates else 1),
                 fontsize=9, color=COLORS['orange'],
                 arrowprops=dict(arrowstyle='->', color=COLORS['orange']))
    
    # Grafik 2: Completion Time
    ax2 = axes[1]
    bars2 = ax2.bar(x, completion_times, color=COLORS['purple'], alpha=0.85,
                    edgecolor='white', linewidth=0.5)
    add_value_labels(ax2, bars2, '{:.1f}s')
    
    ax2.set_xlabel('Timeout Değeri (saniye)', fontweight='bold')
    ax2.set_ylabel('Tamamlanma Süresi (saniye)', fontweight='bold')
    ax2.set_title('Timeout vs Tamamlanma Süresi', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.grid(axis='y', alpha=0.4)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    plt.tight_layout()
    output_path = Path(output_dir) / "scenario2_timeout.png"
    plt.savefig(output_path)
    plt.close()
    print(f"✓ Grafik kaydedildi: {output_path}")


def plot_scenario3(data_dir: str = "data", output_dir: str = "reports"):
    """Senaryo 3: Loss Rate vs Goodput / Completion Time / Retransmission"""
    filepath = Path(data_dir) / "scenario3_results.csv"
    if not filepath.exists():
        print(f"⚠ Senaryo 3 verisi bulunamadı, atlanıyor.")
        return
    
    rows = read_csv(str(filepath))
    
    loss_rates = [r['loss_rate_pct'] for r in rows]
    goodputs = [r['goodput_kbps'] for r in rows]
    throughputs = [r['throughput_kbps'] for r in rows]
    completion_times = [r['completion_time_seconds'] for r in rows]
    retrans_rates = [r['retransmission_rate'] for r in rows]
    
    x = np.arange(len(loss_rates))
    labels = [f"%{int(l)}" for l in loss_rates]
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Senaryo 3: Simüle Paket Kaybı Etkisi', fontsize=16, fontweight='bold',
                 color=COLORS['text'], y=1.02)
    
    # Grafik 1: Goodput vs Throughput
    ax1 = axes[0]
    width = 0.35
    bars1 = ax1.bar(x - width/2, throughputs, width, label='Throughput',
                    color=COLORS['blue'], alpha=0.85)
    bars2 = ax1.bar(x + width/2, goodputs, width, label='Goodput',
                    color=COLORS['green'], alpha=0.85)
    
    ax1.set_xlabel('Kayıp Oranı', fontweight='bold')
    ax1.set_ylabel('Bant Genişliği (Kbps)', fontweight='bold')
    ax1.set_title('Kayıp vs Goodput/Throughput', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.4)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # Grafik 2: Completion Time
    ax2 = axes[1]
    bars3 = ax2.bar(x, completion_times, color=COLORS['orange'], alpha=0.85,
                    edgecolor='white', linewidth=0.5)
    add_value_labels(ax2, bars3, '{:.1f}s')
    
    ax2.set_xlabel('Kayıp Oranı', fontweight='bold')
    ax2.set_ylabel('Tamamlanma Süresi (saniye)', fontweight='bold')
    ax2.set_title('Kayıp vs Tamamlanma Süresi', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.grid(axis='y', alpha=0.4)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    # Grafik 3: Retransmission Rate
    ax3 = axes[2]
    bars4 = ax3.bar(x, retrans_rates, color=COLORS['red'], alpha=0.85,
                    edgecolor='white', linewidth=0.5)
    add_value_labels(ax3, bars4, '{:.1f}%')
    
    ax3.set_xlabel('Kayıp Oranı', fontweight='bold')
    ax3.set_ylabel('Retransmission Oranı (%)', fontweight='bold')
    ax3.set_title('Kayıp vs Retransmission', fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels)
    ax3.grid(axis='y', alpha=0.4)
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    
    plt.tight_layout()
    output_path = Path(output_dir) / "scenario3_paket_kaybi.png"
    plt.savefig(output_path)
    plt.close()
    print(f"✓ Grafik kaydedildi: {output_path}")


def plot_scenario4(data_dir: str = "data", output_dir: str = "reports"):
    """Senaryo 4: Dosya Boyutu vs Completion Time / Throughput"""
    filepath = Path(data_dir) / "scenario4_results.csv"
    if not filepath.exists():
        print(f"⚠ Senaryo 4 verisi bulunamadı, atlanıyor.")
        return
    
    rows = read_csv(str(filepath))
    
    file_sizes_mb = [r['file_size_mb'] for r in rows]
    throughputs = [r['throughput_kbps'] for r in rows]
    goodputs = [r['goodput_kbps'] for r in rows]
    completion_times = [r['completion_time_seconds'] for r in rows]
    
    x = np.arange(len(file_sizes_mb))
    labels = [f"{int(s)}MB" for s in file_sizes_mb]
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Senaryo 4: Dosya Boyutu Etkisi', fontsize=16, fontweight='bold',
                 color=COLORS['text'], y=1.02)
    
    # Grafik 1: Completion Time (lineerlik göster)
    ax1 = axes[0]
    bars1 = ax1.bar(x, completion_times, color=COLORS['teal'], alpha=0.85,
                    edgecolor='white', linewidth=0.5)
    add_value_labels(ax1, bars1, '{:.1f}s')
    
    # Lineer fit çizgisi
    if len(file_sizes_mb) > 1:
        z = np.polyfit(file_sizes_mb, completion_times, 1)
        p = np.poly1d(z)
        xfine = np.linspace(0, max(file_sizes_mb), 100)
        ax1.plot(np.interp(xfine, file_sizes_mb, x) if False else 
                 np.linspace(0, len(x)-1, 100),
                 p(xfine), '--', color=COLORS['orange'], linewidth=2,
                 label='Lineer trend', alpha=0.9)
    
    ax1.set_xlabel('Dosya Boyutu', fontweight='bold')
    ax1.set_ylabel('Tamamlanma Süresi (saniye)', fontweight='bold')
    ax1.set_title('Dosya Boyutu vs Tamamlanma Süresi\n(Lineer ölçekleme bekleniyor)', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.4)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # Grafik 2: Throughput (istikrarı göster)
    ax2 = axes[1]
    width = 0.35
    bars2 = ax2.bar(x - width/2, throughputs, width, label='Throughput',
                    color=COLORS['blue'], alpha=0.85)
    bars3 = ax2.bar(x + width/2, goodputs, width, label='Goodput',
                    color=COLORS['green'], alpha=0.85)
    
    # Ortalama çizgisi
    avg_throughput = sum(throughputs) / len(throughputs) if throughputs else 0
    ax2.axhline(y=avg_throughput, color=COLORS['orange'], linestyle='--',
                linewidth=2, label=f'Ort. Throughput: {avg_throughput:.0f} Kbps')
    
    ax2.set_xlabel('Dosya Boyutu', fontweight='bold')
    ax2.set_ylabel('Bant Genişliği (Kbps)', fontweight='bold')
    ax2.set_title('Dosya Boyutu vs Throughput/Goodput\n(İstikrar bekleniyor)', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.legend(fontsize=9)
    ax2.grid(axis='y', alpha=0.4)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    plt.tight_layout()
    output_path = Path(output_dir) / "scenario4_dosya_boyutu.png"
    plt.savefig(output_path)
    plt.close()
    print(f"✓ Grafik kaydedildi: {output_path}")


def plot_summary_dashboard(data_dir: str = "data", output_dir: str = "reports"):
    """
    Tüm senaryoları tek bir dashboard grafiğine sığdır.
    Sunum için ideal.
    """
    fig = plt.figure(figsize=(20, 12))
    fig.suptitle('NetProbe - Performans Analizi Özeti', fontsize=20, fontweight='bold',
                 color=COLORS['text'], y=0.98)
    
    gs = gridspec.GridSpec(2, 4, figure=fig, hspace=0.45, wspace=0.35)
    
    axes_created = 0
    
    # Senaryo 1 - Throughput
    s1_file = Path(data_dir) / "scenario1_results.csv"
    if s1_file.exists():
        rows = read_csv(str(s1_file))
        packet_sizes = [int(r['packet_size']) for r in rows]
        throughputs = [r['throughput_kbps'] for r in rows]
        
        ax = fig.add_subplot(gs[0, 0])
        bars = ax.bar(range(len(packet_sizes)), throughputs, color=COLORS['blue'], alpha=0.85)
        ax.set_title('S1: Paket Boyutu\nvs Throughput', fontsize=11, fontweight='bold')
        ax.set_xticks(range(len(packet_sizes)))
        ax.set_xticklabels([f"{s}B" for s in packet_sizes], fontsize=8)
        ax.set_ylabel('Throughput (Kbps)', fontsize=9)
        ax.grid(axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    # Senaryo 1 - Completion Time
    if s1_file.exists():
        rows = read_csv(str(s1_file))
        packet_sizes = [int(r['packet_size']) for r in rows]
        completion_times = [r['completion_time_seconds'] for r in rows]
        
        ax = fig.add_subplot(gs[0, 1])
        ax.bar(range(len(packet_sizes)), completion_times, color=COLORS['teal'], alpha=0.85)
        ax.set_title('S1: Paket Boyutu\nvs Süre', fontsize=11, fontweight='bold')
        ax.set_xticks(range(len(packet_sizes)))
        ax.set_xticklabels([f"{s}B" for s in packet_sizes], fontsize=8)
        ax.set_ylabel('Süre (s)', fontsize=9)
        ax.grid(axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    # Senaryo 2
    s2_file = Path(data_dir) / "scenario2_results.csv"
    if s2_file.exists():
        rows = read_csv(str(s2_file))
        timeouts = [r['timeout_seconds'] for r in rows]
        retrans = [r['retransmission_rate'] for r in rows]
        
        ax = fig.add_subplot(gs[0, 2])
        ax.bar(range(len(timeouts)), retrans, color=COLORS['red'], alpha=0.85)
        ax.set_title('S2: Timeout\nvs Retransmission', fontsize=11, fontweight='bold')
        ax.set_xticks(range(len(timeouts)))
        ax.set_xticklabels([f"{t:.1f}s" for t in timeouts], fontsize=8)
        ax.set_ylabel('Retrans (%)', fontsize=9)
        ax.grid(axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    # Senaryo 2 Completion Time
    if s2_file.exists():
        rows = read_csv(str(s2_file))
        timeouts = [r['timeout_seconds'] for r in rows]
        completion = [r['completion_time_seconds'] for r in rows]
        
        ax = fig.add_subplot(gs[0, 3])
        ax.bar(range(len(timeouts)), completion, color=COLORS['purple'], alpha=0.85)
        ax.set_title('S2: Timeout\nvs Süre', fontsize=11, fontweight='bold')
        ax.set_xticks(range(len(timeouts)))
        ax.set_xticklabels([f"{t:.1f}s" for t in timeouts], fontsize=8)
        ax.set_ylabel('Süre (s)', fontsize=9)
        ax.grid(axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    # Senaryo 3
    s3_file = Path(data_dir) / "scenario3_results.csv"
    if s3_file.exists():
        rows = read_csv(str(s3_file))
        loss_rates = [r['loss_rate_pct'] for r in rows]
        goodputs = [r['goodput_kbps'] for r in rows]
        
        ax = fig.add_subplot(gs[1, 0:2])
        ax.bar(range(len(loss_rates)), goodputs, color=COLORS['green'], alpha=0.85,
               width=0.5)
        ax.set_title('S3: Kayıp Oranı vs Goodput', fontsize=11, fontweight='bold')
        ax.set_xticks(range(len(loss_rates)))
        ax.set_xticklabels([f"%{int(l)}" for l in loss_rates])
        ax.set_ylabel('Goodput (Kbps)', fontsize=9)
        ax.set_xlabel('Kayıp Oranı', fontsize=9)
        ax.grid(axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    # Senaryo 4
    s4_file = Path(data_dir) / "scenario4_results.csv"
    if s4_file.exists():
        rows = read_csv(str(s4_file))
        file_sizes = [r['file_size_mb'] for r in rows]
        completion = [r['completion_time_seconds'] for r in rows]
        
        ax = fig.add_subplot(gs[1, 2:4])
        ax.bar(range(len(file_sizes)), completion, color=COLORS['orange'], alpha=0.85,
               width=0.5)
        ax.set_title('S4: Dosya Boyutu vs Tamamlanma Süresi', fontsize=11, fontweight='bold')
        ax.set_xticks(range(len(file_sizes)))
        ax.set_xticklabels([f"{int(s)}MB" for s in file_sizes])
        ax.set_ylabel('Süre (s)', fontsize=9)
        ax.set_xlabel('Dosya Boyutu', fontsize=9)
        ax.grid(axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    output_path = Path(output_dir) / "netprobe_dashboard.png"
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"✓ Dashboard kaydedildi: {output_path}")


def main():
    """Tüm grafikleri oluştur"""
    if not HAS_MATPLOTLIB:
        print("❌ matplotlib/numpy kurulu değil. Grafik oluşturulamıyor.")
        print("   Kurulum: pip install matplotlib numpy seaborn pandas")
        sys.exit(1)
    
    data_dir = "data"
    output_dir = "reports"
    
    Path(output_dir).mkdir(exist_ok=True)
    setup_style()
    
    print("\n" + "="*60)
    print("NETPROBE - GRAFİK OLUŞTURMA")
    print("="*60)
    
    plot_scenario1(data_dir, output_dir)
    plot_scenario2(data_dir, output_dir)
    plot_scenario3(data_dir, output_dir)
    plot_scenario4(data_dir, output_dir)
    plot_summary_dashboard(data_dir, output_dir)
    
    print(f"\n✓ Tüm grafikler {output_dir}/ klasörüne kaydedildi!")
    print("  - scenario1_paket_boyutu.png")
    print("  - scenario2_timeout.png")
    print("  - scenario3_paket_kaybi.png")
    print("  - scenario4_dosya_boyutu.png")
    print("  - netprobe_dashboard.png")


if __name__ == "__main__":
    main()

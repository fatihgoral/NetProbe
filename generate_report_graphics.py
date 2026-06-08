"""
NetProbe Teknik Rapor - Grafik Üretim Scripti

Test sonuçlarından profesyonel grafikler oluşturur
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import json

# Grafik stilini ayarla
sns.set_style("whitegrid")
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'DejaVu Sans'

# Veri yolları
data_dir = Path("data")
results_dir = Path("reports/graphics")
results_dir.mkdir(parents=True, exist_ok=True)

# ============================================================================
# SENARYO 1: Paket Boyutunun Etkisi
# ============================================================================
print("📊 Senaryo 1: Paket Boyutunun Etkisi - Grafikler üretiliyor...")

df1 = pd.read_csv(data_dir / "scenario1_results.csv")

# Grafik 1.1: Throughput vs Paket Boyutu
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Senaryo 1: Paket Boyutunun Etkileri', fontsize=16, fontweight='bold')

ax = axes[0, 0]
bars = ax.bar(df1['packet_size'].astype(str), df1['throughput_kbps'], 
              color=sns.color_palette("husl", len(df1)), alpha=0.8, edgecolor='black')
ax.set_xlabel('Paket Boyutu (bytes)', fontweight='bold')
ax.set_ylabel('Throughput (Kbps)', fontweight='bold')
ax.set_title('Throughput vs Paket Boyutu')
ax.grid(axis='y', alpha=0.3)
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.0f}', ha='center', va='bottom', fontweight='bold')

# Grafik 1.2: Goodput vs Paket Boyutu
ax = axes[0, 1]
bars = ax.bar(df1['packet_size'].astype(str), df1['goodput_kbps'], 
              color=sns.color_palette("husl", len(df1)), alpha=0.8, edgecolor='black')
ax.set_xlabel('Paket Boyutu (bytes)', fontweight='bold')
ax.set_ylabel('Goodput (Kbps)', fontweight='bold')
ax.set_title('Goodput vs Paket Boyutu')
ax.grid(axis='y', alpha=0.3)
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.0f}', ha='center', va='bottom', fontweight='bold')

# Grafik 1.3: Tamamlanma Süresi vs Paket Boyutu
ax = axes[1, 0]
ax.plot(df1['packet_size'], df1['completion_time_seconds'], 
        marker='o', markersize=10, linewidth=2.5, color='#FF6B6B', label='Tamamlanma Süresi')
ax.fill_between(df1['packet_size'], df1['completion_time_seconds'], alpha=0.3, color='#FF6B6B')
ax.set_xlabel('Paket Boyutu (bytes)', fontweight='bold')
ax.set_ylabel('Tamamlanma Süresi (saniye)', fontweight='bold')
ax.set_title('Tamamlanma Süresi vs Paket Boyutu')
ax.grid(True, alpha=0.3)

# Grafik 1.4: Ortalama RTT vs Paket Boyutu
ax = axes[1, 1]
ax.plot(df1['packet_size'], df1['avg_rtt_ms'], 
        marker='s', markersize=10, linewidth=2.5, color='#4ECDC4', label='Ortalama RTT')
ax.fill_between(df1['packet_size'], df1['avg_rtt_ms'], alpha=0.3, color='#4ECDC4')
ax.set_xlabel('Paket Boyutu (bytes)', fontweight='bold')
ax.set_ylabel('Ortalama RTT (ms)', fontweight='bold')
ax.set_title('Ortalama RTT vs Paket Boyutu')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(results_dir / "scenario1_packet_size_effects.png", dpi=300, bbox_inches='tight')
print("✓ Senaryo 1 grafikleri kaydedildi")
plt.close()

# ============================================================================
# SENARYO 2: Timeout Değerinin Etkisi
# ============================================================================
print("📊 Senaryo 2: Timeout Değerinin Etkisi - Grafikler üretiliyor...")

df2 = pd.read_csv(data_dir / "scenario2_results.csv")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Senaryo 2: Timeout Değerinin Etkileri', fontsize=16, fontweight='bold')

# Grafik 2.1: Throughput vs Timeout
ax = axes[0, 0]
bars = ax.bar(df2['timeout_seconds'].astype(str), df2['throughput_kbps'], 
              color=sns.color_palette("RdYlGn_r", len(df2)), alpha=0.8, edgecolor='black')
ax.set_xlabel('Timeout (saniye)', fontweight='bold')
ax.set_ylabel('Throughput (Kbps)', fontweight='bold')
ax.set_title('Throughput vs Timeout Değeri')
ax.grid(axis='y', alpha=0.3)
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.0f}', ha='center', va='bottom', fontweight='bold')

# Grafik 2.2: Tamamlanma Süresi vs Timeout
ax = axes[0, 1]
ax.plot(df2['timeout_seconds'], df2['completion_time_seconds'], 
        marker='o', markersize=10, linewidth=2.5, color='#FF6B6B')
ax.fill_between(df2['timeout_seconds'], df2['completion_time_seconds'], alpha=0.3, color='#FF6B6B')
ax.set_xlabel('Timeout (saniye)', fontweight='bold')
ax.set_ylabel('Tamamlanma Süresi (saniye)', fontweight='bold')
ax.set_title('Tamamlanma Süresi vs Timeout')
ax.grid(True, alpha=0.3)

# Grafik 2.3: Retransmission Rate vs Timeout
ax = axes[1, 0]
bars = ax.bar(df2['timeout_seconds'].astype(str), df2['retransmission_rate'], 
              color=sns.color_palette("YlOrRd", len(df2)), alpha=0.8, edgecolor='black')
ax.set_xlabel('Timeout (saniye)', fontweight='bold')
ax.set_ylabel('Retransmission Rate (%)', fontweight='bold')
ax.set_title('Yeniden Gönderim Oranı vs Timeout')
ax.grid(axis='y', alpha=0.3)
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.2f}%', ha='center', va='bottom', fontweight='bold')

# Grafik 2.4: Ortalama RTT vs Timeout
ax = axes[1, 1]
ax.plot(df2['timeout_seconds'], df2['avg_rtt_ms'], 
        marker='s', markersize=10, linewidth=2.5, color='#4ECDC4')
ax.fill_between(df2['timeout_seconds'], df2['avg_rtt_ms'], alpha=0.3, color='#4ECDC4')
ax.set_xlabel('Timeout (saniye)', fontweight='bold')
ax.set_ylabel('Ortalama RTT (ms)', fontweight='bold')
ax.set_title('Ortalama RTT vs Timeout')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(results_dir / "scenario2_timeout_effects.png", dpi=300, bbox_inches='tight')
print("✓ Senaryo 2 grafikleri kaydedildi")
plt.close()

# ============================================================================
# SENARYO 3: Paket Kaybı Oranının Etkisi
# ============================================================================
print("📊 Senaryo 3: Paket Kaybı Oranının Etkisi - Grafikler üretiliyor...")

df3 = pd.read_csv(data_dir / "scenario3_results.csv")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Senaryo 3: Simüle Edilen Paket Kaybı Oranının Etkileri', fontsize=16, fontweight='bold')

# Grafik 3.1: Goodput vs Simüle Paket Kaybı
ax = axes[0, 0]
bars = ax.bar(df3['loss_rate_pct'].astype(int).astype(str) + '%', df3['goodput_kbps'], 
              color=sns.color_palette("YlGnBu_r", len(df3)), alpha=0.8, edgecolor='black')
ax.set_xlabel('Simüle Edilen Kaybı Oranı', fontweight='bold')
ax.set_ylabel('Goodput (Kbps)', fontweight='bold')
ax.set_title('Goodput vs Simüle Kaybı Oranı')
ax.grid(axis='y', alpha=0.3)
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.0f}', ha='center', va='bottom', fontweight='bold')

# Grafik 3.2: Retransmission Rate vs Simüle Paket Kaybı
ax = axes[0, 1]
bars = ax.bar(df3['loss_rate_pct'].astype(int).astype(str) + '%', df3['retransmission_rate'], 
              color=sns.color_palette("Reds", len(df3)), alpha=0.8, edgecolor='black')
ax.set_xlabel('Simüle Edilen Kaybı Oranı', fontweight='bold')
ax.set_ylabel('Retransmission Rate (%)', fontweight='bold')
ax.set_title('Yeniden Gönderim Oranı vs Simüle Kaybı')
ax.grid(axis='y', alpha=0.3)
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.2f}%', ha='center', va='bottom', fontweight='bold')

# Grafik 3.3: Tamamlanma Süresi vs Simüle Paket Kaybı
ax = axes[1, 0]
ax.plot(df3['loss_rate_pct'], df3['completion_time_seconds'], 
        marker='o', markersize=10, linewidth=2.5, color='#FF6B6B')
ax.fill_between(df3['loss_rate_pct'], df3['completion_time_seconds'], alpha=0.3, color='#FF6B6B')
ax.set_xlabel('Simüle Edilen Kaybı Oranı (%)', fontweight='bold')
ax.set_ylabel('Tamamlanma Süresi (saniye)', fontweight='bold')
ax.set_title('Tamamlanma Süresi vs Simüle Kaybı')
ax.grid(True, alpha=0.3)

# Grafik 3.4: Ortalama RTT vs Kayıp Oranı
ax = axes[1, 1]
ax.plot(df3['loss_rate_pct'], df3['avg_rtt_ms'],
        marker='D', markersize=10, linewidth=2.5, color='#FFD166')
ax.fill_between(df3['loss_rate_pct'], df3['avg_rtt_ms'], alpha=0.3, color='#FFD166')
ax.set_xlabel('Simüle Edilen Kayıp Oranı (%)', fontweight='bold')
ax.set_ylabel('Ortalama RTT (ms)', fontweight='bold')
ax.set_title('Kayıp Oranı vs Ortalama RTT')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(results_dir / "scenario3_loss_rate_effects.png", dpi=300, bbox_inches='tight')
print("✓ Senaryo 3 grafikleri kaydedildi")
plt.close()

# ============================================================================
# SENARYO 4: Dosya Boyutunun Etkisi
# ============================================================================
print("📊 Senaryo 4: Dosya Boyutunun Etkisi - Grafikler üretiliyor...")

df4 = pd.read_csv(data_dir / "scenario4_results.csv")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Senaryo 4: Farklı Dosya Boyutlarının Etkileri', fontsize=16, fontweight='bold')

# Dosya boyutlarını daha okunabilir forma dönüştür
file_labels = [f"{int(size)}MB" for size in df4['file_size_mb']]

# Grafik 4.1: Throughput vs Dosya Boyutu
ax = axes[0, 0]
bars = ax.bar(file_labels, df4['throughput_kbps'], 
              color=sns.color_palette("coolwarm", len(df4)), alpha=0.8, edgecolor='black')
ax.set_xlabel('Dosya Boyutu', fontweight='bold')
ax.set_ylabel('Throughput (Kbps)', fontweight='bold')
ax.set_title('Throughput vs Dosya Boyutu')
ax.grid(axis='y', alpha=0.3)
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.0f}', ha='center', va='bottom', fontweight='bold')

# Grafik 4.2: Tamamlanma Süresi vs Dosya Boyutu
ax = axes[0, 1]
ax.plot(df4['file_size_mb'], df4['completion_time_seconds'], 
        marker='o', markersize=10, linewidth=2.5, color='#4ECDC4')
ax.fill_between(df4['file_size_mb'], df4['completion_time_seconds'], alpha=0.3, color='#4ECDC4')
ax.set_xlabel('Dosya Boyutu (MB)', fontweight='bold')
ax.set_ylabel('Tamamlanma Süresi (saniye)', fontweight='bold')
ax.set_title('Tamamlanma Süresi vs Dosya Boyutu')
ax.grid(True, alpha=0.3)

# Grafik 4.3: Goodput vs Dosya Boyutu
ax = axes[1, 0]
bars = ax.bar(file_labels, df4['goodput_kbps'], 
              color=sns.color_palette("viridis", len(df4)), alpha=0.8, edgecolor='black')
ax.set_xlabel('Dosya Boyutu', fontweight='bold')
ax.set_ylabel('Goodput (Kbps)', fontweight='bold')
ax.set_title('Goodput vs Dosya Boyutu')
ax.grid(axis='y', alpha=0.3)
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.0f}', ha='center', va='bottom', fontweight='bold')

# Grafik 4.4: Toplam İletişim Süresi (çizgi grafik)
ax = axes[1, 1]
ax.plot(df4['file_size_mb'], df4['completion_time_seconds'], 
        marker='s', markersize=10, linewidth=2.5, color='#FF6B6B', label='Toplam Süre')
ax.set_xlabel('Dosya Boyutu (MB)', fontweight='bold')
ax.set_ylabel('Süre (saniye)', fontweight='bold')
ax.set_title('Transfer Süresi Ölçeklenebilirliği')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(results_dir / "scenario4_file_size_effects.png", dpi=300, bbox_inches='tight')
print("✓ Senaryo 4 grafikleri kaydedildi")
plt.close()

# ============================================================================
# KARŞILAŞTIRMA GRAFİKLERİ
# ============================================================================
print("📊 Karşılaştırma grafikleri üretiliyor...")

# Genel Performans Özeti
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Genel Performans Özeti', fontsize=16, fontweight='bold')

# Grafik: Senaryo 1 - Best Packet Size
ax = axes[0, 0]
best_idx1 = df1['throughput_kbps'].idxmax()
scenario1_best = df1.loc[best_idx1]
ax.text(0.5, 0.7, 'Senaryo 1: En İyi Paket Boyutu', 
        ha='center', va='center', fontsize=12, fontweight='bold', transform=ax.transAxes)
ax.text(0.5, 0.5, f"Paket Boyutu: {int(scenario1_best['packet_size'])} bytes\nThroughput: {scenario1_best['throughput_kbps']:.0f} Kbps\nGoodput: {scenario1_best['goodput_kbps']:.0f} Kbps",
        ha='center', va='center', fontsize=11, transform=ax.transAxes, 
        bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
ax.axis('off')

# Grafik: Senaryo 2 - Best Timeout
ax = axes[0, 1]
best_idx2 = df2['throughput_kbps'].idxmax()
scenario2_best = df2.loc[best_idx2]
ax.text(0.5, 0.7, 'Senaryo 2: En İyi Timeout', 
        ha='center', va='center', fontsize=12, fontweight='bold', transform=ax.transAxes)
ax.text(0.5, 0.5, f"Timeout: {scenario2_best['timeout_seconds']} sn\nThroughput: {scenario2_best['throughput_kbps']:.0f} Kbps\nRetransmission: {scenario2_best['retransmission_rate']:.2f}%",
        ha='center', va='center', fontsize=11, transform=ax.transAxes,
        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
ax.axis('off')

# Grafik: Senaryo 3 - Loss Rate Impact
ax = axes[1, 0]
ax.text(0.5, 0.7, 'Senaryo 3: Paket Kaybının Etkisi', 
        ha='center', va='center', fontsize=12, fontweight='bold', transform=ax.transAxes)
ax.text(0.5, 0.5, f"Simüle Edilen Max Kayıp: {df3['loss_rate_pct'].max()}%\nGerçek Max Kayıp: {df3['actual_packet_loss_pct'].max()}%\nRetransmission Rate: {df3['retransmission_rate'].mean():.2f}%",
        ha='center', va='center', fontsize=11, transform=ax.transAxes,
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
ax.axis('off')

# Grafik: Senaryo 4 - File Size Scalability
ax = axes[1, 1]
ax.text(0.5, 0.7, 'Senaryo 4: Dosya Boyutu Ölçeklenebilirliği', 
        ha='center', va='center', fontsize=12, fontweight='bold', transform=ax.transAxes)
max_file = df4['file_size_mb'].max()
max_time = df4['completion_time_seconds'].max()
ax.text(0.5, 0.5, f"Max Dosya: {int(max_file)} MB\nMax Süre: {max_time:.2f} saniye\nAvg Throughput: {df4['throughput_kbps'].mean():.0f} Kbps",
        ha='center', va='center', fontsize=11, transform=ax.transAxes,
        bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.7))
ax.axis('off')

plt.tight_layout()
plt.savefig(results_dir / "summary_performance_metrics.png", dpi=300, bbox_inches='tight')
print("✓ Özet grafikleri kaydedildi")
plt.close()

print("\n✅ Tüm grafikler başarıyla oluşturuldu!")
print(f"📁 Grafikler kaydedildi: {results_dir}")

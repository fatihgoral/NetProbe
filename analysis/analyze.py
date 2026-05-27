"""
NetProbe - Veri Analiz Scripti

4 senaryonun CSV çıktılarını okuyarak istatistiksel analiz yapar.
"""

import csv
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any


def read_csv(filepath: str) -> List[Dict[str, Any]]:
    """CSV dosyasını oku ve satırları dict listesi olarak döndür"""
    rows = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Sayısal değerlere dönüştür
            converted = {}
            for k, v in row.items():
                try:
                    converted[k] = float(v)
                except ValueError:
                    converted[k] = v
            rows.append(converted)
    return rows


def mean(values: List[float]) -> float:
    """Ortalama hesapla"""
    return sum(values) / len(values) if values else 0.0


def std_dev(values: List[float]) -> float:
    """Standart sapma hesapla"""
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    variance = sum((x - avg) ** 2 for x in values) / len(values)
    return variance ** 0.5


def analyze_scenario1(data_dir: str = "data") -> Dict:
    """Senaryo 1: Paket boyutu etkisi analizi"""
    filepath = Path(data_dir) / "scenario1_results.csv"
    
    if not filepath.exists():
        print(f"⚠ Senaryo 1 verisi bulunamadı: {filepath}")
        return {}
    
    rows = read_csv(str(filepath))
    
    print("\n" + "="*70)
    print("SENARYO 1 ANALİZİ: PAKET BOYUTU ETKİSİ")
    print("="*70)
    print(f"{'Paket Boyutu':>15} {'Throughput (Kbps)':>20} {'Goodput (Kbps)':>18} {'Süre (s)':>12} {'Kayıp (%)':>12}")
    print("-"*80)
    
    analysis = {'scenario': 1, 'data': []}
    
    for row in rows:
        pkt_size = int(row['packet_size'])
        throughput = row['throughput_kbps']
        goodput = row['goodput_kbps']
        completion = row['completion_time_seconds']
        loss = row['packet_loss_rate']
        
        print(f"{pkt_size:>15}B {throughput:>18.2f} {goodput:>18.2f} {completion:>12.2f} {loss:>11.2f}%")
        
        analysis['data'].append({
            'packet_size': pkt_size,
            'throughput_kbps': throughput,
            'goodput_kbps': goodput,
            'completion_time_seconds': completion,
            'packet_loss_rate': loss
        })
    
    # Teknik yorum
    if len(rows) >= 2:
        min_tp = min(r['throughput_kbps'] for r in rows)
        max_tp = max(r['throughput_kbps'] for r in rows)
        improvement = ((max_tp - min_tp) / min_tp * 100) if min_tp > 0 else 0
        
        print(f"\n📊 Teknik Analiz:")
        print(f"  • Minimum Throughput (küçük paket): {min_tp:.2f} Kbps")
        print(f"  • Maksimum Throughput (büyük paket): {max_tp:.2f} Kbps")
        print(f"  • Throughput artışı: %{improvement:.1f}")
        print(f"  • Yorum: Büyük paketler header overhead'i azaltır,")
        print(f"    her paketin başına eklenen 19 byte header'ın payload'a")
        print(f"    oranı düşer. Bu nedenle throughput doğrusal artar.")
    
    return analysis


def analyze_scenario2(data_dir: str = "data") -> Dict:
    """Senaryo 2: Timeout değeri etkisi analizi"""
    filepath = Path(data_dir) / "scenario2_results.csv"
    
    if not filepath.exists():
        print(f"⚠ Senaryo 2 verisi bulunamadı: {filepath}")
        return {}
    
    rows = read_csv(str(filepath))
    
    print("\n" + "="*70)
    print("SENARYO 2 ANALİZİ: TIMEOUT DEĞERİ ETKİSİ")
    print("="*70)
    print(f"{'Timeout (s)':>14} {'Throughput (Kbps)':>20} {'Süre (s)':>12} {'Retrans (%)':>14} {'RTT (ms)':>12}")
    print("-"*75)
    
    analysis = {'scenario': 2, 'data': []}
    
    for row in rows:
        timeout = row['timeout_seconds']
        throughput = row['throughput_kbps']
        completion = row['completion_time_seconds']
        retrans = row['retransmission_rate']
        rtt = row['avg_rtt_ms']
        
        print(f"{timeout:>13.1f}s {throughput:>18.2f} {completion:>12.2f} {retrans:>13.2f}% {rtt:>11.2f}")
        
        analysis['data'].append({
            'timeout_seconds': timeout,
            'throughput_kbps': throughput,
            'completion_time_seconds': completion,
            'retransmission_rate': retrans,
            'avg_rtt_ms': rtt
        })
    
    print(f"\n📊 Teknik Analiz:")
    print(f"  • Düşük timeout → erken tetikleyici → yüksek retransmission")
    print(f"  • Yüksek timeout → uzun bekleme → yavaş tamamlanma")
    print(f"  • Optimum: Ağ RTT'sinden biraz büyük (genellikle 2-3x RTT)")
    
    return analysis


def analyze_scenario3(data_dir: str = "data") -> Dict:
    """Senaryo 3: Paket kaybı etkisi analizi"""
    filepath = Path(data_dir) / "scenario3_results.csv"
    
    if not filepath.exists():
        print(f"⚠ Senaryo 3 verisi bulunamadı: {filepath}")
        return {}
    
    rows = read_csv(str(filepath))
    
    print("\n" + "="*70)
    print("SENARYO 3 ANALİZİ: PAKET KAYBI ETKİSİ")
    print("="*70)
    print(f"{'Kayıp (%)':>12} {'Goodput (Kbps)':>18} {'Throughput (Kbps)':>20} {'Süre (s)':>12} {'Retrans (%)':>14}")
    print("-"*80)
    
    analysis = {'scenario': 3, 'data': []}
    
    for row in rows:
        loss_pct = row['loss_rate_pct']
        goodput = row['goodput_kbps']
        throughput = row['throughput_kbps']
        completion = row['completion_time_seconds']
        retrans = row['retransmission_rate']
        
        print(f"{loss_pct:>11.0f}% {goodput:>18.2f} {throughput:>18.2f} {completion:>12.2f} {retrans:>13.2f}%")
        
        analysis['data'].append({
            'loss_rate_pct': loss_pct,
            'goodput_kbps': goodput,
            'throughput_kbps': throughput,
            'completion_time_seconds': completion,
            'retransmission_rate': retrans
        })
    
    # Goodput düşüşü hesapla
    if len(rows) >= 2:
        base_goodput = rows[0]['goodput_kbps']  # %0 kayıp
        print(f"\n📊 Teknik Analiz:")
        for row in rows[1:]:
            drop_pct = (base_goodput - row['goodput_kbps']) / base_goodput * 100 if base_goodput > 0 else 0
            print(f"  • %{row['loss_rate_pct']:.0f} kayıp → Goodput %{drop_pct:.1f} azaldı")
        print(f"  • Retransmission mekanizması kayıpları telafi ediyor")
        print(f"  • Yüksek kayıpta completion time belirgin artar")
    
    return analysis


def analyze_scenario4(data_dir: str = "data") -> Dict:
    """Senaryo 4: Dosya boyutu etkisi analizi"""
    filepath = Path(data_dir) / "scenario4_results.csv"
    
    if not filepath.exists():
        print(f"⚠ Senaryo 4 verisi bulunamadı: {filepath}")
        return {}
    
    rows = read_csv(str(filepath))
    
    print("\n" + "="*70)
    print("SENARYO 4 ANALİZİ: DOSYA BOYUTU ETKİSİ")
    print("="*70)
    print(f"{'Dosya (MB)':>13} {'Throughput (Kbps)':>20} {'Goodput (Kbps)':>18} {'Süre (s)':>12} {'Kayıp (%)':>12}")
    print("-"*78)
    
    analysis = {'scenario': 4, 'data': []}
    
    for row in rows:
        size_mb = row['file_size_mb']
        throughput = row['throughput_kbps']
        goodput = row['goodput_kbps']
        completion = row['completion_time_seconds']
        loss = row['packet_loss_rate']
        
        print(f"{size_mb:>12.0f}MB {throughput:>18.2f} {goodput:>18.2f} {completion:>12.2f} {loss:>11.2f}%")
        
        analysis['data'].append({
            'file_size_mb': size_mb,
            'throughput_kbps': throughput,
            'goodput_kbps': goodput,
            'completion_time_seconds': completion,
            'packet_loss_rate': loss
        })
    
    # Lineerlik analizi
    if len(rows) >= 2:
        print(f"\n📊 Teknik Analiz (Lineerlik Testi):")
        base_size = rows[0]['file_size_mb']
        base_time = rows[0]['completion_time_seconds']
        
        for row in rows[1:]:
            size_ratio = row['file_size_mb'] / base_size if base_size > 0 else 0
            time_ratio = row['completion_time_seconds'] / base_time if base_time > 0 else 0
            linearity = (time_ratio / size_ratio) if size_ratio > 0 else 0
            
            print(f"  • {base_size:.0f}MB → {row['file_size_mb']:.0f}MB: "
                  f"Boyut {size_ratio:.1f}x, Süre {time_ratio:.1f}x "
                  f"(lineerlik: {linearity:.2f})")
        
        # Throughput istikrarı
        throughputs = [r['throughput_kbps'] for r in rows]
        cv = (std_dev(throughputs) / mean(throughputs) * 100) if mean(throughputs) > 0 else 0
        print(f"  • Throughput varyasyon katsayısı: %{cv:.1f} (düşük = istikrarlı)")
    
    return analysis


def save_analysis_results(results: Dict, output_dir: str = "results"):
    """Analiz sonuçlarını JSON'a kaydet"""
    Path(output_dir).mkdir(exist_ok=True)
    output_file = Path(output_dir) / "analysis_results.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Analiz sonuçları kaydedildi: {output_file}")


def main():
    """Tüm senaryoları analiz et"""
    print("\n" + "█"*70)
    print("█" + " "*25 + "NETPROBE ANALİZ" + " "*26 + "█")
    print("█"*70)
    
    data_dir = "data"
    all_results = {}
    
    # Senaryo analizleri
    all_results['scenario1'] = analyze_scenario1(data_dir)
    all_results['scenario2'] = analyze_scenario2(data_dir)
    all_results['scenario3'] = analyze_scenario3(data_dir)
    all_results['scenario4'] = analyze_scenario4(data_dir)
    
    # Sonuçları kaydet
    save_analysis_results(all_results)
    
    print("\n" + "="*70)
    print("✓ Analiz tamamlandı! Grafik oluşturmak için: python analysis/plots.py")
    print("="*70)


if __name__ == "__main__":
    main()

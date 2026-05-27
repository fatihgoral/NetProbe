"""
NetProbe - Tum Senaryo Calistirici

4 deneysel senaryoyu sirayla calistirir, sonra grafikleri olusturur.
Cikti: data/scenario*_results.csv + reports/*.png
"""

import sys
import time
import subprocess
from pathlib import Path

def run_scenario(script: str, name: str):
    print("\n" + "#"*70)
    print(f"# BASLIYOR: {name}")
    print(f"# Script : {script}")
    print("#"*70)
    start = time.time()

    result = subprocess.run(
        [sys.executable, "-X", "utf8", script],
        cwd=str(Path(__file__).parent)
    )

    elapsed = time.time() - start
    mins, secs = divmod(int(elapsed), 60)
    status = "TAMAMLANDI" if result.returncode == 0 else "HATA (devam ediliyor)"
    print(f"\n>> {name}: {status} ({mins}dk {secs}sn)")
    return result.returncode == 0

def main():
    print("="*70)
    print("  NETPROBE - TUM SENARYOLAR")
    print("="*70)
    print("Calistirilacaklar:")
    print("  1) Paket Boyutu Etkisi  (256B / 512B / 1024B / 2048B)")
    print("  2) Timeout Etkisi       (0.5s / 1s / 2s / 5s) + %5 kayip")
    print("  3) Paket Kaybi Etkisi   (%0 / %5 / %10 / %20)")
    print("  4) Dosya Boyutu Etkisi  (1MB / 5MB / 10MB / 50MB)")
    print("  5) Grafik Olusturma     (reports/*.png)")
    print("="*70)

    total_start = time.time()
    results = {}

    results['s1'] = run_scenario("experiments/scenario1_packetsize.py", "SENARYO 1: Paket Boyutu")
    results['s2'] = run_scenario("experiments/scenario2_timeout.py",    "SENARYO 2: Timeout Degeri")
    results['s3'] = run_scenario("experiments/scenario3_loss.py",       "SENARYO 3: Paket Kaybi")
    results['s4'] = run_scenario("experiments/scenario4_filesize.py",   "SENARYO 4: Dosya Boyutu")

    # Grafikleri olustur
    print("\n" + "#"*70)
    print("# GRAFIK OLUSTURULUYOR...")
    print("#"*70)
    subprocess.run([sys.executable, "-X", "utf8", "analysis/plots.py"],
                   cwd=str(Path(__file__).parent))

    # Analiz
    subprocess.run([sys.executable, "-X", "utf8", "analysis/analyze.py"],
                   cwd=str(Path(__file__).parent))

    total = time.time() - total_start
    mins, secs = divmod(int(total), 60)

    print("\n" + "="*70)
    print("  TAMAMLANDI!")
    print("="*70)
    print(f"Toplam sure: {mins}dk {secs}sn")
    print(f"Senaryo 1: {'OK' if results['s1'] else 'HATA'}")
    print(f"Senaryo 2: {'OK' if results['s2'] else 'HATA'}")
    print(f"Senaryo 3: {'OK' if results['s3'] else 'HATA'}")
    print(f"Senaryo 4: {'OK' if results['s4'] else 'HATA'}")
    print("\nSonuclar:")
    print("  data/scenario1_results.csv")
    print("  data/scenario2_results.csv")
    print("  data/scenario3_results.csv")
    print("  data/scenario4_results.csv")
    print("  reports/scenario1_paket_boyutu.png")
    print("  reports/scenario2_timeout.png")
    print("  reports/scenario3_paket_kaybi.png")
    print("  reports/scenario4_dosya_boyutu.png")
    print("  reports/netprobe_dashboard.png")

if __name__ == "__main__":
    main()

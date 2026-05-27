"""
SENARYO 4: Dosya Boyutu Etkisi
Degisken : dosya = 1MB, 5MB, 10MB, 50MB
Sabit    : packet=1024B, timeout=2s, kayip=%0
Her boyut icin 3 deneme, ortalama alinir.
"""
import sys, csv, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scenario_utils import InProcessServer, run_single_transfer, avg_metrics

FILE_SIZES_MB = [1, 5, 10, 50]
TESTS_PER_CFG = 3
PORT          = 5103


def ensure_test_file(size_mb: int) -> Path:
    p = Path(f"data/test_{size_mb}mb.bin")
    if not p.exists():
        p.parent.mkdir(exist_ok=True)
        print(f"  Dosya olusturuluyor: {p} ({size_mb}MB)")
        with open(p, 'wb') as f:
            chunk = b'F' * 1024 * 1024
            for _ in range(size_mb):
                f.write(chunk)
    return p


def main():
    print("\n" + "="*60)
    print("SENARYO 4: DOSYA BOYUTU ETKİSİ")
    print("="*60)

    server = InProcessServer(port=PORT, loss_rate=0.0)
    server.start()
    print(f"Sunucu hazir (port {PORT})")

    all_results = []

    try:
        for size_mb in FILE_SIZES_MB:
            test_file = ensure_test_file(size_mb)
            print(f"\n--- Dosya boyutu: {size_mb}MB ---")
            run_results = []

            for attempt in range(1, TESTS_PER_CFG + 1):
                server.reset()
                print(f"  Deneme {attempt}/{TESTS_PER_CFG}...", end=" ", flush=True)
                t0 = time.time()

                metrics = run_single_transfer(
                    host="localhost", port=PORT,
                    filepath=test_file,
                    packet_size=1024,
                    timeout=2.0,
                    max_retries=5
                )

                elapsed = time.time() - t0
                if metrics:
                    run_results.append(metrics)
                    print(f"OK ({elapsed:.1f}s, {metrics['throughput_kbps']:.0f} Kbps)")
                else:
                    print(f"BASARISIZ ({elapsed:.1f}s)")

                time.sleep(1.0)

            if run_results:
                avg = avg_metrics(run_results)
                avg['file_size_mb'] = size_mb
                avg['file_size_bytes'] = size_mb * 1024 * 1024
                all_results.append(avg)
                print(f"  Ort: {avg['throughput_kbps']:.1f} Kbps | {avg['completion_time_seconds']:.2f}s")

    finally:
        server.stop()

    Path("data").mkdir(exist_ok=True)
    csv_path = Path("data/scenario4_results.csv")
    if all_results:
        fieldnames = ['file_size_mb', 'file_size_bytes', 'tests', 'throughput_kbps',
                      'goodput_kbps', 'completion_time_seconds', 'packet_loss_rate']
        with open(csv_path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            w.writeheader()
            w.writerows(all_results)
        print(f"\nKaydedildi: {csv_path}")

    print("\n=== SENARYO 4 TAMAMLANDI ===")
    for r in all_results:
        print(f"  {r['file_size_mb']}MB -> {r['throughput_kbps']:.1f} Kbps, "
              f"{r['completion_time_seconds']:.2f}s")


if __name__ == "__main__":
    main()

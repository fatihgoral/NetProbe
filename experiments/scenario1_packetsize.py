"""
SENARYO 1: Paket Boyutu Etkisi
Degisken : packet_size = 256, 512, 1024, 2048 byte
Sabit    : dosya=10MB, timeout=2s, kayip=%0
Her boyut icin 3 deneme, ortalama alinir.
"""
import sys, csv, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scenario_utils import InProcessServer, run_single_transfer, avg_metrics

PACKET_SIZES  = [256, 512, 1024, 2048]
TESTS_PER_CFG = 3
PORT          = 5100
FILE_SIZE_MB  = 10
TEST_FILE     = Path("data/test_scenario1.bin")


def main():
    print("\n" + "="*60)
    print("SENARYO 1: PAKET BOYUTU ETKİSİ")
    print("="*60)

    # Test dosyasini kontrol et
    if not TEST_FILE.exists():
        print(f"Dosya olusturuluyor: {TEST_FILE}")
        TEST_FILE.parent.mkdir(exist_ok=True)
        with open(TEST_FILE, 'wb') as f:
            for _ in range(FILE_SIZE_MB):
                f.write(b'X' * 1024 * 1024)

    # Sunucuyu baslat (bir kez, tum testler icin)
    server = InProcessServer(port=PORT, loss_rate=0.0)
    server.start()
    print(f"Sunucu hazir (port {PORT})")

    all_results = []

    try:
        for pkt_size in PACKET_SIZES:
            print(f"\n--- Paket boyutu: {pkt_size}B ---")
            run_results = []

            for attempt in range(1, TESTS_PER_CFG + 1):
                server.reset()
                print(f"  Deneme {attempt}/{TESTS_PER_CFG}...", end=" ", flush=True)
                t0 = time.time()

                metrics = run_single_transfer(
                    host="localhost", port=PORT,
                    filepath=TEST_FILE,
                    packet_size=pkt_size,
                    timeout=2.0,
                    max_retries=5
                )

                elapsed = time.time() - t0
                if metrics:
                    run_results.append(metrics)
                    print(f"OK ({elapsed:.1f}s, {metrics['throughput_kbps']:.0f} Kbps)")
                else:
                    print(f"BASARISIZ ({elapsed:.1f}s)")

                time.sleep(0.5)

            if run_results:
                avg = avg_metrics(run_results)
                avg['packet_size'] = pkt_size
                all_results.append(avg)
                print(f"  Ort: {avg['throughput_kbps']:.1f} Kbps | "
                      f"{avg['completion_time_seconds']:.2f}s | "
                      f"retrans={avg['retransmission_rate']:.1f}%")

    finally:
        server.stop()

    # CSV'ye kaydet
    Path("data").mkdir(exist_ok=True)
    csv_path = Path("data/scenario1_results.csv")
    if all_results:
        fieldnames = ['packet_size', 'tests', 'throughput_kbps', 'goodput_kbps',
                      'completion_time_seconds', 'packet_loss_rate', 'retransmission_rate', 'avg_rtt_ms']
        with open(csv_path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            w.writeheader()
            w.writerows(all_results)
        print(f"\nKaydedildi: {csv_path}")

    print("\n=== SENARYO 1 TAMAMLANDI ===")
    for r in all_results:
        print(f"  {r['packet_size']}B -> {r['throughput_kbps']:.1f} Kbps, "
              f"{r['completion_time_seconds']:.2f}s, retrans={r['retransmission_rate']:.1f}%")


if __name__ == "__main__":
    main()

"""
SENARYO 2: Timeout Degeri Etkisi
Degisken : timeout = 0.5, 1.0, 2.0, 5.0 saniye
Sabit    : dosya=10MB, packet=1024B, kayip=%5 (gercekci timeout icin)
Her timeout icin 3 deneme, ortalama alinir.

Not: Loopback RTT <1ms, bu yuzden %5 kayip olmadan timeout hic gozlemlenmez.
%5 kayip ile: dusuk timeout -> yuksek retransmission, yuksek timeout -> uzun bekleme
"""
import sys, csv, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scenario_utils import InProcessServer, run_single_transfer, avg_metrics

TIMEOUT_VALUES = [0.5, 1.0, 2.0, 5.0]
TESTS_PER_CFG  = 3
PORT           = 5101
LOSS_RATE      = 0.05   # %5 sabit kayip
FILE_SIZE_MB   = 1
TEST_FILE      = Path("data/test_1mb.bin")


def main():
    print("\n" + "="*60)
    print("SENARYO 2: TIMEOUT DEGERİ ETKİSİ (%5 kayipla)")
    print("="*60)

    if not TEST_FILE.exists():
        TEST_FILE.parent.mkdir(exist_ok=True)
        with open(TEST_FILE, 'wb') as f:
            for _ in range(FILE_SIZE_MB):
                f.write(b'T' * 1024 * 1024)

    server = InProcessServer(port=PORT, loss_rate=LOSS_RATE)
    server.start()
    print(f"Lossy sunucu hazir (port {PORT}, loss={LOSS_RATE*100:.0f}%)")

    all_results = []

    try:
        for timeout_val in TIMEOUT_VALUES:
            print(f"\n--- Timeout: {timeout_val}s ---")
            run_results = []

            for attempt in range(1, TESTS_PER_CFG + 1):
                server.reset(loss_rate=LOSS_RATE)
                print(f"  Deneme {attempt}/{TESTS_PER_CFG}...", end=" ", flush=True)
                t0 = time.time()

                metrics = run_single_transfer(
                    host="localhost", port=PORT,
                    filepath=TEST_FILE,
                    packet_size=1024,
                    timeout=timeout_val,
                    max_retries=5
                )

                elapsed = time.time() - t0
                if metrics:
                    run_results.append(metrics)
                    print(f"OK ({elapsed:.1f}s, retrans={metrics['retransmission_rate']:.1f}%)")
                else:
                    print(f"BASARISIZ ({elapsed:.1f}s)")

                time.sleep(0.5)

            if run_results:
                avg = avg_metrics(run_results)
                avg['timeout_seconds'] = timeout_val
                all_results.append(avg)
                print(f"  Ort: {avg['throughput_kbps']:.1f} Kbps | "
                      f"{avg['completion_time_seconds']:.2f}s | "
                      f"retrans={avg['retransmission_rate']:.1f}%")

    finally:
        server.stop()

    Path("data").mkdir(exist_ok=True)
    csv_path = Path("data/scenario2_results.csv")
    if all_results:
        fieldnames = ['timeout_seconds', 'tests', 'throughput_kbps', 'goodput_kbps',
                      'completion_time_seconds', 'retransmission_rate', 'avg_rtt_ms']
        with open(csv_path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            w.writeheader()
            w.writerows(all_results)
        print(f"\nKaydedildi: {csv_path}")

    print("\n=== SENARYO 2 TAMAMLANDI ===")
    for r in all_results:
        print(f"  timeout={r['timeout_seconds']}s -> {r['throughput_kbps']:.1f} Kbps, "
              f"retrans={r['retransmission_rate']:.1f}%, {r['completion_time_seconds']:.2f}s")


if __name__ == "__main__":
    main()

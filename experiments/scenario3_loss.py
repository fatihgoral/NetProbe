"""
SENARYO 3: Simule Paket Kaybi Etkisi
Degisken : loss_rate = %0, %5, %10, %20
Sabit    : dosya=256KB, packet=1024B, timeout=0.5s
Her kayip orani icin 3 deneme, ortalama alinir.
"""
import sys, csv, time, json, io, os
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from scenario_utils import InProcessServer, avg_metrics

LOSS_RATES    = [0.0, 0.05, 0.10, 0.20]
TESTS_PER_CFG = 3
PORT          = 5105
FILE_SIZE     = 256 * 1024   # 256 KB — hizli ama istatistiksel olarak yeterli
TEST_FILE     = Path("data/test_s3.bin")


def run_transfer_silent(host, port, filepath, packet_size, timeout, max_retries):
    """Logger print'lerini susturup transfer calistir."""
    import logger as _lg
    _lg.reset_logger()

    from client import NetProbeClient
    client = NetProbeClient(
        host=host, port=port,
        packet_size=packet_size,
        timeout=timeout,
        max_retries=max_retries
    )

    # print ciktilarini yoksay (StringIO ile - Windows codec hatasi yok)
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        success = client.transfer_file(str(filepath))
    finally:
        sys.stdout = old_stdout

    if success:
        try:
            with open("results/metrics.json", 'r') as f:
                return json.load(f)
        except Exception:
            return None
    return None


def main():
    print("\n" + "="*60)
    print("SENARYO 3: PAKET KAYBI ETKİSİ")
    print("="*60)

    # Test dosyasi olustur
    TEST_FILE.parent.mkdir(exist_ok=True)
    if not TEST_FILE.exists() or TEST_FILE.stat().st_size != FILE_SIZE:
        with open(TEST_FILE, 'wb') as f:
            f.write(b'X' * FILE_SIZE)
        print(f"Test dosyasi: {TEST_FILE} ({FILE_SIZE//1024}KB)")

    Path("results").mkdir(exist_ok=True)

    all_results = []

    for loss_rate in LOSS_RATES:
        loss_pct = loss_rate * 100
        print(f"\n--- Kayip orani: %{loss_pct:.0f} ---")

        server = InProcessServer(port=PORT, loss_rate=loss_rate)
        server.start()

        run_results = []
        try:
            for attempt in range(1, TESTS_PER_CFG + 1):
                server.reset(loss_rate=loss_rate)
                print(f"  Deneme {attempt}/{TESTS_PER_CFG}...", end=" ", flush=True)
                t0 = time.time()

                metrics = run_transfer_silent(
                    host="localhost", port=PORT,
                    filepath=TEST_FILE,
                    packet_size=1024,
                    timeout=0.5,
                    max_retries=5
                )

                elapsed = time.time() - t0
                if metrics:
                    run_results.append(metrics)
                    print(f"OK ({elapsed:.1f}s, goodput={metrics['goodput_kbps']:.0f} Kbps, "
                          f"retrans={metrics['retransmission_rate']:.1f}%)")
                else:
                    print(f"BASARISIZ ({elapsed:.1f}s)")

                time.sleep(0.2)
        finally:
            server.stop()
            time.sleep(0.5)

        if run_results:
            avg = avg_metrics(run_results)
            avg['loss_rate_pct'] = loss_pct
            avg['actual_packet_loss_pct'] = avg.get('packet_loss_rate', 0.0)
            all_results.append(avg)
            print(f"  Ortalama: goodput={avg['goodput_kbps']:.1f} Kbps | "
                  f"{avg['completion_time_seconds']:.2f}s | "
                  f"retrans={avg['retransmission_rate']:.1f}%")

    # CSV kaydet
    csv_path = Path("data/scenario3_results.csv")
    if all_results:
        fieldnames = ['loss_rate_pct', 'tests', 'goodput_kbps', 'throughput_kbps',
                      'completion_time_seconds', 'retransmission_rate', 'avg_rtt_ms',
                      'actual_packet_loss_pct']
        with open(csv_path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            w.writeheader()
            w.writerows(all_results)
        print(f"\nSonuclar kaydedildi: {csv_path}")

    print("\n=== SENARYO 3 SONUCLARI ===")
    for r in all_results:
        print(f"  loss=%{r['loss_rate_pct']:.0f} -> "
              f"goodput={r['goodput_kbps']:.1f} Kbps | "
              f"retrans={r['retransmission_rate']:.1f}% | "
              f"sure={r['completion_time_seconds']:.2f}s")


if __name__ == "__main__":
    main()

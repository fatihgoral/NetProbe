"""
NetProbe Senaryo 5: TCP vs NetProbe (UDP) Karşılaştırması

Aynı dosyayı önce TCP ile sonra NetProbe (UDP) ile göndererek
süreyi ve performans farkını karşılaştırır.
"""

import sys
import time
import socket
import threading
from pathlib import Path
import subprocess

# Proje kök dizinini path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

def tcp_server(port: int, output_file: str, ready_event: threading.Event):
    """Basit TCP Sunucusu"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", port))
    sock.listen(1)
    ready_event.set()
    
    conn, addr = sock.accept()
    with open(output_file, 'wb') as f:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            f.write(data)
    conn.close()
    sock.close()

def tcp_client(host: str, port: int, input_file: str):
    """Basit TCP İstemcisi"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    
    with open(input_file, 'rb') as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            sock.sendall(data)
    sock.close()

def run_scenario():
    print("\n" + "="*50)
    print("SENARYO 5: TCP vs NetProbe (UDP) Performans Karşılaştırması")
    print("="*50)
    
    test_file = Path("data/large_test.bin")
    if not test_file.exists():
        print(f"Test dosyası oluşturuluyor: {test_file}")
        test_file.parent.mkdir(exist_ok=True)
        # 10MB test dosyası
        with open(test_file, 'wb') as f:
            f.write(os.urandom(10 * 1024 * 1024))
            
    # 1. TCP TESTİ
    print("\n--- 1. Aşama: TCP Transferi ---")
    tcp_port = 6000
    tcp_output = "received_files/tcp_output.bin"
    Path("received_files").mkdir(exist_ok=True)
    
    ready = threading.Event()
    server_thread = threading.Thread(target=tcp_server, args=(tcp_port, tcp_output, ready))
    server_thread.start()
    
    ready.wait()
    
    start_time = time.time()
    tcp_client("127.0.0.1", tcp_port, str(test_file))
    server_thread.join()
    tcp_time = time.time() - start_time
    
    print(f"TCP Transfer Süresi: {tcp_time:.2f} saniye")
    
    # 2. NETPROBE (UDP) TESTİ
    print("\n--- 2. Aşama: NetProbe (UDP) Transferi ---")
    udp_port = 6001
    
    # Server'ı başlat
    server_cmd = [
        sys.executable, "src/server.py",
        "--port", str(udp_port),
        "--output-dir", "received_files"
    ]
    server_proc = subprocess.Popen(server_cmd)
    
    time.sleep(1) # Server'ın açılmasını bekle
    
    # Client'ı başlat
    client_cmd = [
        sys.executable, "src/client.py",
        "--port", str(udp_port),
        "--file", str(test_file),
        "--window-size", "20"
    ]
    
    start_time = time.time()
    subprocess.run(client_cmd)
    udp_time = time.time() - start_time
    
    server_proc.terminate()
    
    print(f"\nNetProbe (UDP) Transfer Süresi: {udp_time:.2f} saniye")
    
    # SONUÇ
    print("\n" + "="*50)
    print("KARŞILAŞTIRMA SONUCU")
    print("="*50)
    print(f"TCP Süresi:     {tcp_time:.2f} s")
    print(f"NetProbe Süresi: {udp_time:.2f} s")
    if tcp_time < udp_time:
        diff = ((udp_time - tcp_time) / tcp_time) * 100
        print(f"Sonuç: TCP, NetProbe'dan %{diff:.1f} daha hızlı.")
    else:
        diff = ((tcp_time - udp_time) / udp_time) * 100
        print(f"Sonuç: NetProbe, TCP'den %{diff:.1f} daha hızlı!")

if __name__ == "__main__":
    import os
    run_scenario()

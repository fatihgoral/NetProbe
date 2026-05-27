# NetProbe: UDP Tabanlı Güvenilir Dosya Aktarımı, Trafik İzleme ve Ağ Performans Analiz Platformu

**Bursa Teknik Üniversitesi | Bilgisayar Mühendisliği Bölümü**  
**Bilgisayar Ağları Dersi - Dönem Projesi**

---

## 📋 Proje Özeti

NetProbe, UDP üzerinde çalışan **güvenilir dosya aktarım sistemi** geliştiren bir ağ uygulamasıdır. Proje kapsamında öğrenciler;
- UDP tabanlı istemci-sunucu mimarisi
- Uygulama katmanında güvenilirlik mekanizmaları (ACK, Sequence Number, Timeout, Retransmission)
- Trafik izleme ve olay kayıt sistemi
- Performans analizi ve deneysel evaluasyon

konularında teorik ve pratik bilgi kazanacaklar.

---

## 🎯 Proje Hedefleri

✅ UDP tabanlı güvenilir dosya aktarımı  
✅ Sequence number, ACK, timeout ve retransmission mekanizmaları  
✅ Trafik izleme ve detaylı loglama  
✅ Performans metrikleri hesaplama (Throughput, Goodput, Packet Loss, RTT)  
✅ 4 deneysel senaryo ile sistem evaluasyonu  
✅ Teknik rapor ve sunum hazırlama  
## 📁 Proje Yapısı

```
netprobe/
├── src/                          # Kaynak kodlar
│   ├── client.py                 # İstemci uygulaması
│   ├── server.py                 # Sunucu uygulaması
│   ├── protocol.py               # Paket protokolü ve sınıfları
│   ├── logger.py                 # Olay loglama sistemi
│   └── metrics.py                # Performans metrikleri hesaplama
│
├── tests/                        # Test dosyaları
│   ├── test_protocol.py          # Protokol unit testleri
│   └── test_transfer.py          # Transfer integration testleri
│
├── analysis/                     # Veri analizi ve görselleştirme
│   ├── analyze.py                # CSV analiz ve istatistik
│   └── plots.py                  # Grafik oluşturma (matplotlib)
│
├── experiments/                  # Deneysel senaryolar
│   ├── scenario1_packetsize.py   # Senaryo 1: Paket boyutu etkisi
│   ├── scenario2_timeout.py      # Senaryo 2: Timeout etkisi
│   ├── scenario3_loss.py         # Senaryo 3: Paket kaybı etkisi
│   └── scenario4_filesize.py     # Senaryo 4: Dosya boyutu etkisi
│
├── logs/                         # Deney sonuçları ve loglar
│   └── transfer_log.csv          # Transfer olayları logu
│
├── reports/                      # Raporlar
│   └── NetProbe_TeknikRapor.pdf  # Teknik rapor (8-12 sayfa)
│
├── data/                         # Test dosyaları
│   ├── test_1mb.bin              # 1MB test dosyası
│   ├── test_5mb.bin              # 5MB test dosyası
│   ├── test_10mb.bin             # 10MB test dosyası
│   └── test_50mb.bin             # 50MB test dosyası
│
├── requirements.txt              # Python bağımlılıkları
├── README.md                     # Bu dosya
└── .gitignore                    # Git ignore kuralları
```

## 🚀 Kurulum ve Başlatma

### Gereksinimler
- Python 3.9 veya daha yeni
- pip paket yöneticisi
- Git (optional)

### Adım 1: Depoyu klonla
```bash
git clone https://github.com/fatihgoral/netprobe.git
cd netprobe
```

### Adım 2: Sanal ortam oluştur
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Adım 3: Bağımlılıkları yükle
```bash
pip install -r requirements.txt
```

---

## 💻 Kullanım

### Sunucuyu Başlat
```bash
python src/server.py --port 5000
```

**Seçenekler:**
- `--port`: Dinlenecek port (varsayılan: 5000)
- `--output-dir`: Alınan dosyaların kaydedileceği dizin (varsayılan: ./received_files)

### İstemciden Dosya Gönder
```bash
python src/client.py --host localhost --port 5000 --file data/test_10mb.bin
```

**Seçenekler:**
- `--host`: Sunucu adresi (varsayılan: localhost)
- `--port`: Sunucu portu (varsayılan: 5000)
- `--file`: Gönderilecek dosya yolu
- `--packet-size`: Paket boyutu (varsayılan: 1024 bayt)
- `--timeout`: Timeout süresi (varsayılan: 2.0 saniye)

### Örnek Transfer
```bash
# Terminal 1: Sunucuyu başlat
python src/server.py --port 5000

# Terminal 2: Dosya gönder
python src/client.py --host localhost --port 5000 --file data/test_10mb.bin

# Sonuç: 
# - Dosya alındı ve verify edildi
# - Log: logs/transfer_log.csv
# - Metrikler: results/metrics.json
```

---

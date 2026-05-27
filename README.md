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
## 🧪 Deneysel Senaryolar

### Senaryo 1: Paket Boyutu Etkisi
```bash
python experiments/scenario1_packetsize.py
# Çıktı: data/scenario1_results.csv, plots/scenario1_*.png
```
**Test edilen paket boyutları:** 256B, 512B, 1024B, 2048B  
**Metrik:** Throughput vs Goodput

### Senaryo 2: Timeout Değeri Etkisi
```bash
python experiments/scenario2_timeout.py
# Çıktı: data/scenario2_results.csv, plots/scenario2_*.png
```
**Test edilen timeout:** 0.5s, 1s, 2s, 5s  
**Metrik:** Retransmission Rate vs Completion Time

### Senaryo 3: Simüle Paket Kaybı
```bash
python experiments/scenario3_loss.py
# Çıktı: data/scenario3_results.csv, plots/scenario3_*.png
```
**Test edilen kayıp oranı:** %0, %5, %10, %20  
**Metrik:** Goodput vs Packet Loss Rate

### Senaryo 4: Dosya Boyutu Etkisi
```bash
python experiments/scenario4_filesize.py
# Çıktı: data/scenario4_results.csv, plots/scenario4_*.png
```
**Test edilen dosya boyutu:** 1MB, 5MB, 10MB, 50MB  
**Metrik:** Completion Time vs File Size

---

## 📊 Sonuç Analizi

Tüm deney sonuçları sonra analiz edilir:
```bash
python analysis/analyze.py
python analysis/plots.py
```

Çıktılar:
- `results/metrics_summary.csv`: Özet istatistikler
- `plots/`: Tüm grafikler
- `analysis/report_data.json`: Detaylı analizler

---

## 📄 Teknik Rapor

Detaylı teknik rapor (8-12 sayfa):
- **Dosya:** `reports/NetProbe_TeknikRapor.pdf`
- **İçerik:**
  - Giriş ve problem tanımı
  - Sistem mimarisi ve protokol tasarımı
  - Uygulama detayları
  - Deney ortamı ve metodoloji
  - Performans metrikleri ve sonuçlar
  - Tartışma ve gelecek çalışmalar

---

## 📚 Protokol Spesifikasyonu

### Paket Formatı

**Veri Paketi (DATA - 0x01):**
```
┌─────────────┬──────────┬─────────────┬──────────────┬───────────┬─────────────┐
│Packet Type  │ Seq Num  │Total Pkts   │Payload Len   │Checksum   │ Payload     │
│ 1 byte      │ 4 bytes  │ 4 bytes     │ 2 bytes      │ 8 bytes   │ max 1000B   │
├─────────────┼──────────┼─────────────┼──────────────┼───────────┼─────────────┤
│   0x01      │0-65535   │ n           │ 0-1000       │ SHA-256   │ [data]      │
└─────────────┴──────────┴─────────────┴──────────────┴───────────┴─────────────┘
```

**ACK Paketi (ACK - 0x02):**
```
┌─────────────┬──────────┬───────────┐
│Packet Type  │ ACK Num  │ Checksum  │
│ 1 byte      │ 4 bytes  │ 8 bytes   │
├─────────────┼──────────┼───────────┤
│   0x02      │0-65535   │ SHA-256   │
└─────────────┴──────────┴───────────┘
```

### Mekanizmalar

- **Sequence Number:** Paketlerin sıralanması ve duplicate tespiti
- **ACK (Acknowledgment):** Alıcıdan gönderici'ye başarılı alındı sinyali
- **Timeout:** 2 saniye (configurable), ACK gelmazse retransmit
- **Retransmission:** Max 5 deneme, sonra başarısız
- **Checksum:** SHA-256 ile veri bütünlüğü doğrulaması

---

## 📈 Performans Metrikleri

| Metrik | Formül | Açıklama |
|--------|--------|----------|
| **Throughput** | Total Bytes / Time | Gönderilen tüm veriler / toplam süre |
| **Goodput** | Success Bytes / Time | Sadece başarılı veriler / toplam süre |
| **Packet Loss Rate** | (Sent - Success) / Sent × 100 | Kayıp oranı (%) |
| **Retrans Rate** | Retransmitted / Total × 100 | Yeniden gönderilen oranı (%) |
| **Completion Time** | End - Start | Toplam transfer süresi |
| **Avg RTT** | Σ(ACK Time - Send Time) / n | Ortalama Round Trip Time |

---

## 🔧 Teknoloji Yığını

- **Dil:** Python 3.9+
- **Network:** `socket` (UDP)
- **Concurrency:** `threading`
- **Data Analysis:** `pandas`, `numpy`
- **Visualization:** `matplotlib`, `seaborn`
- **Data Format:** CSV, JSON

---

## 📝 Grup Bilgileri

**Grup Üyeleri:**
- (Üye 1)
- (Üye 2)
- (Üye 3) *(optional)*

**Görev Dağılımı:**
- **Üye 1:** Protocol ve Socket Programming
- **Üye 2:** Logging ve Metrics
- **Üye 3:** Experiments ve Analysis

---

## 🐛 Sorun Giderme

### Hata: "Address already in use"
```bash
# Farklı port kullan
python src/server.py --port 5001
```

### Hata: "Connection refused"
```bash
# Sunucunun çalıştığını kontrol et
# Doğru host ve port kullanıyor musun?
python src/client.py --host localhost --port 5000
```

### Dosya Hash Uyuşmazlığı
```bash
# Sorun: Dosya transfer sırasında bozuldu
# Çözüm: Retransmission limit artır veya timeout değer değiştir
```

---

## 📖 Kaynaklar

- RFC 768 - User Datagram Protocol (UDP)
- Kurose & Ross - "Computer Networking" 
- Python socket documentation
- TCP/IP Protocols Implementation

---

## 📞 İletişim

- **GitHub:** https://github.com/fatihgoral/netprobe
- **E-mail:** (İletişim email)
- **Proje Dönem:** 2026 Bahar

---

## 📄 Lisans

Bu proje Bursa Teknik Üniversitesi Bilgisayar Ağları dersi kapsamında geliştirilmiştir.

---

**Son Güncelleme:** 26 Mayıs 2026  
**Versiyon:** 1.0

---

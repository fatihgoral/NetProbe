# 🌐 NetProbe

**UDP Tabanlı Güvenilir Dosya Aktarımı, Trafik İzleme ve Ağ Performans Analiz Platformu**

**Bursa Teknik Üniversitesi | Bilgisayar Mühendisliği Bölümü**
**Bilgisayar Ağları Dersi - Dönem Projesi**
**Geliştirici:** Muhammed Fatih Göral

---

# 📋 Proje Özeti

NetProbe, UDP üzerinde **stop-and-wait** yaklaşımı temelli güvenilir dosya aktarımı sağlayan; eş zamanlı olarak trafik kayıtlarını üreten ve sistem performansını farklı koşullar altında ölçen tam kapsamlı bir ağ platformudur.

Bu projenin temel amacı yalnızca çalışan bir dosya aktarım sistemi geliştirmek değil, aynı zamanda geliştirilen güvenilirlik mekanizmasının farklı ağ koşulları altındaki davranışını sayısal verilerle analiz etmektir. Paket boyutu, timeout süresi, kayıp oranı ve dosya boyutu gibi parametrelerin performans üzerindeki etkileri deneysel olarak incelenmiştir.

![NetProbe Genel Performans Özeti](reports/graphics/summary_performance_metrics.png)

---

# ✨ Temel Özellikler ve Güvenilirlik Mekanizmaları

UDP'nin bağlantısız ve güvenilmez yapısını uygulama katmanında çözmek amacıyla aşağıdaki mekanizmalar geliştirilmiştir:

* **Sequence Number:**
  Her veri paketi 32-bit benzersiz sıra numarası taşır. Böylece paket sıralaması korunur ve duplicate paketler tespit edilir.

* **ACK (Stop-and-Wait):**
  Gönderilen her veri paketi için alıcıdan onay (ACK) beklenir.

* **Timeout & Retransmission:**
  Beklenen ACK varsayılan olarak 2 saniye içinde gelmezse paket yeniden gönderilir. Maksimum yeniden deneme sayısı 5’tir.

* **Checksum Doğrulaması:**
  Paket başlığında SHA-256 hash değerinin ilk 8 baytı kullanılarak checksum doğrulaması yapılır.

* **Uçtan Uca Bütünlük Kontrolü:**
  Dosyanın SHA-256 özeti aktarım öncesinde gönderilir ve aktarım sonunda tekrar hesaplanarak dosya bütünlüğü doğrulanır.

* **Detaylı Loglama Sistemi:**
  Tüm ağ olayları milisaniye hassasiyetli zaman damgalarıyla kaydedilir. Paket gönderimi, ACK alımı, timeout ve retransmission olayları detaylı olarak loglanır.

---

# 🏗️ Sistem Mimarisi ve Protokol

NetProbe; istemci, sunucu, protokol katmanı, log altyapısı ve yapay kayıp simülatöründen oluşan modüler bir yapıya sahiptir.

## DATA Paketi (0x01)

Maksimum paket boyutu yaklaşık 1019 bayttır.

```text
┌─────────────┬──────────┬─────────────┬──────────────┬───────────┬─────────────┐
│Packet Type  │ Seq Num  │Total Pkts   │Payload Len   │Checksum   │ Payload     │
│ 1 byte      │ 4 bytes  │ 4 bytes     │ 2 bytes      │ 8 bytes   │ max 1000B   │
└─────────────┴──────────┴─────────────┴──────────────┴───────────┴─────────────┘
```

Tam dolu bir paket yaklaşık 1019 bayt boyutundadır. Bu değer Ethernet MTU sınırı olan 1500 baytın altında tutulduğu için IP fragmentation riski azaltılmıştır.

---

## ACK Paketi (0x02)

ACK paketi toplam 13 bayttır.

```text
┌─────────────┬──────────┬───────────┐
│Packet Type  │ ACK Num  │ Checksum  │
│ 1 byte      │ 4 bytes  │ 8 bytes   │
└─────────────┴──────────┴───────────┘
```

---

# 🧪 Deneysel Senaryolar ve Performans Analizi

NetProbe içerisinde farklı ağ koşullarını test eden deney senaryoları bulunmaktadır. Throughput, Goodput, RTT, Completion Time ve Packet Loss gibi metrikler otomatik olarak hesaplanmaktadır.

---

## 1️⃣ Senaryo 1: Paket Boyutu Etkisi

Paket boyutlarının (256B, 512B, 1024B, 2048B) performans üzerindeki etkisi incelenmiştir.

### Bulgular

* Paket boyutu arttıkça throughput değeri belirgin şekilde yükselmiştir.
* Küçük paketlerde protokol overhead maliyeti daha fazla hissedilmiştir.
* 1024 byte paket boyutu performans açısından en verimli değer olarak gözlemlenmiştir.
* 2048 byte paketlerde stop-and-wait yapısının etkisiyle işlem süresi tekrar artış göstermiştir.

---

## 2️⃣ Senaryo 2: Timeout Değeri Etkisi

%5 paket kaybı altında timeout değerlerinin performansa etkisi ölçülmüştür.

Test edilen timeout değerleri:

* 0.5 saniye
* 1.0 saniye
* 2.0 saniye
* 5.0 saniye

### Bulgular

* Timeout süresi arttıkça throughput ciddi şekilde düşmüştür.
* Çok büyük timeout değerleri aktarım süresini gereksiz şekilde uzatmıştır.
* Çok küçük timeout değerleri ise gereksiz retransmission oluşturmuştur.
* En verimli timeout değeri, ortalama RTT’nin küçük bir katı olacak şekilde belirlenmelidir.

---

## 3️⃣ Senaryo 3: Simüle Paket Kaybı Etkisi

Sunucu tarafında ACK paketleri düşürülerek yapay paket kaybı oluşturulmuştur.

Test edilen kayıp oranları:

* %0
* %5
* %10
* %20

### Bulgular

* Paket kaybı arttıkça stop-and-wait protokolünün performansı ciddi şekilde düşmüştür.
* %20 kayıp oranında throughput ve goodput değerleri dramatik şekilde azalmıştır.
* Tamamlanma süresi doğrusal değil, üstel şekilde büyüme göstermiştir.
* Stop-and-wait yaklaşımının paket kayıplarına karşı oldukça hassas olduğu gözlemlenmiştir.

---

## 4️⃣ Senaryo 4: Dosya Boyutu Ölçeklenebilirliği

Farklı dosya boyutlarının sistem performansına etkisi analiz edilmiştir.

Test edilen dosya boyutları:

* 1 MB
* 5 MB
* 10 MB
* 50 MB

### Bulgular

* Tamamlanma süresi dosya boyutuyla neredeyse doğrusal şekilde artmıştır.
* Büyük dosyalarda throughput değerinde hafif düşüş gözlemlenmiştir.
* Bu düşüşün temel nedenleri:

  * Disk I/O maliyetleri
  * Python GIL etkisi
  * Artan RTT bekleme süreleri
  * Yükselen paket sayısıdır.

---

# 🚀 Kurulum ve Kullanım

## Gereksinimler

* Python 3.11 veya daha yeni sürüm

Gerekli kütüphaneleri yüklemek için:

```bash
pip install -r requirements.txt
```

Not: Core sistem yalnızca Python standart kütüphanelerini kullanmaktadır. Pandas ve matplotlib gibi ek kütüphaneler yalnızca analiz ve grafik üretimi için gereklidir.

---

## 1. Sunucuyu Başlatma

```bash
python src/server.py --port 5000 --output-dir ./received_files
```

---

## 2. İstemci ile Dosya Gönderme

```bash
python src/client.py --host localhost --port 5000 --file data/test_10mb.bin --packet-size 1024 --timeout 2.0
```

---

## 3. Deney Senaryolarını Çalıştırma

```bash
python experiments/scenario1_packetsize.py
python experiments/scenario2_timeout.py
python experiments/scenario3_loss.py
python experiments/scenario4_filesize.py
```

Deney sonuçları CSV formatında `data/` klasörüne kaydedilir ve oluşturulan grafikler `plots/` klasörüne yazılır.

---

# 🔮 Sonuç ve Gelecek Çalışmalar

NetProbe, UDP üzerinde güvenilir veri aktarımını başarıyla gerçekleştirmiş ve stop-and-wait yaklaşımının güçlü ve zayıf yönlerini deneysel sonuçlarla ortaya koymuştur.

Gerçekleştirilen testler sonucunda:

* Paket kaybının performansı ciddi şekilde etkilediği,
* Timeout ayarının kritik öneme sahip olduğu,
* Paket boyutunun throughput üzerinde doğrudan etkili olduğu,
* Büyük dosyalarda doğrusal ölçeklenebilirliğin büyük ölçüde korunduğu gözlemlenmiştir.

Gelecek çalışmalarda aşağıdaki geliştirmelerin yapılması planlanmaktadır:

* Sliding Window tabanlı Go-Back-N veya Selective Repeat yapısına geçilmesi
* Adaptif RTO hesaplaması için Jacobson–Karels algoritmasının kullanılması
* Çoklu istemci desteği
* Uçtan uca şifreleme mekanizması eklenmesi
* Gerçek zamanlı trafik izleme paneli geliştirilmesi

---

# 📄 Lisans

Bu proje, Bursa Teknik Üniversitesi Bilgisayar Ağları dersi kapsamında geliştirilmiş akademik bir çalışmadır.

**Tarih:** Bahar 2026

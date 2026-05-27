"""
NetProbe Protokol Testleri

Protokol paketlerinin doğru çalışıp çalışmadığını test et
"""

import sys
sys.path.insert(0, 'src')

from protocol import (
    DataPacket, AckPacket, StartPacket, EndPacket,
    PacketType, Constants, calculate_checksum, verify_checksum
)


def test_checksum():
    """Checksum hesaplama ve doğrulama testini yap"""
    print("=" * 50)
    print("TEST: Checksum Hesaplama ve Doğrulama")
    print("=" * 50)
    
    test_data = b"Merhaba Dunya! Test etmek icin"
    checksum = calculate_checksum(test_data)
    
    print(f"Veri: {test_data}")
    print(f"Checksum: {checksum.hex()[:16]}...")
    
    # Doğru checksum
    assert verify_checksum(test_data, checksum), "Checksum doğrulaması başarısız"
    print("✓ Checksum doğrulaması: BAŞARILI\n")
    
    # Yanlış checksum
    wrong_checksum = b"wrongchecksum"
    assert not verify_checksum(test_data, wrong_checksum), "Yanlış checksum'a izin verildi"
    print("✓ Yanlış checksum reddedildi: BAŞARILI\n")


def test_data_packet():
    """DataPacket serileştirme ve deserileştirme testini yap"""
    print("=" * 50)
    print("TEST: DataPacket Serileştirme/Deserileştirme")
    print("=" * 50)
    
    # Paket oluştur
    payload = b"NetProbe Test Payload"
    pkt = DataPacket(seq_num=1, total_packets=10, payload=payload)
    
    print(f"Orijinal Paket: {pkt}")
    print(f"Payload: {payload}")
    
    # Serileştir
    serialized = pkt.serialize()
    print(f"Serileştirilmiş boyut: {len(serialized)} bytes")
    
    # Deserialize et
    deserialized = DataPacket.deserialize(serialized)
    print(f"Deserileştirilmiş Paket: {deserialized}")
    
    # Kontrol et
    assert deserialized.seq_num == pkt.seq_num, "Seq num uyuşmazlığı"
    assert deserialized.total_packets == pkt.total_packets, "Total packets uyuşmazlığı"
    assert deserialized.payload == payload, "Payload uyuşmazlığı"
    
    print("✓ DataPacket serileştirme: BAŞARILI\n")


def test_ack_packet():
    """ACKPacket testini yap"""
    print("=" * 50)
    print("TEST: AckPacket Serileştirme/Deserileştirme")
    print("=" * 50)
    
    ack_pkt = AckPacket(ack_num=5)
    print(f"Orijinal ACK: {ack_pkt}")
    
    # Serileştir
    serialized = ack_pkt.serialize()
    print(f"Serileştirilmiş boyut: {len(serialized)} bytes")
    
    # Deserialize et
    deserialized = AckPacket.deserialize(serialized)
    print(f"Deserileştirilmiş ACK: {deserialized}")
    
    assert deserialized.ack_num == ack_pkt.ack_num, "ACK num uyuşmazlığı"
    
    print("✓ AckPacket serileştirme: BAŞARILI\n")


def test_start_packet():
    """StartPacket testini yap"""
    print("=" * 50)
    print("TEST: StartPacket Serileştirme/Deserileştirme")
    print("=" * 50)
    
    file_hash = b"0" * 32  # 32 bytes SHA-256
    start_pkt = StartPacket(total_packets=100, file_hash=file_hash)
    
    print(f"Orijinal START: {start_pkt}")
    
    # Serileştir
    serialized = start_pkt.serialize()
    print(f"Serileştirilmiş boyut: {len(serialized)} bytes")
    
    # Deserialize et
    deserialized = StartPacket.deserialize(serialized)
    print(f"Deserileştirilmiş START: {deserialized}")
    
    assert deserialized.total_packets == start_pkt.total_packets, "Total packets uyuşmazlığı"
    assert deserialized.file_hash == file_hash, "File hash uyuşmazlığı"
    
    print("✓ StartPacket serileştirme: BAŞARILI\n")


def test_end_packet():
    """EndPacket testini yap"""
    print("=" * 50)
    print("TEST: EndPacket Serileştirme/Deserileştirme")
    print("=" * 50)
    
    end_pkt = EndPacket(total_packets=100)
    print(f"Orijinal END: {end_pkt}")
    
    # Serileştir
    serialized = end_pkt.serialize()
    print(f"Serileştirilmiş boyut: {len(serialized)} bytes")
    
    # Deserialize et
    deserialized = EndPacket.deserialize(serialized)
    print(f"Deserileştirilmiş END: {deserialized}")
    
    assert deserialized.total_packets == end_pkt.total_packets, "Total packets uyuşmazlığı"
    
    print("✓ EndPacket serileştirme: BAŞARILI\n")


def test_constants():
    """Sabitleri kontrol et"""
    print("=" * 50)
    print("TEST: Protokol Sabitleri")
    print("=" * 50)
    
    print(f"TIMEOUT: {Constants.TIMEOUT_SECONDS}s")
    print(f"MAX_RETRIES: {Constants.MAX_RETRIES}")
    print(f"PACKET_SIZE: {Constants.PACKET_SIZE} bytes")
    print(f"MAX_PAYLOAD: {Constants.MAX_PAYLOAD} bytes")
    print(f"ACK_SIZE: {Constants.ACK_SIZE} bytes")
    print(f"HEADER_SIZE: {Constants.HEADER_SIZE} bytes")
    
    print("✓ Sabitler kontrol edildi\n")


def main():
    """Tüm testleri çalıştır"""
    print("\n" + "="*50)
    print("NETPROBE PROTOKOL TESTLERI")
    print("="*50 + "\n")
    
    try:
        test_checksum()
        test_data_packet()
        test_ack_packet()
        test_start_packet()
        test_end_packet()
        test_constants()
        
        print("=" * 50)
        print("✓ TÜM TESTLER BAŞARILI!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ TEST HATASI: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()

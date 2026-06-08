"""
NetProbe Protokol Testleri — pytest uyumlu
"""

import pytest
from protocol import (
    DataPacket, AckPacket, StartPacket, EndPacket, NackPacket,
    PacketType, Constants, calculate_checksum, verify_checksum
)


# ──────────────────────────────────────────────
# Checksum testleri
# ──────────────────────────────────────────────

def test_checksum_dogru_veri():
    data = b"Merhaba Dunya! Test etmek icin"
    checksum = calculate_checksum(data)
    assert verify_checksum(data, checksum)


def test_checksum_yanlis_veri_reddedilir():
    data = b"Merhaba Dunya! Test etmek icin"
    checksum = calculate_checksum(data)
    assert not verify_checksum(b"yanlis veri", checksum)


def test_checksum_yanlis_checksum_reddedilir():
    data = b"test verisi"
    assert not verify_checksum(data, b"wrongchecksum12")


def test_checksum_bos_veri():
    data = b""
    checksum = calculate_checksum(data)
    assert verify_checksum(data, checksum)


def test_checksum_buyuk_veri():
    data = b"x" * 10000
    checksum = calculate_checksum(data)
    assert verify_checksum(data, checksum)


# ──────────────────────────────────────────────
# DataPacket testleri
# ──────────────────────────────────────────────

def test_data_packet_serialize_deserialize():
    payload = b"NetProbe Test Payload"
    pkt = DataPacket(seq_num=1, total_packets=10, payload=payload)
    deserialized = DataPacket.deserialize(pkt.serialize())

    assert deserialized.seq_num == 1
    assert deserialized.total_packets == 10
    assert deserialized.payload == payload


def test_data_packet_seq_num_sifir():
    pkt = DataPacket(seq_num=0, total_packets=5, payload=b"ilk paket")
    deserialized = DataPacket.deserialize(pkt.serialize())
    assert deserialized.seq_num == 0


def test_data_packet_buyuk_seq_num():
    pkt = DataPacket(seq_num=99999, total_packets=100000, payload=b"son paket")
    deserialized = DataPacket.deserialize(pkt.serialize())
    assert deserialized.seq_num == 99999


def test_data_packet_bos_payload():
    pkt = DataPacket(seq_num=0, total_packets=1, payload=b"")
    deserialized = DataPacket.deserialize(pkt.serialize())
    assert deserialized.payload == b""


def test_data_packet_max_payload():
    payload = b"A" * Constants.MAX_PAYLOAD
    pkt = DataPacket(seq_num=0, total_packets=1, payload=payload)
    deserialized = DataPacket.deserialize(pkt.serialize())
    assert deserialized.payload == payload


def test_data_packet_tip():
    pkt = DataPacket(seq_num=0, total_packets=1, payload=b"data")
    raw = pkt.serialize()
    assert raw[0] == PacketType.DATA


# ──────────────────────────────────────────────
# AckPacket testleri
# ──────────────────────────────────────────────

def test_ack_packet_serialize_deserialize():
    ack = AckPacket(ack_num=5)
    deserialized = AckPacket.deserialize(ack.serialize())
    assert deserialized.ack_num == 5


def test_ack_packet_sifir():
    ack = AckPacket(ack_num=0)
    deserialized = AckPacket.deserialize(ack.serialize())
    assert deserialized.ack_num == 0


def test_ack_packet_buyuk_num():
    ack = AckPacket(ack_num=99999)
    deserialized = AckPacket.deserialize(ack.serialize())
    assert deserialized.ack_num == 99999


def test_ack_packet_boyutu():
    ack = AckPacket(ack_num=1)
    assert len(ack.serialize()) == Constants.ACK_SIZE


def test_ack_packet_tip():
    ack = AckPacket(ack_num=0)
    raw = ack.serialize()
    assert raw[0] == PacketType.ACK


# ──────────────────────────────────────────────
# StartPacket testleri
# ──────────────────────────────────────────────

def test_start_packet_serialize_deserialize():
    file_hash = b"0" * 32
    pkt = StartPacket(total_packets=100, flags=3, file_hash=file_hash)
    deserialized = StartPacket.deserialize(pkt.serialize())

    assert deserialized.total_packets == 100
    assert deserialized.flags == 3
    assert deserialized.file_hash == file_hash


def test_start_packet_flags_sifir():
    pkt = StartPacket(total_packets=50, flags=0, file_hash=b"h" * 32)
    deserialized = StartPacket.deserialize(pkt.serialize())
    assert deserialized.flags == 0


def test_start_packet_hash_korunur():
    import hashlib
    file_hash = hashlib.sha256(b"test dosyasi").digest()
    pkt = StartPacket(total_packets=10, flags=0, file_hash=file_hash)
    deserialized = StartPacket.deserialize(pkt.serialize())
    assert deserialized.file_hash == file_hash


def test_start_packet_tip():
    pkt = StartPacket(total_packets=1, flags=0, file_hash=b"0" * 32)
    raw = pkt.serialize()
    assert raw[0] == PacketType.START


# ──────────────────────────────────────────────
# EndPacket testleri
# ──────────────────────────────────────────────

def test_end_packet_serialize_deserialize():
    pkt = EndPacket(total_packets=100)
    deserialized = EndPacket.deserialize(pkt.serialize())
    assert deserialized.total_packets == 100


def test_end_packet_tip():
    pkt = EndPacket(total_packets=1)
    raw = pkt.serialize()
    assert raw[0] == PacketType.END


# ──────────────────────────────────────────────
# NackPacket testleri
# ──────────────────────────────────────────────

def test_nack_packet_serialize_deserialize():
    pkt = NackPacket(nack_num=7)
    deserialized = NackPacket.deserialize(pkt.serialize())
    assert deserialized.nack_num == 7


def test_nack_packet_tip():
    pkt = NackPacket(nack_num=0)
    raw = pkt.serialize()
    assert raw[0] == PacketType.NACK


# ──────────────────────────────────────────────
# Protokol sabitleri testleri
# ──────────────────────────────────────────────

def test_sabitler_pozitif():
    assert Constants.TIMEOUT_SECONDS > 0
    assert Constants.MAX_RETRIES > 0
    assert Constants.PACKET_SIZE > 0
    assert Constants.MAX_PAYLOAD > 0
    assert Constants.ACK_SIZE > 0
    assert Constants.HEADER_SIZE > 0


def test_payload_header_toplami_packet_size():
    # PACKET_SIZE, header + payload toplamından büyük olabilir (padding/alignment)
    assert Constants.HEADER_SIZE + Constants.MAX_PAYLOAD <= Constants.PACKET_SIZE


def test_paket_tipleri_benzersiz():
    tipler = [PacketType.DATA, PacketType.ACK, PacketType.START, PacketType.END, PacketType.NACK]
    assert len(tipler) == len(set(tipler))

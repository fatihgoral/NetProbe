"""
NetProbe Protocol Module

UDP tabanlı güvenilir dosya aktarım protokolünün paket yapısı ve işlemleri
"""

import struct
import hashlib
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional


class PacketType(IntEnum):
    """Paket tipleri"""
    DATA = 0x01      # Veri paketi
    ACK = 0x02       # ACK paketi
    START = 0x03     # Başlama sinyali
    END = 0x04       # Bitiş sinyali
    NACK = 0x05      # Olumsuz ACK


class Constants:
    """Protokol sabitleri"""
    TIMEOUT_SECONDS = 2.0
    MAX_RETRIES = 5
    PACKET_SIZE = 1024
    MAX_PAYLOAD = 1000
    ACK_SIZE = 13  # 1 + 4 + 8 bytes
    HEADER_SIZE = 19  # 1 + 4 + 4 + 2 + 8 bytes (type + seq + total + paylen + checksum)


def calculate_checksum(data: bytes) -> bytes:
    """
    SHA-256 kullanarak checksum hesapla
    
    Args:
        data: Checksum'u hesaplanacak veri
        
    Returns:
        8 baytlık checksum (SHA-256'nın ilk 8 baytı)
    """
    hash_obj = hashlib.sha256(data)
    return hash_obj.digest()[:8]


def verify_checksum(data: bytes, checksum: bytes) -> bool:
    """
    Checksum doğrula
    
    Args:
        data: Doğrulanacak veri
        checksum: Beklenen checksum
        
    Returns:
        True eğer checksum doğruysa, False aksi halde
    """
    calculated = calculate_checksum(data)
    return calculated == checksum


@dataclass
class DataPacket:
    """Veri Paketi Yapısı"""
    packet_type: int = PacketType.DATA
    seq_num: int = 0
    total_packets: int = 0
    payload: bytes = b''
    
    def serialize(self) -> bytes:
        """
        Paketi bayt formatına dönüştür
        
        Format: [Type(1)] [Seq(4)] [Total(4)] [PayLen(2)] [Checksum(8)] [Payload(var)]
        
        Returns:
            Serileştirilmiş paket
        """
        payload_len = len(self.payload)
        
        # Checksum hesapla (payload için)
        checksum = calculate_checksum(self.payload)
        
        # Header'ı pack et (1 + 4 + 4 + 2 = 11 bytes)
        header = struct.pack(
            '!BIIH',
            self.packet_type,
            self.seq_num,
            self.total_packets,
            payload_len
        )
        
        # Komple paket: header + checksum + payload
        packet = header + checksum + self.payload
        return packet
    
    @staticmethod
    def deserialize(data: bytes) -> 'DataPacket':
        """
        Bayt formatından paketi aç
        
        Args:
            data: Serileştirilmiş paket
            
        Returns:
            DataPacket objesi
            
        Raises:
            ValueError: Paket format hatası
        """
        if len(data) < Constants.HEADER_SIZE:
            raise ValueError(f"Paket çok kısa: {len(data)} bytes")
        
        try:
            # Header'ı unpack et (1 + 4 + 4 + 2 = 11 bytes)
            packet_type, seq_num, total_packets, payload_len = struct.unpack(
                '!BIIH',
                data[:11]
            )
            
            # Checksum'u al (11-19)
            checksum = data[11:19]
            
            # Payload'ı al
            payload = data[19:19+payload_len]
            
            # Checksum doğrula
            if not verify_checksum(payload, checksum):
                raise ValueError("Checksum doğrulaması başarısız")
            
            return DataPacket(
                packet_type=packet_type,
                seq_num=seq_num,
                total_packets=total_packets,
                payload=payload
            )
        except struct.error as e:
            raise ValueError(f"Paket unpack hatası: {e}")
    
    def __repr__(self):
        return f"DataPacket(seq={self.seq_num}, total={self.total_packets}, len={len(self.payload)})"


@dataclass
class AckPacket:
    """ACK Paketi Yapısı"""
    packet_type: int = PacketType.ACK
    ack_num: int = 0
    
    def serialize(self) -> bytes:
        """
        ACK paketini bayt formatına dönüştür
        
        Format: [Type(1)] [AckNum(4)] [Checksum(8)]
        
        Returns:
            Serileştirilmiş ACK paketi
        """
        # Checksum hesapla (ack_num için)
        ack_bytes = struct.pack('!I', self.ack_num)
        checksum = calculate_checksum(ack_bytes)
        
        # Header + Checksum
        packet = struct.pack('!BI', self.packet_type, self.ack_num) + checksum
        return packet
    
    @staticmethod
    def deserialize(data: bytes) -> 'AckPacket':
        """
        Bayt formatından ACK paketini aç
        
        Args:
            data: Serileştirilmiş ACK paketi
            
        Returns:
            AckPacket objesi
            
        Raises:
            ValueError: Paket format hatası
        """
        if len(data) < Constants.ACK_SIZE:
            raise ValueError(f"ACK paketi çok kısa: {len(data)} bytes")
        
        try:
            # Header'ı unpack et
            packet_type, ack_num = struct.unpack('!BI', data[:5])
            
            # Checksum'u al
            checksum = data[5:13]
            
            # Checksum doğrula
            ack_bytes = struct.pack('!I', ack_num)
            if not verify_checksum(ack_bytes, checksum):
                raise ValueError("ACK Checksum doğrulaması başarısız")
            
            return AckPacket(
                packet_type=packet_type,
                ack_num=ack_num
            )
        except struct.error as e:
            raise ValueError(f"ACK unpack hatası: {e}")
    
    def __repr__(self):
        return f"AckPacket(ack={self.ack_num})"


@dataclass
class NackPacket:
    """NACK (Negative ACK) Paketi YapÄ±sÄ±"""
    packet_type: int = PacketType.NACK
    nack_num: int = 0
    
    def serialize(self) -> bytes:
        """
        NACK paketini bayt formatÄ±na dÃ¶nÃ¼ÅtÃ¼r
        
        Format: [Type(1)] [NackNum(4)] [Checksum(8)]
        
        Returns:
            SerileÅtirilmiÅ NACK paketi
        """
        # Checksum hesapla (nack_num iÃ§in)
        nack_bytes = struct.pack('!I', self.nack_num)
        checksum = calculate_checksum(nack_bytes)
        
        # Header + Checksum
        packet = struct.pack('!BI', self.packet_type, self.nack_num) + checksum
        return packet
    
    @staticmethod
    def deserialize(data: bytes) -> 'NackPacket':
        """
        Bayt formatÄ±ndan NACK paketini aÃ§
        """
        if len(data) < Constants.ACK_SIZE:
            raise ValueError(f"NACK paketi Ã§ok kÄ±sa: {len(data)} bytes")
        
        try:
            # Header'Ä± unpack et
            packet_type, nack_num = struct.unpack('!BI', data[:5])
            
            # Checksum'u al
            checksum = data[5:13]
            
            # Checksum doÄrula
            nack_bytes = struct.pack('!I', nack_num)
            if not verify_checksum(nack_bytes, checksum):
                raise ValueError("NACK Checksum doÄrulamasÄ± baÅarÄ±sÄ±z")
            
            return NackPacket(
                packet_type=packet_type,
                nack_num=nack_num
            )
        except struct.error as e:
            raise ValueError(f"NACK unpack hatasÄ±: {e}")
    
    def __repr__(self):
        return f"NackPacket(nack={self.nack_num})"


@dataclass
class StartPacket:
    """Başlama Paketi (dosya bilgileri)"""
    packet_type: int = PacketType.START
    total_packets: int = 0
    flags: int = 0  # Bit 0: Compress, Bit 1: Encrypt
    file_hash: bytes = b''  # SHA-256 hash (32 bytes)
    
    def serialize(self) -> bytes:
        """Başlama paketini bayt formatına dönüştür"""
        packet = struct.pack('!BIB', self.packet_type, self.total_packets, self.flags)
        packet += self.file_hash
        checksum = calculate_checksum(self.file_hash + bytes([self.flags]))
        packet += checksum
        return packet
    
    @staticmethod
    def deserialize(data: bytes) -> 'StartPacket':
        """Başlama paketini aç"""
        if len(data) < 14:
            raise ValueError("START paketi çok kısa")
        
        packet_type, total_packets, flags = struct.unpack('!BIB', data[:6])
        file_hash = data[6:38]
        checksum = data[38:46]
        
        if not verify_checksum(file_hash + bytes([flags]), checksum):
            raise ValueError("START paketi checksum hatası")
        
        return StartPacket(
            packet_type=packet_type,
            total_packets=total_packets,
            flags=flags,
            file_hash=file_hash
        )


@dataclass
class EndPacket:
    """Bitiş Paketi"""
    packet_type: int = PacketType.END
    total_packets: int = 0
    
    def serialize(self) -> bytes:
        """Bitiş paketini bayt formatına dönüştür"""
        return struct.pack('!BI', self.packet_type, self.total_packets)
    
    @staticmethod
    def deserialize(data: bytes) -> 'EndPacket':
        """Bitiş paketini aç"""
        if len(data) < 5:
            raise ValueError("END paketi çok kısa")
        
        packet_type, total_packets = struct.unpack('!BI', data[:5])
        return EndPacket(
            packet_type=packet_type,
            total_packets=total_packets
        )

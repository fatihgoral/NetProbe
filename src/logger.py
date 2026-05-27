"""
NetProbe Logger Module

Transfer olaylarını CSV formatında kayıt etme sistemi
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from enum import Enum


class EventType(Enum):
    """Olay tipleri"""
    SEND = "SEND"
    ACK_RECEIVED = "ACK_RECEIVED"
    TIMEOUT = "TIMEOUT"
    RETRY = "RETRY"
    DUPLICATE = "DUPLICATE"
    ERROR = "ERROR"
    START = "START"
    END = "END"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Logger:
    """Transfer olaylarını CSV'ye log eden sınıf"""
    
    def __init__(self, log_dir: str = "logs", log_file: str = "transfer_log.csv"):
        """
        Logger başlat
        
        Args:
            log_dir: Log dosyaları dizini
            log_file: Log dosyası adı
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.log_dir / log_file
        self.events: List[Dict[str, Any]] = []
        
        # CSV header'ını oluştur
        self._init_csv()
    
    def _init_csv(self):
        """CSV dosyasını başlat (header ekle)"""
        if not self.log_file.exists():
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp',
                    'Event_Type',
                    'SeqNum',
                    'Retries',
                    'Status',
                    'Details'
                ])
    
    def log_event(self,
                  event_type: EventType,
                  seq_num: int = -1,
                  retries: int = 0,
                  status: str = "OK",
                  details: str = ""):
        """
        Olay log et
        
        Args:
            event_type: Olay tipi (EventType)
            seq_num: Paket sequence numarası
            retries: Deneme sayısı
            status: Durum (OK, RETRY, ERROR, vb.)
            details: Detaylı açıklama
        """
        timestamp = datetime.now().isoformat(timespec='milliseconds')
        
        event = {
            'Timestamp': timestamp,
            'Event_Type': event_type.value,
            'SeqNum': seq_num,
            'Retries': retries,
            'Status': status,
            'Details': details
        }
        
        self.events.append(event)
        self._write_to_csv(event)
        
        print(f"[{timestamp}] {event_type.value} - Seq:{seq_num} - Retries:{retries} - {status}")
    
    def _write_to_csv(self, event: Dict[str, Any]):
        """Tek olayı CSV'ye yaz"""
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Timestamp', 'Event_Type', 'SeqNum', 'Retries', 'Status', 'Details'
            ])
            writer.writerow(event)
    
    def log_transfer_start(self, filename: str, file_size: int):
        """Transfer başlangıç log et"""
        self.log_event(
            event_type=EventType.START,
            status="OK",
            details=f"Dosya: {filename}, Boyut: {file_size} bytes"
        )
    
    def log_transfer_end(self, total_packets: int, successful: int):
        """Transfer bitiş log et"""
        success_rate = (successful / total_packets * 100) if total_packets > 0 else 0
        self.log_event(
            event_type=EventType.END,
            status="OK",
            details=f"Toplam: {total_packets}, Başarılı: {successful}, Oran: {success_rate:.2f}%"
        )
    
    def log_send(self, seq_num: int, payload_size: int):
        """Paket gönderimi log et"""
        self.log_event(
            event_type=EventType.SEND,
            seq_num=seq_num,
            retries=0,
            status="OK",
            details=f"Paket boyutu: {payload_size} bytes"
        )
    
    def log_ack_received(self, ack_num: int):
        """ACK alımını log et"""
        self.log_event(
            event_type=EventType.ACK_RECEIVED,
            seq_num=ack_num,
            status="OK",
            details=""
        )
    
    def log_timeout(self, seq_num: int, retry_count: int):
        """Timeout olayını log et"""
        self.log_event(
            event_type=EventType.TIMEOUT,
            seq_num=seq_num,
            retries=retry_count,
            status="RETRY",
            details=f"Timeout oluştu, {retry_count}. deneme"
        )
    
    def log_duplicate(self, seq_num: int):
        """Duplicate paket log et"""
        self.log_event(
            event_type=EventType.DUPLICATE,
            seq_num=seq_num,
            status="IGNORED",
            details="Duplicate paket yok sayıldı"
        )
    
    def log_error(self, seq_num: int, error_msg: str):
        """Hata log et"""
        self.log_event(
            event_type=EventType.ERROR,
            seq_num=seq_num,
            status="ERROR",
            details=error_msg
        )
    
    def log_packet_failed(self, seq_num: int, max_retries: int):
        """Başarısız paket log et"""
        self.log_event(
            event_type=EventType.FAILED,
            seq_num=seq_num,
            retries=max_retries,
            status="FAILED",
            details=f"Paket {max_retries} deneme sonrası başarısız"
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Log özeti al"""
        summary = {
            'total_events': len(self.events),
            'send_count': sum(1 for e in self.events if e['Event_Type'] == 'SEND'),
            'ack_count': sum(1 for e in self.events if e['Event_Type'] == 'ACK_RECEIVED'),
            'timeout_count': sum(1 for e in self.events if e['Event_Type'] == 'TIMEOUT'),
            'error_count': sum(1 for e in self.events if e['Event_Type'] == 'ERROR'),
            'failed_count': sum(1 for e in self.events if e['Event_Type'] == 'FAILED'),
        }
        return summary
    
    def print_summary(self):
        """Özeti yazdır"""
        summary = self.get_summary()
        print("\n" + "="*50)
        print("TRANSFER ÖZETI")
        print("="*50)
        print(f"Toplam Olaylar: {summary['total_events']}")
        print(f"Gönderilen Paketler: {summary['send_count']}")
        print(f"Alınan ACK'ler: {summary['ack_count']}")
        print(f"Timeout Olayları: {summary['timeout_count']}")
        print(f"Hata Sayısı: {summary['error_count']}")
        print(f"Başarısız Paketler: {summary['failed_count']}")
        print("="*50 + "\n")


# Global logger instance
_logger_instance: Logger = None


def get_logger(log_dir: str = "logs", log_file: str = "transfer_log.csv") -> Logger:
    """Singleton logger instance al"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger(log_dir, log_file)
    return _logger_instance


def reset_logger():
    """Logger'ı sıfırla (test için)"""
    global _logger_instance
    _logger_instance = None

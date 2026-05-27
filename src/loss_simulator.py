"""
NetProbe Loss Simulator

Gerçek ağ koşullarını simüle etmek için yapay paket kaybı oluşturucu.
Sunucu tarafında ACK gönderimini rastgele engeller.
"""

import random
import threading


class LossSimulator:
    """
    Paket kaybı simülatörü.
    
    ACK gönderme işlemini belirtilen kayıp oranına göre rastgele engeller.
    Sunucu koduna entegre edilmek üzere tasarlanmıştır.
    """
    
    def __init__(self, loss_rate: float = 0.0, seed: int = None):
        """
        Simülatörü başlat.
        
        Args:
            loss_rate: Paket kayıp oranı (0.0 = kayıp yok, 1.0 = tamamı kayıp)
            seed: Rastgele sayı üreteci seed (tekrarlanabilir testler için)
        """
        self.loss_rate = loss_rate
        self._lock = threading.Lock()
        self._dropped_count = 0
        self._total_count = 0
        
        if seed is not None:
            random.seed(seed)
    
    def should_drop(self) -> bool:
        """
        Bu paketin düşürülmesi gerekip gerekmediğini belirle.
        
        Returns:
            True eğer paket düşürülmeli, False aksi halde
        """
        with self._lock:
            self._total_count += 1
            drop = random.random() < self.loss_rate
            if drop:
                self._dropped_count += 1
            return drop
    
    def should_drop_ack(self, seq_num: int) -> bool:
        """
        ACK paketini düşürüp düşürmeyeceğimizi belirle.
        
        Args:
            seq_num: Paket sequence numarası (loglama için)
            
        Returns:
            True eğer ACK düşürülmeli (yani kayıp simüle ediliyor)
        """
        return self.should_drop()
    
    def get_stats(self) -> dict:
        """
        Simülasyon istatistiklerini döndür.
        
        Returns:
            Simülasyon istatistikleri
        """
        with self._lock:
            actual_loss = (self._dropped_count / self._total_count * 100) if self._total_count > 0 else 0
            return {
                'configured_loss_rate': self.loss_rate * 100,
                'total_packets': self._total_count,
                'dropped_packets': self._dropped_count,
                'actual_loss_rate': actual_loss
            }
    
    def reset(self):
        """İstatistikleri sıfırla"""
        with self._lock:
            self._dropped_count = 0
            self._total_count = 0
    
    def set_loss_rate(self, loss_rate: float):
        """
        Kayıp oranını güncelle.
        
        Args:
            loss_rate: Yeni kayıp oranı (0.0 - 1.0)
        """
        with self._lock:
            self.loss_rate = max(0.0, min(1.0, loss_rate))
    
    def __repr__(self):
        stats = self.get_stats()
        return (f"LossSimulator(configured={stats['configured_loss_rate']:.1f}%, "
                f"actual={stats['actual_loss_rate']:.1f}%, "
                f"dropped={stats['dropped_packets']}/{stats['total_packets']})")


# Global loss simulator instance (senaryo 3 için)
_loss_simulator: LossSimulator = None


def get_loss_simulator(loss_rate: float = 0.0) -> LossSimulator:
    """Global loss simulator instance al veya oluştur"""
    global _loss_simulator
    if _loss_simulator is None:
        _loss_simulator = LossSimulator(loss_rate=loss_rate)
    return _loss_simulator


def set_loss_rate(loss_rate: float):
    """Global kayıp oranını ayarla"""
    global _loss_simulator
    if _loss_simulator is None:
        _loss_simulator = LossSimulator(loss_rate=loss_rate)
    else:
        _loss_simulator.set_loss_rate(loss_rate)
        _loss_simulator.reset()


def reset_loss_simulator():
    """Loss simulator'ı sıfırla"""
    global _loss_simulator
    _loss_simulator = None

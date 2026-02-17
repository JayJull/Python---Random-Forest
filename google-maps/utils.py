"""
utils.py
Fungsi-fungsi helper untuk mendukung proses scraping
"""

import random
import time
from datetime import datetime
import config

def get_random_delay(min_delay=None, max_delay=None):
    """
    Menghasilkan delay acak untuk simulasi perilaku manusia
    
    Args:
        min_delay: Delay minimum (detik)
        max_delay: Delay maksimum (detik)
    
    Returns:
        float: Delay acak dalam detik
    """
    if min_delay is None:
        min_delay = config.MIN_SCROLL_DELAY
    if max_delay is None:
        max_delay = config.MAX_SCROLL_DELAY
    
    return random.uniform(min_delay, max_delay)

def get_random_user_agent():
    """
    Memilih User Agent secara acak dari list
    
    Returns:
        str: User Agent string
    """
    return random.choice(config.USER_AGENTS)

def log_message(message, level="INFO"):
    """
    Logging dengan timestamp
    
    Args:
        message: Pesan yang akan di-log
        level: Level log (INFO, WARNING, ERROR)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def sanitize_text(text):
    """
    Membersihkan teks dari karakter yang tidak diinginkan
    
    Args:
        text: Teks yang akan dibersihkan
    
    Returns:
        str: Teks yang sudah dibersihkan
    """
    if not text:
        return ""
    
    # Hapus whitespace berlebih
    text = " ".join(text.split())
    
    # Hapus karakter khusus yang bisa merusak CSV
    text = text.replace('\n', ' ').replace('\r', ' ')
    
    return text.strip()

def extract_rating(rating_text):
    """
    Ekstrak nilai rating dari teks
    
    Args:
        rating_text: Teks yang mengandung rating
    
    Returns:
        float: Nilai rating atau 0.0 jika tidak ada
    """
    try:
        # Ambil angka pertama yang ditemukan
        rating = float(rating_text.split()[0].replace(',', '.'))
        return rating
    except:
        return 0.0

def extract_review_count(review_text):
    """
    Ekstrak jumlah ulasan dari teks
    
    Args:
        review_text: Teks yang mengandung jumlah ulasan
    
    Returns:
        int: Jumlah ulasan atau 0 jika tidak ada
    """
    try:
        # Hapus karakter non-digit
        number = ''.join(filter(str.isdigit, review_text))
        return int(number) if number else 0
    except:
        return 0

def format_phone_number(phone):
    """
    Format nomor telepon ke format standar
    
    Args:
        phone: Nomor telepon mentah
    
    Returns:
        str: Nomor telepon terformat atau string kosong
    """
    if not phone:
        return ""
    
    # Hapus semua karakter non-digit kecuali +
    phone = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Standardisasi format Indonesia
    if phone.startswith('0'):
        phone = '62' + phone[1:]
    elif not phone.startswith('+') and not phone.startswith('62'):
        phone = '62' + phone
    
    return phone

def is_timeout_reached(start_time, max_hours=None):
    """
    Cek apakah timeout sudah tercapai
    
    Args:
        start_time: Waktu mulai (timestamp)
        max_hours: Maksimal jam (default dari config)
    
    Returns:
        bool: True jika timeout tercapai
    """
    if max_hours is None:
        max_hours = config.TIMEOUT_HOURS
    
    elapsed_hours = (time.time() - start_time) / 3600
    return elapsed_hours >= max_hours
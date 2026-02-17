"""
config.py
Berisi konfigurasi global untuk sistem scraping
"""

# Konfigurasi Batas Scraping
MAX_DATA_LIMIT = 50  # Maksimal 50 data per scraping
TIMEOUT_HOURS = 2    # Timeout maksimal 2 jam
SCROLL_DELAY = 2     # Delay antar scroll (detik)
CLICK_DELAY = 2      # Delay antar klik (detik)
MAX_SCROLL_ATTEMPTS = 80  # Maksimal percobaan scroll

# Konfigurasi Retry
MAX_RETRY_PER_BUSINESS = 3  # Maksimal retry jika gagal ambil data
BACK_TO_LIST_DELAY = 0.5    # Delay setelah kembali ke list

# Konfigurasi Browser
HEADLESS_MODE = False  # Set True untuk mode tanpa GUI
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080

# Konfigurasi Anti-Detection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# Delay random untuk simulasi perilaku manusia
MIN_SCROLL_DELAY = 1.2
MAX_SCROLL_DELAY = 2.5
MIN_CLICK_DELAY = 1.5
MAX_CLICK_DELAY = 2.5

# Output Configuration
OUTPUT_FOLDER = 'output'
CSV_FILENAME = 'google_maps_data.csv'
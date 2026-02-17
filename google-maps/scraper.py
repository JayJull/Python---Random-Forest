"""
scraper.py
Class utama untuk melakukan scraping data dari Google Maps
"""

import time
import random
from playwright.sync_api import TimeoutError as PlaywrightTimeout
import config
import utils

class GoogleMapsScraper:
    """
    Class untuk scraping data bisnis dari Google Maps
    """
    
    def __init__(self, page):
        self.page = page
        self.data_collected = []
        self.processed_names = set()  # Untuk menghindari duplikasi
        self.duplicate_counter = {}    # Track berapa kali nama muncul
        self.failed_indices = set()    # Track index yang gagal/duplikat
        self.max_duplicate_attempts = 2  # Maksimal 2x duplikat, lalu skip
    
    def search_location(self, search_query):
        """
        Melakukan pencarian lokasi di Google Maps
        
        Args:
            search_query: Kata kunci pencarian (misal: "Kafe di Banyuwangi")
        """
        utils.log_message(f"Memulai pencarian: {search_query}")
        
        # Buka Google Maps
        url = f"https://www.google.com/maps/search/{search_query}"
        self.page.goto(url, wait_until="domcontentloaded")
        
        # Tunggu hasil pencarian muncul
        time.sleep(utils.get_random_delay(3, 5))
        
        utils.log_message("Halaman pencarian dimuat")
    
    def scroll_results(self, max_scrolls=50):
        """
        Scroll panel hasil pencarian untuk memuat semua bisnis
        
        Args:
            max_scrolls: Maksimal jumlah scroll
        """
        utils.log_message("Memulai scrolling untuk memuat data...")
        
        try:
            # Selector untuk panel hasil
            results_panel = 'div[role="feed"]'
            
            # Tunggu panel muncul
            self.page.wait_for_selector(results_panel, timeout=10000)
            
            previous_height = 0
            scroll_count = 0
            no_change_count = 0
            
            while scroll_count < max_scrolls:
                # Scroll ke bawah dengan JavaScript yang benar
                self.page.evaluate('''
                    (selector) => {
                        const element = document.querySelector(selector);
                        if (element) {
                            element.scrollTo(0, element.scrollHeight);
                        }
                    }
                ''', results_panel)
                
                # Delay random untuk simulasi manusia
                time.sleep(utils.get_random_delay(1.5, 2.5))
                
                # Cek tinggi panel
                current_height = self.page.evaluate('''
                    (selector) => {
                        const element = document.querySelector(selector);
                        return element ? element.scrollHeight : 0;
                    }
                ''', results_panel)
                
                # Jika tinggi tidak berubah, berarti sudah sampai bawah
                if current_height == previous_height:
                    no_change_count += 1
                    if no_change_count >= 3:
                        utils.log_message("Sudah mencapai akhir hasil pencarian")
                        break
                else:
                    no_change_count = 0
                
                previous_height = current_height
                scroll_count += 1
                
                # Cek jumlah data yang sudah terlihat
                visible_items = self.page.locator('a[href*="/maps/place/"]').count()
                utils.log_message(f"Scroll {scroll_count}/{max_scrolls} - Item terlihat: {visible_items}")
                
                # Jika sudah cukup data, stop
                if visible_items >= config.MAX_DATA_LIMIT + 10:  # Tambah buffer
                    utils.log_message(f"Target {config.MAX_DATA_LIMIT} item tercapai")
                    break
        
        except Exception as e:
            utils.log_message(f"Error saat scrolling: {str(e)}", "ERROR")
    
    def extract_business_data(self):
        """
        Ekstrak data bisnis dari hasil pencarian dengan navigasi yang benar
        Anti-stuck dengan skip otomatis setelah 2x duplikat
        
        Returns:
            list: List dictionary berisi data bisnis
        """
        utils.log_message("Mulai ekstraksi data bisnis...")
        
        try:
            # Selector untuk panel list hasil
            results_panel = 'div[role="feed"]'
            
            # Loop hingga mencapai target
            current_index = 0
            consecutive_failures = 0
            max_consecutive_failures = 5  # Skip setelah 5x gagal berturut-turut
            
            while len(self.data_collected) < config.MAX_DATA_LIMIT:
                try:
                    # Pastikan kita di panel list
                    self.page.wait_for_selector(results_panel, timeout=5000)
                    
                    # Ambil semua link bisnis yang terlihat
                    business_links = self.page.locator('a[href*="/maps/place/"]').all()
                    total_links = len(business_links)
                    
                    if total_links == 0:
                        utils.log_message("Tidak ada bisnis ditemukan", "WARNING")
                        break
                    
                    # Jika index melebihi jumlah link, scroll lagi
                    if current_index >= total_links:
                        utils.log_message(f"Perlu scroll lebih untuk index {current_index}")
                        self.scroll_results(max_scrolls=10)
                        
                        # Refresh link
                        business_links = self.page.locator('a[href*="/maps/place/"]').all()
                        total_links = len(business_links)
                        
                        # Jika masih kurang, berarti sudah habis
                        if current_index >= total_links:
                            utils.log_message("Sudah tidak ada data lagi")
                            break
                    
                    # Skip index yang sudah gagal berkali-kali
                    if current_index in self.failed_indices:
                        utils.log_message(f"⏭ Skip index {current_index} (sudah gagal/duplikat)")
                        current_index += 1
                        continue
                    
                    utils.log_message(f"\n📍 Index {current_index}/{total_links} (Terkumpul: {len(self.data_collected)}/{config.MAX_DATA_LIMIT})")
                    
                    # Refresh link sebelum klik
                    business_links = self.page.locator('a[href*="/maps/place/"]').all()
                    
                    if current_index >= len(business_links):
                        utils.log_message("Index melebihi jumlah link, skip")
                        current_index += 1
                        continue
                    
                    target_link = business_links[current_index]
                    
                    # Klik link untuk membuka detail
                    target_link.click()
                    
                    # Tunggu panel detail muncul
                    time.sleep(utils.get_random_delay(2, 3))
                    
                    # Ekstrak data dari panel detail
                    business_data = self._extract_detail_panel()
                    
                    # Validasi data - HANYA cek nama bisnis untuk duplikasi
                    if not business_data.get('nama_bisnis') or business_data['nama_bisnis'] == '':
                        utils.log_message(f"✗ Nama bisnis kosong")
                        consecutive_failures += 1
                        
                        # Tandai index ini sebagai failed
                        self.failed_indices.add(current_index)
                        
                        # Kembali ke list
                        self._back_to_list()
                        current_index += 1
                        continue
                    
                    nama = business_data['nama_bisnis']
                    
                    # Cek duplikasi dengan counter
                    if nama in self.processed_names:
                        # Tambah counter duplikat
                        if nama not in self.duplicate_counter:
                            self.duplicate_counter[nama] = 1
                        else:
                            self.duplicate_counter[nama] += 1
                        
                        duplicate_count = self.duplicate_counter[nama]
                        
                        utils.log_message(f"✗ Duplikat: {nama} (ke-{duplicate_count}x)")
                        
                        # Jika sudah 2x duplikat, tandai index ini dan skip
                        if duplicate_count >= self.max_duplicate_attempts:
                            utils.log_message(f"⚠ Index {current_index} sudah {duplicate_count}x duplikat, skip permanen!")
                            self.failed_indices.add(current_index)
                        
                        consecutive_failures += 1
                        
                        # Kembali ke list
                        self._back_to_list()
                        current_index += 1
                        continue
                    
                    # Data valid dan unik! Simpan
                    self.data_collected.append(business_data)
                    self.processed_names.add(nama)
                    consecutive_failures = 0  # Reset counter
                    
                    utils.log_message(f"✓ Data tersimpan: {nama}")
                    
                    # Log info kelengkapan
                    info = []
                    if business_data.get('no_telepon'):
                        info.append("☎️")
                    if business_data.get('website') and business_data['website'] != '0':
                        info.append("🌐")
                    if business_data.get('rating') > 0:
                        info.append(f"⭐{business_data['rating']}")
                    
                    if info:
                        utils.log_message(f"   Info: {' '.join(info)}")
                    
                    # Kembali ke list untuk proses berikutnya
                    self._back_to_list()
                    
                    # Pindah ke index berikutnya
                    current_index += 1
                    
                    # Delay sebelum proses berikutnya
                    time.sleep(utils.get_random_delay(0.5, 1))
                
                except Exception as e:
                    utils.log_message(f"⚠ Error pada index {current_index}: {str(e)}", "WARNING")
                    consecutive_failures += 1
                    
                    # Tandai index ini sebagai failed
                    self.failed_indices.add(current_index)
                    
                    # Coba kembali ke list jika error
                    try:
                        self._back_to_list()
                    except:
                        pass
                    
                    current_index += 1
                    
                    # Jika terlalu banyak gagal berturut-turut, break
                    if consecutive_failures >= max_consecutive_failures:
                        utils.log_message(f"⚠ Terlalu banyak kegagalan berturut-turut ({consecutive_failures}x), mungkin sudah habis data", "WARNING")
                        break
                    
                    continue
            
            utils.log_message(f"\n✓ Ekstraksi selesai: {len(self.data_collected)} data terkumpul")
            utils.log_message(f"📊 Statistik: {len(self.failed_indices)} index diskip karena duplikat/error")
        
        except Exception as e:
            utils.log_message(f"Error ekstraksi data: {str(e)}", "ERROR")
        
        return self.data_collected
    
    def _back_to_list(self):
        """
        Kembali ke panel list hasil pencarian
        """
        try:
            # Cara 1: Klik tombol back (panah kiri)
            back_button = self.page.locator('button[aria-label*="Kembali"]').first
            if back_button.count() > 0:
                back_button.click()
                time.sleep(0.5)
                return
        except:
            pass
        
        try:
            # Cara 2: Klik area list panel
            results_panel = self.page.locator('div[role="feed"]').first
            if results_panel.count() > 0:
                results_panel.click()
                time.sleep(0.5)
                return
        except:
            pass
        
        try:
            # Cara 3: Tekan tombol Escape
            self.page.keyboard.press('Escape')
            time.sleep(0.5)
        except:
            pass
    
    def _extract_detail_panel(self):
        """
        Ekstrak data dari panel detail bisnis
        Tetap ambil data meskipun beberapa field kosong
        
        Returns:
            dict: Dictionary berisi data bisnis
        """
        data = {
            'nama_bisnis': '',
            'kategori': '',
            'rating': 0.0,
            'jumlah_ulasan': 0,
            'no_telepon': '',
            'website': '',
            'alamat': ''
        }
        
        try:
            # Tunggu panel detail muncul
            self.page.wait_for_selector('h1.DUwDvf', timeout=5000)
            
            # Nama bisnis - WAJIB ADA
            try:
                # Selector utama
                nama = self.page.locator('h1.DUwDvf').first.inner_text(timeout=3000)
                if nama:
                    data['nama_bisnis'] = utils.sanitize_text(nama)
            except:
                # Coba selector alternatif
                try:
                    nama = self.page.locator('h1[class*="fontHeadline"]').first.inner_text(timeout=2000)
                    if nama:
                        data['nama_bisnis'] = utils.sanitize_text(nama)
                except:
                    utils.log_message("Nama bisnis tidak ditemukan", "WARNING")
            
            # FIELD OPSIONAL - Tetap lanjut meskipun kosong
            
            # Kategori
            try:
                kategori = self.page.locator('button[jsaction*="category"]').first.inner_text(timeout=2000)
                if kategori:
                    data['kategori'] = utils.sanitize_text(kategori)
            except:
                try:
                    kategori = self.page.locator('button[class*="DkEaL"]').first.inner_text(timeout=1000)
                    if kategori:
                        data['kategori'] = utils.sanitize_text(kategori)
                except:
                    pass  # Kategori kosong tidak masalah
            
            # Rating dan Ulasan
            try:
                rating_text = self.page.locator('div.F7nice span[aria-hidden="true"]').first.inner_text(timeout=2000)
                if rating_text:
                    data['rating'] = utils.extract_rating(rating_text)
                
                review_text = self.page.locator('div.F7nice span[aria-label*="ulasan"]').first.inner_text(timeout=2000)
                if review_text:
                    data['jumlah_ulasan'] = utils.extract_review_count(review_text)
            except:
                try:
                    rating_element = self.page.locator('span.ceNzKf[aria-hidden="true"]').first
                    if rating_element:
                        rating_text = rating_element.inner_text(timeout=1000)
                        data['rating'] = utils.extract_rating(rating_text)
                except:
                    pass  # Rating kosong tidak masalah
            
            # Alamat
            try:
                alamat = self.page.locator('button[data-item-id="address"]').first.inner_text(timeout=2000)
                if alamat:
                    data['alamat'] = utils.sanitize_text(alamat)
            except:
                try:
                    alamat = self.page.locator('button[data-item-id*="address"]').first.get_attribute('aria-label', timeout=1000)
                    if alamat:
                        data['alamat'] = utils.sanitize_text(alamat)
                except:
                    pass  # Alamat kosong tidak masalah
            
            # Nomor Telepon
            try:
                phone_button = self.page.locator('button[data-item-id*="phone"]').first
                if phone_button:
                    phone = phone_button.get_attribute('data-item-id', timeout=2000)
                    if phone and ':' in phone:
                        phone_number = phone.split(':')[-1]
                        data['no_telepon'] = utils.format_phone_number(phone_number)
            except:
                try:
                    phone_button = self.page.locator('button[aria-label*="Telepon"]').first
                    if phone_button:
                        aria_label = phone_button.get_attribute('aria-label', timeout=1000)
                        if aria_label:
                            import re
                            phone_match = re.search(r'[\d\s\+\-\(\)]+', aria_label)
                            if phone_match:
                                data['no_telepon'] = utils.format_phone_number(phone_match.group())
                except:
                    pass  # Telepon kosong tidak masalah
            
            # Website (set 0 jika kosong)
            try:
                website = self.page.locator('a[data-item-id="authority"]').first.get_attribute('href', timeout=2000)
                if website:
                    data['website'] = utils.sanitize_text(website)
                else:
                    data['website'] = '0'
            except:
                try:
                    website_link = self.page.locator('a[aria-label*="Situs"]').first
                    if website_link:
                        website = website_link.get_attribute('href', timeout=1000)
                        if website:
                            data['website'] = utils.sanitize_text(website)
                        else:
                            data['website'] = '0'
                    else:
                        data['website'] = '0'
                except:
                    data['website'] = '0'  # Website kosong = 0
        
        except Exception as e:
            utils.log_message(f"Error ekstraksi detail: {str(e)}", "WARNING")
        
        return data
    
    def get_collected_data(self):
        """
        Mendapatkan semua data yang telah dikumpulkan
        
        Returns:
            list: List dictionary berisi data bisnis
        """
        return self.data_collected
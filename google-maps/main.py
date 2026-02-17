"""
main.py
Program utama untuk menjalankan Google Maps Scraper
"""

import time
import sys
from browser_manager import BrowserManager
from scraper import GoogleMapsScraper
from data_manager import DataManager
import config
import utils

def main():
    """
    Fungsi utama aplikasi
    """
    print("\n" + "="*70)
    print("GOOGLE MAPS SCRAPER - INERSIA DEV")
    print("Sistem Klasifikasi Kelayakan Prospek Klien")
    print("="*70 + "\n")
    
    # Input dari user
    search_query = input("Masukkan keyword pencarian (contoh: 'Kafe di Banyuwangi'): ").strip()
    
    if not search_query:
        utils.log_message("Keyword pencarian tidak boleh kosong!", "ERROR")
        return
    
    utils.log_message(f"Keyword: {search_query}")
    utils.log_message(f"Target data: {config.MAX_DATA_LIMIT} bisnis")
    utils.log_message(f"Timeout maksimal: {config.TIMEOUT_HOURS} jam\n")
    
    # Konfirmasi
    confirm = input("Lanjutkan scraping? (y/n): ").strip().lower()
    if confirm != 'y':
        utils.log_message("Scraping dibatalkan")
        return
    
    print("\n" + "-"*70 + "\n")
    
    # Inisialisasi komponen
    browser_manager = BrowserManager()
    data_manager = DataManager()
    
    start_time = time.time()
    
    try:
        # 1. Launch browser
        page = browser_manager.launch_browser()
        
        # 2. Inisialisasi scraper
        scraper = GoogleMapsScraper(page)
        
        # 3. Cari lokasi
        scraper.search_location(search_query)
        
        # 4. Scroll untuk load semua hasil
        scraper.scroll_results(max_scrolls=50)  # Tingkatkan ke 50 scroll
        
        # 5. Ekstrak data bisnis
        utils.log_message("\n" + "="*70)
        utils.log_message("MEMULAI EKSTRAKSI DATA")
        utils.log_message("="*70 + "\n")
        
        collected_data = scraper.extract_business_data()
        
        # 6. Cek timeout
        if utils.is_timeout_reached(start_time):
            utils.log_message("⚠ Timeout tercapai, menghentikan scraping", "WARNING")
        
        # 7. Validasi data
        utils.log_message("\n" + "="*70)
        utils.log_message("VALIDASI DATA")
        utils.log_message("="*70 + "\n")
        
        validation_result = data_manager.validate_data(collected_data)
        
        if validation_result['valid']:
            utils.log_message(f"✓ Data valid: {validation_result['total_rows']} baris")
            
            # Tampilkan kelengkapan data
            utils.log_message("\nKelengkapan Data:")
            for field, percent in validation_result['completeness_percent'].items():
                status = "✓" if percent >= 80 else "⚠"
                utils.log_message(f"  {status} {field}: {percent:.1f}%")
        else:
            utils.log_message("⚠ Data tidak memenuhi standar kualitas minimum", "WARNING")
        
        # 8. Tampilkan ringkasan
        data_manager.print_summary(collected_data)
        
        # 9. Simpan ke CSV
        utils.log_message("\n" + "="*70)
        utils.log_message("MENYIMPAN DATA")
        utils.log_message("="*70 + "\n")
        
        filepath = data_manager.save_to_csv(collected_data, search_query)
        
        # 10. Statistik akhir
        elapsed_time = time.time() - start_time
        elapsed_minutes = elapsed_time / 60
        
        utils.log_message("\n" + "="*70)
        utils.log_message("SCRAPING SELESAI")
        utils.log_message("="*70)
        utils.log_message(f"Total waktu: {elapsed_minutes:.2f} menit")
        utils.log_message(f"Data terkumpul: {len(collected_data)} bisnis")
        utils.log_message(f"File tersimpan: {filepath}")
        utils.log_message("="*70 + "\n")
        
    except KeyboardInterrupt:
        utils.log_message("\n\n⚠ Scraping dihentikan oleh user (Ctrl+C)", "WARNING")
    
    except Exception as e:
        utils.log_message(f"\n\n❌ Error fatal: {str(e)}", "ERROR")
        import traceback
        utils.log_message(traceback.format_exc(), "ERROR")
    
    finally:
        # Tutup browser
        utils.log_message("\nMembersihkan resource...")
        browser_manager.close_browser()
        utils.log_message("✓ Selesai\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        utils.log_message(f"Error menjalankan program: {str(e)}", "ERROR")
        sys.exit(1)
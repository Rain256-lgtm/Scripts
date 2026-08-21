#!/usr/bin/env python3

import requests
import json
import time
import os
import sys
import asyncio
import urllib.parse
import gzip
import zlib
import re
from datetime import datetime
from typing import Optional, Dict, Any
from telethon import TelegramClient, functions, types
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)

# Color codes
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    GOLD = '\033[38;5;214m'
    PURPLE = '\033[38;5;141m'
    SKY = '\033[38;5;117m'
    MINT = '\033[38;5;157m'
    ROSE = '\033[38;5;204m'
    ORANGE = '\033[38;5;208m'

class Config:
    """Configuration manager"""
    CONFIG_FILE = "doge_faucet_config.json"
    
    @staticmethod
    def load() -> Dict:
        if os.path.exists(Config.CONFIG_FILE):
            try:
                with open(Config.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    @staticmethod
    def save(config: Dict):
        try:
            with open(Config.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"{Colors.MINT}[✓] Configuration saved{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.YELLOW}[!] Error saving config: {e}{Colors.RESET}")

class SliderCaptchaSolver:
    """Simulated slider captcha solver"""
    
    @staticmethod
    def solve():
        """
        In a real scenario, you would need to:
        1. Download the captcha image
        2. Detect the slider position using computer vision
        3. Calculate the required offset
        4. Send the solved result
        
        For this demo, we'll simulate a successful solve
        """
        print(f"{Colors.SKY}[*] Solving slider captcha...{Colors.RESET}")
        
        # Simulate captcha solving process
        time.sleep(2)
        
        # Return simulated captcha token/response
        return {
            "captcha_token": "simulated_captcha_token_" + str(int(time.time())),
            "solved": True
        }

class DogeFaucetBot:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.session.timeout = 30
        
        self.base_url = "https://doge-drop-daily.base44.app"
        self.api_url = f"{self.base_url}/api/apps/6a13f1a4804d249d12145f41"
        
        # Auth data
        self.init_data = None
        self.user_id = None
        self.anonymous_id = None
        
        # Account data
        self.user_data = {}
        self.balance = 0
        self.total_claimed = 0
        
        # Telegram client
        self.telegram_client = None
        
        # API Configuration
        self.api_id = None
        self.api_hash = None
        self.phone_number = None
        
        # Bot username - FIXED
        self.bot_username = 'my_doge_faucet_bot'  # Changed from 'DOGE_FUACET_bot'
        
        # Headers
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 15; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.7871.181 Mobile Safari/537.36 Telegram-Android/12.9.1 (Oppo CPH2505; Android 15; SDK 35; AVERAGE)',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en,en-PH;q=0.9,en-US;q=0.8',
            'Sec-Ch-Ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Android WebView";v="150"',
            'Sec-Ch-Ua-Mobile': '?1',
            'Sec-Ch-Ua-Platform': '"Android"',
            'X-Requested-With': 'org.telegram.messenger.web',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/',
            'Connection': 'keep-alive',
            'X-App-Id': '6a13f1a4804d249d12145f41',
        }
        
        self.headers = self.base_headers.copy()
        
        # Load config
        self.config = Config.load()
        self.load_config()

    def load_config(self):
        if self.config:
            self.api_id = self.config.get('api_id')
            self.api_hash = self.config.get('api_hash')
            self.phone_number = self.config.get('phone_number')
            self.anonymous_id = self.config.get('anonymous_id', 'tok7comujf7q53ik5vm')
            print(f"{Colors.MINT}[✓] Loaded configuration{Colors.RESET}")

    def setup_config(self):
        print(f"\n{Colors.GOLD}{Colors.BOLD}╔═══════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.GOLD}{Colors.BOLD}║              ⚙️ CONFIGURATION SETUP                  ║{Colors.RESET}")
        print(f"{Colors.GOLD}{Colors.BOLD}╚═══════════════════════════════════════════════════════╝{Colors.RESET}")
        
        if not self.api_id:
            self.api_id = input(f"{Colors.CYAN}[?] Enter API ID: {Colors.WHITE}").strip()
            while not self.api_id.isdigit():
                print(f"{Colors.RED}[!] API ID must be a number{Colors.RESET}")
                self.api_id = input(f"{Colors.CYAN}[?] Enter API ID: {Colors.WHITE}").strip()
        
        if not self.api_hash:
            self.api_hash = input(f"{Colors.CYAN}[?] Enter API Hash: {Colors.WHITE}").strip()
            while len(self.api_hash) < 20:
                print(f"{Colors.RED}[!] Invalid API Hash{Colors.RESET}")
                self.api_hash = input(f"{Colors.CYAN}[?] Enter API Hash: {Colors.WHITE}").strip()
        
        if not self.phone_number:
            self.phone_number = input(f"{Colors.CYAN}[?] Enter Phone Number (e.g., +1234567890): {Colors.WHITE}").strip()
            while not self.phone_number.startswith('+') or len(self.phone_number) < 10:
                print(f"{Colors.RED}[!] Invalid phone number (must include country code){Colors.RESET}")
                self.phone_number = input(f"{Colors.CYAN}[?] Enter Phone Number: {Colors.WHITE}").strip()
        
        self.save_config()
        print(f"\n{Colors.GREEN}[✓] Configuration complete!{Colors.RESET}")

    def save_config(self):
        self.config = {
            'api_id': self.api_id,
            'api_hash': self.api_hash,
            'phone_number': self.phone_number,
            'anonymous_id': self.anonymous_id,
        }
        Config.save(self.config)

    def set_auth(self, init_data: str):
        """Set authentication data"""
        self.init_data = init_data
        self.headers['x-base44-anonymous-id'] = self.anonymous_id
        
        # Parse user info
        try:
            params = dict(urllib.parse.parse_qsl(init_data))
            if 'user' in params:
                import html
                user_data = json.loads(html.unescape(params['user']))
                self.user_id = user_data.get('id')
                print(f"{Colors.MINT}[✓] User ID: {self.user_id}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.YELLOW}[!] Could not parse user: {e}{Colors.RESET}")

    async def get_init_data_telegram(self):
        """Get init data using Telethon"""
        print(f"\n{Colors.SKY}[*] Connecting to Telegram...{Colors.RESET}")
        
        # Create client
        self.telegram_client = TelegramClient(
            'doge_session_auth',
            int(self.api_id), 
            self.api_hash
        )
        
        await self.telegram_client.start(phone=self.phone_number)
        print(f"{Colors.MINT}[✓] Successfully Logged In!{Colors.RESET}")
        
        try:
            print(f"{Colors.SKY}[*] Fetching Bot Info @{self.bot_username}...{Colors.RESET}")
            
            # Try to get the bot entity
            try:
                bot = await self.telegram_client.get_input_entity(self.bot_username)
                print(f"{Colors.MINT}[✓] Bot found: @{self.bot_username}{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.YELLOW}[!] Could not find bot @{self.bot_username}{Colors.RESET}")
                print(f"{Colors.YELLOW}[!] Trying to get from messages...{Colors.RESET}")
                
                # Try to get bot from recent messages
                try:
                    # Search for the bot in dialogs
                    async for dialog in self.telegram_client.iter_dialogs():
                        if dialog.entity and hasattr(dialog.entity, 'username'):
                            if dialog.entity.username and 'doge' in dialog.entity.username.lower():
                                bot = dialog.entity
                                print(f"{Colors.MINT}[✓] Found bot in dialogs: @{dialog.entity.username}{Colors.RESET}")
                                break
                    else:
                        # Try to get bot info directly
                        bot = await self.telegram_client.get_entity(self.bot_username)
                except Exception as e2:
                    print(f"{Colors.RED}[!] Failed to find bot: {e2}{Colors.RESET}")
                    # Try using the bot username directly
                    bot = await self.telegram_client.get_entity('my_doge_faucet_bot')
            
            # Get bot info to find URL
            full_user_request = await self.telegram_client(functions.users.GetFullUserRequest(id=bot))
            bot_info = full_user_request.full_user.bot_info
            
            # Get URL from menu button
            target_url = None
            if bot_info and bot_info.menu_button:
                if hasattr(bot_info.menu_button, 'url'):
                    target_url = bot_info.menu_button.url
                    print(f"{Colors.MINT}[✓] Auto-detected URL: {target_url}{Colors.RESET}")
            
            if not target_url:
                target_url = 'https://doge-drop-daily.base44.app/'
                print(f"{Colors.YELLOW}[!] Using fallback URL: {target_url}{Colors.RESET}")
            
            print(f"{Colors.SKY}[*] Requesting WebView...{Colors.RESET}")
            
            # Request WebView
            result = await self.telegram_client(functions.messages.RequestWebViewRequest(
                peer=bot,
                bot=bot,
                platform='android',
                from_bot_menu=True,
                url=target_url
            ))
            
            print(f"{Colors.MINT}[✓] WebView URL: {result.url}{Colors.RESET}")
            
            # Parse the result
            parsed_url = urllib.parse.urlparse(result.url)
            
            # Try to get from fragment
            if parsed_url.fragment:
                fragment_params = urllib.parse.parse_qs(parsed_url.fragment)
                init_data = fragment_params.get('tgWebAppData', [None])[0]
                if init_data:
                    print(f"{Colors.MINT}[✓] Got init data from fragment!{Colors.RESET}")
                    with open("doge_init_data.txt", "w") as f:
                        f.write(init_data)
                    return init_data
            
            # Try to get from query string
            if parsed_url.query:
                query_params = urllib.parse.parse_qs(parsed_url.query)
                init_data = query_params.get('tgWebAppData', [None])[0]
                if init_data:
                    print(f"{Colors.MINT}[✓] Got init data from query string!{Colors.RESET}")
                    with open("doge_init_data.txt", "w") as f:
                        f.write(init_data)
                    return init_data
            
            # If we have the full URL with init data
            if 'tgWebAppData=' in result.url:
                match = re.search(r'tgWebAppData=([^&]+)', result.url)
                if match:
                    init_data = match.group(1)
                    print(f"{Colors.MINT}[✓] Extracted init data from URL!{Colors.RESET}")
                    with open("doge_init_data.txt", "w") as f:
                        f.write(init_data)
                    return init_data
            
            print(f"{Colors.RED}[!] Failed to get init data{Colors.RESET}")
            return None
                
        except Exception as e:
            print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            await self.telegram_client.disconnect()

    def get_init_data_sync(self):
        """Synchronous wrapper for getting init data"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            init_data = loop.run_until_complete(self.get_init_data_telegram())
            loop.close()
            return init_data
        except Exception as e:
            print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")
            return None

    def load_init_data(self) -> Optional[str]:
        if os.path.exists("doge_init_data.txt"):
            try:
                with open("doge_init_data.txt", "r") as f:
                    data = f.read().strip()
                    if data:
                        print(f"{Colors.MINT}[✓] Loaded init data from file{Colors.RESET}")
                        return data
            except Exception as e:
                print(f"{Colors.YELLOW}[!] Error loading init data: {e}{Colors.RESET}")
        return None

    def decompress_response(self, content, encoding):
        """Decompress response content based on encoding"""
        if not content:
            return content
        
        try:
            if encoding == 'gzip':
                return gzip.decompress(content).decode('utf-8')
            elif encoding == 'deflate':
                return zlib.decompress(content, -zlib.MAX_WBITS).decode('utf-8')
            elif encoding == 'br':
                try:
                    import brotli
                    return brotli.decompress(content).decode('utf-8')
                except:
                    return content.decode('utf-8', errors='ignore')
            elif encoding == 'zstd':
                try:
                    import zstandard as zstd
                    dctx = zstd.ZstdDecompressor()
                    return dctx.decompress(content).decode('utf-8')
                except:
                    try:
                        return gzip.decompress(content).decode('utf-8')
                    except:
                        pass
                    return content.decode('utf-8', errors='ignore')
            else:
                return content.decode('utf-8')
        except Exception as e:
            print(f"{Colors.YELLOW}[!] Decompression error: {e}{Colors.RESET}")
            try:
                return content.decode('utf-8')
            except:
                return str(content)

    def api_request(self, method: str, endpoint: str, data: Dict = None, custom_headers: Dict = None) -> Optional[Dict]:
        """Make API request"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        headers = self.headers.copy()
        if custom_headers:
            headers.update(custom_headers)
        
        # Add init_data to headers if available
        if self.init_data:
            headers['x-init-data'] = self.init_data
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, timeout=15)
            elif method.upper() == 'POST':
                response = self.session.post(url, headers=headers, json=data, timeout=15)
            else:
                return None
            
            print(f"{Colors.SKY}[*] Status: {response.status_code}{Colors.RESET}")
            print(f"{Colors.SKY}[*] Content-Encoding: {response.headers.get('Content-Encoding', 'none')}{Colors.RESET}")
            
            if response.status_code == 200:
                # Get the response content
                content = response.content
                encoding = response.headers.get('Content-Encoding', '')
                
                # Decompress if needed
                if encoding:
                    text = self.decompress_response(content, encoding)
                else:
                    text = response.text
                
                # Try to parse JSON
                try:
                    return json.loads(text)
                except json.JSONDecodeError as e:
                    print(f"{Colors.YELLOW}[!] JSON Parse Error: {e}{Colors.RESET}")
                    print(f"{Colors.YELLOW}[!] Response preview: {text[:200]}{Colors.RESET}")
                    return None
                    
            elif response.status_code == 401:
                print(f"{Colors.RED}[!] Unauthorized - Need fresh init data{Colors.RESET}")
                return None
            else:
                print(f"{Colors.YELLOW}[!] API Error {response.status_code}{Colors.RESET}")
                return None
                
        except Exception as e:
            print(f"{Colors.YELLOW}[!] Request error: {e}{Colors.RESET}")
            import traceback
            traceback.print_exc()
            return None

    def authenticate(self) -> bool:
        """Authenticate with the faucet"""
        print(f"{Colors.SKY}[*] Authenticating with Doge Faucet...{Colors.RESET}")
        
        data = {
            "action": "tg_auth",
            "init_data": self.init_data,
            "landing_lang": "en"
        }
        
        response = self.api_request('POST', 'functions/faucetAccount', data)
        
        if response and 'user' in response:
            self.user_data = response['user']
            self.balance = self.user_data.get('balance', 0)
            self.total_claimed = self.user_data.get('total_claimed', 0)
            print(f"{Colors.GREEN}[✓] Authentication successful!{Colors.RESET}")
            print(f"{Colors.GOLD}💰 Balance: {self.balance} DOGE{Colors.RESET}")
            print(f"{Colors.SKY}📊 Total Claimed: {self.total_claimed} DOGE{Colors.RESET}")
            return True
        return False

    def get_faucet_settings(self) -> Optional[Dict]:
        """Get faucet settings"""
        print(f"{Colors.SKY}[*] Fetching faucet settings...{Colors.RESET}")
        
        response = self.api_request('GET', 'entities/FaucetSettings?sort=-created_date&limit=1')
        
        if response and len(response) > 0:
            settings = response[0]
            print(f"{Colors.GREEN}[✓] Settings loaded!{Colors.RESET}")
            print(f"{Colors.SKY}💰 Reward Amount: {settings.get('reward_amount', 0)} DOGE{Colors.RESET}")
            print(f"{Colors.SKY}⏱️ Cooldown: {settings.get('cooldown_minutes', 0)} minutes{Colors.RESET}")
            return settings
        return None

    def claim_faucet(self) -> bool:
        """Claim faucet reward"""
        print(f"{Colors.ORANGE}[*] Claiming faucet reward...{Colors.RESET}")
        
        # First, solve the slider captcha if needed
        print(f"{Colors.SKY}[*] Solving slider captcha...{Colors.RESET}")
        captcha_result = SliderCaptchaSolver.solve()
        
        if not captcha_result.get('solved'):
            print(f"{Colors.RED}[!] Failed to solve captcha{Colors.RESET}")
            return False
        
        # Prepare claim data
        data = {
            "action": "faucet_claim",
            "faucetpay_email": f"tg{self.user_id}@dogefaucet.app",
            "init_data": self.init_data,
            "captcha_token": captcha_result.get('captcha_token')
        }
        
        response = self.api_request('POST', 'functions/creditReward', data)
        
        if response:
            if response.get('ok', False):
                reward = response.get('reward', 0)
                self.balance += reward
                self.total_claimed += reward
                print(f"{Colors.GREEN}[✓] Claim successful!{Colors.RESET}")
                print(f"{Colors.GOLD}💰 Reward: +{reward} DOGE{Colors.RESET}")
                print(f"{Colors.GOLD}💰 New Balance: {self.balance} DOGE{Colors.RESET}")
                return True
            else:
                print(f"{Colors.RED}[!] Claim failed: {response.get('error', 'Unknown error')}{Colors.RESET}")
                return False
        return False

    def redeem_promo_code(self, code: str) -> bool:
        """Redeem a promo code"""
        print(f"{Colors.ORANGE}[*] Redeeming promo code: {code}{Colors.RESET}")
        
        data = {
            "stage": "validate",
            "code": code,
            "faucetpay_email": f"tg{self.user_id}@dogefaucet.app",
            "init_data": self.init_data
        }
        
        response = self.api_request('POST', 'functions/redeemPromoCode', data)
        
        if response:
            if response.get('ok', False):
                print(f"{Colors.GREEN}[✓] Promo code redeemed successfully!{Colors.RESET}")
                return True
            else:
                print(f"{Colors.RED}[!] Promo code failed: {response.get('error', 'Unknown error')}{Colors.RESET}")
                return False
        return False

    def track_event(self, event_name: str, page_url: str = "/home"):
        """Track analytics event"""
        data = {
            "events": [{
                "event_name": event_name,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "page_url": page_url,
                "user_id": None,
                "session_id": self.anonymous_id
            }]
        }
        
        self.api_request('POST', 'analytics/track/batch', data)

    def display_stats(self):
        """Display account statistics"""
        print(f"\n{Colors.GOLD}{Colors.BOLD}╔═══════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.GOLD}{Colors.BOLD}║           📊 DOGE FAUCET STATS                      ║{Colors.RESET}")
        print(f"{Colors.GOLD}{Colors.BOLD}╚═══════════════════════════════════════════════════════╝{Colors.RESET}")
        
        print(f"{Colors.CYAN}{Colors.BOLD}👤 USER INFO:{Colors.RESET}")
        print(f"  {Colors.MINT}Name: {self.user_data.get('telegram_name', 'Unknown')}{Colors.RESET}")
        print(f"  {Colors.MINT}Username: @{self.user_data.get('telegram_username', 'Unknown')}{Colors.RESET}")
        print(f"  {Colors.MINT}User ID: {self.user_data.get('telegram_id', 'Unknown')}{Colors.RESET}")
        
        print(f"\n{Colors.GOLD}💰 BALANCE:{Colors.RESET}")
        print(f"  {Colors.ORANGE}Balance: {self.balance} DOGE{Colors.RESET}")
        print(f"  {Colors.SKY}Total Claimed: {self.total_claimed} DOGE{Colors.RESET}")
        
        print(f"\n{Colors.PURPLE}📈 STATS:{Colors.RESET}")
        print(f"  {Colors.MINT}Daily Claims: {self.user_data.get('daily_claims_today', 0)}{Colors.RESET}")
        print(f"  {Colors.MINT}Referral Code: {self.user_data.get('referral_code', 'N/A')}{Colors.RESET}")
        print(f"  {Colors.MINT}Referral Count: {self.user_data.get('referral_count', 0)}{Colors.RESET}")
        
        print(f"{Colors.GOLD}{Colors.BOLD}╚═══════════════════════════════════════════════════════╝{Colors.RESET}\n")

    def refresh_auth(self) -> bool:
        """Refresh authentication"""
        print(f"{Colors.SKY}[*] Refreshing auth...{Colors.RESET}")
        
        if os.path.exists("doge_init_data.txt"):
            os.remove("doge_init_data.txt")
            print(f"{Colors.YELLOW}[!] Removed old init data{Colors.RESET}")
        
        init_data = self.get_init_data_sync()
        
        if init_data:
            self.set_auth(init_data)
            print(f"{Colors.GREEN}[✓] Auth refreshed successfully!{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}[!] Failed to refresh auth{Colors.RESET}")
            return False

    def auto_run(self):
        """Run in auto mode"""
        print(f"\n{Colors.GOLD}{Colors.BOLD}╔═══════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.GOLD}{Colors.BOLD}║           🔄 AUTO MODE STARTING                      ║{Colors.RESET}")
        print(f"{Colors.GOLD}{Colors.BOLD}║      Claiming faucet every 10 minutes                ║{Colors.RESET}")
        print(f"{Colors.GOLD}{Colors.BOLD}╚═══════════════════════════════════════════════════════╝{Colors.RESET}")
        
        cycle = 0
        claim_interval = 600  # 10 minutes in seconds
        
        while True:
            cycle += 1
            
            print(f"\n{Colors.SKY}{Colors.BOLD}═══ Cycle {cycle} ═══{Colors.RESET}")
            print(f"{Colors.WHITE}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
            
            # Authenticate first
            if not self.authenticate():
                print(f"{Colors.RED}[!] Authentication failed, refreshing...{Colors.RESET}")
                if not self.refresh_auth():
                    print(f"{Colors.RED}[!] Auth refresh failed, stopping{Colors.RESET}")
                    break
                if not self.authenticate():
                    print(f"{Colors.RED}[!] Still cannot authenticate after refresh{Colors.RESET}")
                    break
                continue
            
            self.display_stats()
            
            # Try to claim
            self.claim_faucet()
            
            # Wait for next cycle
            print(f"{Colors.YELLOW}[*] Next claim in {claim_interval}s...{Colors.RESET}")
            time.sleep(claim_interval)

def display_banner():
    os.system('clear' if os.name != 'nt' else 'cls')
    
    print(f"{Colors.GOLD}{Colors.BOLD}╔═══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.ORANGE}{Colors.BOLD}")
    print("   ██████╗  ██████╗  ██████╗ ███████╗    ███████╗ █████╗ ██╗   ██╗ ██████╗███████╗████████╗")
    print("   ██╔══██╗██╔═══██╗██╔════╝ ██╔════╝    ██╔════╝██╔══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝")
    print("   ██║  ██║██║   ██║██║  ███╗█████╗      █████╗  ███████║██║   ██║██║     █████╗     ██║   ")
    print("   ██║  ██║██║   ██║██║   ██║██╔══╝      ██╔══╝  ██╔══██║██║   ██║██║     ██╔══╝     ██║   ")
    print("   ██████╔╝╚██████╔╝╚██████╔╝███████╗    ██║     ██║  ██║╚██████╔╝╚██████╗███████╗   ██║   ")
    print("   ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝   ╚═╝   ")
    print(Colors.RESET)
    print(f"{Colors.GOLD}{Colors.BOLD}              🐕 DOGE FAUCET AUTO CLAIM BOT 🐕{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")

def main():
    try:
        display_banner()
        
        bot = DogeFaucetBot()
        bot.setup_config()
        
        # Try to load init data
        init_data = bot.load_init_data()
        
        if not init_data:
            print(f"{Colors.YELLOW}[!] No init data found, getting fresh...{Colors.RESET}")
            init_data = bot.get_init_data_sync()
            
            if not init_data:
                print(f"{Colors.RED}[!] Failed to get init data{Colors.RESET}")
                return
        
        bot.set_auth(init_data)
        
        # Test connection
        print(f"\n{Colors.SKY}[*] Testing connection...{Colors.RESET}")
        if not bot.authenticate():
            print(f"{Colors.RED}[!] Connection failed. Refreshing...{Colors.RESET}")
            if bot.refresh_auth():
                if bot.authenticate():
                    print(f"{Colors.GREEN}[✓] Connection successful!{Colors.RESET}")
                else:
                    print(f"{Colors.RED}[!] Still cannot connect{Colors.RESET}")
                    return
            else:
                print(f"{Colors.RED}[!] Failed to refresh auth{Colors.RESET}")
                return
        
        bot.display_stats()
        
        while True:
            print(f"\n{Colors.GOLD}{Colors.BOLD}╔═══════════════════════════════════════════════════════╗{Colors.RESET}")
            print(f"{Colors.GOLD}{Colors.BOLD}║                    📋 MENU                          ║{Colors.RESET}")
            print(f"{Colors.GOLD}{Colors.BOLD}╚═══════════════════════════════════════════════════════╝{Colors.RESET}")
            print(f"  {Colors.GREEN}1{Colors.WHITE}. 🔄 Auto Mode")
            print(f"  {Colors.PURPLE}2{Colors.WHITE}. 📊 Show Stats")
            print(f"  {Colors.ORANGE}3{Colors.WHITE}. 💰 Claim Faucet")
            print(f"  {Colors.BLUE}4{Colors.WHITE}. 🔑 Refresh Auth")
            print(f"  {Colors.MAGENTA}5{Colors.WHITE}. 🎯 Redeem Promo Code")
            print(f"  {Colors.RED}6{Colors.WHITE}. 🚪 Exit")
            print(f"{Colors.GOLD}{Colors.BOLD}╚═══════════════════════════════════════════════════════╝{Colors.RESET}")
            
            choice = input(f"{Colors.YELLOW}[?] Choice: {Colors.WHITE}").strip()
            
            if choice == '1':
                bot.auto_run()
            elif choice == '2':
                bot.authenticate()
                bot.display_stats()
            elif choice == '3':
                bot.authenticate()
                bot.claim_faucet()
                bot.display_stats()
            elif choice == '4':
                if bot.refresh_auth():
                    bot.authenticate()
                    bot.display_stats()
            elif choice == '5':
                code = input(f"{Colors.CYAN}[?] Enter promo code: {Colors.WHITE}").strip()
                if code:
                    bot.redeem_promo_code(code)
                else:
                    print(f"{Colors.RED}[!] Invalid promo code{Colors.RESET}")
            elif choice == '6':
                print(f"\n{Colors.ROSE}[!] Goodbye!{Colors.RESET}")
                break
            else:
                print(f"{Colors.RED}[!] Invalid choice{Colors.RESET}")
                
    except KeyboardInterrupt:
        print(f"\n{Colors.ROSE}[!] Stopped{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
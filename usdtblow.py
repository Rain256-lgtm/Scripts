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
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from telethon import TelegramClient, functions, types
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)

# ============================================================================
# COLOR CODES
# ============================================================================
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
    DIM = '\033[2m'


# ============================================================================
# CONFIGURATION MANAGER
# ============================================================================
class Config:
    CONFIG_FILE = "usdtflow_config.json"
    
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


# ============================================================================
# PANEL UI CLASS
# ============================================================================
class Panel:
    @staticmethod
    def header(title: str, subtitle: str = ""):
        """Display a header panel"""
        width = 60
        print(f"\n{Colors.GOLD}{Colors.BOLD}╔{'═' * (width - 2)}╗{Colors.RESET}")
        print(f"{Colors.GOLD}{Colors.BOLD}║{Colors.CYAN}{Colors.BOLD}{title.center(width - 2)}{Colors.GOLD}{Colors.BOLD}║{Colors.RESET}")
        if subtitle:
            print(f"{Colors.GOLD}{Colors.BOLD}║{Colors.SKY}{subtitle.center(width - 2)}{Colors.GOLD}{Colors.BOLD}║{Colors.RESET}")
        print(f"{Colors.GOLD}{Colors.BOLD}╚{'═' * (width - 2)}╝{Colors.RESET}")

    @staticmethod
    def stats(label: str, value: str, color: str = Colors.WHITE):
        """Display a stats line"""
        print(f"  {Colors.CYAN}{label}:{Colors.RESET} {color}{value}{Colors.RESET}")

    @staticmethod
    def divider():
        """Display a divider line"""
        print(f"{Colors.DIM}{'─' * 60}{Colors.RESET}")

    @staticmethod
    def progress_bar(current: int, total: int, width: int = 30):
        """Display a progress bar"""
        if total == 0:
            return
        percentage = (current / total) * 100
        filled = int((current / total) * width)
        bar = '█' * filled + '░' * (width - filled)
        print(f"  {Colors.SKY}[{bar}]{Colors.RESET} {Colors.WHITE}{current}/{total} ({percentage:.1f}%){Colors.RESET}")

    @staticmethod
    def countdown(seconds: int, message: str = "Waiting", show_animation: bool = True):
        """Display a countdown timer with animation"""
        if not show_animation:
            time.sleep(seconds)
            return
            
        for remaining in range(seconds, 0, -1):
            # Create a simple spinner animation
            spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            frame = spinner[remaining % len(spinner)]
            
            # Format time as minutes:seconds for longer waits
            if seconds > 60:
                mins = remaining // 60
                secs = remaining % 60
                time_str = f"{mins:2d}m {secs:2d}s"
            else:
                time_str = f"{remaining:2d}s"
            
            sys.stdout.write(f"\r{Colors.SKY}  {frame} {message}: {Colors.WHITE}{time_str}{Colors.RESET} remaining")
            sys.stdout.flush()
            time.sleep(1)
        
        sys.stdout.write(f"\r{Colors.GREEN}  ✅ {message} complete!{' ' * 30}{Colors.RESET}\n")
        sys.stdout.flush()

    @staticmethod
    def watch_ad_timer(ad_duration: int, provider: str, ad_number: int, total_ads: int):
        """Display ad watching timer with animation"""
        print(f"\n{Colors.ORANGE}  🎬 [{ad_number}/{total_ads}] Watching {provider} ad...{Colors.RESET}")
        print(f"  {Colors.DIM}⏱️  Ad duration: {ad_duration} seconds{Colors.RESET}")
        
        # Progress bar for ad watching
        for remaining in range(ad_duration, 0, -1):
            progress = ((ad_duration - remaining) / ad_duration) * 100
            filled = int(((ad_duration - remaining) / ad_duration) * 30)
            bar = '█' * filled + '░' * (30 - filled)
            
            # Spinner animation
            spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            frame = spinner[remaining % len(spinner)]
            
            sys.stdout.write(f"\r  {Colors.SKY}{frame} Watching: {Colors.WHITE}[{bar}]{Colors.RESET} {Colors.WHITE}{remaining:2d}s{Colors.RESET} remaining")
            sys.stdout.flush()
            time.sleep(1)
        
        sys.stdout.write(f"\r  {Colors.GREEN}✅ Ad completed!{' ' * 50}{Colors.RESET}\n")
        sys.stdout.flush()

    @staticmethod
    def cooldown_timer(seconds: int, cycle: int):
        """Display cooldown timer with progress"""
        minutes = seconds // 60
        print(f"\n{Colors.ROSE}{Colors.BOLD}╔{'═' * 58}╗{Colors.RESET}")
        print(f"{Colors.ROSE}{Colors.BOLD}║{Colors.WHITE}{Colors.BOLD}{'☕ COOLDOWN PERIOD'.center(58)}{Colors.ROSE}{Colors.BOLD}║{Colors.RESET}")
        print(f"{Colors.ROSE}{Colors.BOLD}║{Colors.SKY}{f'Completed {cycle} cycles, taking a break...'.center(58)}{Colors.ROSE}{Colors.BOLD}║{Colors.RESET}")
        print(f"{Colors.ROSE}{Colors.BOLD}╚{'═' * 58}╝{Colors.RESET}")
        
        for remaining in range(seconds, 0, -1):
            # Calculate progress
            progress = ((seconds - remaining) / seconds) * 100
            filled = int(((seconds - remaining) / seconds) * 40)
            bar = '█' * filled + '░' * (40 - filled)
            
            # Format time
            mins = remaining // 60
            secs = remaining % 60
            time_str = f"{mins:2d}m {secs:2d}s"
            
            # Spinner
            spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            frame = spinner[remaining % len(spinner)]
            
            sys.stdout.write(f"\r{Colors.ORANGE}  {frame} Cooldown: {Colors.WHITE}[{bar}]{Colors.RESET} {Colors.WHITE}{time_str}{Colors.RESET} remaining ({progress:.0f}%)")
            sys.stdout.flush()
            time.sleep(1)
        
        sys.stdout.write(f"\r{Colors.GREEN}  ✅ Cooldown complete!{' ' * 50}{Colors.RESET}\n")
        sys.stdout.flush()

    @staticmethod
    def menu(options: Dict[int, str]):
        """Display a menu"""
        width = 60
        print(f"\n{Colors.GOLD}{Colors.BOLD}╔{'═' * (width - 2)}╗{Colors.RESET}")
        print(f"{Colors.GOLD}{Colors.BOLD}║{Colors.WHITE}{Colors.BOLD}{'📋 MENU'.center(width - 2)}{Colors.GOLD}{Colors.BOLD}║{Colors.RESET}")
        print(f"{Colors.GOLD}{Colors.BOLD}╠{'═' * (width - 2)}╣{Colors.RESET}")
        for key, value in options.items():
            print(f"{Colors.GOLD}{Colors.BOLD}║{Colors.RESET}  {Colors.GREEN}{key}{Colors.RESET}. {value.ljust(width - 6)}{Colors.GOLD}{Colors.BOLD}║{Colors.RESET}")
        print(f"{Colors.GOLD}{Colors.BOLD}╚{'═' * (width - 2)}╝{Colors.RESET}")


# ============================================================================
# USDTFLOW BOT CLASS
# ============================================================================
class USDTFlowBot:
    def __init__(self):
        # Session
        self.session = requests.Session()
        self.session.verify = False
        self.session.timeout = 30
        
        # URLs
        self.base_url = "https://usdtflow.ru"
        self.api_url = f"{self.base_url}/api"
        
        # Auth
        self.init_data = None
        self.user_id = None
        self.cookies = {}
        
        # User data
        self.user_data = {}
        self.balance_usdt = 0.0
        self.balance_ton = 0.0
        self.total_earned = 0.0
        self.ads_count = 0
        self.watched_today = 0
        self.daily_limits = {}
        
        # Ad config
        self.ad_config = {}
        self.rewards = {}
        self.ad_providers = []
        
        # Ad watching simulation
        self.ad_duration_min = 15  # Minimum ad duration in seconds
        self.ad_duration_max = 30  # Maximum ad duration in seconds
        
        # Cooldown settings
        self.cycles_before_cooldown = 5  # Number of cycles before cooldown
        self.cooldown_minutes = 15  # Cooldown duration in minutes
        self.cooldown_min = 15  # Minimum cooldown in minutes
        self.cooldown_max = 20  # Maximum cooldown in minutes
        
        # Telegram
        self.telegram_client = None
        self.api_id = None
        self.api_hash = None
        self.phone_number = None
        self.bot_username = 'UsdtTonFlow_bot'
        
        # Headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 15; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.7871.181 Mobile Safari/537.36 Telegram-Android/12.9.1',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en,en-PH;q=0.9,en-US;q=0.8',
            'Sec-Ch-Ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Android WebView";v="150"',
            'Sec-Ch-Ua-Mobile': '?1',
            'Sec-Ch-Ua-Platform': '"Android"',
            'X-Requested-With': 'org.telegram.messenger.web',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/',
            'Connection': 'keep-alive',
        }
        
        # Settings
        self.min_delay = 10
        self.max_delay = 30
        
        # Load config
        self.config = Config.load()
        self._load_config()
    
    # ------------------------------------------------------------------------
    # Configuration Methods
    # ------------------------------------------------------------------------
    def _load_config(self):
        if self.config:
            self.api_id = self.config.get('api_id')
            self.api_hash = self.config.get('api_hash')
            self.phone_number = self.config.get('phone_number')
            self.min_delay = self.config.get('min_delay', 10)
            self.max_delay = self.config.get('max_delay', 30)
            self.ad_duration_min = self.config.get('ad_duration_min', 15)
            self.ad_duration_max = self.config.get('ad_duration_max', 30)
            self.cycles_before_cooldown = self.config.get('cycles_before_cooldown', 5)
            self.cooldown_min = self.config.get('cooldown_min', 15)
            self.cooldown_max = self.config.get('cooldown_max', 20)
    
    def setup_config(self):
        Panel.header("⚙️ CONFIGURATION SETUP")
        
        # API ID
        if not self.api_id:
            self.api_id = input(f"{Colors.CYAN}[?] Enter API ID: {Colors.WHITE}").strip()
            while not self.api_id.isdigit():
                print(f"{Colors.RED}[!] API ID must be a number{Colors.RESET}")
                self.api_id = input(f"{Colors.CYAN}[?] Enter API ID: {Colors.WHITE}").strip()
        
        # API Hash
        if not self.api_hash:
            self.api_hash = input(f"{Colors.CYAN}[?] Enter API Hash: {Colors.WHITE}").strip()
            while len(self.api_hash) < 20:
                print(f"{Colors.RED}[!] Invalid API Hash{Colors.RESET}")
                self.api_hash = input(f"{Colors.CYAN}[?] Enter API Hash: {Colors.WHITE}").strip()
        
        # Phone Number
        if not self.phone_number:
            self.phone_number = input(f"{Colors.CYAN}[?] Enter Phone Number (e.g., +1234567890): {Colors.WHITE}").strip()
            while not self.phone_number.startswith('+') or len(self.phone_number) < 10:
                print(f"{Colors.RED}[!] Invalid phone number (must include country code){Colors.RESET}")
                self.phone_number = input(f"{Colors.CYAN}[?] Enter Phone Number: {Colors.WHITE}").strip()
        
        # Ad duration settings
        print(f"\n{Colors.SKY}[*] Current ad duration: {self.ad_duration_min}-{self.ad_duration_max} seconds{Colors.RESET}")
        change_duration = input(f"{Colors.YELLOW}[?] Change ad duration range? (y/n): {Colors.WHITE}").strip().lower()
        if change_duration == 'y':
            self.ad_duration_min = int(input(f"{Colors.CYAN}[?] Min ad duration (seconds): {Colors.WHITE}").strip() or "15")
            self.ad_duration_max = int(input(f"{Colors.CYAN}[?] Max ad duration (seconds): {Colors.WHITE}").strip() or "30")
            if self.ad_duration_min < 5:
                self.ad_duration_min = 5
            if self.ad_duration_max < self.ad_duration_min:
                self.ad_duration_max = self.ad_duration_min + 10
        
        # Delay settings
        print(f"\n{Colors.SKY}[*] Current delay range: {self.min_delay}-{self.max_delay} seconds{Colors.RESET}")
        change_delay = input(f"{Colors.YELLOW}[?] Change delay range? (y/n): {Colors.WHITE}").strip().lower()
        if change_delay == 'y':
            self.min_delay = int(input(f"{Colors.CYAN}[?] Min delay (seconds): {Colors.WHITE}").strip() or "10")
            self.max_delay = int(input(f"{Colors.CYAN}[?] Max delay (seconds): {Colors.WHITE}").strip() or "30")
            if self.min_delay < 5:
                self.min_delay = 5
            if self.max_delay < self.min_delay:
                self.max_delay = self.min_delay + 10
        
        # Cooldown settings
        print(f"\n{Colors.SKY}[*] Current cooldown: {self.cycles_before_cooldown} cycles, {self.cooldown_min}-{self.cooldown_max} minutes{Colors.RESET}")
        change_cooldown = input(f"{Colors.YELLOW}[?] Change cooldown settings? (y/n): {Colors.WHITE}").strip().lower()
        if change_cooldown == 'y':
            self.cycles_before_cooldown = int(input(f"{Colors.CYAN}[?] Cycles before cooldown: {Colors.WHITE}").strip() or "5")
            self.cooldown_min = int(input(f"{Colors.CYAN}[?] Min cooldown (minutes): {Colors.WHITE}").strip() or "15")
            self.cooldown_max = int(input(f"{Colors.CYAN}[?] Max cooldown (minutes): {Colors.WHITE}").strip() or "20")
            if self.cooldown_min < 5:
                self.cooldown_min = 5
            if self.cooldown_max < self.cooldown_min:
                self.cooldown_max = self.cooldown_min + 5
        
        self._save_config()
        print(f"\n{Colors.GREEN}[✓] Configuration complete!{Colors.RESET}")
    
    def _save_config(self):
        self.config = {
            'api_id': self.api_id,
            'api_hash': self.api_hash,
            'phone_number': self.phone_number,
            'min_delay': self.min_delay,
            'max_delay': self.max_delay,
            'ad_duration_min': self.ad_duration_min,
            'ad_duration_max': self.ad_duration_max,
            'cycles_before_cooldown': self.cycles_before_cooldown,
            'cooldown_min': self.cooldown_min,
            'cooldown_max': self.cooldown_max,
        }
        Config.save(self.config)
    
    # ------------------------------------------------------------------------
    # Authentication Methods
    # ------------------------------------------------------------------------
    def set_auth(self, init_data: str):
        self.init_data = init_data
        self.headers['X-Telegram-Init-Data'] = init_data
        
        try:
            params = dict(urllib.parse.parse_qsl(init_data))
            if 'user' in params:
                import html
                user_data = json.loads(html.unescape(params['user']))
                self.user_id = user_data.get('id')
                print(f"{Colors.MINT}[✓] User ID: {self.user_id}{Colors.RESET}")
        except:
            pass
    
    async def _get_init_data_telegram(self):
        print(f"\n{Colors.SKY}[*] Connecting to Telegram...{Colors.RESET}")
        
        self.telegram_client = TelegramClient(
            'session_usdtflow',
            int(self.api_id),
            self.api_hash
        )
        
        await self.telegram_client.start(phone=self.phone_number)
        print(f"{Colors.MINT}[✓] Successfully Logged In!{Colors.RESET}")
        
        try:
            print(f"{Colors.SKY}[*] Fetching Bot @{self.bot_username}...{Colors.RESET}")
            bot = await self.telegram_client.get_input_entity(self.bot_username)
            
            full_user = await self.telegram_client(functions.users.GetFullUserRequest(id=bot))
            bot_info = full_user.full_user.bot_info
            
            target_url = 'https://usdtflow.ru/'
            if bot_info and bot_info.menu_button and hasattr(bot_info.menu_button, 'url'):
                target_url = bot_info.menu_button.url
                print(f"{Colors.MINT}[✓] Auto-detected URL: {target_url}{Colors.RESET}")
            
            print(f"{Colors.SKY}[*] Requesting WebView...{Colors.RESET}")
            
            result = await self.telegram_client(functions.messages.RequestWebViewRequest(
                peer=bot,
                bot=bot,
                platform='android',
                from_bot_menu=True,
                url=target_url
            ))
            
            parsed_url = urllib.parse.urlparse(result.url)
            
            # Try to extract init data
            if parsed_url.fragment:
                fragment_params = urllib.parse.parse_qs(parsed_url.fragment)
                init_data = fragment_params.get('tgWebAppData', [None])[0]
                if init_data:
                    with open("usdtflow_init_data.txt", "w") as f:
                        f.write(init_data)
                    return init_data
            
            if parsed_url.query:
                query_params = urllib.parse.parse_qs(parsed_url.query)
                init_data = query_params.get('tgWebAppData', [None])[0]
                if init_data:
                    with open("usdtflow_init_data.txt", "w") as f:
                        f.write(init_data)
                    return init_data
            
            if 'tgWebAppData=' in result.url:
                import re
                match = re.search(r'tgWebAppData=([^&]+)', result.url)
                if match:
                    init_data = match.group(1)
                    with open("usdtflow_init_data.txt", "w") as f:
                        f.write(init_data)
                    return init_data
            
            return None
                
        except Exception as e:
            print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")
            return None
        finally:
            await self.telegram_client.disconnect()
    
    def get_init_data(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            init_data = loop.run_until_complete(self._get_init_data_telegram())
            loop.close()
            return init_data
        except Exception as e:
            print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")
            return None
    
    def load_init_data(self):
        if os.path.exists("usdtflow_init_data.txt"):
            try:
                with open("usdtflow_init_data.txt", "r") as f:
                    data = f.read().strip()
                    if data:
                        print(f"{Colors.MINT}[✓] Loaded init data from file{Colors.RESET}")
                        return data
            except:
                pass
        return None
    
    def authenticate(self) -> bool:
        print(f"{Colors.SKY}[*] Authenticating...{Colors.RESET}")
        
        if not self.init_data:
            print(f"{Colors.RED}[!] No init data available{Colors.RESET}")
            return False
        
        # Try to get user data
        data = self._api_request('GET', 'user')
        if data:
            self._update_user_data(data)
            print(f"{Colors.GREEN}[✓] Authentication successful!{Colors.RESET}")
            print(f"  {Colors.CYAN}Balance: {self.balance_usdt:.6f} USDT{Colors.RESET}")
            return True
        
        # Try auth endpoint
        data = self._api_request('POST', 'auth/telegram', {'initData': self.init_data})
        if data and data.get('success'):
            self._update_user_data(data.get('user', {}))
            print(f"{Colors.GREEN}[✓] Authentication successful!{Colors.RESET}")
            print(f"  {Colors.CYAN}Balance: {self.balance_usdt:.6f} USDT{Colors.RESET}")
            return True
        
        print(f"{Colors.RED}[!] Authentication failed{Colors.RESET}")
        return False
    
    def refresh_auth(self) -> bool:
        print(f"{Colors.SKY}[*] Refreshing auth...{Colors.RESET}")
        
        if os.path.exists("usdtflow_init_data.txt"):
            os.remove("usdtflow_init_data.txt")
        
        init_data = self.get_init_data()
        if init_data:
            self.set_auth(init_data)
            return self.authenticate()
        
        print(f"{Colors.RED}[!] Failed to refresh auth{Colors.RESET}")
        return False
    
    # ------------------------------------------------------------------------
    # API Methods
    # ------------------------------------------------------------------------
    def _decompress_response(self, content, encoding):
        if not content:
            return content
        try:
            if encoding == 'gzip':
                return gzip.decompress(content).decode('utf-8')
            elif encoding == 'deflate':
                return zlib.decompress(content, -zlib.MAX_WBITS).decode('utf-8')
            else:
                return content.decode('utf-8')
        except:
            try:
                return content.decode('utf-8')
            except:
                return str(content)
    
    def _api_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=self.headers, timeout=15)
            elif method.upper() == 'POST':
                response = self.session.post(url, headers=self.headers, json=data, timeout=15)
            else:
                return None
            
            if response.cookies:
                for cookie in response.cookies:
                    self.session.cookies.set(cookie.name, cookie.value)
            
            if response.status_code == 200:
                content = response.content
                encoding = response.headers.get('Content-Encoding', '')
                
                if encoding:
                    text = self._decompress_response(content, encoding)
                else:
                    text = response.text
                
                try:
                    return json.loads(text)
                except:
                    return None
                    
            elif response.status_code == 401:
                print(f"{Colors.RED}[!] Unauthorized - Need fresh init data{Colors.RESET}")
                return None
            else:
                return None
                
        except Exception as e:
            print(f"{Colors.YELLOW}[!] Request error: {e}{Colors.RESET}")
            return None
    
    def _update_user_data(self, data: Dict):
        self.user_data = data
        self.balance_usdt = float(data.get('balance_usdt', 0))
        self.balance_ton = float(data.get('balance_ton', 0))
        self.total_earned = float(data.get('total_earned', 0))
        self.ads_count = data.get('ads_count', 0)
    
    def get_user_data(self) -> bool:
        data = self._api_request('GET', 'user')
        if data:
            self._update_user_data(data)
            return True
        return False
    
    def get_ad_config(self) -> bool:
        data = self._api_request('GET', 'ads/config')
        if data:
            self.ad_config = data
            self.rewards = data.get('rewards_usdt', {})
            self.daily_limits = data.get('daily_limits', {})
            
            self.ad_providers = []
            for provider in ['gigapub', 'adexium', 'tads_fullscreen', 'monetix', 'adsgram', 'towerads']:
                if provider in self.rewards:
                    self.ad_providers.append(provider)
            return True
        return False
    
    def get_ads_status(self) -> bool:
        data = self._api_request('GET', 'ads')
        if data:
            self.watched_today = data.get('watched_today', 0)
            if 'daily_limits' in data:
                self.daily_limits = data.get('daily_limits', {})
            return True
        return False
    
    def watch_ad(self, provider: str) -> bool:
        # Simulate watching the ad with timer
        ad_duration = random.randint(self.ad_duration_min, self.ad_duration_max)
        
        # Show ad watching progress
        # The timer will be displayed by the caller
        time.sleep(ad_duration)
        
        # Now send the API request to claim reward
        data = self._api_request('POST', 'ads', {'provider': provider, 'flow': 'sdk'})
        
        if data and data.get('success'):
            reward = float(data.get('reward_usdt', 0))
            tickets = data.get('reward_tickets', 0)
            
            self.balance_usdt += reward
            self.total_earned += reward
            
            print(f"\n{Colors.GREEN}  ✅ Ad completed!{Colors.RESET}")
            print(f"  {Colors.GOLD}  +{reward:.6f} USDT{Colors.RESET}")
            if tickets > 0:
                print(f"  {Colors.PURPLE}  +{tickets} tickets{Colors.RESET}")
            print(f"  {Colors.CYAN}  New Balance: {self.balance_usdt:.6f} USDT{Colors.RESET}")
            return True
        else:
            print(f"\n{Colors.YELLOW}  ❌ Failed to watch {provider} ad{Colors.RESET}")
            return False
    
    def get_daily_bonus_status(self) -> Optional[Dict]:
        return self._api_request('GET', 'bonus/daily')
    
    def claim_daily_bonus(self) -> bool:
        data = self._api_request('POST', 'bonus/daily', {})
        
        if data and data.get('success'):
            reward = float(data.get('reward_usdt', 0))
            self.balance_usdt = float(data.get('balance_usdt', self.balance_usdt))
            self.total_earned += reward
            
            print(f"{Colors.GREEN}[✓] Daily bonus claimed!{Colors.RESET}")
            print(f"  {Colors.GOLD}+{reward:.6f} USDT{Colors.RESET}")
            return True
        else:
            print(f"{Colors.YELLOW}[!] Failed to claim daily bonus{Colors.RESET}")
            return False
    
    # ------------------------------------------------------------------------
    # Display Methods
    # ------------------------------------------------------------------------
    def display_stats(self):
        Panel.header("📊 USDTFLOW STATS")
        
        Panel.divider()
        print(f"{Colors.CYAN}{Colors.BOLD}👤 USER{Colors.RESET}")
        Panel.stats("ID", str(self.user_data.get('id', 'N/A')))
        Panel.stats("Username", f"@{self.user_data.get('username', 'N/A')}")
        Panel.stats("Referral Code", self.user_data.get('referral_code', 'N/A'))
        
        Panel.divider()
        print(f"{Colors.GOLD}{Colors.BOLD}💰 BALANCES{Colors.RESET}")
        Panel.stats("USDT", f"{self.balance_usdt:.6f}", Colors.GOLD)
        Panel.stats("TON", f"{self.balance_ton:.6f}", Colors.SKY)
        Panel.stats("Total Earned", f"{self.total_earned:.6f} USDT", Colors.MINT)
        
        Panel.divider()
        print(f"{Colors.PURPLE}{Colors.BOLD}📊 ADS{Colors.RESET}")
        Panel.stats("Watched Today", str(self.watched_today))
        Panel.stats("Total Ads", str(self.ads_count))
        
        Panel.divider()
        print(f"{Colors.MAGENTA}{Colors.BOLD}⚡ DAILY LIMITS{Colors.RESET}")
        for provider, limit in self.daily_limits.items():
            if provider != 'total':
                print(f"  {Colors.SKY}{provider}:{Colors.RESET} {Colors.WHITE}{limit} ads/day{Colors.RESET}")
        if self.daily_limits.get('total', 0) > 0:
            print(f"  {Colors.GOLD}Total:{Colors.RESET} {Colors.WHITE}{self.daily_limits.get('total', 0)} ads/day{Colors.RESET}")
        
        Panel.divider()
        print(f"{Colors.ORANGE}{Colors.BOLD}⚙️ SETTINGS{Colors.RESET}")
        Panel.stats("Ad Duration", f"{self.ad_duration_min}-{self.ad_duration_max} seconds")
        Panel.stats("Delay Range", f"{self.min_delay}-{self.max_delay} seconds")
        Panel.stats("Cooldown", f"Every {self.cycles_before_cooldown} cycles, {self.cooldown_min}-{self.cooldown_max} mins")
        print()
    
    # ------------------------------------------------------------------------
    # Main Automation
    # ------------------------------------------------------------------------
    def run_auto_mode(self):
        Panel.header("🔄 AUTO MODE", f"Ad: {self.ad_duration_min}-{self.ad_duration_max}s | Delay: {self.min_delay}-{self.max_delay}s | Cooldown: {self.cycles_before_cooldown} cycles")
        
        # Load initial data
        print(f"{Colors.SKY}[*] Loading data...{Colors.RESET}")
        if not self.get_user_data():
            print(f"{Colors.RED}[!] Failed to get user data{Colors.RESET}")
            return
        if not self.get_ad_config():
            print(f"{Colors.RED}[!] Failed to get ad config{Colors.RESET}")
            return
        if not self.get_ads_status():
            print(f"{Colors.RED}[!] Failed to get ads status{Colors.RESET}")
            return
        
        self.display_stats()
        
        # Check daily bonus
        bonus_data = self.get_daily_bonus_status()
        if bonus_data and bonus_data.get('can_claim', False):
            print(f"{Colors.GREEN}[✓] Daily bonus available!{Colors.RESET}")
            self.claim_daily_bonus()
            print()
        
        cycle = 0
        total_ads = 0
        total_earned_cycle = 0.0
        
        while True:
            cycle += 1
            
            print(f"\n{Colors.GOLD}{Colors.BOLD}═══ CYCLE {cycle} ═══{Colors.RESET}")
            print(f"{Colors.WHITE}⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
            
            # Refresh data
            if not self.get_user_data():
                print(f"{Colors.RED}[!] Failed to get user data, refreshing...{Colors.RESET}")
                if not self.refresh_auth():
                    break
                self.get_user_data()
            
            if not self.get_ads_status():
                print(f"{Colors.RED}[!] Failed to get ads status{Colors.RESET}")
                break
            
            # Check daily limit
            total_limit = self.daily_limits.get('total', 0)
            if total_limit > 0 and self.watched_today >= total_limit:
                print(f"{Colors.YELLOW}[!] Daily limit reached ({self.watched_today}/{total_limit}){Colors.RESET}")
                next_check = datetime.now() + timedelta(hours=1)
                print(f"{Colors.SKY}[*] Next check: {next_check.strftime('%H:%M:%S')}{Colors.RESET}")
                Panel.countdown(3600, "Waiting for reset")
                continue
            
            # Count available ads
            available_ads = []
            for provider in self.ad_providers:
                provider_limit = self.daily_limits.get(provider, 0)
                if provider_limit > 0 and self.watched_today < provider_limit:
                    available_ads.append(provider)
            
            if not available_ads:
                print(f"{Colors.YELLOW}[!] No ads available{Colors.RESET}")
                Panel.countdown(random.randint(60, 180), "Waiting before retry")
                continue
            
            print(f"\n{Colors.MINT}[*] Found {len(available_ads)} ad(s) available{Colors.RESET}\n")
            
            # Watch ads
            ads_watched = 0
            cycle_earned = 0.0
            
            for idx, provider in enumerate(available_ads, 1):
                # Show ad watching timer
                ad_duration = random.randint(self.ad_duration_min, self.ad_duration_max)
                Panel.watch_ad_timer(ad_duration, provider, idx, len(available_ads))
                
                # Get balance before watching
                balance_before = self.balance_usdt
                
                # Now claim the reward
                if self.watch_ad(provider):
                    ads_watched += 1
                    total_ads += 1
                    self.watched_today += 1
                    
                    # Calculate earned this cycle
                    earned = self.balance_usdt - balance_before
                    cycle_earned += earned
                    total_earned_cycle += earned
                    
                    # Progress
                    progress = (idx / len(available_ads)) * 100
                    print(f"  {Colors.SKY}  📊 Progress: {idx}/{len(available_ads)} ({progress:.0f}%){Colors.RESET}")
                    
                    # Delay between ads
                    if idx < len(available_ads):
                        delay = random.randint(self.min_delay, self.max_delay)
                        print()
                        Panel.countdown(delay, "Waiting before next ad")
                        print()
                    
                    self.get_user_data()
                
                # Check daily limit
                if total_limit > 0 and self.watched_today >= total_limit:
                    print(f"\n{Colors.YELLOW}[!] Daily limit reached{Colors.RESET}")
                    break
            
            # Cycle summary
            print(f"\n{Colors.GOLD}━━━ CYCLE {cycle} SUMMARY ━━━{Colors.RESET}")
            print(f"  {Colors.GREEN}✅ Ads watched: {ads_watched}{Colors.RESET}")
            print(f"  {Colors.GOLD}💰 Earned this cycle: {cycle_earned:.6f} USDT{Colors.RESET}")
            print(f"  {Colors.CYAN}💰 Balance: {self.balance_usdt:.6f} USDT{Colors.RESET}")
            print(f"  {Colors.MINT}📈 Total earned: {self.total_earned:.6f} USDT{Colors.RESET}")
            print(f"  {Colors.PURPLE}📊 Today: {self.watched_today} ads{Colors.RESET}")
            
            # Check if cooldown is needed
            if cycle % self.cycles_before_cooldown == 0 and ads_watched > 0:
                cooldown_seconds = random.randint(self.cooldown_min * 60, self.cooldown_max * 60)
                Panel.cooldown_timer(cooldown_seconds, cycle)
                
                # Show stats after cooldown
                self.display_stats()
                
                # Check if we should continue after cooldown
                print(f"\n{Colors.SKY}[*] Resuming operations...{Colors.RESET}")
                continue
            
            if ads_watched == 0:
                Panel.countdown(random.randint(60, 180), "Waiting before retry")
            else:
                wait_time = random.randint(30, 60)
                print(f"\n{Colors.SKY}[*] Next cycle in {wait_time}s...{Colors.RESET}")
                Panel.countdown(wait_time, "Preparing next cycle")
            
            if cycle % 3 == 0:
                self.display_stats()


# ============================================================================
# MAIN APPLICATION
# ============================================================================
def display_banner():
    os.system('clear' if os.name != 'nt' else 'cls')
    
    print(f"{Colors.GOLD}{Colors.BOLD}╔{'═' * 78}╗{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("  ██╗   ██╗███████╗██████╗ ████████╗███████╗██╗      ██████╗ ██╗    ██╗")
    print("  ██║   ██║██╔════╝██╔══██╗╚══██╔══╝██╔════╝██║     ██╔═══██╗██║    ██║")
    print("  ██║   ██║███████╗██████╔╝   ██║   █████╗  ██║     ██║   ██║██║ █╗ ██║")
    print("  ██║   ██║╚════██║██╔══██╗   ██║   ██╔══╝  ██║     ██║   ██║██║███╗██║")
    print("  ╚██████╔╝███████║██║  ██║   ██║   ██║     ███████╗╚██████╔╝╚███╔███╔╝")
    print("   ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝ ")
    print(Colors.RESET)
    print(f"{Colors.GOLD}{Colors.BOLD}                    💰 USDTFLOW AUTOMATION v1 💰{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}╚{'═' * 78}╝{Colors.RESET}")


def main():
    try:
        display_banner()
        
        bot = USDTFlowBot()
        bot.setup_config()
        
        # Get init data
        init_data = bot.load_init_data()
        if not init_data:
            print(f"{Colors.YELLOW}[!] No init data found, getting fresh...{Colors.RESET}")
            init_data = bot.get_init_data()
            if not init_data:
                print(f"{Colors.RED}[!] Failed to get init data{Colors.RESET}")
                return
        
        bot.set_auth(init_data)
        
        # Authenticate
        print(f"\n{Colors.SKY}[*] Authenticating...{Colors.RESET}")
        if not bot.authenticate():
            print(f"{Colors.RED}[!] Authentication failed. Refreshing...{Colors.RESET}")
            if not bot.refresh_auth():
                print(f"{Colors.RED}[!] Failed to authenticate{Colors.RESET}")
                return
        
        # Load data
        bot.get_user_data()
        bot.get_ad_config()
        bot.get_ads_status()
        bot.display_stats()
        
        # Main menu loop
        while True:
            Panel.menu({
                1: "🔄 Auto Mode (Watch Ads)",
                2: "📊 Show Stats",
                3: "🎁 Claim Daily Bonus",
                4: "🔑 Refresh Auth",
                5: "⚙️ Change Settings",
                6: "🚪 Exit"
            })
            
            choice = input(f"{Colors.YELLOW}[?] Choice: {Colors.WHITE}").strip()
            
            if choice == '1':
                bot.run_auto_mode()
            elif choice == '2':
                bot.get_user_data()
                bot.get_ads_status()
                bot.display_stats()
            elif choice == '3':
                bot.get_user_data()
                bonus_data = bot.get_daily_bonus_status()
                if bonus_data and bonus_data.get('can_claim', False):
                    bot.claim_daily_bonus()
                else:
                    print(f"{Colors.YELLOW}[!] Daily bonus not available{Colors.RESET}")
                    if bonus_data and bonus_data.get('claimed_today', False):
                        print(f"{Colors.YELLOW}[!] Already claimed today{Colors.RESET}")
                bot.display_stats()
            elif choice == '4':
                if bot.refresh_auth():
                    bot.get_user_data()
                    bot.display_stats()
            elif choice == '5':
                print(f"\n{Colors.SKY}[*] Current Settings:{Colors.RESET}")
                print(f"  Ad Duration: {bot.ad_duration_min}-{bot.ad_duration_max}s")
                print(f"  Delay Range: {bot.min_delay}-{bot.max_delay}s")
                print(f"  Cooldown: Every {bot.cycles_before_cooldown} cycles, {bot.cooldown_min}-{bot.cooldown_max} mins")
                print()
                
                new_min_ad = input(f"{Colors.CYAN}[?] Min ad duration (seconds): {Colors.WHITE}").strip()
                new_max_ad = input(f"{Colors.CYAN}[?] Max ad duration (seconds): {Colors.WHITE}").strip()
                new_min = input(f"{Colors.CYAN}[?] Min delay (seconds): {Colors.WHITE}").strip()
                new_max = input(f"{Colors.CYAN}[?] Max delay (seconds): {Colors.WHITE}").strip()
                new_cycles = input(f"{Colors.CYAN}[?] Cycles before cooldown: {Colors.WHITE}").strip()
                new_cooldown_min = input(f"{Colors.CYAN}[?] Min cooldown (minutes): {Colors.WHITE}").strip()
                new_cooldown_max = input(f"{Colors.CYAN}[?] Max cooldown (minutes): {Colors.WHITE}").strip()
                
                if new_min_ad.isdigit():
                    bot.ad_duration_min = int(new_min_ad)
                if new_max_ad.isdigit():
                    bot.ad_duration_max = int(new_max_ad)
                if new_min.isdigit():
                    bot.min_delay = int(new_min)
                if new_max.isdigit():
                    bot.max_delay = int(new_max)
                if new_cycles.isdigit():
                    bot.cycles_before_cooldown = int(new_cycles)
                if new_cooldown_min.isdigit():
                    bot.cooldown_min = int(new_cooldown_min)
                if new_cooldown_max.isdigit():
                    bot.cooldown_max = int(new_cooldown_max)
                
                if bot.ad_duration_min < 5:
                    bot.ad_duration_min = 5
                if bot.ad_duration_max < bot.ad_duration_min:
                    bot.ad_duration_max = bot.ad_duration_min + 10
                if bot.min_delay < 5:
                    bot.min_delay = 5
                if bot.max_delay < bot.min_delay:
                    bot.max_delay = bot.min_delay + 10
                if bot.cooldown_min < 5:
                    bot.cooldown_min = 5
                if bot.cooldown_max < bot.cooldown_min:
                    bot.cooldown_max = bot.cooldown_min + 5
                if bot.cycles_before_cooldown < 1:
                    bot.cycles_before_cooldown = 1
                
                bot._save_config()
                print(f"{Colors.GREEN}[✓] Settings updated!{Colors.RESET}")
                print(f"  Ad Duration: {bot.ad_duration_min}-{bot.ad_duration_max}s")
                print(f"  Delay Range: {bot.min_delay}-{bot.max_delay}s")
                print(f"  Cooldown: Every {bot.cycles_before_cooldown} cycles, {bot.cooldown_min}-{bot.cooldown_max} mins")
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
#!/usr/bin/env python3
"""
OpenEarn Bot – Advanced Multi-Account Dashboard with Live Logs
Support for multiple accounts with different IP addresses
"""

import os
import sys
import asyncio

# ========== FIX: Set event loop BEFORE importing pyrogram ==========
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import json
import time
import random
import re
import tempfile
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from urllib.parse import parse_qs, urlparse

import requests
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== SUPPRESS PYROGRAM WELCOME ==========
import contextlib
with contextlib.redirect_stdout(open(os.devnull, 'w')):
    from pyrogram import Client
    from pyrogram.raw.functions.messages import RequestWebView

# ========== COLORS ==========
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    GOLD = '\033[38;5;214m'
    PURPLE = '\033[38;5;141m'
    SKY = '\033[38;5;117m'
    MINT = '\033[38;5;157m'
    ROSE = '\033[38;5;204m'
    ORANGE = '\033[38;5;208m'

# ========== CONFIG ==========
API_ID = 32744606
API_HASH = 'f58682565ec84dcd4e529a33246f07aa'
BOT_USERNAME = 'TheOpenEarnAppBot'
BASE_URL = "https://app.theopenearn.info/api"
AD_WATCH_DURATION = 30
TAPS_PER_REQUEST = 25
TOTAL_TAPS = 100
LOG_FILE = "openearn.log"
LIVE_LOG = []
PROVIDER_COOLDOWN = 30  # minutes

# Provider configurations with correct ad types
PROVIDER_CONFIG = {
    'adsgram': {'ad_type': 'video', 'fallback': True, 'click_simulate': True},
    'adsgram_task': {'ad_type': 'task', 'fallback': True, 'click_simulate': False},
    'monetag': {'ad_type': 'impression', 'fallback': True, 'click_simulate': True},
    'richads': {'ad_type': 'video', 'fallback': True, 'click_simulate': True},
    'telega': {'ad_type': 'video', 'fallback': True, 'click_simulate': True},
    'onclicka': {'ad_type': 'video', 'fallback': True, 'click_simulate': True},
    'taddy': {'ad_type': 'video', 'fallback': True, 'click_simulate': True},
    'gigapub': {'ad_type': 'video', 'fallback': True, 'click_simulate': True},
}

def add_log(message: str):
    """Add message to live log"""
    global LIVE_LOG
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")
    
    LIVE_LOG.append(log_entry)
    if len(LIVE_LOG) > 8:
        LIVE_LOG.pop(0)

# ========== CONFIG MANAGER ==========
class Config:
    CONFIG_FILE = "openearn_config.json"
    
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
        except Exception as e:
            print(f"{Colors.YELLOW}! Error saving config: {e}{Colors.RESET}")

# ========== PROXY MANAGER ==========
class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        self.load_proxies()
    
    def load_proxies(self):
        """Load proxies from file or use default list"""
        if os.path.exists("proxies.json"):
            try:
                with open("proxies.json", "r") as f:
                    self.proxies = json.load(f)
                print(f"{Colors.GREEN}✓ Loaded {len(self.proxies)} proxies from file{Colors.RESET}")
                return
            except Exception as e:
                print(f"{Colors.YELLOW}! Error loading proxies: {e}{Colors.RESET}")
        
        print(f"{Colors.YELLOW}! No proxies configured, using direct connection{Colors.RESET}")
    
    def get_proxy_for_account(self, account_index: int) -> Optional[Dict]:
        """Get a proxy for a specific account (ensures different IP per account)"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[account_index % len(self.proxies)]
        return proxy

proxy_manager = ProxyManager()

# ========== SESSION WITH PROXY ==========
def create_session_with_proxy(proxy: Optional[Dict] = None) -> requests.Session:
    """Create a requests session with optional proxy"""
    session = requests.Session()
    session.verify = False
    session.timeout = 30
    
    if proxy:
        session.proxies.update(proxy)
    
    return session

# ========== ACCOUNT ENGINE ==========
class AccountEngine:
    def __init__(self, account_info: Dict, account_index: int, proxy: Optional[Dict] = None):
        self.phone = account_info['phone']
        self.username = account_info['username']
        self.session_str = account_info['session']
        self.account_index = account_index
        self.proxy = proxy
        self.session = create_session_with_proxy(proxy)
        
        self.headers = None
        self.next_tap = time.time()
        self.next_ad = time.time()
        self.balance = "0"
        self.tot = "0"
        self.info = "INIT"
        self.progress = ""
        self.user_id = None
        self.user_data = None
        self.ad_session_active = False
        self.total_ads = 0
        self.total_tot = 0
        self.total_ton = 0.0
        self.providers_status = {}
        self.running = True
        self.ad_timer = 0
        self.current_provider = ""
        self.last_log = ""
        self.auth_initialized = False
        self.ip_address = self._get_ip_address()
        
        # Provider cooldown tracking
        self.provider_cooldown_until = {}
        self.provider_failures = {}
        self.max_failures = 3
        
        if proxy:
            self.log(f"🌐 Using proxy: {proxy.get('http', 'unknown')}")
        else:
            self.log(f"🌐 Direct connection")
        
        self.update_status()

    def _get_ip_address(self) -> str:
        """Get the IP address being used"""
        try:
            if self.proxy:
                proxy_url = self.proxy.get('http', '')
                if proxy_url:
                    import re
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', proxy_url)
                    if match:
                        return match.group(1)
            
            response = self.session.get('https://api.ipify.org?format=json', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('ip', 'unknown')
        except:
            pass
        return 'unknown'

    def update_status(self):
        return {
            'username': self.username,
            'info': self.info,
            'progress': self.progress,
            'balance': self.balance,
            'tot': self.tot,
            'total_ads': self.total_ads,
            'total_tot': self.total_tot,
            'total_ton': self.total_ton,
            'providers': self.providers_status if self.providers_status else {},
            'ad_timer': self.ad_timer,
            'current_provider': self.current_provider,
            'ip': self.ip_address
        }

    def log(self, message: str):
        log_msg = f"[{self.username}] {message}"
        add_log(log_msg)
        self.last_log = message
        self.update_status()

    async def fetch_initial_tg_data(self):
        try:
            tg_data = await self.refresh_tg_data()
            self.headers = self.build_headers(tg_data)
            self.auth_initialized = True
            
            params = dict(urllib.parse.parse_qsl(tg_data))
            user_param = params.get('user', '')
            if user_param:
                user_json = json.loads(urllib.parse.unquote(user_param))
                self.user_id = str(user_json.get('id', ''))
            
            resp = self.session.get(f"{BASE_URL}/user", headers=self.headers, timeout=10)
            
            if resp.status_code == 200:
                self.user_data = resp.json()
                self.balance = str(self.user_data.get('balance', '0'))
                self.tot = str(self.user_data.get('tot_balance', '0'))
                self.log(f"💰 Balance: {self.balance} TON, TOT: {self.tot}")
            
            self.info = "🟢 READY"
            return True
        except Exception as e:
            self.log(f"❌ Fetch error: {e}")
            return False

    async def refresh_tg_data(self):
        client = Client(":memory:", session_string=self.session_str, api_id=API_ID, api_hash=API_HASH)
        await client.connect()
        bot_peer = await client.resolve_peer(BOT_USERNAME)
        web_view = await client.invoke(
            RequestWebView(peer=bot_peer, bot=bot_peer, url="https://app.theopenearn.com/", platform="ios")
        )
        parsed = urlparse(web_view.url)
        fragment = parse_qs(parsed.fragment)
        tg_data = fragment['tgWebAppData'][0]
        await client.disconnect()
        return tg_data

    def build_headers(self, tg_data):
        return {
            'Authorization': f"tma {tg_data}",
            'Accept': '*/*',
            'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'
        }

    def api_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        if not self.auth_initialized:
            return None
            
        url = f"{BASE_URL}/{endpoint.lstrip('/')}"
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=self.headers, timeout=30)
            else:
                response = self.session.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    return None
            elif response.status_code == 401:
                self.auth_initialized = False
                return None
            else:
                return None
        except:
            return None

    async def get_daily_ad_status(self) -> Tuple[Optional[List[str]], Optional[Dict]]:
        try:
            data = self.api_request('GET', 'ads/daily-status')
            if data:
                providers = data.get('providers', {})
                self.providers_status = {}
                available = []
                
                for name, info in providers.items():
                    remaining = info.get('remaining', 0)
                    blocked = info.get('blocked', False)
                    cooldown = info.get('cooldown_remaining', 0)
                    limit = info.get('limit', 0)
                    used = info.get('used', 0)
                    
                    self.providers_status[name] = {
                        'remaining': remaining,
                        'blocked': blocked,
                        'cooldown': cooldown,
                        'limit': limit,
                        'used': used
                    }
                    
                    if name in self.provider_cooldown_until:
                        if time.time() < self.provider_cooldown_until[name]:
                            continue
                        else:
                            del self.provider_cooldown_until[name]
                            if name in self.provider_failures:
                                del self.provider_failures[name]
                    
                    if remaining > 0 and not blocked and cooldown == 0:
                        available.append(name)
                
                return available, self.providers_status
            return [], {}
        except Exception as e:
            self.log(f"❌ Daily status error: {e}")
            return [], {}

    async def complete_ad(self, provider: str) -> Optional[Dict]:
        try:
            self.ad_session_active = True
            self.current_provider = provider
            self.info = f"📺 WATCHING {provider.upper()}"
            self.ad_timer = AD_WATCH_DURATION
            
            for remaining in range(AD_WATCH_DURATION, 0, -1):
                if not self.running:
                    return None
                self.ad_timer = remaining
                self.progress = f"⏳ {remaining}s"
                self.update_status()
                await asyncio.sleep(1)
            
            self.ad_timer = 0
            self.info = f"💰 CLAIMING {provider.upper()}"
            self.progress = "claiming..."
            
            config = PROVIDER_CONFIG.get(provider, {'ad_type': 'video', 'fallback': True})
            ad_type = config.get('ad_type', 'video')
            
            if provider == 'adsgram_task':
                ad_type = 'task'
            elif provider == 'monetag':
                ad_type = 'impression'
            
            payload = {
                "ad_type": ad_type,
                "provider": provider,
                "watched": True,
                "fallback": config.get('fallback', True)
            }
            
            data = self.api_request('POST', 'ads/complete', payload)
            self.ad_session_active = False
            
            if data:
                reward = data.get('reward', 0)
                tot_reward = data.get('tot_reward', 0)
                is_bonus = data.get('is_bonus', False)
                is_tot_only = data.get('is_tot_only', False)
                new_balance = data.get('new_balance')
                
                if new_balance:
                    self.balance = str(new_balance)
                if tot_reward:
                    self.tot = str(float(self.tot) + tot_reward if self.tot else tot_reward)
                
                self.total_ads += 1
                self.total_tot += tot_reward if tot_reward else 0
                self.total_ton += reward if reward else 0
                
                if provider in self.providers_status:
                    self.providers_status[provider]['remaining'] -= 1
                
                self.provider_cooldown_until[provider] = time.time() + (PROVIDER_COOLDOWN * 60)
                
                reward_msg = f"✅ {provider}: 💰 +{reward} TON | 💎 +{tot_reward} TOT"
                if is_bonus:
                    reward_msg += " | 🎉 BONUS!"
                if is_tot_only:
                    reward_msg += " | 📌 TOT-only"
                self.log(reward_msg)
                
                await self.check_and_spin_wheel()
                return data
            else:
                self.info = "❌ FAILED"
                self.progress = "failed"
                self.log(f"❌ {provider} ad failed")
                return None
                
        except Exception as e:
            self.ad_session_active = False
            self.log(f"❌ {provider} ad error: {e}")
            return None

    async def check_and_spin_wheel(self):
        try:
            data = self.api_request('GET', 'wheel/status')
            if data:
                free_spins = data.get('free_spins_available', 0)
                if free_spins > 0:
                    self.info = "🎰 WHEEL"
                    self.progress = "spinning..."
                    self.log(f"🎰 Spinning wheel ({free_spins} free spins)")
                    spin = self.api_request('POST', 'wheel/spin', {"is_paid": False})
                    if spin:
                        self.balance = str(spin.get('new_balance', self.balance))
                        self.log("🎉 Wheel spin complete!")
                    await asyncio.sleep(1)
        except Exception as e:
            pass

    async def tapping_cycle(self):
        self.info = "👆 TAPPING"
        self.progress = "0/100"
        url = f"{BASE_URL}/earn"
        tap_headers = self.headers.copy()
        tap_headers['Referer'] = 'https://app.theopenearn.info/earn'
        tap_headers['Origin'] = 'https://app.theopenearn.info'
        total_taps = 0
        
        while self.running and total_taps < TOTAL_TAPS:
            remaining = TOTAL_TAPS - total_taps
            taps = min(TAPS_PER_REQUEST, remaining)
            payload = {"taps": taps}
            
            try:
                resp = self.session.post(url, json=payload, headers=tap_headers, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    total_taps += taps
                    self.progress = f"{total_taps}/{TOTAL_TAPS}"
                    
                    if data.get('cycle_complete') == True or total_taps >= TOTAL_TAPS:
                        user_data = self.api_request('GET', 'user')
                        if user_data:
                            self.balance = str(user_data.get('balance', '0'))
                            self.tot = str(user_data.get('tot_balance', '0'))
                        
                        cooldown_until = data.get('cooldown_until')
                        if cooldown_until:
                            cooldown_time = datetime.fromisoformat(cooldown_until.replace('Z', '+00:00'))
                            wait = max(0, (cooldown_time - datetime.now().astimezone()).total_seconds())
                            self.info = "⏳ TAP COOLDOWN"
                            self.progress = f"{int(wait)}s"
                            self.log(f"⏳ Tap cooldown: {int(wait)}s")
                            return time.time() + wait
                        else:
                            self.info = "🟢 READY"
                            self.progress = ""
                            return time.time() + 210
                    await asyncio.sleep(0.5)
                elif resp.status_code == 429:
                    error = resp.json()
                    detail = error.get('detail', '')
                    match = re.search(r'(\d+)\s*s', detail)
                    wait = int(match.group(1)) if match else 30
                    self.info = "⏳ RATE LIMIT"
                    self.progress = f"{wait}s"
                    self.log(f"⏳ Tap rate limit: {wait}s")
                    return time.time() + wait
                else:
                    await asyncio.sleep(5)
                    return time.time() + 60
            except Exception as e:
                await asyncio.sleep(5)
                return time.time() + 60
        
        self.info = "🟢 READY"
        self.progress = ""
        return time.time() + 60

    async def watch_ad_cycle(self):
        self.info = "🔍 CHECKING ADS"
        self.progress = "fetching..."
        
        available, providers = await self.get_daily_ad_status()
        
        if not available:
            min_cooldown = None
            if providers:
                for name, info in providers.items():
                    cd = info.get('cooldown', 0)
                    if cd > 0:
                        if min_cooldown is None or cd < min_cooldown:
                            min_cooldown = cd
            
            if min_cooldown:
                self.info = "⏳ COOLDOWN"
                self.progress = f"{min_cooldown}s"
                return time.time() + min_cooldown
            else:
                self.info = "📭 NO ADS"
                self.progress = "waiting..."
                self.log("📭 No ads available")
                return time.time() + 60
        
        self.info = "📺 WATCHING ADS"
        success_count = 0
        
        for provider in available:
            self.log(f"▶️ Starting {provider} ad...")
            result = await self.complete_ad(provider)
            
            if result:
                success_count += 1
            else:
                if self.info == "⏳ RATE_LIMIT":
                    return time.time() + 60
        
        if success_count > 0:
            self.log(f"✅ Completed {success_count} ads!")
            
        self.info = "🟢 READY"
        self.progress = "waiting..."
        return time.time() + 5

    async def run(self):
        if not await self.fetch_initial_tg_data():
            self.info = "❌ LOGIN FAIL"
            return
        
        self.next_tap = time.time()
        self.next_ad = time.time()
        
        self.info = "🟢 READY"
        self.progress = "starting..."
        self.log("🚀 Started")
        
        while self.running:
            now = time.time()
            
            if self.ad_session_active:
                await asyncio.sleep(1)
                continue
            
            if now >= self.next_ad:
                self.next_ad = await self.watch_ad_cycle()
                if self.next_ad > now + 60:
                    self.next_tap = max(self.next_tap, now + 10)
            elif now >= self.next_tap:
                self.next_tap = await self.tapping_cycle()
            else:
                wait = min(self.next_tap - now, self.next_ad - now)
                if wait > 0:
                    if wait < 60:
                        for remaining in range(int(wait), 0, -1):
                            if not self.running:
                                break
                            self.progress = f"{remaining}s"
                            if remaining % 10 == 0:
                                self.info = "⏳ WAITING"
                            await asyncio.sleep(1)
                    else:
                        self.info = "⏳ WAITING"
                        self.progress = f"{int(wait)}s"
                        await asyncio.sleep(min(wait, 30))
            
            await asyncio.sleep(0.5)

    def stop(self):
        self.running = False

# ========== PYROGRAM LOGIN ==========
async def pyrogram_login(phone):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        session_path = tmp.name
    client = Client(session_path, api_id=API_ID, api_hash=API_HASH)
    await client.connect()
    try:
        sent_code = await client.send_code(phone)
        print(f"{Colors.GREEN}{Colors.BOLD}Enter confirmation code: {Colors.RESET}", end="")
        code = input().strip()
        try:
            await client.sign_in(phone, sent_code.phone_code_hash, code)
        except Exception:
            print(f"{Colors.GREEN}{Colors.BOLD}Enter 2FA password: {Colors.RESET}", end="")
            pwd = input().strip()
            await client.check_password(pwd)
        me = await client.get_me()
        session_str = await client.export_session_string()
        await client.disconnect()
        os.unlink(session_path)
        return me, session_str
    except Exception as e:
        await client.disconnect()
        os.unlink(session_path)
        raise e

async def add_accounts():
    print(f"\n{Colors.CYAN}{Colors.BOLD}🔹 ADD TELEGRAM ACCOUNTS{Colors.RESET}")
    print(f"{Colors.BOLD}{'─' * 50}{Colors.RESET}")
    num = int(input(f"{Colors.YELLOW}{Colors.BOLD}How many accounts to add? : {Colors.RESET}"))
    new_accounts = []
    for i in range(num):
        print(f"\n{Colors.MAGENTA}{Colors.BOLD}--- Account {i+1} ---{Colors.RESET}")
        phone = input(f"{Colors.GREEN}{Colors.BOLD}Phone number (with country code): {Colors.RESET}").strip()
        print(f"{Colors.YELLOW}{Colors.BOLD}ℹ️ Logging in...{Colors.RESET}")
        try:
            me, session_str = await pyrogram_login(phone)
            username = me.username or phone
            new_accounts.append({
                "phone": phone,
                "session": session_str,
                "username": username
            })
            print(f"{Colors.GREEN}{Colors.BOLD}✅ Account {username} added.{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}{Colors.BOLD}❌ Login failed: {e}{Colors.RESET}")
    return new_accounts

async def manage_accounts():
    existing = []
    if os.path.exists("pyro_accounts.json"):
        with open("pyro_accounts.json", "r") as f:
            existing = json.load(f)
        if existing:
            print(f"\n{Colors.CYAN}{Colors.BOLD}🔹 EXISTING ACCOUNTS{Colors.RESET}")
            print(f"{Colors.BOLD}{'─' * 50}{Colors.RESET}")
            for acc in existing:
                print(f"{Colors.GREEN}{Colors.BOLD}  - {acc.get('username', acc['phone'])}{Colors.RESET}")
            add_more = input(f"\n{Colors.YELLOW}{Colors.BOLD}Add more accounts? (y/n): {Colors.RESET}").strip().lower()
            if add_more == 'y':
                new_accs = await add_accounts()
                existing.extend(new_accs)
                with open("pyro_accounts.json", "w") as f:
                    json.dump(existing, f, indent=4)
            return existing
    new_accs = await add_accounts()
    if new_accs:
        with open("pyro_accounts.json", "w") as f:
            json.dump(new_accs, f, indent=4)
    return new_accs

def manage_proxies():
    """Manage proxy configuration"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}🔹 PROXY CONFIGURATION{Colors.RESET}")
    print(f"{Colors.BOLD}{'─' * 50}{Colors.RESET}")
    
    if os.path.exists("proxies.json"):
        with open("proxies.json", "r") as f:
            proxies = json.load(f)
        print(f"{Colors.GREEN}✓ Loaded {len(proxies)} proxies from file{Colors.RESET}")
        for i, p in enumerate(proxies):
            print(f"  {i+1}. {p.get('http', 'unknown')}")
        update = input(f"\n{Colors.YELLOW}Update proxies? (y/n): {Colors.RESET}").strip().lower()
        if update != 'y':
            return proxies
    
    print(f"\n{Colors.YELLOW}Enter proxies (one per line, empty line to finish){Colors.RESET}")
    print(f"{Colors.CYAN}Format: http://user:pass@ip:port or http://ip:port{Colors.RESET}")
    proxies = []
    while True:
        proxy = input(f"{Colors.GREEN}Proxy: {Colors.RESET}").strip()
        if not proxy:
            break
        if '://' not in proxy:
            proxy = f"http://{proxy}"
        proxies.append({
            'http': proxy,
            'https': proxy.replace('http://', 'https://')
        })
    
    if proxies:
        with open("proxies.json", "w") as f:
            json.dump(proxies, f, indent=4)
        print(f"{Colors.GREEN}✓ Saved {len(proxies)} proxies{Colors.RESET}")
    
    return proxies

# ========== DASHBOARD FUNCTIONS ==========
def format_cooldown(seconds: int) -> str:
    if seconds <= 0:
        return "DONE"
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}m {secs}s"

def format_balance(balance: str) -> str:
    try:
        return f"${float(balance):.8f}"
    except:
        return balance

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def display_dashboard(engines: List[AccountEngine]):
    """Display the dashboard with tables"""
    clear_screen()
    
    # Header
    print(f"{Colors.GOLD}{Colors.BOLD}╔═══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║  {Colors.CYAN}{Colors.BOLD} ██████╗ ██████╗ ███████╗███╗   ██╗    ███████╗ █████╗ ██████╗ ███╗   ██╗{Colors.RESET} {Colors.GOLD}║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║  {Colors.CYAN}{Colors.BOLD}██╔═══██╗██╔══██╗██╔════╝████╗  ██║    ██╔════╝██╔══██╗██╔══██╗████╗  ██║{Colors.RESET} {Colors.GOLD}║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║  {Colors.CYAN}{Colors.BOLD}██║   ██║██████╔╝█████╗  ██╔██╗ ██║    █████╗  ███████║██████╔╝██╔██╗ ██║{Colors.RESET} {Colors.GOLD}║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║  {Colors.CYAN}{Colors.BOLD}██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║    ██╔══╝  ██╔══██║██╔══██╗██║╚██╗██║{Colors.RESET} {Colors.GOLD}║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║  {Colors.CYAN}{Colors.BOLD}╚██████╔╝██║     ███████╗██║ ╚████║    ███████╗██║  ██║██║  ██║██║ ╚████║{Colors.RESET} {Colors.GOLD}║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║  {Colors.CYAN}{Colors.BOLD} ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝{Colors.RESET} {Colors.GOLD}║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║                                                                                           ║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║           {Colors.GREEN}{Colors.BOLD}🚀 OPEN EARN BOT - ADVANCED DASHBOARD {Colors.YELLOW}{Colors.BOLD}v2.0{Colors.RESET}            ║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print()
    
    # Account Table
    print(f"{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║                          📊 ACCOUNT STATUS                                                ║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}╠══════════════════════════════════════════════════════════════════════════════════════════════════╣{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.RESET} {Colors.GREEN}{Colors.BOLD}{'ACCOUNT':<14}{Colors.RESET} {Colors.WHITE}{'IP':<15}{Colors.RESET} {Colors.WHITE}{'STATUS':<18}{Colors.RESET} {Colors.WHITE}{'PROGRESS':<12}{Colors.RESET} {Colors.WHITE}{'BALANCE':<14}{Colors.RESET} {Colors.WHITE}{'TOT':<10}{Colors.RESET} {Colors.WHITE}{'ADS':<6}{Colors.RESET} {Colors.CYAN}{Colors.BOLD}║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}╠══════════════════════════════════════════════════════════════════════════════════════════════════╣{Colors.RESET}")
    
    for eng in engines:
        status = eng.update_status()
        info = status['info'][:16] if len(status['info']) > 16 else status['info']
        progress = status['progress']
        if status['ad_timer'] > 0:
            progress = f"⏱️ {status['ad_timer']}s"
        ip_display = status.get('ip', 'unknown')[:14]
        
        print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.RESET} {Colors.GREEN}{status['username'][:12]:<14}{Colors.RESET} ", end="")
        print(f"{Colors.MAGENTA}{ip_display:<15}{Colors.RESET} ", end="")
        print(f"{Colors.WHITE}{info:<18}{Colors.RESET} ", end="")
        print(f"{Colors.YELLOW}{progress[:10]:<12}{Colors.RESET} ", end="")
        print(f"{Colors.CYAN}{format_balance(status['balance']):<14}{Colors.RESET} ", end="")
        print(f"{Colors.PURPLE}{status['tot'][:8]:<10}{Colors.RESET} ", end="")
        print(f"{Colors.WHITE}{status['total_ads']:<6}{Colors.RESET} {Colors.CYAN}{Colors.BOLD}║{Colors.RESET}")
    
    print(f"{Colors.CYAN}{Colors.BOLD}╚══════════════════════════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print()
    
    # Provider Table - FIXED: Check if providers_status exists and is not None
    if engines and engines[0].providers_status:
        print(f"{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}║                    📡 AD PROVIDERS (cooldown updates in real-time)                  ║{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}╠══════════════════════════════════════════════════════════════════════════════════════╣{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.RESET} {Colors.BLUE}{Colors.BOLD}{'Provider':<16}{Colors.RESET} {Colors.WHITE}{'Remaining':<12}{Colors.RESET} {Colors.WHITE}{'Used':<8}{Colors.RESET} {Colors.WHITE}{'Cooldown':<16}{Colors.RESET} {Colors.WHITE}{'Status':<14}{Colors.RESET} {Colors.CYAN}{Colors.BOLD}║{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}╠══════════════════════════════════════════════════════════════════════════════════════╣{Colors.RESET}")
        
        # Sort providers
        sorted_providers = sorted(
            engines[0].providers_status.items(),
            key=lambda x: x[1].get('cooldown', 0),
            reverse=True
        )
        
        for name, info in sorted_providers:
            remaining = info.get('remaining', 0)
            used = info.get('used', 0)
            cooldown = info.get('cooldown', 0)
            blocked = info.get('blocked', False)
            
            # Check local cooldown
            if name in engines[0].provider_cooldown_until:
                local_cd = int(engines[0].provider_cooldown_until[name] - time.time())
                if local_cd > 0:
                    cooldown = max(cooldown, local_cd)
            
            if cooldown > 0:
                status_text = f"⏳ {format_cooldown(cooldown)}"
                status_color = Colors.YELLOW
            elif blocked:
                status_text = "🚫 BLOCKED"
                status_color = Colors.RED
            elif remaining > 0:
                status_text = "🟢 READY"
                status_color = Colors.GREEN
            else:
                status_text = "⚪ DONE"
                status_color = Colors.WHITE
            
            print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.RESET} {Colors.WHITE}{name[:14]:<16}{Colors.RESET} ", end="")
            print(f"{Colors.GREEN}{remaining:<12}{Colors.RESET} ", end="")
            print(f"{Colors.YELLOW}{used:<8}{Colors.RESET} ", end="")
            print(f"{Colors.MAGENTA}{format_cooldown(cooldown):<16}{Colors.RESET} ", end="")
            print(f"{status_color}{status_text:<14}{Colors.RESET} {Colors.CYAN}{Colors.BOLD}║{Colors.RESET}")
        
        print(f"{Colors.CYAN}{Colors.BOLD}╚══════════════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
        print()
    
    # Live Logs
    print(f"{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║                           📝 LIVE LOGS (last 8)                                    ║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}╠══════════════════════════════════════════════════════════════════════════════════════╣{Colors.RESET}")
    
    current_logs = LIVE_LOG.copy() if LIVE_LOG else ["Waiting for logs..."]
    for log in current_logs[-8:]:
        if len(log) > 80:
            log = log[:77] + "..."
        print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.RESET} {Colors.WHITE}{log:<82}{Colors.RESET} {Colors.CYAN}{Colors.BOLD}║{Colors.RESET}")
    
    print(f"{Colors.CYAN}{Colors.BOLD}╚══════════════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print()
    
    proxy_count = len(proxy_manager.proxies) if proxy_manager.proxies else 0
    print(f"{Colors.YELLOW}💡 Press Ctrl+C to stop | Logs: {LOG_FILE} | Simulated: {AD_WATCH_DURATION}s | Cooldown: {PROVIDER_COOLDOWN}min | Proxies: {proxy_count}{Colors.RESET}")

# ========== MAIN ==========
async def main():
    clear_screen()
    
    print(f"{Colors.GOLD}{Colors.BOLD}╔═══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║  {Colors.CYAN}{Colors.BOLD} ██████╗ ██████╗ ███████╗███╗   ██╗    ███████╗ █████╗ ██████╗ ███╗   ██╗{Colors.RESET} {Colors.GOLD}║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║  {Colors.CYAN}{Colors.BOLD}██╔═══██╗██╔══██╗██╔════╝████╗  ██║    ██╔════╝██╔══██╗██╔══██╗████╗  ██║{Colors.RESET} {Colors.GOLD}║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║  {Colors.CYAN}{Colors.BOLD}██║   ██║██████╔╝█████╗  ██╔██╗ ██║    █████╗  ███████║██████╔╝██╔██╗ ██║{Colors.RESET} {Colors.GOLD}║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║  {Colors.CYAN}{Colors.BOLD}██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║    ██╔══╝  ██╔══██║██╔══██╗██║╚██╗██║{Colors.RESET} {Colors.GOLD}║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║  {Colors.CYAN}{Colors.BOLD}╚██████╔╝██║     ███████╗██║ ╚████║    ███████╗██║  ██║██║  ██║██║ ╚████║{Colors.RESET} {Colors.GOLD}║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║  {Colors.CYAN}{Colors.BOLD} ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝{Colors.RESET} {Colors.GOLD}║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║                                                                                           ║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}║           {Colors.GREEN}{Colors.BOLD}🚀 OPEN EARN BOT - ADVANCED DASHBOARD {Colors.YELLOW}{Colors.BOLD}v2.0{Colors.RESET}            ║{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print()
    print(f"{Colors.YELLOW}📝 Logs saved to: {LOG_FILE}{Colors.RESET}")
    print(f"{Colors.YELLOW}⏱️ Simulated ad watching: {AD_WATCH_DURATION}s{Colors.RESET}")
    print(f"{Colors.YELLOW}⏱️ Provider cooldown: {PROVIDER_COOLDOWN} minutes{Colors.RESET}")
    print()
    
    proxies = manage_proxies()
    if proxies:
        print(f"{Colors.GREEN}✓ Using {len(proxies)} proxies for load balancing{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}! No proxies configured - all accounts will use the same IP{Colors.RESET}")
    print()
    
    accounts = await manage_accounts()
    if not accounts:
        print(f"{Colors.RED}{Colors.BOLD}❌ No accounts available. Exiting.{Colors.RESET}")
        sys.exit(1)
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Loaded {len(accounts)} account(s){Colors.RESET}")
    
    engines = []
    for i, acc in enumerate(accounts):
        proxy = proxy_manager.get_proxy_for_account(i) if proxies else None
        eng = AccountEngine(acc, i, proxy)
        engines.append(eng)
        if proxy:
            print(f"{Colors.CYAN}  📡 {acc['username']} -> {proxy.get('http', 'unknown')}{Colors.RESET}")
    
    print(f"{Colors.CYAN}{Colors.BOLD}Starting automation...{Colors.RESET}\n")
    await asyncio.sleep(2)
    
    tasks = [asyncio.create_task(eng.run()) for eng in engines]
    
    async def update_dashboard():
        while True:
            display_dashboard(engines)
            await asyncio.sleep(1)
    
    dash_task = asyncio.create_task(update_dashboard())
    
    try:
        await asyncio.gather(*tasks, dash_task)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}Stopping all accounts...{Colors.RESET}")
        for eng in engines:
            eng.stop()
        await asyncio.sleep(2)
        print(f"{Colors.GREEN}{Colors.BOLD}All accounts stopped!{Colors.RESET}")

if __name__ == "__main__":
    try:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.RESET}")
        sys.exit(1)
#!/usr/bin/env python3
"""
LiteBits Auto Faucet Bot - Clean Version
"""

import os
import sys
import asyncio
import tempfile

# ========== FIX: Set event loop BEFORE importing pyrogram ==========
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import json
import time
import random
import urllib.parse
from datetime import datetime
from typing import Optional, Dict
from urllib.parse import parse_qs, urlparse

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== SUPPRESS PYROGRAM WELCOME ==========
import contextlib
with contextlib.redirect_stdout(open(os.devnull, 'w')):
    from pyrogram import Client
    from pyrogram.raw.functions.messages import RequestWebView

# ========== COLORS ==========
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

# ========== CONFIG ==========
API_ID = 32744606
API_HASH = 'f58682565ec84dcd4e529a33246f07aa'
BOT_USERNAME = 'litebits_faucet_bot'
BASE_URL = "https://mini.litebits.io/api"
AD_WATCH_TIME = 12  # seconds

class LiteBitsBot:
    def __init__(self, account_info: Dict):
        self.phone = account_info.get('phone', '')
        self.username = account_info.get('username', '')
        self.session_str = account_info.get('session', '')
        self.token = None
        self.balance = 0.0
        self.reward = 0.0
        self.next_claim_at = None
        self.session = requests.Session()
        self.session.verify = False
        self.headers = {}
        self.running = True
        self.is_authenticated = False
        self.claim_count = 0
        self.total_earned = 0.0
        
    async def get_tg_data(self) -> str:
        """Get Telegram WebApp data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = os.path.join(temp_dir, "session")
            client = Client(
                session_path,
                session_string=self.session_str,
                api_id=API_ID,
                api_hash=API_HASH,
                workdir=temp_dir
            )
            
            await client.start()
            try:
                bot_peer = await client.resolve_peer(BOT_USERNAME)
                web_view = await client.invoke(
                    RequestWebView(
                        peer=bot_peer,
                        bot=bot_peer,
                        url="https://mini.litebits.io/",
                        platform="android"
                    )
                )
                parsed = urlparse(web_view.url)
                fragment = parse_qs(parsed.fragment)
                return fragment.get('tgWebAppData', [''])[0]
            finally:
                await client.stop()
    
    def build_headers(self, token: str = None):
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 15) AppleWebKit/537.36 Chrome/150.0.7871.181 Mobile Safari/537.36 Telegram-Android/12.9.1',
            'x-platform': 'telegram',
            'Origin': 'https://mini.litebits.io',
            'Referer': 'https://mini.litebits.io/?v5'
        }
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers
    
    async def authenticate(self) -> bool:
        """Authenticate with LiteBits"""
        try:
            tg_data = await self.get_tg_data()
            if not tg_data:
                return False
            
            response = self.session.post(
                f"{BASE_URL}/auth/telegram/validate",
                json={"initData": tg_data},
                headers=self.build_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.token = data.get('token')
                    user_data = data.get('user', {})
                    self.balance = float(user_data.get('balance', 0))
                    self.username = user_data.get('telegramUsername', self.username)
                    self.next_claim_at = user_data.get('nextClaimAt')
                    self.headers = self.build_headers(self.token)
                    self.is_authenticated = True
                    return True
            return False
        except Exception:
            return False
    
    def api_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make API request"""
        if not self.is_authenticated:
            return None
        
        try:
            url = f"{BASE_URL}/{endpoint.lstrip('/')}"
            if method.upper() == 'GET':
                response = self.session.get(url, headers=self.headers, timeout=30)
            else:
                response = self.session.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                self.is_authenticated = False
                return None
            return None
        except Exception:
            return None
    
    async def get_profile(self):
        """Get user profile"""
        data = self.api_request('GET', 'user/profile')
        if data:
            self.balance = float(data.get('balance', self.balance))
            self.next_claim_at = data.get('nextClaimAt')
            return True
        return False
    
    async def start_claim(self) -> Optional[str]:
        """Start claim and return claim_id"""
        payload = {
            "h-captcha-response": "",
            "captchaProvider": "hcaptcha",
            "tapTimings": [{"delay": 0, "x": random.randint(100, 400), "y": random.randint(200, 600)}],
            "fingerprint": ""
        }
        
        data = self.api_request('POST', 'claim/start', payload)
        if data and data.get('success'):
            return data.get('claimId')
        return None
    
    async def get_ad_token(self, claim_id: str) -> Optional[str]:
        """Get ad token for claim"""
        data = self.api_request('GET', f'claim/{claim_id}/ads')
        if data and data.get('success'):
            ad_data = data.get('adsUrl', {})
            return ad_data.get('token')
        return None
    
    async def complete_claim(self, claim_id: str, token: str) -> bool:
        """Complete claim and get reward"""
        payload = {"token": token}
        data = self.api_request('POST', f'claim/{claim_id}/complete', payload)
        
        if data and data.get('success'):
            reward = float(data.get('reward', 0))
            self.reward = reward
            self.balance += reward
            self.total_earned += reward
            self.claim_count += 1
            self.next_claim_at = data.get('nextClaimAt')
            return True
        return False
    
    def format_cooldown(self, seconds: int) -> str:
        """Format cooldown time"""
        if seconds <= 0:
            return "Ready!"
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    
    async def run(self):
        """Main bot loop"""
        print(f"{Colors.CYAN}🔐 Logging in...{Colors.RESET}")
        
        if not await self.authenticate():
            print(f"{Colors.RED}❌ Login failed!{Colors.RESET}")
            return
        
        print(f"{Colors.GREEN}✅ Logged in as: {self.username}{Colors.RESET}")
        print(f"{Colors.YELLOW}💰 Balance: {self.balance:.2f} bits{Colors.RESET}")
        print("-" * 50)
        
        while self.running:
            try:
                # Check cooldown
                if self.next_claim_at:
                    try:
                        next_time = datetime.fromisoformat(self.next_claim_at.replace('Z', '+00:00'))
                        now = datetime.now().astimezone()
                        if next_time > now:
                            wait = int((next_time - now).total_seconds())
                            if wait > 0:
                                print(f"\r⏳ Cooldown: {self.format_cooldown(wait)}", end="")
                                await asyncio.sleep(1)
                                continue
                    except:
                        pass
                
                # Start claim
                print(f"\r🎯 Starting claim...", end="")
                claim_id = await self.start_claim()
                if not claim_id:
                    await asyncio.sleep(5)
                    continue
                
                # Get ad token
                ad_token = await self.get_ad_token(claim_id)
                if not ad_token:
                    await asyncio.sleep(5)
                    continue
                
                # Watch ad with timer
                print(f"\r📺 Watching ad... {AD_WATCH_TIME}s", end="")
                for remaining in range(AD_WATCH_TIME, 0, -1):
                    if not self.running:
                        return
                    print(f"\r📺 Watching ad... {remaining:2d}s", end="")
                    await asyncio.sleep(1)
                
                # Complete claim
                success = await self.complete_claim(claim_id, ad_token)
                if success:
                    print(f"\r{Colors.GREEN}✅ Faucet | reward: {self.reward:.2f} bits | Balance: {self.balance:.2f} bits{Colors.RESET}")
                    
                    # Check if there's a cooldown
                    if self.next_claim_at:
                        try:
                            next_time = datetime.fromisoformat(self.next_claim_at.replace('Z', '+00:00'))
                            now = datetime.now().astimezone()
                            if next_time > now:
                                wait = int((next_time - now).total_seconds())
                                print(f"⏳ Cooldown: {self.format_cooldown(wait)}")
                        except:
                            pass
                else:
                    print(f"\r{Colors.RED}❌ Claim failed!{Colors.RESET}")
                
                # Small delay before next claim
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\r{Colors.RED}❌ Error: {e}{Colors.RESET}")
                await asyncio.sleep(5)
                
                # Try to re-authenticate
                if not self.is_authenticated:
                    await self.authenticate()
        
        print(f"\n{Colors.YELLOW}📊 Total claims: {self.claim_count} | Total earned: {self.total_earned:.2f} bits{Colors.RESET}")

# ========== PYROGRAM LOGIN ==========
async def pyrogram_login(phone: str):
    """Login to Telegram"""
    with tempfile.TemporaryDirectory() as temp_dir:
        session_path = os.path.join(temp_dir, "session")
        client = Client(session_path, api_id=API_ID, api_hash=API_HASH, workdir=temp_dir)
        
        await client.start()
        try:
            sent_code = await client.send_code(phone)
            print(f"{Colors.GREEN}Enter confirmation code: {Colors.RESET}", end="")
            code = input().strip()
            
            try:
                await client.sign_in(phone, sent_code.phone_code_hash, code)
            except:
                print(f"{Colors.GREEN}Enter 2FA password: {Colors.RESET}", end="")
                pwd = input().strip()
                await client.check_password(pwd)
            
            me = await client.get_me()
            session_str = await client.export_session_string()
            await client.stop()
            return me, session_str
        except Exception as e:
            await client.stop()
            raise e

async def add_account():
    """Add a new account"""
    print(f"\n{Colors.CYAN}📱 ADD TELEGRAM ACCOUNT{Colors.RESET}")
    print("-" * 50)
    
    phone = input(f"{Colors.YELLOW}Phone number (with country code): {Colors.RESET}").strip()
    
    try:
        me, session_str = await pyrogram_login(phone)
        username = me.username or phone
        account = {"phone": phone, "session": session_str, "username": username}
        
        # Save account
        accounts = []
        if os.path.exists("litebits_accounts.json"):
            with open("litebits_accounts.json", "r") as f:
                accounts = json.load(f)
        
        # Check if account already exists
        for acc in accounts:
            if acc.get('phone') == phone:
                accounts.remove(acc)
                break
        
        accounts.append(account)
        with open("litebits_accounts.json", "w") as f:
            json.dump(accounts, f, indent=4)
        
        print(f"{Colors.GREEN}✅ Account {username} added!{Colors.RESET}")
        return account
    except Exception as e:
        print(f"{Colors.RED}❌ Login failed: {e}{Colors.RESET}")
        return None

async def main():
    # Ensure event loop
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print(f"{Colors.CYAN}{Colors.BOLD}╔════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║        ⭐ LITEBITS AUTO FAUCET BOT v2.0          ║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}╚════════════════════════════════════════════════════╝{Colors.RESET}")
    print()
    
    # Load accounts
    accounts = []
    if os.path.exists("litebits_accounts.json"):
        with open("litebits_accounts.json", "r") as f:
            accounts = json.load(f)
    
    if not accounts:
        print(f"{Colors.YELLOW}⚠️ No accounts found.{Colors.RESET}")
        account = await add_account()
        if not account:
            print(f"{Colors.RED}❌ No account added. Exiting.{Colors.RESET}")
            sys.exit(1)
        accounts = [account]
    
    # Select account
    if len(accounts) > 1:
        print(f"{Colors.CYAN}📋 Available accounts:{Colors.RESET}")
        for i, acc in enumerate(accounts):
            print(f"  {i+1}. {acc.get('username', acc.get('phone'))}")
        print(f"  {len(accounts)+1}. Add new account")
        
        choice = input(f"\n{Colors.YELLOW}Select account (number): {Colors.RESET}").strip()
        try:
            idx = int(choice) - 1
            if idx == len(accounts):
                account = await add_account()
                if not account:
                    sys.exit(1)
                accounts.append(account)
                with open("litebits_accounts.json", "w") as f:
                    json.dump(accounts, f, indent=4)
            else:
                account = accounts[idx]
        except:
            account = accounts[0]
    else:
        account = accounts[0]
    
    print(f"\n{Colors.GREEN}✅ Using account: {account.get('username', account.get('phone'))}{Colors.RESET}")
    print("-" * 50)
    print()
    
    # Start bot
    bot = LiteBitsBot(account)
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}🛑 Stopped by user{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Fatal error: {e}{Colors.RESET}")
        sys.exit(1)
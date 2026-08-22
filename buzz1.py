#!/usr/bin/env python3
"""
BuzzReferrals Auto Task Bot
Auto-login with phone + code, auto-complete ALL featured & YouTube tasks
"""

import os
import sys
import asyncio
import json
import time
import random
import re
import tempfile
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, List, Any
from urllib.parse import parse_qs, urlparse

import requests
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== SETUP EVENT LOOP ==========
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

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
    MINT = '\033[38;5;157m'
    ROSE = '\033[38;5;204m'
    ORANGE = '\033[38;5;208m'

# ========== CONFIG ==========
API_ID = 32744606
API_HASH = 'f58682565ec84dcd4e529a33246f07aa'
BOT_USERNAME = 'Buzzreferralbot'
BASE_URL = "https://bisque-gerbil-233581.hostingersite.com/api"
TASK_COOLDOWN = 2
CYCLE_WAIT_MIN = 10
CYCLE_WAIT_MAX = 20

# ========== COMPREHENSIVE ANSWERS ==========
ALL_ANSWERS = [
    # SEO answers
    'usdt', 'telegram', 'buzzreferrals', 'buzzreferrals.site',
    'referrals', 'buzzgrowth', 'startnearn', 'phone', 'tiktok',
    'algorithm', 'retention', 'reddit', 'depin', 'cati',
    'ton', 'kyc', 'nigeria', 'botfather', 'api', 'pengu',
    'blum', 'beermoney', 'wholesale', 'appsflyer', 'refill',
    'tgstat', 'manually', 'cryptocurrency', 'dropbox',
    '50', '37', '7', '3', 'twenty', 'mute', 'views',
    'buzz', 'growth', 'signup', 'register', 'yes', 'no',
    'buzzreferrals', 'buzzfollowers', 'startnearn.pro',
    'buzzgrowth.site', 'buzzreferralz', 'buzzreferralbot',
    
    # YouTube answers
    '50,000', '50000', '50k', '99%', '99 percent',
    '3,200', '3200', '10', '100', '1028', '2000', '462',
    'referral', 'directanswer', 'done', 'complete',
    
    # Instagram/Buzz answers
    'how', 'guide', 'referrals', 'buzz', 'growth',
    'comment', 'share', 'like', 'follow', 'subscribe',
    
    # Additional common answers
    '1', '2', '3', '4', '5', '10', '15', '20', '25', '30',
    '100', '500', '1000', '5000', '10000',
    'true', 'false', 'none', 'null',
    'email', 'phone', 'password', 'username',
    'google', 'facebook', 'instagram', 'youtube', 'twitter',
    'crypto', 'bitcoin', 'ethereum', 'ton', 'usdt', 'btc',
    'airdrop', 'reward', 'bonus', 'earning', 'income',
    'task', 'complete', 'finish', 'done', 'ok',
    'start', 'begin', 'go', 'continue', 'next',
    'yes', 'no', 'maybe', 'sure', 'okay'
]


class BuzzBot:
    """Main bot class for BuzzReferrals automation"""

    def __init__(self):
        # Auth
        self.init_data = None
        self.headers = None
        self.authenticated = False

        # User
        self.telegram_id = None
        self.user_id = None
        self.username = None
        self.balance = 0.0
        self.usdt_balance = 0.0

        # Stats
        self.completed = 0
        self.failed = 0
        self.earned = 0.0
        self.total_tasks = 0

        # Session
        self.session = requests.Session()
        self.session.verify = False
        self.session.timeout = 30

        # State
        self.running = True
        self.last_request = 0
        self.request_delay = 1.0
        
        # Track completed task IDs
        self.completed_task_ids = set()
        self.skipped_task_ids = set()

    # ==================== LOGGING ====================

    def log(self, msg: str, color: str = Colors.WHITE):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.MINT}[{ts}]{Colors.RESET} {color}{msg}{Colors.RESET}")

    def ok(self, msg: str): self.log(f"✓ {msg}", Colors.GREEN)
    def err(self, msg: str): self.log(f"✗ {msg}", Colors.RED)
    def info(self, msg: str): self.log(f"ℹ {msg}", Colors.CYAN)
    def warn(self, msg: str): self.log(f"⚠ {msg}", Colors.YELLOW)

    def _safe_float(self, val, default=0.0) -> float:
        try:
            return float(val) if val is not None else default
        except (ValueError, TypeError):
            return default

    def _safe_int(self, val, default=0) -> int:
        try:
            return int(val) if val is not None else default
        except (ValueError, TypeError):
            return default

    # ==================== AUTH ====================

    def _build_headers(self, init_data: str) -> Dict:
        return {
            'Authorization': f"tma {init_data}",
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'
        }

    async def _get_init_data(self, phone: str = None, session_str: str = None) -> Optional[str]:
        """Get init_data from Telegram"""
        try:
            if session_str:
                client = Client(":memory:", session_string=session_str, api_id=API_ID, api_hash=API_HASH)
            else:
                tmp = tempfile.NamedTemporaryFile(delete=False)
                session_path = tmp.name
                tmp.close()
                client = Client(session_path, api_id=API_ID, api_hash=API_HASH)

            await client.connect()

            bot = await client.resolve_peer(BOT_USERNAME)
            web = await client.invoke(RequestWebView(
                peer=bot, bot=bot,
                url="https://app.theopenearn.com/",
                platform="ios"
            ))

            parsed = urlparse(web.url)
            data = parse_qs(parsed.fragment).get('tgWebAppData', [None])[0]

            await client.disconnect()

            if not session_str and os.path.exists(session_path):
                os.unlink(session_path)

            return data

        except Exception as e:
            self.err(f"Init data error: {e}")
            return None

    async def _pyrogram_login(self, phone: str) -> tuple:
        """Login with phone + code"""
        self.info(f"Logging in: {phone}")

        tmp = tempfile.NamedTemporaryFile(delete=False)
        session_path = tmp.name
        tmp.close()

        client = Client(session_path, api_id=API_ID, api_hash=API_HASH)
        await client.connect()

        try:
            await client.sign_in(phone)
        except Exception as e:
            err = str(e).lower()
            if "phone" in err or "invalid" in err:
                self.err("Invalid phone number")
                await client.disconnect()
                os.unlink(session_path)
                return None, None
            elif "code" in err:
                sent = await client.send_code(phone)
                code = input(f"{Colors.YELLOW}Enter code: {Colors.RESET}").strip()
                try:
                    await client.sign_in(phone, sent.phone_code_hash, code)
                except Exception:
                    pwd = input(f"{Colors.YELLOW}2FA password: {Colors.RESET}").strip()
                    await client.check_password(pwd)

        me = await client.get_me()
        username = me.username or phone
        self.ok(f"Logged in: {username}")

        session_str = await client.export_session_string()
        with open("buzz_session.txt", "w") as f:
            f.write(session_str)

        await client.disconnect()
        os.unlink(session_path)

        init_data = await self._get_init_data(phone, session_str)
        return init_data, session_str

    async def _login(self, phone: str = None) -> bool:
        """Main login flow"""
        session_str = None

        if os.path.exists("buzz_session.txt"):
            try:
                with open("buzz_session.txt", "r") as f:
                    session_str = f.read().strip()
                self.info("Loaded saved session")
            except:
                pass

        if session_str:
            init_data = await self._get_init_data(phone, session_str)
            if init_data:
                self.init_data = init_data
                return True

        if not phone:
            phone = input(f"{Colors.GREEN}Phone (with country code): {Colors.RESET}").strip()

        init_data, session_str = await self._pyrogram_login(phone)
        if init_data:
            self.init_data = init_data
            return True

        return False

    async def _get_user_id(self) -> bool:
        """Get internal user ID"""
        if not self.telegram_id:
            return False

        resp = await self._api_request(
            "/user/get_user_id.php",
            {"telegram_id": self.telegram_id},
            method='GET'
        )

        if resp and resp.get('user_id'):
            self.user_id = resp['user_id']
            self.ok(f"User ID: {self.user_id}")
            return True
        return False

    # ==================== API ====================

    async def _wait(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.request_delay:
            await asyncio.sleep(self.request_delay - elapsed)
        self.last_request = time.time()

    async def _api_request(self, endpoint: str, data: Dict = None, method: str = 'POST', retry: int = 0) -> Any:
        """Make API request"""
        if retry > 3 or not self.authenticated:
            return None

        await self._wait()

        url = f"{BASE_URL}{endpoint}"
        payload = data or {}

        if self.user_id and 'user_id' not in payload:
            payload['user_id'] = self.user_id

        try:
            if method.upper() == 'GET':
                resp = self.session.get(url, params=payload, headers=self.headers, timeout=30)
            else:
                resp = self.session.post(url, json=payload, headers=self.headers, timeout=30)

            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                wait = random.uniform(20, 35)
                self.warn(f"Rate limited, waiting {wait:.1f}s")
                await asyncio.sleep(wait)
                return await self._api_request(endpoint, data, method, retry + 1)
            elif resp.status_code == 401:
                self.authenticated = False
                self.err("Auth expired")
                return None

        except Exception as e:
            if retry < 2:
                await asyncio.sleep(3)
                return await self._api_request(endpoint, data, method, retry + 1)
            self.err(f"API error: {e}")

        return None

    async def _fetch_balance(self) -> bool:
        """Fetch balance from server"""
        if not self.user_id:
            return False

        try:
            resp = self.session.post(
                f"{BASE_URL}/interface/update.php",
                data={"user_id": self.user_id, "user_name": self.username or str(self.telegram_id)},
                headers=self.headers,
                timeout=30
            )

            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    self.balance = self._safe_float(data.get('balance'), 0.0)
                    self.usdt_balance = self._safe_float(data.get('usdt_balance'), 0.0)
                    return True

        except Exception as e:
            pass

        return False

    async def _fetch_tasks(self, endpoint: str) -> List[Dict]:
        """Fetch tasks from endpoint"""
        if not self.user_id:
            return []

        result = await self._api_request(endpoint, {"user_id": self.user_id})

        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            if result.get('status') == 'success' and 'data' in result:
                return result['data']
            for key in ['tasks', 'featured', 'youtube']:
                if key in result and isinstance(result[key], list):
                    return result[key]
        return []

    async def _submit_answer(self, task_id: int, answer: str) -> Optional[Dict]:
        if not self.user_id:
            return None
        return await self._api_request(
            "/tasks/submit_answer.php",
            {"user_id": self.user_id, "task_id": task_id, "user_answer": answer}
        )

    # ==================== TASK COMPLETION ====================

    async def _complete_task(self, task: Dict) -> bool:
        """Complete a task by trying all possible answers"""
        task_id = task.get('id')
        category = task.get('category', '')
        brief = task.get('brief', 'Unknown')
        answer = task.get('answer', '')
        
        # Skip if already completed
        if task_id in self.completed_task_ids:
            return True
        
        # Skip if already skipped (failed too many times)
        if task_id in self.skipped_task_ids:
            return True

        # Determine task type for display
        if category == 'seo_search':
            icon = "📝"
        elif category in ['youtube_video', 'youtube_short']:
            icon = "🎬"
        else:
            icon = "📌"
        
        self.info(f"{icon} {brief[:35]}...")

        # Build answer list - try exact answer first, then all common answers
        answers_to_try = []
        
        # Add exact answer if exists and not empty
        if answer and answer not in answers_to_try:
            answers_to_try.append(answer)
        
        # Add all common answers
        for ans in ALL_ANSWERS:
            if ans not in answers_to_try:
                answers_to_try.append(ans)
        
        # Add some variations
        variations = [
            str(answer).lower(), str(answer).upper(), str(answer).capitalize(),
            str(answer).strip(), str(answer).replace(' ', ''),
            str(answer).replace('-', ''), str(answer).replace('_', '')
        ]
        for var in variations:
            if var and var not in answers_to_try:
                answers_to_try.append(var)

        # Try each answer
        for ans in answers_to_try:
            if not ans or len(ans) < 1:
                continue
                
            result = await self._submit_answer(task_id, ans)
            
            if result:
                status = result.get('status')
                
                if status == 'success':
                    reward = self._safe_float(result.get('reward', 0))
                    self.earned += reward
                    self.completed += 1
                    self.completed_task_ids.add(task_id)
                    self.ok(f"{icon} Done! +{reward:.2f} BZ")
                    await self._fetch_balance()
                    return True
                    
                elif status == 'already_completed':
                    self.completed_task_ids.add(task_id)
                    self.info(f"{icon} Already completed")
                    return True
                    
                elif status == 'error':
                    # Continue trying other answers
                    continue
            
            # Small delay between attempts
            await asyncio.sleep(0.5)

        # If we get here, task couldn't be completed
        self.failed += 1
        self.skipped_task_ids.add(task_id)
        self.warn(f"{icon} Could not complete task {task_id}")
        return False

    async def _process_tasks(self, tasks: List[Dict], label: str):
        """Process a list of tasks"""
        if not tasks:
            return

        # Filter out already completed/skipped
        pending = []
        for t in tasks:
            task_id = t.get('id')
            if task_id not in self.completed_task_ids and task_id not in self.skipped_task_ids:
                pending.append(t)
        
        if not pending:
            self.info(f"📋 All {label} tasks are done")
            return

        self.info(f"📋 Found {len(pending)} {label} tasks to complete")
        
        for task in pending:
            if not self.running:
                break
            await self._complete_task(task)
            await asyncio.sleep(TASK_COOLDOWN)

    # ==================== MAIN LOOP ====================

    async def _run_loop(self):
        """Main task loop"""
        self.info("🔄 Starting task loop...")
        cycle = 0

        while self.running:
            cycle += 1
            self.info(f"📊 Cycle {cycle}")
            self.info(f"💰 Balance: {self.balance:.2f} BZ")

            try:
                # Refresh balance
                await self._fetch_balance()
                
                # Get and process featured tasks
                featured = await self._fetch_tasks("/tasks/fetch_featured_tasks.php")
                await self._process_tasks(featured, "featured")
                
                # Get and process YouTube tasks
                youtube = await self._fetch_tasks("/tasks/fetch_youtube_tasks.php")
                await self._process_tasks(youtube, "YouTube")

                # Report progress
                self.info(f"📊 Completed: {self.completed} | Failed: {self.failed} | Earned: {self.earned:.2f} BZ")

                # Check if all tasks are done
                total_pending = len([t for t in featured if t.get('id') not in self.completed_task_ids and t.get('id') not in self.skipped_task_ids])
                total_pending += len([t for t in youtube if t.get('id') not in self.completed_task_ids and t.get('id') not in self.skipped_task_ids])
                
                if total_pending == 0:
                    self.info("🎉 All tasks completed! Waiting for new tasks...")
                    await asyncio.sleep(60)
                    continue

                # Wait before next cycle
                wait = random.randint(CYCLE_WAIT_MIN, CYCLE_WAIT_MAX)
                self.info(f"⏳ Waiting {wait}s...")
                await asyncio.sleep(wait)

            except Exception as e:
                self.err(f"Loop error: {e}")
                await asyncio.sleep(10)

    # ==================== START ====================

    async def start(self):
        """Start the bot"""
        self.log("═" * 60, Colors.GOLD)
        self.log("BUZZREFERRALS AUTO TASK BOT", Colors.GOLD)
        self.log("═" * 60, Colors.GOLD)

        if os.path.exists("init_data.txt"):
            self.info("Found saved init_data.txt")
            use = input(f"{Colors.CYAN}Use saved? (Y/n): {Colors.RESET}").strip().lower()
            if use in ('', 'y', 'yes'):
                with open("init_data.txt", "r") as f:
                    self.init_data = f.read().strip()
                if await self._init():
                    await self._run_loop()
                    return

        if not await self._login():
            self.err("Login failed")
            return

        if not await self._init():
            self.err("Init failed")
            return

        try:
            with open("init_data.txt", "w") as f:
                f.write(self.init_data)
            self.info("Saved init_data.txt")
        except:
            pass

        self.log("═" * 60, Colors.GOLD)
        self.log("BOT STATUS", Colors.GOLD)
        self.log("═" * 60, Colors.GOLD)
        self.log(f"Balance: {self.balance:.2f} BZ", Colors.GOLD)
        self.log(f"USDT: {self.usdt_balance:.8f}", Colors.CYAN)
        self.log(f"User ID: {self.user_id}", Colors.MINT)
        self.log("═" * 60, Colors.GOLD)

        await self._run_loop()

    async def _init(self) -> bool:
        """Initialize bot with init_data"""
        if not self.init_data:
            return False

        self.info("Initializing...")
        self.headers = self._build_headers(self.init_data)
        self.authenticated = True

        try:
            params = dict(parse_qs(self.init_data))
            user_param = params.get('user', [''])[0]
            if user_param:
                user_json = json.loads(urllib.parse.unquote(user_param))
                self.telegram_id = user_json.get('id')
                self.username = user_json.get('username', str(self.telegram_id))
                self.info(f"User: {self.username} (ID: {self.telegram_id})")
        except:
            pass

        if not await self._get_user_id():
            return False

        await self._fetch_balance()
        self.ok("Initialization complete!")
        return True


# ==================== ENTRY ====================

async def main():
    print(f"{Colors.PURPLE}{Colors.BOLD}")
    print("  ██████╗ ██╗   ██╗███████╗███████╗    ██████╗  █████╗ ████████╗")
    print("  ██╔══██╗██║   ██║╚══███╔╝╚══███╔╝    ██╔══██╗██╔══██╗╚══██╔╝")
    print("  ██████╔╝██║   ██║  ███╔╝   ███╔╝     ██████╔╝███████║   ██║ ")
    print("  ██╔══██╗██║   ██║ ███╔╝   ███╔╝      ██╔══██╗██╔══██║   ██║ ")
    print("  ██████╔╝╚██████╔╝███████╗███████╗    ██████╔╝██║  ██║   ██║ ")
    print("  ╚═════╝  ╚═════╝ ╚══════╝╚══════╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝ ")
    print(f"{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}        BUZZREFERRALS AUTO TASK BOT{Colors.RESET}\n")

    bot = BuzzBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        print(f"\n{Colors.ROSE}Stopped{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped")
        sys.exit(0)
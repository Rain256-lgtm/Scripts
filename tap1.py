#!/usr/bin/env python3

import asyncio
import json
import time
import os
import random
import re
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any

import requests

# Color codes
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    GOLD = '\033[38;5;214m'
    PURPLE = '\033[38;5;141m'
    MINT = '\033[38;5;157m'
    ROSE = '\033[38;5;204m'

class BleonTapBot:
    def __init__(self, init_data: str, bot_username: str = "BTCTapperbot"):
        self.init_data = init_data
        self.bot_username = bot_username
        self.tap_token = None
        
        self.api_base = "https://panel-api.bleon.net/v1"
        
        # Player data
        self.balance = 0.0
        self.energy = 0
        self.max_energy = 3000
        self.streak_day = 0
        self.last_spin = 0
        self.last_streak_claim = 0
        self.turbo_until = 0
        self.taps_sent = 0
        self.total_earned = 0.0
        self.claims_made = 0
        self.ads_watched = 0
        self.upgrades_bought = 0
        
        # Shop data
        self.upgrades = {}
        self.consumables = {}
        self.shop_last_sync = 0
        self.config = {}
        self.player_data = {}
        
        # State
        self.running = True
        self.last_tap_sync = 0
        self._auth_fail_count = 0
        self.consecutive_errors = 0
        self.last_request_time = 0
        self.min_request_interval = 1.5
        
        # Session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 15; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.7871.181 Mobile Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Origin': 'https://tapgame.bleon.net',
            'Referer': 'https://tapgame.bleon.net/',
            'X-Requested-With': 'org.telegram.messenger.web',
        })
        
        self.user_id = self._extract_user_id()

    def log(self, msg: str, color: str = Colors.WHITE):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.MINT}[{timestamp}]{Colors.RESET} {color}{msg}{Colors.RESET}")

    def log_success(self, msg: str):
        self.log(f"✓ {msg}", Colors.GREEN)

    def log_error(self, msg: str):
        self.log(f"✗ {msg}", Colors.RED)

    def log_info(self, msg: str):
        self.log(f"ℹ {msg}", Colors.CYAN)

    def log_warning(self, msg: str):
        self.log(f"⚠ {msg}", Colors.YELLOW)

    def _extract_user_id(self) -> Optional[int]:
        try:
            match = re.search(r'"id":(\d+)', self.init_data)
            if match:
                return int(match.group(1))
            match = re.search(r'user%22%3A%7B%22id%22%3A(\d+)', self.init_data)
            if match:
                return int(match.group(1))
            if 'user=' in self.init_data:
                for part in self.init_data.split('&'):
                    if part.startswith('user='):
                        user_part = part.split('=', 1)[1]
                        decoded = urllib.parse.unquote(user_part)
                        match = re.search(r'"id":(\d+)', decoded)
                        if match:
                            return int(match.group(1))
        except:
            pass
        return None

    def _safe_int(self, value, default=0) -> int:
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _safe_float(self, value, default=0.0) -> float:
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    async def _wait_if_needed(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    async def api_request(self, endpoint: str, data: Dict = None, retry: int = 0) -> Dict:
        if retry > 3:
            return {}
        
        await self._wait_if_needed()
        
        url = f"{self.api_base}{endpoint}"
        payload = {"bot": self.bot_username, "initData": self.init_data}
        if data:
            payload.update(data)
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.session.post(url, json=payload, timeout=30)
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self._auth_fail_count = 0
                    return result
                return {}
            elif response.status_code == 429:
                wait = random.uniform(20, 35)
                self.log_warning(f"Rate limited, waiting {wait:.1f}s...")
                await asyncio.sleep(wait)
                return await self.api_request(endpoint, data, retry + 1)
            elif response.status_code in (401, 403):
                self._auth_fail_count += 1
                if self._auth_fail_count >= 2:
                    self.log_error("Auth failed. Init data may be expired.")
                    self.running = False
                return {}
            return {}
        except Exception as e:
            if retry < 2:
                await asyncio.sleep(3)
                return await self.api_request(endpoint, data, retry + 1)
            return {}

    async def init_game(self) -> bool:
        result = await self.api_request("/game/init", {"open": True})
        if not result:
            return False
        
        self.tap_token = result.get('tapToken', '')
        self.config = result.get('config', {})
        self.player_data = result.get('player', {})
        
        self.balance = self._safe_float(self.player_data.get('balance'), 0.0)
        self.energy = self._safe_int(self.player_data.get('energy'), 0)
        self.max_energy = self._safe_int(self.config.get('maxEnergy'), 3000)
        self.streak_day = self._safe_int(self.player_data.get('streakDay'), 0)
        self.last_spin = self._safe_int(self.player_data.get('lastSpin'), 0)
        self.last_streak_claim = self._safe_int(self.player_data.get('lastStreakClaim'), 0)
        
        return True

    async def load_shop(self) -> bool:
        if time.time() - self.shop_last_sync < 120:
            return True
            
        result = await self.api_request("/game/shop")
        if not result:
            return False
        
        self.upgrades = {u['kind']: u for u in result.get('upgrades', [])}
        self.consumables = {c['kind']: c for c in result.get('consumables', [])}
        self.turbo_until = self._safe_int(result.get('turboUntil'), 0)
        self.shop_last_sync = time.time()
        return True

    async def buy_upgrade(self, kind: str) -> bool:
        result = await self.api_request("/game/shop/buy", {"kind": kind})
        if not result:
            return False
        
        cost = self._safe_float(result.get('cost'), 0)
        if cost > 0:
            self.balance -= cost
        
        if result.get('turboUntil'):
            self.turbo_until = self._safe_int(result['turboUntil'], 0)
        
        self.upgrades_bought += 1
        self.log_success(f"Upgraded {kind}!")
        await self.load_shop()
        return True

    async def use_consumable(self, kind: str) -> bool:
        result = await self.api_request("/game/shop/buy", {"kind": kind})
        if not result:
            return False
        
        if kind == 'refill' and result.get('player'):
            self.energy = self._safe_int(result['player'].get('energy'), self.energy)
            self.log_success(f"Energy refilled!")
        
        if kind == 'turbo' and result.get('turboUntil'):
            self.turbo_until = self._safe_int(result['turboUntil'], 0)
            self.log_success("Turbo activated!")
        
        await self.load_shop()
        return True

    async def watch_ad(self, ad_type: str) -> bool:
        """Watch an ad - only used for streak and spin"""
        self.log_info(f"📺 Watching ad for {ad_type}...")
        
        duration = random.uniform(5.0, 8.0)
        await asyncio.sleep(duration)
        
        self.ads_watched += 1
        self.log_success(f"✅ Ad done!")
        return True

    async def tap_one(self) -> bool:
        if not self.tap_token:
            await self.init_game()
            if not self.tap_token:
                return False
            
        result = await self.api_request("/game/tap", {
            "taps": 1,
            "token": self.tap_token
        })
        
        if not result:
            return False
        
        self.tap_token = result.get('tapToken', self.tap_token)
        
        player = result.get('player', {})
        if player:
            self.balance = self._safe_float(player.get('balance'), self.balance)
            self.energy = self._safe_int(player.get('energy'), self.energy)
            self.taps_sent += 1
        
        gained = result.get('gained', 0)
        if gained:
            self.total_earned += self._safe_float(gained, 0)
        
        return True

    async def auto_shop(self):
        await self.load_shop()
        
        # Check consumables
        for kind in ['refill', 'turbo']:
            item = self.consumables.get(kind)
            if not item:
                continue
            
            free = self._safe_int(item.get('freeRemaining'), 0)
            
            if kind == 'refill' and free > 0 and self.energy < self.max_energy * 0.2:
                self.log_info(f"Using free refill ({free} left)")
                await self.use_consumable(kind)
                await asyncio.sleep(random.uniform(2, 4))
            
            elif kind == 'turbo' and free > 0 and time.time() * 1000 > self.turbo_until:
                self.log_info(f"Using free turbo ({free} left)")
                await self.use_consumable(kind)
                await asyncio.sleep(random.uniform(2, 4))
        
        # Check upgrades
        for kind in ['multitap', 'energy', 'recharge']:
            upgrade = self.upgrades.get(kind)
            if not upgrade:
                continue
            
            price = upgrade.get('nextPrice')
            level = self._safe_int(upgrade.get('level'), 0)
            
            if price is None:
                continue
            
            price = self._safe_float(price, 0)
            
            if self.balance >= price * 2 and level < 99:
                self.log_info(f"Buying {kind} (Lv{level}) for {price:.8f}")
                await self.buy_upgrade(kind)
                await asyncio.sleep(random.uniform(2, 4))

    async def tap_loop(self):
        """ULTRA SLOW tapping loop - 1 tap every 2-5 seconds"""
        self.log_info("🖐️ Tapping (1 tap every 2-5s)...")
        
        energy_per_tap = self._safe_int(self.config.get('energyPerTap'), 3)
        regen_per_sec = self._safe_float(self.config.get('regenPerSec'), 1.0)
        
        min_delay = 2.0
        max_delay = 5.0
        tap_counter = 0
        
        while self.running:
            if not self.init_data:
                await asyncio.sleep(5)
                continue
            
            # Auto shop periodically
            if time.time() - self.shop_last_sync > 180:
                await self.auto_shop()
            
            # Random long breaks
            if random.random() < 0.03:
                duration = random.uniform(8.0, 15.0)
                self.log_info(f"☕ Break ({duration:.1f}s)")
                await asyncio.sleep(duration)
                continue
            
            # Check energy
            if self.energy < energy_per_tap:
                await self.load_shop()
                refill = self.consumables.get('refill', {})
                free = self._safe_int(refill.get('freeRemaining'), 0)
                if free > 0:
                    await self.use_consumable('refill')
                    await self.init_game()
                    await asyncio.sleep(random.uniform(2, 4))
                    continue
                
                wait = max(5, (energy_per_tap - self.energy) / regen_per_sec)
                self.log_info(f"⚡ Energy low ({self.energy}), waiting {wait:.1f}s")
                await asyncio.sleep(min(wait, 20))
                await self.init_game()
                continue
            
            # Tap
            success = await self.tap_one()
            if not success:
                self.consecutive_errors += 1
                if self.consecutive_errors > 2:
                    await asyncio.sleep(random.uniform(10, 20))
                    self.consecutive_errors = 0
                continue
            
            self.consecutive_errors = 0
            tap_counter += 1
            
            # Random delay (2-5 seconds)
            delay = random.uniform(min_delay, max_delay)
            if random.random() < 0.1:
                delay += random.uniform(2, 4)
            
            await asyncio.sleep(delay)
            
            # Sync occasionally
            if time.time() - self.last_tap_sync > 60:
                await self.init_game()
                self.last_tap_sync = time.time()
            
            # Show progress every 5 taps
            if tap_counter >= 5:
                self.log_info(f"💪 Taps: {self.taps_sent} | Earned: {self.total_earned:.8f} | Energy: {self.energy}")
                tap_counter = 0

    async def claim_streak(self) -> bool:
        if self.streak_day == 0:
            return False
        
        last_claim = self._safe_int(self.player_data.get('lastStreakClaim'), 0)
        current = time.time() * 1000
        
        if current - last_claim < 24 * 60 * 60 * 1000:
            return False
        
        grant_id = None
        if self.config.get('streakAdEnabled', False):
            await self.watch_ad("streak")
            result = await self.api_request("/game/ad/grant", {"kind": "streak"})
            if result:
                grant_id = result.get('grantId')
        
        data = {"grant_id": grant_id} if grant_id else {}
        result = await self.api_request("/game/streak", data)
        
        if result and result.get('reward', 0) > 0:
            reward = self._safe_float(result.get('reward'), 0)
            self.balance += reward
            self.total_earned += reward
            self.claims_made += 1
            
            player = result.get('player', {})
            if player:
                self.streak_day = self._safe_int(player.get('streakDay'), self.streak_day)
                self.last_streak_claim = self._safe_int(player.get('lastStreakClaim'), 0)
                self.player_data = player
            
            self.log_success(f"⭐ Streak! +{reward:.8f}")
            return True
        
        return False

    async def spin(self) -> bool:
        cooldown = self._safe_int(self.config.get('spinCooldownHours'), 6) * 60 * 60 * 1000
        current = time.time() * 1000
        
        if current - self.last_spin < cooldown:
            return False
        
        grant_id = None
        if self.config.get('spinAdEnabled', False):
            await self.watch_ad("spin")
            result = await self.api_request("/game/ad/grant", {"kind": "spin"})
            if result:
                grant_id = result.get('grantId')
        
        data = {"grant_id": grant_id} if grant_id else {}
        result = await self.api_request("/game/spin", data)
        
        if result and result.get('reward', 0) > 0:
            reward = self._safe_float(result.get('reward'), 0)
            self.balance += reward
            self.total_earned += reward
            self.claims_made += 1
            
            player = result.get('player', {})
            if player:
                self.last_spin = self._safe_int(player.get('lastSpin'), self.last_spin)
                self.player_data = player
            
            self.log_success(f"🎰 Spin! +{reward:.8f}")
            return True
        
        return False

    async def claim_loop(self):
        self.log_info("Starting claim loop...")
        
        while self.running:
            try:
                if not self.init_data:
                    await asyncio.sleep(5)
                    continue
                
                await self.init_game()
                await self.claim_streak()
                await self.spin()
                await self.auto_shop()
                
                await asyncio.sleep(random.uniform(300, 600))
                
            except Exception as e:
                self.log_error(f"Claim error: {e}")
                await asyncio.sleep(60)

    async def run(self):
        self.log("═" * 60, Colors.GOLD)
        self.log("BTC TAPPER BOT v1.0", Colors.GOLD)
        self.log("═" * 60, Colors.GOLD)
        
        if not self.init_data:
            self.log_error("No init data provided")
            return
        
        self.log_info(f"User ID: {self.user_id}")
        
        if not await self.init_game():
            self.log_error("Failed to initialize game")
            return
        
        await self.load_shop()
        
        self.log("═" * 60, Colors.GOLD)
        self.log("BOT STATUS", Colors.GOLD)
        self.log("═" * 60, Colors.GOLD)
        self.log(f"Balance: {self.balance:.8f}", Colors.GOLD)
        self.log(f"Energy: {self.energy}/{self.max_energy}", Colors.CYAN)
        self.log(f"Streak: {self.streak_day} days", Colors.MINT)
        
        for kind in ['multitap', 'energy', 'recharge']:
            up = self.upgrades.get(kind, {})
            if up:
                level = up.get('level', 0)
                self.log(f"{kind}: Lv {level}", Colors.YELLOW)
        
        self.log("═" * 60, Colors.GOLD)
        self.log_info("Starting bots...")
        
        tap_task = asyncio.create_task(self.tap_loop())
        claim_task = asyncio.create_task(self.claim_loop())
        
        try:
            await asyncio.gather(tap_task, claim_task)
        except KeyboardInterrupt:
            self.log("Stopping...", Colors.ROSE)
            self.running = False
            tap_task.cancel()
            claim_task.cancel()
            
            self.log("\n" + "═" * 60, Colors.GOLD)
            self.log("FINAL STATS", Colors.GOLD)
            self.log("═" * 60, Colors.GOLD)
            self.log(f"Taps: {self.taps_sent}", Colors.CYAN)
            self.log(f"Earned: {self.total_earned:.8f}", Colors.GOLD)
            self.log(f"Claims: {self.claims_made}", Colors.MINT)
            self.log(f"Ads: {self.ads_watched}", Colors.PURPLE)
            self.log(f"Upgrades: {self.upgrades_bought}", Colors.BLUE)
            self.log(f"Balance: {self.balance:.8f}", Colors.GOLD)
            self.log("═" * 60, Colors.GOLD)

def get_init_data_from_file() -> Optional[str]:
    try:
        if os.path.exists("init_data.txt"):
            with open("init_data.txt", "r") as f:
                data = f.read().strip()
                if data and len(data) > 50:
                    return data
    except:
        pass
    return None

def save_init_data(data: str):
    try:
        with open("init_data.txt", "w") as f:
            f.write(data)
        print(f"{Colors.GREEN}✓ Saved to init_data.txt{Colors.RESET}")
    except:
        pass

async def main():
    print(f"{Colors.PURPLE}{Colors.BOLD}")
    print("  ██████╗ ██╗     ███████╗ ██████╗ ███╗   ██╗")
    print("  ██╔══██╗██║     ██╔════╝██╔═══██╗████╗  ██║")
    print("  ██████╔╝██║     █████╗  ██║   ██║██╔██╗ ██║")
    print("  ██╔══██╗██║     ██╔══╝  ██║   ██║██║╚██╗██║")
    print("  ██████╔╝███████╗███████╗╚██████╔╝██║ ╚████║")
    print("  ╚═════╝ ╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝")
    print(f"{Colors.RESET}")
    print(f"{Colors.GOLD}{Colors.BOLD}        BTC TAPPER BOT v1.0{Colors.RESET}\n")
    print(f"{Colors.YELLOW}💡 ULTRA SLOW MODE - 1 tap every 2-5 seconds{Colors.RESET}\n")
    
    init_data = get_init_data_from_file()
    
    if init_data:
        print(f"{Colors.GREEN}Found saved init data{Colors.RESET}")
        use_saved = input(f"{Colors.CYAN}Use saved? (Y/n): {Colors.RESET}").strip().lower()
        if use_saved in ('', 'y', 'yes'):
            bot_username = input(f"{Colors.CYAN}Bot (default: BTCTapperbot): {Colors.RESET}").strip()
            if not bot_username:
                bot_username = "BTCTapperbot"
            bot_username = bot_username.lstrip('@')
            
            bot = BleonTapBot(init_data, bot_username)
            try:
                await bot.run()
            except KeyboardInterrupt:
                pass
            return
    
    print(f"{Colors.CYAN}Enter init data:{Colors.RESET}")
    print(f"{Colors.YELLOW}Paste the init data (query_id=...):{Colors.RESET}")
    
    init_data = input(f"{Colors.WHITE}> {Colors.RESET}").strip()
    
    if not init_data:
        print(f"{Colors.RED}Init data is required!{Colors.RESET}")
        return
    
    save_init_data(init_data)
    
    bot_username = input(f"{Colors.CYAN}Bot (default: BTCTapperbot): {Colors.RESET}").strip()
    if not bot_username:
        bot_username = "BTCTapperbot"
    bot_username = bot_username.lstrip('@')
    
    bot = BleonTapBot(init_data, bot_username)
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.ROSE}Stopped{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
# runner.py
import time
import random
import signal
import sys
from typing import Optional, Callable, List
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
from human_core import HumanCore
from state_engine import StateEngine

class SessionManager:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.session_count = 0
    
    def create_session(self) -> Optional[Page]:
        try:
            if self.playwright is None:
                self.playwright = sync_playwright().start()
            
            if self.browser:
                self._cleanup()
            
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            
            self.context = self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                locale="en-US",
                timezone_id="America/New_York"
            )
            
            self.page = self.context.new_page()
            self.page.set_default_timeout(30000)
            self.session_count += 1
            
            return self.page
        except Exception as e:
            print(f"[MANAGER] Failed to create session: {e}")
            self._cleanup()
            return None
    
    def _cleanup(self):
        try:
            if self.page and not self.page.is_closed():
                self.page.close()
        except:
            pass
        try:
            if self.context:
                self.context.close()
        except:
            pass
        try:
            if self.browser:
                self.browser.close()
        except:
            pass
        
        self.page = None
        self.context = None
        self.browser = None
    
    def shutdown(self):
        self._cleanup()
        if self.playwright:
            self.playwright.stop()

class ProductionRunner:
    def __init__(self, target_urls: List[str], task_callback: Callable[[Page], None]):
        self.target_urls = target_urls
        self.task_callback = task_callback
        self.manager = SessionManager()
        self.running = False
        self.max_runtime = 86400
        self.max_sessions = 1000
        self.session_cooldown = (10, 30)
        self.failure_cooldown = (30, 60)
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print(f"[RUNNER] Received signal {signum}, shutting down...")
        self.running = False
    
    def _twitter_task(self, page: Page):
        try:
            time.sleep(random.uniform(1, 3))
            
            scroll_amt = random.randint(300, 700)
            page.mouse.wheel(0, scroll_amt)
            time.sleep(random.uniform(0.5, 1.5))
            
            tweet_selectors = ['article[data-testid="tweet"]', 'div[data-testid="tweet"]']
            for selector in tweet_selectors:
                tweets = page.locator(selector).all()
                if tweets:
                    tweet = random.choice(tweets[:3])
                    if tweet.is_visible():
                        like_btn = tweet.locator('[data-testid="like"]').first
                        if like_btn.is_visible():
                            like_btn.click()
                            time.sleep(random.uniform(0.8, 1.5))
                            break
            
            time.sleep(random.uniform(2, 4))
        except:
            pass
    
    def run_session(self) -> bool:
        page = self.manager.create_session()
        if not page:
            print("[RUNNER] Failed to create page")
            return False
        
        try:
            core = HumanCore(page)
            engine = StateEngine(
                page=page,
                human_core=core,
                target_urls=self.target_urls,
                task_callback=self.task_callback or self._twitter_task
            )
            return engine.run()
        except Exception as e:
            print(f"[RUNNER] Session error: {e}")
            return False
        finally:
            try:
                time.sleep(random.uniform(2, 4))
            except:
                pass
    
    def run(self):
        self.running = True
        start_time = time.time()
        
        try:
            while (self.running and 
                   time.time() - start_time < self.max_runtime and
                   self.manager.session_count < self.max_sessions):
                
                print(f"[RUNNER] Session {self.manager.session_count + 1} starting")
                
                success = self.run_session()
                
                if success:
                    print(f"[RUNNER] Session {self.manager.session_count} completed")
                    cooldown = random.uniform(*self.session_cooldown)
                else:
                    print(f"[RUNNER] Session {self.manager.session_count} failed")
                    cooldown = random.uniform(*self.failure_cooldown)
                
                if self.running:
                    print(f"[RUNNER] Cooldown: {cooldown:.1f}s")
                    
                    elapsed = 0
                    while elapsed < cooldown and self.running:
                        time.sleep(1)
                        elapsed += 1
                        if elapsed % 10 == 0:
                            print(f"[RUNNER] Waiting... {elapsed:.0f}s / {cooldown:.0f}s")
                
                if random.random() < 0.05:
                    print("[RUNNER] Force cleanup cycle")
                    self.manager._cleanup()
                    time.sleep(random.uniform(5, 10))
        
        except Exception as e:
            print(f"[RUNNER] Critical error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        self.running = False
        self.manager.shutdown()
        print("[RUNNER] Shutdown complete")

def twitter_task_example(page: Page):
    try:
        time.sleep(random.uniform(1, 3))
        
        page.mouse.wheel(0, random.randint(200, 600))
        time.sleep(random.uniform(0.5, 1.5))
        
        buttons = page.locator('button:visible').all()
        if buttons:
            btn = random.choice(buttons[:5])
            btn.click()
            time.sleep(random.uniform(0.8, 1.5))
        
        time.sleep(random.uniform(2, 4))
    except:
        pass

if __name__ == "__main__":
    TARGET_URLS = [
        "https://twitter.com/home",
        "https://twitter.com/explore",
        "https://twitter.com/notifications"
    ]
    
    runner = ProductionRunner(
        target_urls=TARGET_URLS,
        task_callback=twitter_task_example
    )
    
    try:
        runner.run()
    except KeyboardInterrupt:
        runner.stop()

# state_engine.py
import time
import random
from enum import Enum, auto
from typing import Optional, Callable, List
from playwright.sync_api import Page, TimeoutError

class State(Enum):
    INIT = auto()
    NAVIGATE = auto()
    WAIT_READY = auto()
    IDLE = auto()
    ACTION = auto()
    VERIFY = auto()
    RECOVER = auto()
    EXIT = auto()

class StateEngine:
    def __init__(self, page: Page, human_core, target_urls: List[str], task_callback: Callable[[Page], None]):
        self.page = page
        self.core = human_core
        self.target_urls = target_urls
        self.task_callback = task_callback
        
        self.state = State.INIT
        self.state_start = time.time()
        self.retry_count = 0
        self.max_retries = 3
        self.recovery_step = 0
        self.max_recovery_steps = 4
        self.session_start = time.time()
        self.max_session_time = random.randint(600, 1800)
        
        self.heartbeat_last = time.time()
        self.heartbeat_interval = 15
        
        self.action_timeout = 30
        self.danger_selectors = [
            "[href*='logout']",
            "[href*='signout']",
            "[href*='exit']",
            "[aria-label*='log out']",
            "[aria-label*='sign out']",
            "button[type='submit'][value*='logout']"
        ]
        
        self.state_sleep_map = {
            State.INIT: (0.5, 1.5),
            State.NAVIGATE: (2.0, 4.0),
            State.WAIT_READY: (0.3, 0.7),
            State.IDLE: (0.1, 0.3),
            State.ACTION: (0.05, 0.15),
            State.VERIFY: (1.0, 2.0),
            State.RECOVER: (0.5, 1.0),
            State.EXIT: (0, 0)
        }
    
    def _check_heartbeat(self) -> bool:
        if time.time() - self.heartbeat_last > self.heartbeat_interval:
            try:
                alive = self.page.evaluate("""
                    () => {
                        try {
                            return document.readyState === 'complete';
                        } catch {
                            return false;
                        }
                    }
                """)
                self.heartbeat_last = time.time()
                return alive
            except:
                return False
        return True
    
    def _check_timeout(self) -> bool:
        if time.time() - self.session_start > self.max_session_time:
            return True
        if time.time() - self.state_start > self.action_timeout:
            return True
        return False
    
    def _page_valid(self) -> bool:
        try:
            url = self.page.url
            if not url or url == "about:blank" or "chrome-error://" in url:
                return False
            return True
        except:
            return False
    
    def _is_dangerous_element(self, element) -> bool:
        try:
            for selector in self.danger_selectors:
                if element.locator(f"xpath=ancestor-or-self::{selector}").count() > 0:
                    return True
            
            text = element.text_content().lower()
            danger_phrases = ["log out", "sign out", "exit", "logout", "signout"]
            if any(phrase in text for phrase in danger_phrases):
                return True
                
            return False
        except:
            return True
    
    def _find_safe_clickable(self) -> bool:
        selectors = [
            "button:visible",
            "a:visible",
            "[role='button']:visible",
            "[onclick]:visible",
            "input[type='button']:visible",
            "input[type='submit']:visible"
        ]
        
        for selector in selectors:
            try:
                elements = self.page.locator(selector).all()
                if not elements:
                    continue
                    
                safe_elements = []
                for elem in elements[:5]:
                    try:
                        if not elem.is_visible():
                            continue
                            
                        if self._is_dangerous_element(elem):
                            continue
                            
                        box = elem.bounding_box()
                        if not box:
                            continue
                            
                        if box['width'] < 10 or box['height'] < 10:
                            continue
                            
                        if box['width'] * box['height'] < 100:
                            continue
                            
                        safe_elements.append(elem)
                    except:
                        continue
                
                if safe_elements:
                    elem = random.choice(safe_elements)
                    self.core.hesitation_pause()
                    elem.click(timeout=5000)
                    time.sleep(random.uniform(0.5, 1.5))
                    return True
            except:
                continue
        return False
    
    def _execute_action(self):
        if random.random() < 0.3:
            self.task_callback(self.page)
        else:
            action_type = random.choices(
                ["idle", "scroll", "click"],
                weights=[50, 35, 15]
            )[0]
            
            if action_type == "idle":
                idle_type = random.choices(
                    ["short", "medium", "long", "burst"],
                    weights=[40, 30, 20, 10]
                )[0]
                
                if idle_type == "short":
                    self.core.idle_short()
                elif idle_type == "medium":
                    self.core.idle_medium()
                elif idle_type == "long":
                    self.core.idle_long()
                else:
                    self.core.idle_burst()
            
            elif action_type == "scroll":
                self.core.random_scroll()
            
            elif action_type == "click":
                if not self._find_safe_clickable():
                    self.core.random_scroll()
    
    def _execute_recovery(self) -> bool:
        self.recovery_step += 1
        
        if self.recovery_step > self.max_recovery_steps:
            return False
        
        try:
            if self.recovery_step == 1:
                print("[RECOVER] Step 1: Wait and scroll")
                time.sleep(random.uniform(5, 10))
                self.core.scroll_down()
                time.sleep(2)
                return True
            
            elif self.recovery_step == 2:
                print("[RECOVER] Step 2: Try go back")
                try:
                    self.page.go_back(timeout=10000)
                    time.sleep(random.uniform(3, 5))
                    return True
                except:
                    return True
            
            elif self.recovery_step == 3:
                print("[RECOVER] Step 3: Soft reload")
                try:
                    self.page.reload(timeout=15000)
                    time.sleep(random.uniform(3, 5))
                    return True
                except:
                    return True
            
            elif self.recovery_step == 4:
                print("[RECOVER] Step 4: Navigate to new URL")
                try:
                    new_url = random.choice(self.target_urls)
                    self.page.goto(new_url, timeout=30000)
                    time.sleep(random.uniform(3, 5))
                    return True
                except:
                    return False
        
        except Exception:
            return self.recovery_step < self.max_recovery_steps
    
    def _change_state(self, new_state: State):
        self.state = new_state
        self.state_start = time.time()
        self.retry_count = 0
        
        if new_state == State.RECOVER:
            self.recovery_step = 0
        else:
            self.recovery_step = 0
    
    def _get_state_sleep(self) -> float:
        min_sleep, max_sleep = self.state_sleep_map.get(self.state, (0.1, 0.3))
        return random.uniform(min_sleep, max_sleep)
    
    def run(self) -> bool:
        while self.state != State.EXIT:
            if self._check_timeout():
                return True
            
            if not self._check_heartbeat():
                self._change_state(State.RECOVER)
                time.sleep(self._get_state_sleep())
                continue
            
            if self.state == State.INIT:
                self.core.idle_short()
                self._change_state(State.NAVIGATE)
            
            elif self.state == State.NAVIGATE:
                self.retry_count += 1
                try:
                    target_url = random.choice(self.target_urls)
                    self.page.goto(target_url, timeout=30000)
                    self._change_state(State.WAIT_READY)
                except Exception:
                    if self.retry_count >= self.max_retries:
                        self._change_state(State.RECOVER)
                    else:
                        time.sleep(random.uniform(3, 6))
            
            elif self.state == State.WAIT_READY:
                self.retry_count += 1
                try:
                    self.page.wait_for_load_state("load", timeout=15000)
                    time.sleep(random.uniform(1, 3))
                    
                    ready = self.page.evaluate("""
                        () => {
                            try {
                                return document.body && 
                                       document.body.children.length > 2;
                            } catch {
                                return false;
                            }
                        }
                    """)
                    
                    if ready:
                        self._change_state(State.ACTION)
                    else:
                        if self.retry_count >= self.max_retries:
                            self._change_state(State.RECOVER)
                        else:
                            time.sleep(random.uniform(2, 4))
                except TimeoutError:
                    if self.retry_count >= self.max_retries:
                        self._change_state(State.RECOVER)
                    else:
                        self.core.scroll_down()
                        time.sleep(2)
            
            elif self.state == State.ACTION:
                try:
                    if not self._page_valid():
                        self._change_state(State.RECOVER)
                        continue
                    
                    self._execute_action()
                    self._change_state(State.VERIFY)
                except Exception:
                    self._change_state(State.RECOVER)
            
            elif self.state == State.VERIFY:
                self.retry_count += 1
                try:
                    if self._page_valid():
                        self._change_state(State.IDLE)
                    else:
                        if self.retry_count >= self.max_retries:
                            self._change_state(State.RECOVER)
                        else:
                            time.sleep(random.uniform(1, 3))
                except:
                    self._change_state(State.RECOVER)
            
            elif self.state == State.IDLE:
                self.core.idle_medium()
                self._change_state(State.ACTION)
            
            elif self.state == State.RECOVER:
                self.retry_count += 1
                
                if self.retry_count >= self.max_retries:
                    return False
                
                recovery_success = self._execute_recovery()
                
                if recovery_success:
                    self._change_state(State.WAIT_READY)
                else:
                    return False
            
            elif self.state == State.EXIT:
                break
            
            time.sleep(self._get_state_sleep())
        
        return True

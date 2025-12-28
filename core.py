import random
import time
from typing import Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


class HumanCore:
    def __init__(self, page: Page):
        self.page = page
        self.blank_hits = 0
        self.max_blank_hits = 2
        self.page_load_timeout = 30000  # ms
        self.last_activity = time.time()
        self.inactive_threshold = 45  # seconds

    # ---------- PAGE LOAD ----------
    def wait_for_page_load(self, timeout: int = None) -> bool:
        if timeout is None:
            timeout = self.page_load_timeout

        max_retries = 2
        for retry in range(max_retries):
            try:
                self.page.wait_for_load_state(
                    "domcontentloaded", timeout=min(timeout, 15000)
                )

                try:
                    self.page.wait_for_load_state("networkidle", timeout=5000)
                except PlaywrightTimeoutError:
                    pass

                start_time = time.time()
                while time.time() - start_time < 10:
                    try:
                        content = self.page.content()
                        if content and len(content) > 1000:
                            body_ok = self.page.evaluate(
                                """
                                () => {
                                    const body = document.body;
                                    if (!body) return false;
                                    if (body.children.length < 3) return false;
                                    if (!body.textContent || body.textContent.trim().length < 100) return false;
                                    return true;
                                }
                                """
                            )
                            if body_ok:
                                time.sleep(random.uniform(0.5, 1.5))
                                return True
                    except:
                        pass
                    time.sleep(0.5)

                if retry < max_retries - 1:
                    self.page.reload()
                    continue

            except PlaywrightTimeoutError:
                if retry < max_retries - 1:
                    try:
                        self.page.reload()
                    except:
                        pass
                else:
                    return False

            except Exception:
                if retry < max_retries - 1:
                    continue

        return False

    # ---------- GUARD ----------
    def guard_blank_page(self) -> bool:
        try:
            url = self.page.url or ""

            if "about:blank" in url or "chrome-error://" in url:
                self.blank_hits += 1

                if self.blank_hits >= self.max_blank_hits:
                    return False

                recovery = [
                    lambda: self.page.go_back(),
                    lambda: self.page.reload(),
                    lambda: self.page.evaluate("window.history.back()"),
                ]

                for action in recovery:
                    try:
                        action()
                        time.sleep(random.uniform(2.0, 4.0))
                        if self.wait_for_page_load(15000):
                            return True
                    except:
                        continue

                return False

            if time.time() - self.last_activity > self.inactive_threshold:
                try:
                    content_len = len(self.page.content() or "")
                    if content_len < 500:
                        self.page.reload()
                        time.sleep(random.uniform(2.0, 3.5))
                        self.wait_for_page_load()
                except:
                    pass

            self.blank_hits = 0
            return True

        except Exception:
            return True

    # ---------- IDLE ----------
    def idle_short(self):
        if random.random() < 0.3:
            try:
                vp = self.page.viewport_size
                if vp:
                    self.page.mouse.move(
                        random.randint(-5, 5),
                        random.randint(-3, 3),
                        steps=random.randint(2, 5),
                    )
            except:
                pass
        time.sleep(random.uniform(0.8, 2.5))

    def idle_medium(self):
        pause = random.uniform(3.0, 7.0)
        if random.random() < 0.4:
            time.sleep(pause * 0.6)
            self.page.mouse.wheel(0, random.randint(-30, 30))
            time.sleep(pause * 0.4)
        else:
            time.sleep(pause)

    def idle_long(self):
        pause = random.uniform(8.0, 15.0)
        segments = random.randint(2, 4)
        part = pause / segments

        for i in range(segments):
            time.sleep(part * random.uniform(0.8, 1.2))
            if i < segments - 1 and random.random() < 0.25:
                try:
                    vp = self.page.viewport_size
                    if vp:
                        if random.random() < 0.5:
                            self.page.mouse.wheel(0, random.randint(-15, 15))
                        else:
                            self.page.mouse.move(
                                random.randint(-10, 10),
                                random.randint(-5, 5),
                                steps=random.randint(3, 8),
                            )
                except:
                    pass

    def idle_burst(self):
        for i in range(random.randint(2, 5)):
            time.sleep(random.uniform(0.3, 0.9))
            if i < 4 and random.random() < 0.4:
                try:
                    vp = self.page.viewport_size
                    if vp:
                        self.page.mouse.move(
                            random.randint(-20, 20),
                            random.randint(-15, 15),
                            steps=random.randint(2, 4),
                        )
                except:
                    pass

    # ---------- SCROLL ----------
    def _scroll_with_human_rhythm(self, amount: int):
        direction = 1 if amount > 0 else -1
        total = abs(amount)

        if total <= 300:
            steps = random.randint(1, 3)
        elif total <= 700:
            steps = random.randint(2, 4)
        else:
            steps = random.randint(3, 6)

        step = total / steps

        for i in range(steps):
            delta = step * random.uniform(0.7, 1.3) * direction
            self.page.mouse.wheel(0, delta)

            if i < steps - 1:
                time.sleep(random.uniform(0.05, 0.3))
                if random.random() < 0.15:
                    self.page.mouse.wheel(0, -random.randint(5, 20))
                    time.sleep(random.uniform(0.05, 0.15))

    def random_scroll(self):
        patterns = [
            random.randint(150, 400),
            random.randint(400, 800),
            random.randint(800, 1500),
            -random.randint(100, 300),
            -random.randint(300, 600),
        ]

        amt = random.choice(patterns)
        self._scroll_with_human_rhythm(amt)

        if random.random() < 0.2:
            time.sleep(random.uniform(0.4, 1.2))
            self._scroll_with_human_rhythm(-random.randint(50, 150))

        if random.random() < 0.5:
            time.sleep(random.uniform(0.3, 0.8))
        else:
            self.idle_short()

    # ---------- CLICK ----------
    def hesitant_click(self) -> Optional[bool]:
        try:
            vp = self.page.viewport_size
            if not vp:
                return None

            x = random.randint(100, max(150, vp["width"] - 200))
            y = random.randint(120, max(180, vp["height"] - 200))

            self.page.mouse.move(x, y, steps=random.randint(3, 8))

            r = random.random()
            if r < 0.1:
                for _ in range(random.randint(2, 4)):
                    self.page.mouse.move(
                        x + random.randint(-25, 25),
                        y + random.randint(-20, 20),
                        steps=random.randint(2, 5),
                    )
                    time.sleep(random.uniform(0.2, 0.5))
                if random.random() < 0.3:
                    return False
            elif r < 0.25:
                time.sleep(random.uniform(0.5, 1.2))

            self.page.mouse.down()
            time.sleep(random.uniform(0.04, 0.12))
            self.page.mouse.up()

            if random.random() < 0.4:
                time.sleep(random.uniform(0.1, 0.3))

            return True

        except Exception:
            return None

    # ---------- REFRESH ----------
    def rare_refresh(self):
        if random.random() < 0.04:
            self.idle_medium()
            try:
                self.page.reload()
                self.wait_for_page_load(20000)
                time.sleep(random.uniform(1.0, 2.5))
            except:
                pass

    # ---------- MAIN LOOP ----------
    def run(self, duration_seconds: int):
        if duration_seconds <= 0:
            return

        end_time = time.time() + duration_seconds
        cycle = 0

        while time.time() < end_time:
            cycle += 1

            if not self.guard_blank_page():
                break

            actions = [
                ("idle_short", 25),
                ("idle_medium", 20),
                ("idle_long", 15),
                ("idle_burst", 10),
                ("scroll", 18),
                ("click", 8),
                ("refresh", 4),
            ]

            names, weights = zip(*actions)
            act = random.choices(names, weights=weights, k=1)[0]

            if act == "idle_short":
                self.idle_short()
            elif act == "idle_medium":
                self.idle_medium()
            elif act == "idle_long":
                self.idle_long()
            elif act == "idle_burst":
                self.idle_burst()
            elif act == "scroll":
                self.random_scroll()
            elif act == "click":
                self.hesitant_click()
            elif act == "refresh":
                self.rare_refresh()

            self.last_activity = time.time()

            if random.random() < 0.8:
                time.sleep(random.uniform(0.1, 0.5))

            if random.random() < 0.05 and end_time - time.time() < 5:
                break

        print(f"[CORE] Completed {cycle} cycles")

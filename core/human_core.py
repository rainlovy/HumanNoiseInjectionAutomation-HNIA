# human_core.py
import random
import time
from playwright.sync_api import Page

class HumanCore:
    def __init__(self, page: Page):
        self.page = page
    
    def idle_short(self):
        time.sleep(random.uniform(0.8, 2.5))
    
    def idle_medium(self):
        time.sleep(random.uniform(3.0, 7.0))
    
    def idle_long(self):
        time.sleep(random.uniform(8.0, 15.0))
    
    def idle_burst(self):
        bursts = random.randint(2, 4)
        for _ in range(bursts):
            time.sleep(random.uniform(0.4, 1.2))
    
    def micro_movement(self):
        try:
            vp = self.page.viewport_size
            if vp:
                self.page.mouse.move(
                    random.randint(-5, 5),
                    random.randint(-3, 3),
                    steps=random.randint(2, 4)
                )
        except:
            pass
    
    def _human_scroll(self, amount: int):
        direction = 1 if amount > 0 else -1
        abs_amount = abs(amount)
        
        if abs_amount < 400:
            steps = random.randint(1, 2)
        else:
            steps = random.randint(2, 4)
        
        remaining = abs_amount
        for step in range(steps):
            if step == steps - 1:
                step_amt = remaining
            else:
                step_amt = random.randint(int(remaining * 0.3), int(remaining * 0.7))
                remaining -= step_amt
            
            final = int(step_amt * random.uniform(0.9, 1.1)) * direction
            scroll_steps = random.randint(1, 2)
            
            for _ in range(scroll_steps):
                partial = final / scroll_steps
                self.page.mouse.wheel(0, partial)
                time.sleep(random.uniform(0.02, 0.06))
            
            if step < steps - 1:
                pause = random.uniform(0.1, 0.3)
                time.sleep(pause)
                
                if random.random() < 0.15:
                    correction = -random.randint(5, 15) * direction
                    self.page.mouse.wheel(0, correction)
                    time.sleep(0.05)
    
    def scroll_down(self):
        if random.random() < 0.7:
            self._human_scroll(random.randint(200, 500))
        else:
            self._human_scroll(random.randint(500, 900))
        time.sleep(random.uniform(0.3, 0.8))
    
    def scroll_up(self):
        self._human_scroll(-random.randint(100, 300))
        time.sleep(random.uniform(0.3, 0.8))
    
    def random_scroll(self):
        if random.random() < 0.8:
            self.scroll_down()
        else:
            self.scroll_up()
    
    def hesitation_pause(self):
        time.sleep(random.uniform(0.5, 1.5))
        self.micro_movement()

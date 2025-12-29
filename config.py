# config.py
SESSION_MIN_SECONDS = 600
SESSION_MAX_SECONDS = 1800
MAX_RELOADS = 3
MAX_RETRIES = 3
HEARTBEAT_INTERVAL = 15
ACTION_TIMEOUT = 30
RECOVERY_COOLDOWN = 5
MAX_RUNTIME_HOURS = 24
MAX_SESSIONS = 1000
SESSION_COOLDOWN = (10, 30)
FAILURE_COOLDOWN = (30, 60)

DANGER_SELECTORS = [
    "[href*='logout']",
    "[href*='signout']",
    "[href*='exit']",
    "[aria-label*='log out']",
    "[aria-label*='sign out']",
    "button[type='submit'][value*='logout']"
]

STATE_SLEEP_MAP = {
    "INIT": (0.5, 1.5),
    "NAVIGATE": (2.0, 4.0),
    "WAIT_READY": (0.3, 0.7),
    "IDLE": (0.1, 0.3),
    "ACTION": (0.05, 0.15),
    "VERIFY": (1.0, 2.0),
    "RECOVER": (0.5, 1.0),
    "EXIT": (0, 0)
}

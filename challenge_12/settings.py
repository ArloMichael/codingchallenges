from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent / "assets"
SAVE_PATH = BASE_DIR.parent / "save.json"
AUTOSAVE_INTERVAL = 30

WIDTH, HEIGHT = 800, 600
FPS = 120
SIMULATION_STEP_SECONDS = 1 / 60
PIXEL_SCALE = 4
VIRTUAL_WIDTH = WIDTH // PIXEL_SCALE
VIRTUAL_HEIGHT = HEIGHT // PIXEL_SCALE

REAL_SECONDS_PER_GAME_DAY = 60
GAME_SECONDS_PER_REAL_SECOND = (
    24 * 60 * 60 / REAL_SECONDS_PER_GAME_DAY
)
PET_DEFAULT_NAME = "PET"
PET_NAME_MAX_LENGTH = 12
PET_ADULT_AGE_DAYS = 3
PET_SENIOR_AGE_DAYS = 10
PET_PERSONALITIES = ("LAZY", "ENERGETIC", "MOODY")
PERSONALITY_PROFILES = {
    "BALANCED": {
        "stat_rates": {},
        "actions": {},
        "sleep_energy_gain": 1.0,
        "animation_choices": ("idle", "run"),
    },
    "LAZY": {
        "stat_rates": {"energy": 0.7},
        "actions": {
            "play": {"energy": 1.5},
        },
        "sleep_energy_gain": 1.5,
        "animation_choices": ("idle", "idle", "idle", "run"),
    },
    "ENERGETIC": {
        "stat_rates": {"energy": 1.2},
        "actions": {
            "play": {
                "happiness": 1.5,
                "energy": 0.5,
            },
        },
        "sleep_energy_gain": 1.0,
        "animation_choices": ("idle", "run", "run", "run"),
    },
    "MOODY": {
        "stat_rates": {"happiness": 1.5},
        "actions": {
            "feed": {"happiness": 1.5},
            "play": {"happiness": 1.5},
            "rest": {"happiness": 1.5},
        },
        "sleep_energy_gain": 1.0,
        "animation_choices": ("idle", "idle", "run"),
    },
}

BUTTON_CLICK_HOLD_TIME = 0.05
STAT_MIN = 0
STAT_MAX = 100
STAT_DECAY_RATES = {
    "food": -2.0,
    "energy": -1.0,
    "happiness": -0.5,
}
ACTION_EFFECTS = {
    "feed": {
        "food": 20,
        "happiness": 2,
    },
    "play": {
        "food": -5,
        "happiness": 15,
        "energy": -10,
    },
    "rest": {
        "happiness": -5,
    },
}
ACTION_COSTS = {
    "feed": 5,
    "play": 10,
    "rest": 8,
}
STORE_ITEMS = {
    "meal": {
        "label": "FOOD +30",
        "price": 15,
        "effects": {"food": 30},
    },
    "toy": {
        "label": "HAPPY +25",
        "price": 20,
        "effects": {"happiness": 25},
    },
    "battery": {
        "label": "ENERGY +25",
        "price": 20,
        "effects": {"energy": 25},
    },
}
RPS_CHOICES = ("rock", "paper", "scissors")
RPS_BEATS = {
    "rock": "scissors",
    "paper": "rock",
    "scissors": "paper",
}
RPS_WIN_REWARD = 25
RPS_DRAW_REWARD = 5

HUD_TEXT_COLOR = (240, 240, 240)
CRITICAL_TEXT_COLOR = (240, 48, 48)
NAME_TAG_COLOR = (135, 135, 135)
NAME_TAG_BACKGROUND = (40, 40, 40)
NAME_TAG_IDLE_X_OFFSET = 1
NAME_CURSOR_BLINK_MS = 500
MOOD_LOW_THRESHOLD = 25
MOOD_RECOVERY_THRESHOLD = 35
MOOD_MESSAGES = {
    "food": {
        "low": "I'M HUNGRY",
        "recovered": "I'M FULL",
    },
    "happiness": {
        "low": "I'M SAD",
        "recovered": "I'M HAPPY",
    },
    "energy": {
        "low": "I'M TIRED",
        "recovered": "I'M RESTED",
    },
}
PERSONALITY_MOOD_MESSAGES = {
    "LAZY": {
        "food": {
            "low": "SNACK TIME...",
            "recovered": "NICE...",
        },
        "happiness": {
            "low": "BORED...",
            "recovered": "NICE...",
        },
        "energy": {
            "low": "NAP TIME...",
            "recovered": "RESTED...",
        },
    },
    "ENERGETIC": {
        "food": {
            "low": "NEED FUEL!",
            "recovered": "FUELLED UP!",
        },
        "happiness": {
            "low": "LET'S PLAY!",
            "recovered": "LET'S GO!",
        },
        "energy": {
            "low": "NEED A BREAK",
            "recovered": "FULL POWER!",
        },
    },
    "MOODY": {
        "food": {
            "low": "FEED ME!",
            "recovered": "ABOUT TIME!",
        },
        "happiness": {
            "low": "LEAVE ME...",
            "recovered": "I FEEL BETTER",
        },
        "energy": {
            "low": "I'M EXHAUSTED",
            "recovered": "FINALLY...",
        },
    },
}
TOAST_BACKGROUND_COLOR = (60, 60, 60)
CRITICAL_THRESHOLD = 10
CRITICAL_FLASH_MS = 250
FOOD_DEATH_COUNTDOWN = 10
REST_DURATION = 10
SLEEP_FOOD_COST = 20
SLEEP_ENERGY_GAIN_RATE = 1
ENERGY_SLEEP_WAKE_THRESHOLD = CRITICAL_THRESHOLD
HEALTHY_STAT_THRESHOLD = 50
HAPPINESS_RECOVERY_RATE = 0.5

STAT_ROW_HEIGHT = 18
STAT_ICON_TEXT_GAP = 3
HUD_FONT_SIZE = 8
FONT_PATH = BASE_DIR / "fonts" / "PressStart2P-Regular.ttf"
MUSIC_PATH = BASE_DIR / "audio" / "music.wav"
MUSIC_ENABLED = True
SFX_ENABLED = True
MUSIC_VOLUME = 0.5
SFX_VOLUME = 0.2
SFX_REVERB_ENABLED = True
SFX_REVERB_DRY = 0.65
SFX_REVERB_WET = 0.8
SFX_REVERB_DURATION_SECONDS = 3.0
SFX_REVERB_DECAY_SECONDS = 2.5
SFX_REVERB_PREDELAY_MS = 24
SFX_REVERB_DAMPING = 0.25
SFX_REVERB_COMB_DELAYS_MS = (29.7, 37.1, 41.1, 43.7)
SFX_REVERB_ALLPASS_DELAYS_MS = (5.0, 1.7)
SFX_REVERB_ALLPASS_FEEDBACK = 0.65
SFX_REVERB_STEREO_SPREAD = 0.013
SFX_REVERB_CHANNELS = 32
SFX_PATHS = {
    name: BASE_DIR / "audio" / "sfx" / f"{name}.wav"
    for name in (
        "click",
        "coin",
        "denied",
        "purchase",
        "death",
    )
}
BYPASS = False

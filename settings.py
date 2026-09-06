"""Runtime settings and backwards-compatible plan defaults (no import-time writes)."""

import copy
import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

CATEGORIES = {
    "regular": {
        "name": "کانفیگ عادی",
        "emoji": "🌐",
        "description": "برای وب‌گردی، شبکه‌های اجتماعی و تماشای ویدیو",
    },
    "gaming": {"name": "کانفیگ گیمینگ", "emoji": "🎮", "description": "پلن‌های جداگانه برای بازی آنلاین"},
}

DEFAULT_PLANS = {
    "regular_light": {
        "name": "پینگینو سبک",
        "category": "regular",
        "price": 89000,
        "traffic_gb": 30,
        "days": 30,
        "enabled": True,
        "featured": False,
    },
    "regular_plus": {
        "name": "پینگینو پلاس",
        "category": "regular",
        "price": 149000,
        "traffic_gb": 60,
        "days": 30,
        "enabled": True,
        "featured": True,
    },
    "regular_pro": {
        "name": "پینگینو پرو",
        "category": "regular",
        "price": 249000,
        "traffic_gb": 120,
        "days": 30,
        "enabled": True,
        "featured": False,
    },
    "gaming_light": {
        "name": "گیمینگ استارتر",
        "category": "gaming",
        "price": 129000,
        "traffic_gb": 20,
        "days": 30,
        "enabled": True,
        "featured": False,
    },
    "gaming_plus": {
        "name": "گیمینگ پلاس",
        "category": "gaming",
        "price": 229000,
        "traffic_gb": 50,
        "days": 30,
        "enabled": True,
        "featured": True,
    },
    "gaming_pro": {
        "name": "گیمینگ پرو",
        "category": "gaming",
        "price": 389000,
        "traffic_gb": 100,
        "days": 30,
        "enabled": True,
        "featured": False,
    },
}

DEFAULT_SETTINGS = {
    "bot_token": "",
    "bot_username": "",
    "panel_url": "http://localhost:8000",
    "panel_password": "",
    "admin_ids": [],
    "welcome_message": "به پینگینو خوش اومدی؛ اینجا به دنیای خودت وصل شو! 🐧",
    "required_channel": "@pingino_org",
    "required_channel_url": "https://t.me/pingino_org",
    "support_username": "",
    "card_number": "",
    "card_name": "",
    "webapp_url": "",
    "proxy_url": None,
    "colored_buttons": True,
    "init_data_max_age": 3600,
    # Point gaming at a separate HS Panel or protocol when available. A label
    # alone cannot improve latency; no unsupported routing fields are sent.
    "panel_profiles": {"regular": {}, "gaming": {}},
    "trial": {"enabled": True, "days": 1, "traffic_gb": 1, "category": "regular"},
}


def load_settings(data_dir: Path | None = None) -> dict:
    directory = Path(data_dir or os.getenv("PINGINOO_DATA_DIR", ROOT))
    path = directory / "config.json"
    raw = json.loads(path.read_text("utf-8")) if path.exists() else {}
    if not isinstance(raw, dict):
        raise ValueError("config.json must contain a JSON object")
    config = copy.deepcopy(DEFAULT_SETTINGS)
    config.update(raw)
    config["trial"] = {**DEFAULT_SETTINGS["trial"], **raw.get("trial", {}), "days": 1}
    for env, key in {
        "BOT_TOKEN": "bot_token",
        "BOT_USERNAME": "bot_username",
        "PANEL_URL": "panel_url",
        "PANEL_PASSWORD": "panel_password",
        "WEBAPP_URL": "webapp_url",
        "SUPPORT_USERNAME": "support_username",
        "CARD_NUMBER": "card_number",
        "CARD_NAME": "card_name",
    }.items():
        if env in os.environ:
            config[key] = os.environ[env]
    if os.getenv("ADMIN_IDS"):
        config["admin_ids"] = [int(v.strip()) for v in os.environ["ADMIN_IDS"].split(",") if v.strip()]
    config["admin_ids"] = [int(uid) for uid in config.get("admin_ids", [])]
    config["bot_username"] = config.get("bot_username", "").lstrip("@")
    config["support_username"] = config.get("support_username", "").lstrip("@")
    config["data_dir"] = directory
    return config


def initial_catalog(config: dict) -> dict:
    """Preserve old plan identifiers, prices and quotas; add a missing category."""
    plans = copy.deepcopy(config.get("plans") or DEFAULT_PLANS)
    for plan in plans.values():
        plan.setdefault("category", "regular")
        plan.setdefault("enabled", True)
        plan.setdefault("featured", False)
    for category in CATEGORIES:
        if not any(p.get("category") == category for p in plans.values()):
            plans.update({k: copy.deepcopy(p) for k, p in DEFAULT_PLANS.items() if p["category"] == category})
    return {"plans": plans, "trial": copy.deepcopy(config["trial"])}

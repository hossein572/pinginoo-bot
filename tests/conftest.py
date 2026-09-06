import asyncio
import copy
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from settings import DEFAULT_SETTINGS
from shop import Shop


@pytest.fixture
def config(tmp_path):
    return {
        **copy.deepcopy(DEFAULT_SETTINGS),
        "data_dir": tmp_path,
        "bot_token": "123456:TEST_TOKEN_NOT_A_REAL_TELEGRAM_TOKEN",
        "bot_username": "pinginoo_test_bot",
        "admin_ids": [1],
        "panel_url": "https://panel.example.invalid",
        "panel_password": "test-only-password",
        "card_number": "0000-0000-0000-0000",
        "card_name": "Test account, not real",
    }


class FakePanel:
    def __init__(self, category="regular"):
        self.base = f"https://{category}.example.invalid"
        self.login_ok = True
        self.result = None
        self.creates = []
        self.extensions = []
        self.gets = []
        self.wait = None

    async def ensure_logged_in(self):
        return self.login_ok

    async def create_link(self, **kwargs):
        self.creates.append(kwargs)
        await asyncio.sleep(0)  # Let concurrent callers race the atomic claim.
        if self.wait:
            await self.wait.wait()
        return self.result or {"status": "ok", "data": {"uuid": "cfg_" + str(len(self.creates))}}

    async def get_sub_link(self, uid):
        return f"{self.base}/sub/{uid}"

    async def extend_link(self, uid, days, traffic_gb):
        self.extensions.append((uid, days, traffic_gb))
        await asyncio.sleep(0)
        return self.result or {"status": "ok", "data": {"uuid": uid}}

    async def get_sub(self, uid):
        self.gets.append(uid)
        return {"status": "ok", "data": {"uuid": uid}}


@pytest.fixture
def panels():
    return {category: FakePanel(category) for category in ("regular", "gaming")}


@pytest.fixture
def shop(config, panels):
    return Shop(config, panel_factory=lambda category, base=None: panels[category])


def signed_data(config, uid=7, *, auth_date=None, first_name="کاربر تست", token=None):
    fields = {
        "auth_date": str(int(time.time()) if auth_date is None else auth_date),
        "query_id": "query_test",
        "user": json.dumps(
            {"id": uid, "first_name": first_name, "username": "test_user"},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }
    check = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", (token or config["bot_token"]).encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


@pytest.fixture
def auth(config):
    return lambda uid=7, **kwargs: {"Authorization": "tma " + signed_data(config, uid, **kwargs)}

from unittest.mock import AsyncMock

import pytest

from panel_api import PanelAPI
from shop import Shop


@pytest.mark.parametrize(
    "code,uncertain,retries",
    [(404, False, 2), (405, False, 2), (401, False, 1), (500, True, 1), (408, True, 1), (None, True, 1)],
)
async def test_mutating_fallback_only_on_unsupported_endpoint(code, uncertain, retries):
    panel = PanelAPI("https://panel.example.invalid", "password")
    panel._req = AsyncMock(
        side_effect=[
            {"status": "error", "code": code, "uncertain": uncertain},
            {"status": "ok", "data": {"uuid": "new"}},
        ]
    )
    result = await panel.create_link(1.5, 1, label="trial_7")
    assert panel._req.await_count == retries
    payload = panel._req.call_args_list[0].kwargs["json"]
    assert payload["traffic"] == round(1.5 * 1024**3)
    assert payload["days"] == 1
    if retries == 1:
        assert result["status"] == "error"


def test_gaming_profile_uses_separate_backend_and_protocol(config):
    config["panel_profiles"]["gaming"] = {
        "panel_url": "https://games.example.invalid/",
        "panel_password": "games-password",
        "protocol": "vless",
    }
    shop = Shop(config)
    gaming = shop.panel("gaming")
    assert gaming.base == "https://games.example.invalid"
    assert gaming.password == "games-password"
    assert gaming.protocol == "vless"
    assert shop.panel("regular").base == config["panel_url"]
    assert (
        shop.panel("gaming", "https://old-games.example.invalid").base == "https://old-games.example.invalid"
    )


async def test_subscription_payload_uses_telegram_label_without_email():
    panel = PanelAPI("https://panel.example.invalid", "password", protocol="vless")
    panel._req = AsyncMock(return_value={"status": "ok", "data": {"uuid": "new"}})
    await panel.create_link(1, 1, label="trial_7_reference")
    assert panel._req.call_args.kwargs["json"] == {
        "name": "trial_7_reference",
        "traffic": 1024**3,
        "days": 1,
        "protocol": "vless",
    }

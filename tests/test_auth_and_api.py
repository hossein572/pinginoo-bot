import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from conftest import signed_data
from fastapi.testclient import TestClient
from telegram.error import Forbidden, NetworkError

from gateway import check_membership
from shop import ShopError
from telegram_auth import validate_init_data
from webapp import create_app


@pytest.mark.parametrize(
    "status,is_member,expected",
    [
        ("member", False, True),
        ("administrator", False, True),
        ("creator", False, True),
        ("restricted", True, True),
        ("restricted", False, False),
        ("left", False, False),
        ("kicked", False, False),
    ],
)
async def test_membership_statuses(config, status, is_member, expected):
    bot = SimpleNamespace(
        get_chat_member=AsyncMock(return_value=SimpleNamespace(status=status, is_member=is_member))
    )
    assert await check_membership(bot, 7, config) == expected
    bot.get_chat_member.assert_awaited_once_with("@pingino_org", 7)


async def test_membership_api_failure_fails_closed(config):
    bot = SimpleNamespace(get_chat_member=AsyncMock(side_effect=NetworkError("offline")))
    with pytest.raises(ShopError) as exc:
        await check_membership(bot, 7, config)
    assert exc.value.code == "membership_unavailable"


def test_auth_hmac_and_unicode(config):
    encoded = signed_data(config, first_name="<مریم & علی>")
    assert validate_init_data(encoded, config["bot_token"])["first_name"] == "<مریم & علی>"


@pytest.mark.parametrize("variant", ["tampered", "expired", "future", "duplicate", "other_bot", "empty"])
def test_auth_rejects_invalid_data(config, variant):
    value = signed_data(config)
    if variant == "tampered":
        value = value.replace("query_test", "evil_query")
    elif variant == "expired":
        value = signed_data(config, auth_date=int(time.time()) - 3601)
    elif variant == "future":
        value = signed_data(config, auth_date=int(time.time()) + 120)
    elif variant == "duplicate":
        value += "&auth_date=0"
    elif variant == "other_bot":
        value = signed_data(config, token="another-test-bot")
    else:
        value = ""
    with pytest.raises(ShopError) as exc:
        validate_init_data(value, config["bot_token"])
    assert exc.value.status == 401


@pytest.fixture
def telegram_bot():
    bot = AsyncMock()
    bot.get_chat_member.return_value = SimpleNamespace(status="member", is_member=True)
    return bot


@pytest.fixture
def client(config, shop, telegram_bot):
    with TestClient(create_app(config, demo=False, shop=shop, telegram_bot=telegram_bot)) as client:
        yield client


def test_public_bootstrap_does_not_expose_secrets(client):
    response = client.get("/api/bootstrap")
    assert response.status_code == 200
    assert response.json()["channel"] == "@pingino_org"
    assert "bot_token" not in response.text and "panel_password" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert client.get("/config.json").status_code == 404
    assert client.get("/pinginoo.sqlite3").status_code == 404


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("GET", "/api/session", None),
        ("GET", "/api/admin/overview", None),
        ("POST", "/api/trial", None),
        ("POST", "/api/orders", {"plan_id": "regular_plus"}),
        ("PATCH", "/api/admin/plans/regular_plus", {"price": 10000}),
        ("POST", "/api/admin/orders/ord_x/approve", None),
    ],
)
def test_production_has_no_unauthenticated_or_demo_bypass(client, method, path, body):
    response = client.request(method, path, json=body, headers={"X-Demo-Role": "admin", "X-User-Id": "1"})
    assert response.status_code == 401


def test_user_api_requires_current_membership_on_every_call(client, auth, telegram_bot, panels):
    assert client.get("/api/session", headers=auth()).status_code == 200
    telegram_bot.get_chat_member.return_value.status = "left"
    for path, body in [
        ("/api/trial", None),
        ("/api/orders", {"plan_id": "regular_plus"}),
        ("/api/membership/check", None),
    ]:
        response = client.post(path, json=body, headers=auth())
        assert response.status_code == 403
        assert response.json()["code"] == "membership_required"
    assert not panels["regular"].creates
    telegram_bot.get_chat_member.return_value.status = "member"
    assert client.post("/api/membership/check", headers=auth()).json()["joined"] is True


def test_membership_network_failure_never_serves_private_data(client, auth, telegram_bot):
    telegram_bot.get_chat_member.side_effect = NetworkError("temporarily unavailable")
    response = client.get("/api/session", headers=auth())
    assert response.status_code == 503
    assert "configs" not in response.json()


def test_server_side_admin_access_not_browser_flags(client, auth, shop):
    assert client.get("/api/admin/overview", headers=auth(7)).status_code == 403
    assert (
        client.patch("/api/admin/plans/regular_plus", headers=auth(7), json={"price": 10000}).status_code
        == 403
    )
    response = client.patch(
        "/api/admin/plans/regular_plus", headers=auth(1), json={"price": "۲۲۲٬۰۰۰", "traffic_gb": "۹۰"}
    )
    assert response.status_code == 200
    assert (
        client.get("/api/session", headers=auth()).json()["catalog"]["plans"]["regular_plus"]["price"]
        == 222000
    )
    assert shop.catalog()["plans"]["regular_plus"]["traffic_gb"] == 90


def test_order_api_ignores_no_client_pricing_and_enforces_owner(client, auth):
    response = client.post("/api/orders", headers=auth(), json={"plan_id": "regular_plus", "price": 1})
    assert response.status_code == 422
    response = client.post("/api/orders", headers=auth(), json={"plan_id": "regular_plus"})
    assert response.status_code == 201
    order_id = response.json()["order"]["id"]
    assert response.json()["order"]["price"] == 149000
    assert response.json()["receipt_url"].endswith(f"start=receipt_{order_id}")
    assert client.get(f"/api/orders/{order_id}", headers=auth(8)).status_code == 404
    assert client.post(f"/api/orders/{order_id}/cancel", headers=auth(8)).status_code == 404
    assert client.post(f"/api/demo/orders/{order_id}/receipt", headers=auth()).status_code == 404
    assert client.get(f"/api/admin/orders/{order_id}/receipt", headers=auth()).status_code == 403


def test_trial_api_delivers_once(client, auth, shop, telegram_bot):
    response = client.post("/api/trial", headers=auth())
    assert response.status_code == 201
    assert response.json()["user"]["trial_used"]
    assert response.json()["configs"][0]["config_link"]
    assert response.json()["notified"] is True
    sent = telegram_bot.send_message.call_args.kwargs
    assert sent["chat_id"] == 7
    assert response.json()["configs"][0]["config_link"] in sent["text"]
    assert client.post("/api/trial", headers=auth()).status_code == 409
    assert len(shop.store.user(7)["configs"]) == 1


def test_demo_data_isolation(config, shop, panels):
    real_before = shop.catalog()
    with TestClient(create_app(config, demo=True)) as demo:
        assert demo.get("/api/bootstrap").json()["demo"]
        assert demo.get("/api/session").status_code == 200
        assert demo.patch("/api/admin/plans/regular_plus", json={"price": 333333}).status_code == 200
        assert demo.post("/api/trial").status_code == 201
        order = demo.post("/api/orders", json={"plan_id": "regular_plus"}).json()["order"]
        assert demo.post(f"/api/demo/orders/{order['id']}/receipt").status_code == 200
        assert demo.post(f"/api/admin/orders/{order['id']}/approve").status_code == 200
        cfg = demo.get("/api/session").json()["configs"][0]
        assert cfg["config_link"].startswith("https://example.invalid/")
    assert shop.catalog() == real_before
    assert not shop.store.orders()
    assert not panels["regular"].creates


def test_preview_host_is_allowed_without_embedding_rejection(client):
    response = client.get("/", headers={"Host": "8080-sandbox.e2b.app", "Origin": "https://arena.ai"})
    assert response.status_code == 200
    assert 'dir="rtl"' in response.text
    assert "x-frame-options" not in response.headers
    assert "frame-ancestors *" in response.headers["content-security-policy"]


def test_miniapp_trial_reports_delivery_failure_without_consuming_another_trial(
    client, auth, shop, telegram_bot
):
    telegram_bot.send_message.side_effect = Forbidden("bot blocked")
    response = client.post("/api/trial", headers=auth())
    assert response.status_code == 201
    assert response.json()["notified"] is False
    assert response.json()["configs"][0]["config_link"]
    assert client.post("/api/trial", headers=auth()).status_code == 409
    assert len(shop.store.user(7)["configs"]) == 1


@pytest.mark.parametrize("delivery_ok", [True, False])
def test_web_admin_approval_delivers_to_telegram_owner_and_preserves_config_on_failure(
    client, auth, shop, telegram_bot, panels, delivery_ok
):
    response = client.post("/api/orders", headers=auth(7), json={"plan_id": "regular_plus"})
    assert response.status_code == 201
    order = response.json()["order"]
    shop.submit_receipt(7, order["id"], "photo_id")
    if not delivery_ok:
        telegram_bot.send_message.side_effect = Forbidden("bot blocked")
    response = client.post(f"/api/admin/orders/{order['id']}/approve", headers=auth(1))
    assert response.json() == {"ok": True, "notified": delivery_ok}
    cfg = shop.store.user(7)["configs"][0]
    sent = telegram_bot.send_message.call_args.kwargs
    assert sent["chat_id"] == 7
    assert cfg["config_link"] in sent["text"]
    assert "email" not in panels["regular"].creates[0]
    assert client.post(f"/api/admin/orders/{order['id']}/approve", headers=auth(1)).status_code == 409
    assert len(panels["regular"].creates) == 1
    assert len(shop.store.user(7)["configs"]) == 1

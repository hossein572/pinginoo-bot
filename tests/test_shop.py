import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest

from settings import initial_catalog
from shop import Shop, ShopError, numeric
from storage import Store, active_config, parse_date


def invoice(shop, uid=7, plan="regular_plus", renewal=None):
    order = shop.new_order(uid, plan, renewal)
    return shop.submit_receipt(uid, order["id"], "telegram-photo-id")


def test_legacy_plans_keep_prices_and_identifiers(config):
    config["plans"] = {"monthly": {"name": "قدیمی", "price": 43210, "days": 30, "traffic_gb": 17}}
    catalog = initial_catalog(config)
    assert catalog["plans"]["monthly"]["price"] == 43210
    assert catalog["plans"]["monthly"]["traffic_gb"] == 17
    assert catalog["plans"]["monthly"]["category"] == "regular"
    assert any(p["category"] == "gaming" for p in catalog["plans"].values())


def test_import_legacy_users_receipts_once(config):
    root = config["data_dir"]
    user = {
        "id": 7,
        "first_name": "Legacy",
        "configs": [{"plan_name": "old", "status": "active", "expires_at": "2030-01-01T12:00:00"}],
        "created_at": "2025-01-01",
    }
    payment = {
        "id": "pay_7_123",
        "user_id": 7,
        "plan_key": "monthly",
        "price": 50000,
        "status": "pending",
        "receipt_path": str(root / "receipts" / "receipt.jpg"),
        "created_at": "2025-01-01",
    }
    users_file = root / "users.json"
    pending_file = root / "pending_payments.json"
    users_file.write_text(json.dumps({"7": user}))
    pending_file.write_text(json.dumps({"pay_7_123": payment}))
    original = users_file.read_bytes()
    store = Store(config)
    assert store.user(7)["configs"][0]["id"]
    assert store.order("pay_7_123")["status"] == "review"
    store.user(7, first_name="Updated")
    assert Store(config).user(7)["first_name"] == "Updated"
    assert users_file.read_bytes() == original
    assert pending_file.exists()


def test_default_categories_and_trial(shop):
    catalog = shop.catalog()
    assert len(catalog["plans"]) == 6
    assert {p["category"] for p in catalog["plans"].values()} == {"regular", "gaming"}
    assert catalog["trial"] == {"enabled": True, "days": 1, "traffic_gb": 1, "category": "regular"}


@pytest.mark.parametrize(
    "value,expected", [("۱۲۳٬۴۵۶", 123456), ("١٢٣,٤٥٦", 123456), ("0.5", 0.5), ("۰٫۷۵", 0.75)]
)
def test_numeric_accepts_persian_arabic_and_decimal(value, expected):
    assert numeric(value, minimum=0.1, maximum=1e9, integer=False) == expected


@pytest.mark.parametrize(
    "value", [True, False, 0, -1, "nan", "Infinity", "1e100", "۱۲x", [], {}, "", "1.001"]
)
def test_invalid_volumes_rejected(shop, value):
    with pytest.raises(ShopError):
        shop.edit_plan(1, "regular_plus", {"traffic_gb": value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("price", "0"),
        ("price", "15.5"),
        ("days", "1.5"),
        ("days", "3651"),
        ("enabled", "true"),
        ("category", "gaming"),
        ("name", "x"),
    ],
)
def test_invalid_plan_changes_do_not_persist(shop, field, value):
    before = shop.catalog()
    with pytest.raises(ShopError):
        shop.edit_plan(1, "regular_plus", {field: value})
    assert shop.catalog() == before


def test_admin_edits_survive_restart_and_leave_old_orders_intact(shop, config):
    old = shop.new_order(7, "regular_plus")
    shop.edit_plan(1, "regular_plus", {"price": "۱۸۰٬۰۰۰", "traffic_gb": "۷۵", "days": "۴۵"})
    restarted = Shop(config)
    assert restarted.catalog()["plans"]["regular_plus"]["price"] == 180000
    assert restarted.store.order(old["id"])["price"] == 149000
    assert restarted.store.order(old["id"])["traffic_gb"] == 60
    new = restarted.new_order(7, "regular_plus")
    assert new["id"] != old["id"]
    assert (new["price"], new["traffic_gb"], new["days"]) == (180000, 75, 45)


def test_disabled_plan_hidden_and_stale_buttons_rejected(shop):
    shop.edit_plan(1, "regular_plus", {"enabled": False})
    assert "regular_plus" not in shop.catalog()["plans"]
    assert "regular_plus" in shop.catalog(admin=True)["plans"]
    with pytest.raises(ShopError):
        shop.new_order(7, "regular_plus")


def test_duplicate_unpaid_order_reused(shop):
    assert shop.new_order(7, "regular_plus")["id"] == shop.new_order(7, "regular_plus")["id"]


def test_receipt_and_cancellation_enforce_ownership_and_state(shop):
    order = shop.new_order(7, "regular_plus")
    with pytest.raises(ShopError):
        shop.submit_receipt(8, order["id"], "stolen")
    with pytest.raises(ShopError):
        shop.cancel_order(8, order["id"])
    shop.submit_receipt(7, order["id"], "original")
    with pytest.raises(ShopError):
        shop.submit_receipt(7, order["id"], "again")
    with pytest.raises(ShopError):
        shop.cancel_order(7, order["id"])
    assert shop.store.order(order["id"])["receipt_file_id"] == "original"


async def test_approve_requires_receipt_and_admin(shop, panels):
    order = shop.new_order(7, "regular_plus")
    with pytest.raises(ShopError):
        await shop.approve(8, order["id"])
    with pytest.raises(ShopError):
        await shop.approve(1, order["id"])
    assert not panels["regular"].creates


async def test_gaming_order_is_provisioned_on_gaming_profile(shop, panels):
    order = invoice(shop, plan="gaming_plus")
    cfg = await shop.approve(1, order["id"])
    assert len(panels["gaming"].creates) == 1
    assert not panels["regular"].creates
    assert not panels["gaming"].extensions  # No second extension after creation.
    assert cfg["category"] == "gaming"
    assert cfg["config_link"].startswith("https://gaming.example.invalid/")
    assert panels["gaming"].creates[0]["traffic_gb"] == 50
    assert shop.store.order(order["id"])["status"] == "approved"


async def test_concurrent_approval_is_idempotent_across_store_instances(shop, config, panels):
    order = invoice(shop)
    other = Shop(config, panel_factory=lambda category, base=None: panels[category])
    results = await asyncio.gather(
        shop.approve(1, order["id"]), other.approve(1, order["id"]), return_exceptions=True
    )
    assert sum(isinstance(r, ShopError) for r in results) == 1
    assert len(panels["regular"].creates) == 1
    assert len(shop.store.user(7)["configs"]) == 1
    with pytest.raises(ShopError):
        shop.reject(1, order["id"])


async def test_definite_panel_failure_does_not_approve_or_save_phantom_config(shop, panels):
    order = invoice(shop)
    panels["regular"].login_ok = False
    with pytest.raises(ShopError) as exc:
        await shop.approve(1, order["id"])
    assert exc.value.code == "panel_unavailable"
    assert shop.store.order(order["id"])["status"] == "review"
    assert shop.store.user(7)["configs"] == []
    panels["regular"].login_ok = True
    await shop.approve(1, order["id"])
    assert shop.store.order(order["id"])["status"] == "approved"


async def test_ambiguous_panel_result_needs_review_and_cannot_be_retried(shop, panels):
    order = invoice(shop)
    panels["regular"].result = {"status": "error", "uncertain": True}
    with pytest.raises(ShopError) as exc:
        await shop.approve(1, order["id"])
    assert exc.value.code == "delivery_review"
    assert shop.store.order(order["id"])["status"] == "needs_review"
    with pytest.raises(ShopError):
        await shop.approve(1, order["id"])
    assert len(panels["regular"].creates) == 1
    assert not shop.store.user(7)["configs"]
    cfg = await shop.recover(1, order["id"], "existing_uuid")
    assert cfg["panel_uuid"] == "existing_uuid"
    assert len(panels["regular"].creates) == 1
    assert shop.store.order(order["id"])["status"] == "approved"
    with pytest.raises(ShopError):
        await shop.recover(1, order["id"], "existing_uuid")


async def test_success_without_subscription_id_never_activates(shop, panels):
    panels["regular"].result = {"status": "ok", "data": {"message": "unknown result"}}
    order = invoice(shop)
    with pytest.raises(ShopError):
        await shop.approve(1, order["id"])
    assert shop.store.order(order["id"])["status"] == "needs_review"
    assert not shop.store.user(7)["configs"]


async def test_trial_exactly_one_day_once_per_user_and_persists(shop, config, panels):
    before = datetime.now(timezone.utc)
    cfg = await shop.claim_trial(7)
    after = datetime.now(timezone.utc)
    assert before + timedelta(days=1) <= parse_date(cfg["expires_at"]) <= after + timedelta(days=1)
    assert panels["regular"].creates[0]["days"] == 1
    assert panels["regular"].creates[0]["traffic_gb"] == 1
    assert len(shop.store.orders(7)) == 0
    assert cfg["is_trial"] is True
    with pytest.raises(ShopError):
        await Shop(config, panel_factory=lambda cat, base: panels[cat]).claim_trial(7)
    assert len(panels["regular"].creates) == 1


async def test_concurrent_trial_claims_only_make_one_subscription(shop, panels):
    results = await asyncio.gather(*(shop.claim_trial(7) for _ in range(5)), return_exceptions=True)
    assert sum(isinstance(r, ShopError) for r in results) == 4
    assert len(panels["regular"].creates) == 1
    assert len(shop.store.user(7)["configs"]) == 1


async def test_failed_trial_is_not_consumed_but_uncertain_trial_is_locked(shop, panels):
    panels["regular"].login_ok = False
    with pytest.raises(ShopError):
        await shop.claim_trial(7)
    assert not shop.store.user(7)["trial_used"]
    assert shop.store.user(7)["trial_status"] == "available"
    panels["regular"].login_ok = True
    panels["regular"].result = {"status": "error", "uncertain": True}
    with pytest.raises(ShopError):
        await shop.claim_trial(7)
    with pytest.raises(ShopError):
        await shop.claim_trial(7)
    assert shop.store.user(7)["trial_status"] == "needs_review"
    assert len(panels["regular"].creates) == 1
    await shop.recover(1, "7", "trial_from_panel", trial_user=7)
    assert shop.store.user(7)["trial_used"]


async def test_admin_cannot_recover_in_flight_request(shop, panels):
    order = invoice(shop)
    shop.store.edit_order(
        order["id"],
        lambda p: p.update(status="provisioning", delivery_started_at=datetime.now(timezone.utc).isoformat()),
    )
    with pytest.raises(ShopError) as exc:
        await shop.recover(1, order["id"], "existing_uuid")
    assert exc.value.code == "delivery_pending"
    assert not panels["regular"].gets


async def test_trial_settings_and_disabled_trial(shop, panels):
    shop.edit_trial(1, {"enabled": False, "traffic_gb": "۲٫۵", "category": "gaming"})
    with pytest.raises(ShopError):
        await shop.claim_trial(7)
    assert not panels["gaming"].creates
    with pytest.raises(ShopError):
        shop.edit_trial(1, {"days": 2})
    shop.edit_trial(1, {"enabled": True})
    cfg = await shop.claim_trial(7)
    assert (cfg["traffic_gb"], cfg["days"], cfg["category"]) == (2.5, 1, "gaming")


async def test_renewal_updates_existing_subscription_and_preserves_link(shop, panels):
    cfg = await shop.claim_trial(7)
    old_expiry = parse_date(cfg["expires_at"])
    with pytest.raises(ShopError):
        shop.new_order(8, "regular_plus", cfg["id"])
    with pytest.raises(ShopError):
        shop.new_order(7, "gaming_plus", cfg["id"])
    renewal = invoice(shop, renewal=cfg["id"])
    with pytest.raises(ShopError):
        shop.new_order(7, "regular_pro", cfg["id"])
    renewed = await shop.approve(1, renewal["id"])
    assert renewed["id"] == cfg["id"]
    assert renewed["config_link"] == cfg["config_link"]
    assert parse_date(renewed["expires_at"]) == old_expiry + timedelta(days=30)
    assert len(shop.store.user(7)["configs"]) == 1
    assert len(panels["regular"].creates) == 1
    assert panels["regular"].extensions == [(cfg["panel_uuid"], 30, 60)]
    assert renewed["is_trial"] is False
    assert shop.store.user(7)["trial_used"]  # Paying to renew never re-enables the gift.


def test_naive_dates_and_actual_expiry_time():
    assert parse_date("2030-01-01T12:00:00").tzinfo == timezone.utc
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    assert active_config({"status": "active", "expires_at": future})
    assert not active_config({"status": "active", "expires_at": "invalid"})


@pytest.mark.parametrize(
    "operation",
    [
        lambda s: s.edit_plan(7, "regular_plus", {"price": 10000}),
        lambda s: s.edit_trial(7, {"enabled": False}),
        lambda s: s.admin_snapshot(7),
        lambda s: s.reject(7, "anything"),
    ],
)
def test_all_admin_service_operations_require_admin(shop, operation):
    with pytest.raises(ShopError) as exc:
        operation(shop)
    assert exc.value.status == 403

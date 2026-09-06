"""Authenticated Mini App API and static frontend; demo mode is explicitly isolated."""

import asyncio
import copy
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from telegram import Bot
from telegram.error import TelegramError
from telegram.request import HTTPXRequest

from gateway import check_membership, legacy_receipt_path, notify_delivery, notify_rejection
from settings import DEFAULT_SETTINGS, ROOT, load_settings
from shop import Shop, ShopError
from storage import now_iso
from telegram_auth import validate_init_data

logger = logging.getLogger(__name__)


class OrderInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_id: str = Field(min_length=1, max_length=64)
    renewal_id: str | None = Field(default=None, max_length=64)


class RecoveryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    panel_id: str = Field(min_length=1, max_length=128)


def seed_demo(shop):
    """Small, clearly labelled sample records, never a copy of production data."""
    with shop.store.transaction() as conn:
        if shop.store._get(conn, "meta", "demo_seeded"):
            return
        ago = (datetime.now(timezone.utc) - timedelta(days=12)).isoformat()
        config = {
            "id": "demo_config",
            "plan": "regular_plus",
            "plan_name": "پینگینو پلاس",
            "category": "regular",
            "traffic_gb": 60,
            "days": 30,
            "is_trial": False,
            "purchased_at": ago,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=18)).isoformat(),
            "status": "active",
            "panel_uuid": "demo_subscription",
            "config_link": "https://example.invalid/pinginoo-demo/sub/demo_subscription",
        }
        shop.store._put(
            conn,
            "users",
            "10001",
            {
                "id": 10001,
                "first_name": "دوست پینگینویی",
                "username": "pingino_friend",
                "email": None,
                "configs": [config],
                "trial_used": False,
                "is_active": True,
                "created_at": ago,
            },
        )
        shop.store._put(
            conn,
            "users",
            "10002",
            {
                "id": 10002,
                "first_name": "کاربر نمونه",
                "username": "demo_user",
                "email": None,
                "configs": [],
                "trial_used": False,
                "is_active": True,
                "created_at": now_iso(),
            },
        )
        common = {
            "plan_key": "regular_plus",
            "plan_name": "پینگینو پلاس",
            "category": "regular",
            "price": 149000,
            "traffic_gb": 60,
            "days": 30,
            "email": None,
            "renewal_id": None,
        }
        shop.store._put(
            conn,
            "orders",
            "ord_demo_approved",
            {
                **common,
                "id": "ord_demo_approved",
                "user_id": 10001,
                "status": "approved",
                "created_at": ago,
                "approved_at": ago,
                "config_id": "demo_config",
            },
        )
        shop.store._put(
            conn,
            "orders",
            "ord_demo_review",
            {
                **common,
                "id": "ord_demo_review",
                "user_id": 10002,
                "status": "review",
                "created_at": now_iso(),
                "receipt_file_id": "demo_receipt",
            },
        )
        shop.store._put(conn, "meta", "demo_seeded", {"at": now_iso()})


def create_app(config=None, *, demo=None, shop=None, telegram_bot=None):
    config = config or load_settings()
    demo = os.getenv("PINGINOO_DEMO", "0") == "1" if demo is None else demo
    if demo:
        directory = Path(config["data_dir"]) / "demo-data"
        config = {
            **copy.deepcopy(DEFAULT_SETTINGS),
            "data_dir": directory,
            "admin_ids": [10001],
            "card_number": "0000-0000-0000-0000",
            "card_name": "حساب نمایشی — واریز نکنید",
        }
    shop = shop or Shop(config, demo=demo)
    if demo:
        seed_demo(shop)

    @asynccontextmanager
    async def lifespan(app):
        logging.getLogger("httpx").setLevel(logging.WARNING)
        if telegram_bot is not None:
            app.state.telegram = telegram_bot
            yield
        elif config["bot_token"] and not demo:
            request = HTTPXRequest(
                proxy=config.get("proxy_url"), connect_timeout=15, read_timeout=20, connection_pool_size=32
            )
            # Bot initialization failures should not expose an ungated storefront.
            bot = Bot(config["bot_token"], request=request)
            try:
                await bot.initialize()
                app.state.telegram = bot
                shop.config["bot_username"] = bot.username
            except TelegramError:
                logger.warning("Telegram is unavailable; user endpoints remain closed")
            try:
                yield
            finally:
                await bot.shutdown()
        else:
            yield

    app = FastAPI(
        title="Pinginoo Mini App", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan
    )
    app.state.shop = shop
    app.state.telegram = telegram_bot

    @app.exception_handler(ShopError)
    async def shop_error(request, exc):
        return JSONResponse({"message": str(exc), "code": exc.code}, status_code=exc.status)

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' https://telegram.org; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; frame-ancestors *; base-uri 'self'; form-action 'self'"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    async def identity(request: Request):
        if demo:
            return {"id": 10001, "first_name": "دوست پینگینویی", "username": "pingino_friend"}
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("tma "):
            raise ShopError("فروشگاه را از دکمهٔ داخل ربات تلگرام باز کنید.", "unauthorized", 401)
        user = validate_init_data(authorization[4:], config["bot_token"], max_age=config["init_data_max_age"])
        shop.store.user(
            user["id"], first_name=user.get("first_name", "دوست من"), username=user.get("username")
        )
        return user

    async def member(request: Request, user=Depends(identity)):
        if not demo and not await check_membership(request.app.state.telegram, user["id"], config):
            raise ShopError(
                "برای استفاده از پینگینو ابتدا عضو کانال شو و بعد عضویتت را بررسی کن.",
                "membership_required",
                403,
            )
        return user

    async def admin(user=Depends(identity)):
        shop.require_admin(user["id"])
        return user

    def payment(order):
        username = shop.config.get("bot_username", "")
        return {
            "order": {
                k: order.get(k)
                for k in (
                    "id",
                    "plan_name",
                    "category",
                    "price",
                    "traffic_gb",
                    "days",
                    "status",
                    "created_at",
                    "renewal_id",
                )
            },
            "payment": {"card_number": config["card_number"], "card_name": config["card_name"]},
            "receipt_url": f"https://t.me/{username}?start=receipt_{order['id']}" if username else None,
        }

    @app.get("/api/bootstrap")
    async def bootstrap():
        return {
            "demo": demo,
            "channel_url": config["required_channel_url"],
            "channel": config["required_channel"],
            "support_username": config["support_username"],
            "bot_username": shop.config["bot_username"],
            "configured": bool(config["bot_token"]) or demo,
        }

    @app.get("/api/session")
    async def session(user=Depends(member)):
        return shop.snapshot(user["id"])

    @app.post("/api/membership/check")
    async def membership_check(user=Depends(member)):
        return {"joined": True, **shop.snapshot(user["id"])}

    @app.post("/api/orders", status_code=201)
    async def new_order(body: OrderInput, user=Depends(member)):
        return payment(shop.new_order(user["id"], body.plan_id, body.renewal_id))

    @app.get("/api/orders/{order_id}")
    async def get_order(order_id: str, user=Depends(member)):
        return payment(shop.owned_order(user["id"], order_id))

    @app.post("/api/orders/{order_id}/cancel")
    async def cancel_order(order_id: str, user=Depends(member)):
        shop.cancel_order(user["id"], order_id)
        return {"ok": True}

    @app.post("/api/trial", status_code=201)
    async def trial(request: Request, user=Depends(member)):
        cfg = await shop.claim_trial(user["id"])
        await notify_delivery(request.app.state.telegram, user["id"], cfg)
        return shop.snapshot(user["id"])

    @app.post("/api/demo/orders/{order_id}/receipt")
    async def demo_receipt(order_id: str, user=Depends(member)):
        if not demo:
            raise ShopError("مسیر پیدا نشد.", "not_found", 404)
        shop.submit_receipt(user["id"], order_id, "demo_receipt")
        return {"ok": True, "demo": True}

    @app.get("/api/admin/overview")
    async def overview(user=Depends(admin)):
        result = shop.admin_snapshot(user["id"])
        result["orders"] = [
            {
                **{k: v for k, v in p.items() if k not in {"receipt_file_id", "receipt_path", "email"}},
                "has_receipt": bool(p.get("receipt_file_id") or p.get("receipt_path")),
            }
            for p in result["orders"]
        ]
        return result

    @app.patch("/api/admin/plans/{plan_id}")
    async def edit_plan(plan_id: str, changes: dict, user=Depends(admin)):
        return shop.edit_plan(user["id"], plan_id, changes)

    @app.patch("/api/admin/trial")
    async def edit_trial(changes: dict, user=Depends(admin)):
        return shop.edit_trial(user["id"], changes)

    @app.post("/api/admin/orders/{order_id}/approve")
    async def approve_order(order_id: str, request: Request, user=Depends(admin)):
        cfg = await shop.approve(user["id"], order_id)
        order = shop.store.order(order_id)
        notified = await notify_delivery(request.app.state.telegram, order["user_id"], cfg)
        return {"ok": True, "notified": notified}

    @app.post("/api/admin/orders/{order_id}/reject")
    async def reject_order(order_id: str, request: Request, user=Depends(admin)):
        order = shop.reject(user["id"], order_id)
        await notify_rejection(request.app.state.telegram, order)
        return {"ok": True}

    @app.post("/api/admin/orders/{order_id}/recover")
    async def recover_order(order_id: str, body: RecoveryInput, request: Request, user=Depends(admin)):
        cfg = await shop.recover(user["id"], order_id, body.panel_id)
        await notify_delivery(request.app.state.telegram, shop.store.order(order_id)["user_id"], cfg)
        return {"ok": True}

    @app.post("/api/admin/users/{uid}/recover-trial")
    async def recover_trial(uid: int, body: RecoveryInput, request: Request, user=Depends(admin)):
        cfg = await shop.recover(user["id"], str(uid), body.panel_id, trial_user=uid)
        await notify_delivery(request.app.state.telegram, uid, cfg)
        return {"ok": True}

    @app.get("/api/admin/orders/{order_id}/receipt")
    async def receipt(order_id: str, request: Request, user=Depends(admin)):
        order = shop.store.order(order_id)
        if not order:
            raise ShopError("سفارش پیدا نشد.", "not_found", 404)
        if demo:
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="500"><rect width="600" height="500" rx="24" fill="#f3f0fc"/><text x="300" y="160" text-anchor="middle" fill="#7860bd" font-size="25">DEMO RECEIPT · NOT A PAYMENT</text><text x="300" y="250" text-anchor="middle" fill="#28203f" font-size="40">{order["price"]:,} TOMAN</text><text x="300" y="330" text-anchor="middle" fill="#7860bd" font-size="18">{escape(order_id)}</text></svg>'
            return Response(svg, media_type="image/svg+xml")
        if order.get("receipt_file_id") and request.app.state.telegram:
            try:
                file = await request.app.state.telegram.get_file(order["receipt_file_id"])
                content = await file.download_as_bytearray()
                return Response(bytes(content), media_type="image/jpeg")
            except TelegramError as exc:
                raise ShopError(
                    "دریافت رسید از تلگرام ممکن نشد؛ دوباره امتحان کن.", "receipt_unavailable", 503
                ) from exc
        path = await asyncio.to_thread(legacy_receipt_path, config, order)
        if path is not None:
            return FileResponse(path, media_type="image/jpeg")
        raise ShopError("تصویر رسید پیدا نشد.", "not_found", 404)

    @app.get("/health")
    async def health():
        return {"status": "ok", "demo": demo}

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(ROOT / "static" / "index.html")

    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    return app


app = create_app()

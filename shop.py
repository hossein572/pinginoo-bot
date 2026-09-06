"""Shared, transport-independent sales logic for Telegram and the Mini App."""

import copy
import logging
import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from panel_api import DemoPanel, PanelAPI
from settings import CATEGORIES
from storage import Store, active_config, now_iso, parse_date

logger = logging.getLogger(__name__)


class ShopError(Exception):
    def __init__(self, message: str, code: str = "invalid_request", status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


class DeliveryError(Exception):
    def __init__(self, uncertain=False):
        self.uncertain = uncertain


def numeric(value, *, minimum, maximum, integer=True):
    if isinstance(value, bool):
        raise ShopError("لطفاً یک عدد معتبر وارد کنید.")
    translated = str(value).strip().translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))
    translated = translated.replace(",", "").replace("٬", "").replace("٫", ".")
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", translated):
        raise ShopError("لطفاً فقط عدد مثبت وارد کنید.")
    number = float(translated)
    if not minimum <= number <= maximum or (integer and not number.is_integer()):
        raise ShopError(f"مقدار باید {'عدد صحیح ' if integer else ''}بین {minimum:,} و {maximum:,} باشد.")
    return int(number) if number.is_integer() else number


def safe_link(value: str | None) -> str | None:
    if (
        value
        and isinstance(value, str)
        and value.startswith(("https://", "http://", "vless://", "vmess://", "trojan://", "ss://"))
    ):
        return value
    return None


def subscription_data(result: dict) -> dict:
    data = result.get("data", {})
    if not isinstance(data, dict):
        return {}
    for key in ("data", "sub", "link", "subscription"):
        if isinstance(data.get(key), dict):
            return data[key]
    return data


class Shop:
    def __init__(self, config: dict, store: Store | None = None, *, demo=False, panel_factory=None):
        self.config = config
        self.store = store or Store(config, demo=demo)
        self.demo = demo
        self.panel_factory = panel_factory

    def is_admin(self, uid: int) -> bool:
        return int(uid) in self.config["admin_ids"]

    def require_admin(self, uid: int):
        if not self.is_admin(uid):
            raise ShopError("دسترسی به این بخش فقط برای ادمین است.", "forbidden", 403)

    def panel(self, category: str, base: str | None = None):
        if self.panel_factory:
            return self.panel_factory(category, base)
        if self.demo:
            return DemoPanel()
        profile = self.config.get("panel_profiles", {}).get(category, {})
        return PanelAPI(
            base or profile.get("panel_url") or self.config["panel_url"],
            profile.get("panel_password") or self.config["panel_password"],
            profile.get("protocol"),
        )

    def catalog(self, *, admin=False) -> dict:
        catalog = self.store.catalog()
        if not admin:
            catalog["plans"] = {k: p for k, p in catalog["plans"].items() if p.get("enabled", True)}
        return catalog

    def edit_plan(self, admin_id: int, plan_id: str, changes: dict) -> dict:
        self.require_admin(admin_id)
        if not changes or not set(changes) <= {"price", "traffic_gb", "days", "enabled", "name"}:
            raise ShopError("فیلد ویرایش نامعتبر است.")
        validated = {}
        for field, value in changes.items():
            if field == "price":
                validated[field] = numeric(value, minimum=1000, maximum=1_000_000_000)
            elif field == "traffic_gb":
                validated[field] = numeric(value, minimum=0.1, maximum=100_000, integer=False)
            elif field == "days":
                validated[field] = numeric(value, minimum=1, maximum=3650)
            elif field == "enabled":
                if not isinstance(value, bool):
                    raise ShopError("وضعیت پلن نامعتبر است.")
                validated[field] = value
            elif field == "name":
                if not isinstance(value, str) or not 2 <= len(value.strip()) <= 40:
                    raise ShopError("نام پلن باید بین ۲ تا ۴۰ حرف باشد.")
                validated[field] = value.strip()

        def edit(catalog):
            if plan_id not in catalog["plans"]:
                raise ShopError("پلن پیدا نشد.", "not_found", 404)
            catalog["plans"][plan_id].update(validated)
            return copy.deepcopy(catalog["plans"][plan_id])

        return self.store.edit_catalog(edit)

    def edit_trial(self, admin_id: int, changes: dict) -> dict:
        self.require_admin(admin_id)
        if not changes or not set(changes) <= {"enabled", "traffic_gb", "category"}:
            raise ShopError("تست همیشه یک‌روزه است؛ فقط وضعیت، نوع و حجم آن قابل تغییر است.")
        validated = {}
        if "traffic_gb" in changes:
            validated["traffic_gb"] = numeric(changes["traffic_gb"], minimum=0.1, maximum=1000, integer=False)
        if "enabled" in changes:
            if not isinstance(changes["enabled"], bool):
                raise ShopError("وضعیت تست نامعتبر است.")
            validated["enabled"] = changes["enabled"]
        if "category" in changes:
            if changes["category"] not in CATEGORIES:
                raise ShopError("نوع کانفیگ نامعتبر است.")
            validated["category"] = changes["category"]

        def edit(catalog):
            catalog["trial"].update(validated, days=1)
            return copy.deepcopy(catalog["trial"])

        return self.store.edit_catalog(edit)

    def new_order(self, uid: int, plan_id: str, renewal_id=None):
        if not self.demo and (not self.config.get("card_number") or not self.config.get("admin_ids")):
            raise ShopError(
                "خرید هنوز توسط مدیر فعال نشده است؛ با پشتیبانی تماس بگیرید.", "payment_unavailable", 503
            )
        try:
            return self.store.create_order(uid, plan_id, renewal_id)
        except ValueError as exc:
            raise ShopError(str(exc)) from exc

    def owned_order(self, uid: int, order_id: str) -> dict:
        order = self.store.order(order_id)
        if not order or order["user_id"] != uid:
            raise ShopError("سفارش پیدا نشد.", "not_found", 404)
        return order

    def cancel_order(self, uid: int, order_id: str):
        self.owned_order(uid, order_id)

        def edit(order):
            if order["status"] != "awaiting_receipt":
                raise ShopError("فقط سفارش بدون رسید قابل لغو است.")
            order.update(status="cancelled", cancelled_at=now_iso())

        self.store.edit_order(order_id, edit)

    def submit_receipt(self, uid: int, order_id: str, file_id: str):
        self.owned_order(uid, order_id)

        def edit(order):
            if order["status"] != "awaiting_receipt":
                raise ShopError("این رسید قبلاً ثبت یا سفارش بسته شده است.", "already_processed", 409)
            order.update(status="review", receipt_file_id=file_id, receipt_at=now_iso())
            return copy.deepcopy(order)

        return self.store.edit_order(order_id, edit)

    def reject(self, admin_id: int, order_id: str):
        self.require_admin(admin_id)
        if not self.store.order(order_id):
            raise ShopError("سفارش پیدا نشد.", "not_found", 404)

        def edit(order):
            if order["status"] != "review":
                raise ShopError("فقط رسید در انتظار بررسی قابل رد است.", "already_processed", 409)
            order.update(status="rejected", rejected_at=now_iso(), rejected_by=admin_id)
            return copy.deepcopy(order)

        return self.store.edit_order(order_id, edit)

    async def _create(self, uid: int, terms: dict, reference: str, *, trial=False) -> dict:
        client = self.panel(terms["category"])
        if not await client.ensure_logged_in():
            raise DeliveryError()
        # Telegram user/order IDs identify the subscription; no email is needed,
        # including when fulfilling an invoice imported from the old JSON store.
        result = await client.create_link(
            traffic_gb=terms["traffic_gb"],
            days=terms["days"],
            label=f"{'trial' if trial else terms['category']}_{uid}_{reference}",
        )
        if result.get("status") != "ok":
            raise DeliveryError(result.get("uncertain", False))
        data = subscription_data(result)
        panel_id = data.get("uuid") or data.get("id") or data.get("uid")
        if not panel_id:
            raise DeliveryError(True)
        link = safe_link(
            data.get("subscription_url") or data.get("sub_url") or data.get("url")
        ) or await client.get_sub_link(str(panel_id))
        return self._config(terms, panel_id, link, client.base, trial=trial)

    @staticmethod
    def _config(terms, panel_id, link, base, *, trial=False):
        started = (
            parse_date(terms["delivery_started_at"])
            if terms.get("delivery_started_at")
            else datetime.now(timezone.utc)
        )
        return {
            "id": uuid4().hex[:12],
            "plan": terms.get("plan_key", "trial"),
            "plan_name": terms.get("plan_name", "تست یک‌روزه پینگینو"),
            "category": terms["category"],
            "traffic_gb": terms["traffic_gb"],
            "days": terms["days"],
            "purchased_at": started.isoformat(),
            "expires_at": (started + timedelta(days=terms["days"])).isoformat(),
            "status": "active",
            "panel_uuid": str(panel_id),
            "panel_base": base,
            "config_link": link,
            "is_trial": trial,
        }

    async def claim_trial(self, uid: int):
        terms = self.catalog()["trial"]
        if not terms["enabled"]:
            raise ShopError("تست رایگان موقتاً غیرفعال است.", "trial_disabled", 409)
        reference = uuid4().hex[:12]

        def claim(user):
            if user.get("trial_used") or any(c.get("is_trial") for c in user["configs"]):
                raise ShopError("تست رایگان هر حساب فقط یک‌بار قابل دریافت است.", "trial_used", 409)
            if user.get("trial_status") in {"provisioning", "needs_review"}:
                raise ShopError(
                    "درخواست تست قبلی در حال پردازش یا بررسی است؛ دوباره کانفیگ ساخته نمی‌شود.",
                    "trial_pending",
                    409,
                )
            user.update(
                trial_status="provisioning",
                trial_reference=reference,
                trial_terms=terms,
                trial_started_at=now_iso(),
            )

        self.store.edit_user(uid, claim)
        try:
            config = await self._create(uid, terms, reference, trial=True)
        except Exception as exc:
            uncertain = not isinstance(exc, DeliveryError) or exc.uncertain
            self.store.edit_user(
                uid, lambda u: u.update(trial_status="needs_review" if uncertain else "available")
            )
            if uncertain:
                raise ShopError(
                    "پاسخ ساخت تست مشخص نیست. برای جلوگیری از ساخت تکراری، پشتیبانی باید پنل را بررسی کند.",
                    "delivery_review",
                    503,
                ) from exc
            raise ShopError(
                "پنل در دسترس نیست و تست شما مصرف نشد؛ کمی بعد دوباره امتحان کنید.", "panel_unavailable", 503
            ) from exc
        self.store.finish_trial(uid, config)
        return config

    async def approve(self, admin_id: int, order_id: str):
        self.require_admin(admin_id)
        if not self.store.order(order_id):
            raise ShopError("سفارش پیدا نشد.", "not_found", 404)

        def claim(order):
            if order["status"] != "review":
                raise ShopError("سفارش قبلاً پردازش شده یا برای تأیید آماده نیست.", "already_processed", 409)
            order.update(status="provisioning", delivery_started_at=now_iso())
            return copy.deepcopy(order)

        order = self.store.edit_order(order_id, claim)
        try:
            if order.get("renewal_id"):
                cfg = self.owned_config(order["user_id"], order["renewal_id"])
                client = self.panel(cfg.get("category", "regular"), cfg.get("panel_base"))
                if not await client.ensure_logged_in():
                    raise DeliveryError()
                result = await client.extend_link(cfg["panel_uuid"], order["days"], order["traffic_gb"])
                if result["status"] != "ok":
                    raise DeliveryError(result.get("uncertain", False))
                config = self._renewed_config(cfg, order)
            else:
                config = await self._create(order["user_id"], order, order_id)
        except Exception as exc:
            uncertain = not isinstance(exc, DeliveryError) or exc.uncertain
            self.store.edit_order(
                order_id,
                lambda p: p.update(
                    status="needs_review" if uncertain else "review",
                    delivery_error="ambiguous" if uncertain else "panel_unavailable",
                ),
            )
            if uncertain:
                raise ShopError(
                    "پاسخ پنل نامشخص است. ابتدا کانفیگ را در پنل بررسی و شناسهٔ موجود را بازیابی کنید؛ تأیید مجدد مسدود است.",
                    "delivery_review",
                    503,
                ) from exc
            raise ShopError(
                "ساخت کانفیگ انجام نشد. سفارش همچنان در صف بررسی است و قابل تلاش مجدد خواهد بود.",
                "panel_unavailable",
                503,
            ) from exc
        self.store.finish_delivery(order_id, config, admin_id)
        return config

    @staticmethod
    def _check_recovery_window(status, started_at):
        if status == "provisioning":
            try:
                elapsed = datetime.now(timezone.utc) - parse_date(started_at)
            except (TypeError, ValueError):
                elapsed = timedelta(0)
            if elapsed < timedelta(minutes=5):
                raise ShopError(
                    "درخواست هنوز در حال پردازش است. حداقل ۵ دقیقه صبر کن و سپس پنل را بررسی کن.",
                    "delivery_pending",
                    409,
                )

    @staticmethod
    def _renewed_config(cfg, order):
        expiry = max(parse_date(cfg["expires_at"]), datetime.now(timezone.utc)) + timedelta(
            days=order["days"]
        )
        cfg.update(
            plan=order["plan_key"],
            plan_name=order["plan_name"],
            traffic_gb=order["traffic_gb"],
            days=order["days"],
            expires_at=expiry.isoformat(),
            status="active",
            renewed_at=now_iso(),
            is_trial=False,
        )
        return cfg

    async def recover(self, admin_id: int, reference: str, panel_id: str, *, trial_user: int | None = None):
        """Attach an existing subscription after explicit admin reconciliation.

        This performs a GET only: it never creates/extends a subscription again.
        Admin must verify the label, user, quota and expiration on HS Panel first.
        """
        self.require_admin(admin_id)
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", panel_id):
            raise ShopError("شناسهٔ پنل معتبر نیست.")
        if trial_user is not None:
            user = self.store.user(trial_user)
            if user.get("trial_status") not in {"needs_review", "provisioning"} or user.get("trial_used"):
                raise ShopError("این تست نیاز به بازیابی ندارد.")
            self._check_recovery_window(user.get("trial_status"), user.get("trial_started_at"))
            terms = {**user["trial_terms"], "delivery_started_at": user.get("trial_started_at")}
        else:
            terms = self.store.order(reference)
            if not terms or terms["status"] not in {"needs_review", "provisioning"}:
                raise ShopError("این سفارش نیاز به بازیابی ندارد.")
            self._check_recovery_window(terms["status"], terms.get("delivery_started_at"))
        cfg = None
        if terms.get("renewal_id"):
            cfg = self.owned_config(terms["user_id"], terms["renewal_id"])
            if cfg["panel_uuid"] != panel_id:
                raise ShopError("شناسه باید متعلق به همان کانفیگ در حال تمدید باشد.")
        client = self.panel(terms["category"], cfg.get("panel_base") if cfg else None)
        if not await client.ensure_logged_in() or (await client.get_sub(panel_id))["status"] != "ok":
            raise ShopError("کانفیگ با این شناسه در پنل پیدا نشد؛ چیزی تغییر نکرد.")
        config = (
            self._renewed_config(cfg, terms)
            if cfg
            else self._config(
                terms,
                panel_id,
                await client.get_sub_link(panel_id),
                client.base,
                trial=trial_user is not None,
            )
        )
        if trial_user is not None:

            def claim(user):
                if user.get("trial_used") or user.get("trial_status") not in {"needs_review", "provisioning"}:
                    raise ShopError("تست قبلاً بازیابی شده است.", "already_processed", 409)
                user["trial_status"] = "provisioning"

            self.store.edit_user(trial_user, claim)
            self.store.finish_trial(trial_user, config)
        else:

            def claim(order):
                if order["status"] not in {"needs_review", "provisioning"}:
                    raise ShopError("سفارش قبلاً بازیابی شده است.", "already_processed", 409)
                order["status"] = "provisioning"

            self.store.edit_order(reference, claim)
            self.store.finish_delivery(reference, config, admin_id)
        return config

    def owned_config(self, uid: int, config_id: str):
        cfg = next((c for c in self.store.user(uid)["configs"] if c.get("id") == config_id), None)
        if not cfg:
            raise ShopError("کانفیگ پیدا نشد.", "not_found", 404)
        return cfg

    def snapshot(self, uid: int) -> dict:
        user = self.store.user(uid)
        configs = [
            {
                **{
                    k: c.get(k)
                    for k in (
                        "id",
                        "plan_name",
                        "category",
                        "traffic_gb",
                        "days",
                        "expires_at",
                        "config_link",
                        "is_trial",
                    )
                },
                "active": active_config(c),
                "renewable": bool(c.get("panel_uuid")),
            }
            for c in reversed(user["configs"])
        ]
        orders = [
            {
                k: p.get(k)
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
            }
            for p in self.store.orders(uid)
        ]
        return {
            "user": {k: user.get(k) for k in ("id", "first_name", "username", "trial_used", "trial_status")},
            "is_admin": self.is_admin(uid),
            "catalog": self.catalog(),
            "configs": configs,
            "orders": orders,
        }

    def admin_snapshot(self, admin_id: int) -> dict:
        self.require_admin(admin_id)
        users, orders = self.store.all("users"), self.store.orders()
        return {
            "catalog": self.catalog(admin=True),
            "stats": {
                "users": len(users),
                "active_configs": sum(active_config(c) for u in users for c in u.get("configs", [])),
                "revenue": sum(p["price"] for p in orders if p["status"] == "approved"),
                "pending": sum(p["status"] in {"review", "needs_review", "provisioning"} for p in orders),
                "trials": sum(bool(u.get("trial_used")) for u in users),
            },
            "orders": orders[:100],
            "users": [
                {
                    k: u.get(k)
                    for k in (
                        "id",
                        "first_name",
                        "username",
                        "created_at",
                        "trial_used",
                        "trial_status",
                        "trial_reference",
                    )
                }
                for u in sorted(users, key=lambda u: u["created_at"], reverse=True)[:100]
            ],
        }

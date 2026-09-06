#!/usr/bin/env python3
"""
HS Panel Telegram Bot - Config Sales Bot
Full integration with HS Panel API for config management
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest

import httpx

# ─── Config ───────────────────────────────────────────────────────────────────
BOT_DIR = Path(__file__).parent
CONFIG_FILE = BOT_DIR / "config.json"
USERS_FILE = BOT_DIR / "users.json"
PENDING_FILE = BOT_DIR / "pending_payments.json"

def load_json(path: Path, default: Any = None) -> Any:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Create default config if missing
if not CONFIG_FILE.exists():
    save_json(CONFIG_FILE, {
        "bot_token": "",
        "panel_url": "http://localhost:8000",
        "panel_password": "123456",
        "admin_ids": [],
        "welcome_message": "به ربات فروش کانفیگ HS Panel خوش آمدید!",
        "support_username": "support",
        "card_number": "6037-0000-0000-0000",
        "card_name": "نام صاحب کارت",
        "plans": {
            "monthly": {"name": "ماهانه", "price": 50000, "days": 30, "traffic_gb": 50},
            "quarterly": {"name": "سه ماهه", "price": 130000, "days": 90, "traffic_gb": 150},
            "yearly": {"name": "سالانه", "price": 450000, "days": 365, "traffic_gb": 600}
        }
    })
    print(f"Created {CONFIG_FILE} — please fill in bot_token and admin_ids!")

CONFIG = load_json(CONFIG_FILE)
USERS = load_json(USERS_FILE, {})
PENDING = load_json(PENDING_FILE, {})

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Panel API Client ──────────────────────────────────────────────────────────
class PanelAPI:
    def __init__(self):
        self.base = CONFIG["panel_url"].rstrip("/")
        self.password = CONFIG.get("panel_password", "123456")
        self._token: Optional[str] = None

    async def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    async def _req(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base}{path}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.request(
                    method, url,
                    headers=await self._headers(),
                    **kwargs
                )
                if resp.status_code in (200, 201):
                    return {"status": "ok", "data": resp.json()}
                else:
                    return {"status": "error", "code": resp.status_code, "body": resp.text[:300]}
        except Exception as e:
            logger.error(f"Panel request failed: {method} {path}: {e}")
            return {"status": "error", "detail": str(e)}

    async def login(self) -> bool:
        """Login to panel with password"""
        result = await self._req("POST", "/api/login", json={"password": self.password})
        if result.get("status") == "ok":
            data = result.get("data", {})
            self._token = data.get("token") or data.get("access_token") or ""
            return bool(self._token)
        return False

    async def ensure_logged_in(self) -> bool:
        return await self.login()

    async def create_link(self, traffic_gb: int, days: int,
                          email: str = None, label: str = None) -> Dict[str, Any]:
        """Create a subscription on the panel"""
        payload = {
            "traffic": traffic_gb * (1024 ** 3),
            "days": days,
            "name": label or f"bot_{int(datetime.now().timestamp())}",
        }
        if email:
            payload["email"] = email
        # Try /api/subs first (main endpoint), fallback to /api/links
        result = await self._req("POST", "/api/subs", json=payload)
        if result.get("status") != "ok":
            result = await self._req("POST", "/api/links", json=payload)
        return result

    async def get_sub_link(self, uuid_key: str) -> str:
        """Get subscription share link"""
        return f"{self.base}/sub/{uuid_key}"

    async def extend_link(self, uid: str, days: int, traffic_gb: int = None) -> bool:
        payload = {"days": days}
        if traffic_gb:
            payload["traffic"] = traffic_gb * (1024 ** 3)
        result = await self._req("PATCH", f"/api/subs/{uid}", json=payload)
        if result.get("status") == "ok":
            return True
        result2 = await self._req("PATCH", f"/api/links/{uid}", json=payload)
        return result2.get("status") == "ok"

    async def get_stats(self) -> Dict[str, Any]:
        result = await self._req("GET", "/stats")
        if result.get("status") == "ok":
            return result.get("data", result)
        return {}

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base}/health")
                return resp.status_code == 200
        except Exception:
            return False

panel_api = PanelAPI()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def is_admin(uid: int) -> bool:
    return str(uid) in [str(a) for a in CONFIG.get("admin_ids", [])]

def get_user(uid: int) -> Dict:
    uid_s = str(uid)
    if uid_s not in USERS:
        USERS[uid_s] = {
            "id": uid, "username": None, "first_name": None,
            "email": None, "configs": [],
            "created_at": datetime.now().isoformat(), "is_active": True
        }
        save_json(USERS_FILE, USERS)
    return USERS[uid_s]

def save_users():
    save_json(USERS_FILE, USERS)

def save_pending():
    save_json(PENDING_FILE, PENDING)

def fmt(t: int) -> str:
    return f"{t:,}"

def plan_desc(plan: Dict) -> str:
    return (f"{plan['name']} — {fmt(plan['price'])} تومان | "
            f"{plan['traffic_gb']}GB | {plan['days']} روز")

# ─── /start ───────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    logger.info(f"cmd_start from user {update.effective_user.id if update.effective_user else 'no_user'}")
    user = update.effective_user
    ud = get_user(user.id)
    ud["username"] = user.username
    ud["first_name"] = user.first_name
    save_users()

    kb = [
        [InlineKeyboardButton("🛒 خرید کانفیگ", callback_data="buy_config")],
        [InlineKeyboardButton("📦 کانفیگ‌های من", callback_data="my_configs")],
        [InlineKeyboardButton("💰 موجودی و تاریخچه", callback_data="balance")],
        [InlineKeyboardButton("ℹ️ راهنما", callback_data="help")],
    ]
    if is_admin(user.id):
        kb.append([InlineKeyboardButton("⚙️ پنل ادمین", callback_data="admin_panel")])

    txt = (f"{CONFIG['welcome_message']}\n\n"
           f"سلام {user.first_name}! 👋\n"
           f"از منوی زیر انتخاب کنید:")
    rm = InlineKeyboardMarkup(kb)

    # Always send new message, never edit
    msg = update.effective_message
    if msg:
        await msg.reply_text(txt, reply_markup=rm, parse_mode=ParseMode.HTML)
    else:
        # Fallback: use bot.send_message
        await ctx.bot.send_message(
            chat_id=user.id,
            text=txt,
            reply_markup=rm,
            parse_mode=ParseMode.HTML
        )

# ─── Callback Dispatcher ───────────────────────────────────────────────────────
async def cb_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    user = q.from_user

    # Admin-only actions
    if data.startswith(("approve_", "reject_")):
        if not is_admin(user.id):
            await q.answer("⛔ دسترسی ندارید!", show_alert=True)
            return
        pid = data.replace("approve_", "").replace("reject_", "")
        if data.startswith("approve_"):
            await do_approve(q, ctx, pid)
        else:
            await do_reject(q, ctx, pid)
        return

    # pay_ handled separately
    if data.startswith("pay_"):
        await handle_pay_callback(update, ctx)
        return

    # Route user callbacks
    dispatch = {
        "buy_config":    show_plans,
        "my_configs":    show_my_configs,
        "balance":       show_balance,
        "help":          show_help,
        "admin_panel":  admin_panel,
        "admin_stats":   admin_stats,
        "admin_users":   admin_users,
        "admin_broadcast": admin_broadcast,
        "back_main":     cmd_start,
        "cancel_purchase": do_cancel,
    }
    if data in dispatch:
        await dispatch[data](update, ctx)
        return

    if data.startswith("plan_"):
        await select_plan(q, ctx, data.replace("plan_", ""))
    elif data.startswith("get_link_"):
        await get_config_link(q, ctx, int(data.replace("get_link_", "")))
    elif data.startswith("renew_"):
        await renew_config(q, ctx, int(data.replace("renew_", "")))

# ─── Plans ─────────────────────────────────────────────────────────────────────
async def show_plans(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    plans = CONFIG.get("plans", {})
    kb = [[InlineKeyboardButton(plan_desc(p), callback_data=f"plan_{k}")]
          for k, p in plans.items()]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    txt = "📋 <b>پلن‌های موجود:</b>\nروی پلن مورد نظر ضربه بزنید."
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def select_plan(q, ctx, plan_key: str):
    plans = CONFIG.get("plans", {})
    plan = plans.get(plan_key)
    if not plan:
        await q.answer("❌ پلن یافت نشد!", show_alert=True)
        return

    ctx.user_data["pending_plan"] = plan_key
    user = get_user(q.from_user.id)

    if not user.get("email"):
        txt = (f"📧 برای خرید <b>{plan['name']}</b>، ایمیل خود را وارد کنید:\n\n"
               f"ایمیل برای ارسال لینک کانفیگ استفاده می‌شود.")
        kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="buy_config")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        ctx.user_data["awaiting_email"] = True
    else:
        await start_payment(q, ctx, plan_key, user["email"])

async def start_payment(q, ctx, plan_key: str, email: str):
    plan = CONFIG["plans"][plan_key]
    pid = f"pay_{q.from_user.id}_{int(datetime.now().timestamp())}"

    PENDING[pid] = {
        "id": pid, "user_id": q.from_user.id,
        "plan_key": plan_key, "plan_name": plan["name"],
        "price": plan["price"], "traffic_gb": plan["traffic_gb"],
        "days": plan["days"], "email": email,
        "status": "pending", "created_at": datetime.now().isoformat()
    }
    save_pending()

    card = CONFIG.get("card_number", "XXXX-XXXX-XXXX-XXXX")
    card_name = CONFIG.get("card_name", "HS Panel")

    txt = (
        f"💳 <b>پرداخت {plan['name']}</b>\n\n"
        f"💰 مبلغ: {fmt(plan['price'])} تومان\n"
        f"📦 ترافیک: {plan['traffic_gb']} گیگ\n"
        f"📅 مدت: {plan['days']} روز\n"
        f"📧 ایمیل: {email}\n\n"
        f"🆔 شناسه: <code>{pid}</code>\n\n"
        f"مبلغ را به کارت زیر واریز کنید:\n\n"
        f"💳 <b>{card}</b>\n"
        f"👤 {card_name}\n\n"
        f"سپس دکمه تأیید را بزنید."
    )
    kb = [
        [InlineKeyboardButton("✅ تأیید پرداخت", callback_data=f"pay_{pid}")],
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel_purchase")],
    ]
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def handle_pay_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    pid = q.data.replace("pay_", "")
    pay = PENDING.get(pid)
    if not pay:
        await q.answer("❌ پرداخت یافت نشد!", show_alert=True)
        return
    if pay["status"] != "pending":
        await q.answer("⏳ قبلاً پردازش شده.", show_alert=True)
        return

    ctx.user_data["awaiting_receipt"] = pid
    txt = (f"📤 عکس رسید واریز را ارسال کنید:\n\n"
           f"💰 {fmt(pay['price'])} تومان\n"
           f"🆔 {pid}")
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="buy_config")]]
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def do_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await cmd_start(update, ctx)

# ─── Text/Photo Message Handler ────────────────────────────────────────────────
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # Admin broadcast
    if ctx.user_data.get("broadcast_mode") and is_admin(update.effective_user.id):
        ctx.user_data["broadcast_mode"] = False
        sent = failed = 0
        for uid in USERS:
            try:
                await ctx.bot.copy_message(
                    chat_id=int(uid),
                    from_chat_id=update.effective_chat.id,
                    message_id=update.message.message_id
                )
                sent += 1
            except Exception:
                failed += 1
        await update.message.reply_text(f"📢 ارسال شد: ✅{sent} | ❌{failed}")
        return

    # Email input
    if ctx.user_data.get("awaiting_email"):
        email = update.message.text.strip()
        if "@" not in email or "." not in email:
            await update.message.reply_text("❌ ایمیل نامعتبر!")
            return
        ctx.user_data.pop("awaiting_email")
        user = get_user(update.effective_user.id)
        user["email"] = email
        save_users()
        plan_key = ctx.user_data.pop("pending_plan", None)
        if not plan_key:
            await update.message.reply_text("❌ خطا در خرید.")
            return

        class FakeQ:
            def __init__(self, msg):
                self.message = msg
                self.from_user = msg.from_user
            async def edit_message_text(self, txt, reply_markup=None, parse_mode=None):
                await self.message.reply_text(txt, reply_markup=reply_markup, parse_mode=parse_mode)
            async def answer(self, *a, **k): pass

        await start_payment(FakeQ(update.message), ctx, plan_key, email)
        return

    # Receipt photo
    if ctx.user_data.get("awaiting_receipt"):
        pid = ctx.user_data.pop("awaiting_receipt")
        pay = PENDING.get(pid)
        if pay and update.message.photo and pay["user_id"] == update.effective_user.id:
            photo = update.message.photo[-1]
            receipt_dir = BOT_DIR / "receipts"
            receipt_dir.mkdir(exist_ok=True)
            path = receipt_dir / f"{pid}.jpg"
            await photo.get_file().download_to_drive(str(path))
            pay["receipt_path"] = str(path)
            pay["receipt_at"] = datetime.now().isoformat()
            save_pending()

            for aid in CONFIG.get("admin_ids", []):
                try:
                    await ctx.bot.send_message(
                        chat_id=aid,
                        text=(f"🧾 رسید جدید\n"
                              f"کاربر: {pay['user_id']}\n"
                              f"پلن: {pay['plan_name']}\n"
                              f"مبلغ: {fmt(pay['price'])} تومان\n"
                              f"🆔 {pid}"),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{pid}"),
                             InlineKeyboardButton("❌ رد", callback_data=f"reject_{pid}")]
                        ])
                    )
                except Exception as e:
                    logger.error(f"Admin notify failed {aid}: {e}")

            await update.message.reply_text(
                "✅ رسید دریافت شد. پس از تأیید ادمین، کانفیگ فعال می‌شود."
            )
            return

    await cmd_start(update, ctx)

# ─── Admin: Approve / Reject ───────────────────────────────────────────────────
async def do_approve(q, ctx, pid: str):
    pay = PENDING.get(pid)
    if not pay:
        await q.edit_message_text("❌ پرداخت یافت نشد.")
        return

    pay["status"] = "approved"
    pay["approved_at"] = datetime.now().isoformat()
    pay["approved_by"] = q.from_user.id
    save_pending()

    # Create config on panel
    cfg_uuid = None
    cfg_link = None
    try:
        if await panel_api.ensure_logged_in():
            result = await panel_api.create_link(
                traffic_gb=pay["traffic_gb"],
                days=pay["days"],
                email=pay["email"],
                label=f"user_{pay['user_id']}"
            )
            if result.get("status") == "ok":
                data = result.get("data", {})
                cfg_uuid = data.get("uuid") or data.get("id") or data.get("uid")
                if cfg_uuid:
                    cfg_link = await panel_api.get_sub_link(cfg_uuid)
                    await panel_api.extend_link(cfg_uuid, pay["days"], pay["traffic_gb"])
    except Exception as e:
        logger.error(f"Config creation failed: {e}")

    # Save to user
    user = get_user(pay["user_id"])
    expires = datetime.now() + timedelta(days=pay["days"])
    cfg_info = {
        "plan": pay["plan_key"],
        "plan_name": pay["plan_name"],
        "email": pay["email"],
        "traffic_gb": pay["traffic_gb"],
        "days": pay["days"],
        "purchased_at": datetime.now().isoformat(),
        "expires_at": expires.isoformat(),
        "status": "active",
        "panel_uuid": cfg_uuid,
        "config_link": cfg_link,
    }
    user["configs"].append(cfg_info)
    save_users()

    msg = (f"✅ <b>پرداخت تأیید شد!</b>\n\n"
           f"📦 پلن: {pay['plan_name']}\n"
           f"📅 انقضا: {expires.strftime('%Y-%m-%d')}\n"
           f"📧 ایمیل: {pay['email']}\n\n"
           f"از بخش «کانفیگ‌های من» لینک را دریافت کنید.")
    try:
        await ctx.bot.send_message(chat_id=pay["user_id"], text=msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Notify user failed: {e}")

    await q.edit_message_text(f"✅ پرداخت {pid} تأیید و کانفیگ فعال شد.")

async def do_reject(q, ctx, pid: str):
    pay = PENDING.get(pid)
    if not pay:
        await q.edit_message_text("❌ پرداخت یافت نشد.")
        return
    pay["status"] = "rejected"
    pay["rejected_at"] = datetime.now().isoformat()
    save_pending()
    try:
        await ctx.bot.send_message(
            chat_id=pay["user_id"],
            text=f"❌ پرداخت {pid} رد شد. با پشتیبانی تماس بگیرید."
        )
    except Exception:
        pass
    await q.edit_message_text(f"❌ پرداخت {pid} رد شد.")

# ─── User Views ───────────────────────────────────────────────────────────────
async def show_my_configs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = get_user(q.from_user.id)
    cfgs = user.get("configs", [])

    if not cfgs:
        txt = "📭 شما کانفیگی ندارید."
        kb = [[InlineKeyboardButton("🛒 خرید", callback_data="buy_config")]]
    else:
        txt = "📦 <b>کانفیگ‌های شما:</b>\n\n"
        kb = []
        for i, cfg in enumerate(cfgs):
            exp = cfg.get("expires_at", "")[:10]
            exp_dt = datetime.fromisoformat(exp) if exp else datetime.now()
            status = "🟢" if exp_dt > datetime.now() else "🔴"
            txt += f"{i+1}. {cfg.get('plan_name','')} | {cfg.get('traffic_gb','')}GB | {exp} {status}\n"
            row = [InlineKeyboardButton(f"🔗 لینک #{i+1}", callback_data=f"get_link_{i}")]
            if exp_dt <= datetime.now():
                row.append(InlineKeyboardButton(f"🔄 تمدید #{i+1}", callback_data=f"renew_{i}"))
            kb.append(row)

    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def get_config_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE, idx: int):
    q = update.callback_query
    user = get_user(q.from_user.id)
    cfgs = user.get("configs", [])
    if idx >= len(cfgs):
        await q.answer("❌ یافت نشد!", show_alert=True)
        return

    cfg = cfgs[idx]
    link = cfg.get("config_link")
    if not link:
        uuid = cfg.get("panel_uuid")
        if uuid:
            link = f"{CONFIG['panel_url'].rstrip('/')}/sub/{uuid}"
        else:
            link = "⏳ لینک هنوز تولید نشده. با پشتیبانی تماس بگیرید."

    txt = (f"🔗 <b>لینک کانفیگ {idx+1}</b>\n\n"
           f"پلن: {cfg.get('plan_name','')}\n"
           f"انقضا: {cfg.get('expires_at','')[:10]}\n\n"
           f"🔗 {link}")
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="my_configs")]]
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def renew_config(update: Update, ctx: ContextTypes.DEFAULT_TYPE, idx: int):
    q = update.callback_query
    ctx.user_data["renew_idx"] = idx
    txt = "🔄 <b>تمدید کانفیگ</b>\nپلن مورد نظر را انتخاب کنید:"
    kb = [[InlineKeyboardButton(plan_desc(p), callback_data=f"plan_{k}")]
          for k, p in CONFIG.get("plans", {}).items()]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="my_configs")])
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def show_balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = get_user(q.from_user.id)
    pays = [p for p in PENDING.values() if p["user_id"] == q.from_user.id]

    txt = (f"💰 <b>موجودی و تاریخچه</b>\n\n"
           f"👤 {user.get('first_name','')}\n"
           f"📧 {user.get('email','تنظیم نشده')}\n\n")

    if pays:
        txt += "<b>پرداخت‌ها:</b>\n"
        for p in sorted(pays, key=lambda x: x["created_at"], reverse=True)[:10]:
            em = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(p["status"], "?")
            txt += f"{em} {p['plan_name']} | {fmt(p['price'])} تومان | {p['created_at'][:10]}\n"
    else:
        txt += "تراکنشی یافت نشد."

    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def show_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    sup = CONFIG.get("support_username", "support")
    txt = ("ℹ️ <b>راهنما</b>\n\n"
           "🛒 <b>خرید:</b> انتخاب پلن → ایمیل → پرداخت → ارسال رسید\n"
           "📦 <b>کانفیگ:</b> از بخش کانفیگ‌های من لینک بگیرید\n"
           "🔄 <b>تمدید:</b> کانفیگ منقضی‌شده را تمدید کنید\n"
           "💰 <b>تاریخچه:</b> لیست پرداخت‌ها\n\n"
           f"📞 پشتیبانی: @{sup}")
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

# ─── Admin Panel ──────────────────────────────────────────────────────────────
async def admin_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    txt = "⚙️ <b>پنل ادمین</b>\n\nعملیات:"
    kb = [
        [InlineKeyboardButton("📊 آمار", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("📢 همگانی", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ]
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def admin_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    total = len(USERS)
    active = sum(1 for u in USERS.values() if u.get("is_active"))
    cfgs = sum(len(u.get("configs", [])) for u in USERS.values())
    pending = sum(1 for p in PENDING.values() if p["status"] == "pending")
    approved = sum(1 for p in PENDING.values() if p["status"] == "approved")
    revenue = sum(p["price"] for p in PENDING.values() if p["status"] == "approved")
    panel_ok = await panel_api.health_check()
    panel_txt = "✅ آنلاین" if panel_ok else "❌ آفلاین"

    txt = (f"📊 <b>آمار ربات</b>\n\n"
           f"👥 کاربران: {total} (فعال: {active})\n"
           f"📦 کانفیگ‌ها: {cfgs}\n"
           f"⏳ در انتظار: {pending}\n"
           f"✅ تأیید شده: {approved}\n"
           f"💰 درآمد: {fmt(revenue)} تومان\n\n"
           f"🖥️ پنل: {panel_txt}")
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]]
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def admin_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    users = sorted(USERS.values(), key=lambda x: x.get("created_at", ""), reverse=True)[:20]
    txt = "👥 <b>کاربران (۲۰ کاربر آخر):</b>\n\n"
    for u in users:
        cnt = len(u.get("configs", []))
        txt += f"👤 {u.get('first_name','?')} (@{u.get('username','—')}) | ID:{u['id']} | {cnt} کانفیگ\n"
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]]
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def admin_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    ctx.user_data["broadcast_mode"] = True
    txt = "📢 <b>ارسال همگانی</b>\n\nپیام (متن/عکس/فایل) را ارسال کنید:"
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]]
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

# ─── Error Handler ─────────────────────────────────────────────────────────────
async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {ctx.error}")

# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    token = CONFIG.get("bot_token", "")
    if not token:
        print("ERROR: bot_token not set in config.json — get it from @BotFather")
        return

    proxy_url = CONFIG.get("proxy_url", None)
    connect_timeout = 30.0
    read_timeout = 30.0

    # Build HTTPX request with proxy
    http_client = HTTPXRequest(
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
        proxy=proxy_url,
    )

    app = (Application.builder()
           .token(token)
           .request(http_client)
           .build())

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(cb_handler, pattern="^(?!pay_).*$"))
    app.add_handler(CallbackQueryHandler(handle_pay_callback, pattern="^pay_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_text))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    logger.info("Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

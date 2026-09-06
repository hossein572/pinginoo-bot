#!/usr/bin/env python3
"""پینگینو — Persian Telegram storefront, membership gate and admin console."""

import asyncio
import logging
from html import escape as esc

from telegram import (
    BotCommand,
    InlineKeyboardMarkup,
    KeyboardButton,
    MenuButtonCommands,
    MenuButtonWebApp,
    ReplyKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.constants import ChatType, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from gateway import (
    button,
    check_membership,
    legacy_receipt_path,
    notify_delivery,
    notify_receipt,
    notify_rejection,
)
from settings import CATEGORIES, load_settings
from shop import Shop, ShopError
from storage import active_config, parse_date

logger = logging.getLogger(__name__)

LABELS = {
    "🌐 کانفیگ عادی": "category:regular",
    "🎮 کانفیگ گیمینگ": "category:gaming",
    "🎁 تست یک‌روزه": "trial",
    "📦 کانفیگ‌های من": "my_configs",
    "🧾 سفارش‌های من": "history",
    "💬 پشتیبانی": "support",
    "🏠 منوی اصلی": "home",
    "⚙️ پنل ادمین": "admin:home",
}
STATUS = {
    "awaiting_receipt": "منتظر رسید",
    "review": "در انتظار تأیید",
    "provisioning": "در حال فعال‌سازی",
    "needs_review": "نیازمند بررسی پنل",
    "approved": "تأیید شده",
    "rejected": "رد شده",
    "cancelled": "لغو شده",
}


def service(ctx) -> Shop:
    return ctx.application.bot_data["shop"]


def b(ctx, text, callback=None, **kwargs):
    return button(service(ctx).config, text, callback, **kwargs)


def back(ctx, target="home"):
    return [b(ctx, "‹ بازگشت به منو", target)]


async def render(update, ctx, text, rows=None):
    kwargs = {
        "parse_mode": ParseMode.HTML,
        "reply_markup": InlineKeyboardMarkup(rows) if rows else None,
        "disable_web_page_preview": True,
    }
    query = update.callback_query
    if query and query.message and query.message.text:
        try:
            await query.edit_message_text(text, **kwargs)
            return
        except BadRequest as exc:
            if "not modified" in str(exc).lower():
                return
            # Old/inaccessible messages can be replaced with a fresh menu.
    await ctx.bot.send_message(chat_id=update.effective_chat.id, text=text, **kwargs)


async def access(update, ctx, *, admin=False):
    if not update.effective_user or not update.effective_chat:
        return False
    if update.effective_chat.type != ChatType.PRIVATE:
        await update.effective_message.reply_text("🐧 برای استفاده، در گفتگوی خصوصی ربات /start را بزن.")
        return False
    # Discard any stale conversation state from the former email checkout.
    ctx.user_data.pop("awaiting_email", None)
    ctx.user_data.pop("pending_plan", None)
    shop = service(ctx)
    uid = update.effective_user.id
    shop.store.user(uid, first_name=update.effective_user.first_name, username=update.effective_user.username)
    if admin:
        shop.require_admin(uid)
        return True
    try:
        joined = await check_membership(ctx.bot, uid, shop.config)
    except ShopError as exc:
        await join_prompt(update, ctx, str(exc))
        return False
    if not joined:
        await join_prompt(update, ctx)
        return False
    return True


async def join_prompt(update, ctx, error=None):
    config = service(ctx).config
    text = (
        "🐧 <b>به پینگینو خوش اومدی!</b>\n\n"
        "برای استفاده از ربات، اول عضو کانال پینگینو شو.\n"
        "خبرها، آموزش‌ها و تازه‌ترین پلن‌ها اونجا منتظرته.\n\n"
        "<b>۱.</b> روی «عضویت در کانال» بزن.\n"
        "<b>۲.</b> بعد از عضویت، برگرد و دکمهٔ بررسی رو بزن."
    )
    if error:
        text += f"\n\n⚠️ {esc(error)}"
    await render(
        update,
        ctx,
        text,
        [
            [b(ctx, "📣 عضویت در کانال پینگینو", url=config["required_channel_url"], style="primary")],
            [b(ctx, "✅ عضو شدم؛ بررسی کن", "check_membership", style="success")],
        ],
    )


async def persistent_menu(update, ctx):
    admin = service(ctx).is_admin(update.effective_user.id)
    rows = [
        [
            KeyboardButton(
                "🌐 کانفیگ عادی", style="primary" if service(ctx).config.get("colored_buttons") else None
            ),
            KeyboardButton("🎮 کانفیگ گیمینگ"),
        ],
        [
            KeyboardButton(
                "🎁 تست یک‌روزه", style="success" if service(ctx).config.get("colored_buttons") else None
            ),
            KeyboardButton("📦 کانفیگ‌های من"),
        ],
        [KeyboardButton("🧾 سفارش‌های من"), KeyboardButton("💬 پشتیبانی")],
        [KeyboardButton("🏠 منوی اصلی")],
    ]
    if admin:
        rows[-1].append(KeyboardButton("⚙️ پنل ادمین"))
    await ctx.bot.send_message(
        chat_id=update.effective_chat.id,
        text="✨ عضویتت تأیید شد. منوی پینگینو همیشه پایین صفحه در دسترسته.",
        reply_markup=ReplyKeyboardMarkup(
            rows, resize_keyboard=True, is_persistent=True, input_field_placeholder="به دنیای خودت وصل شو…"
        ),
    )


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    payload = ctx.args[0] if ctx.args else None
    ctx.user_data.clear()
    if payload:
        ctx.user_data["start_payload"] = payload
    if not await access(update, ctx):
        return
    await persistent_menu(update, ctx)
    await resume_start(update, ctx)


async def resume_start(update, ctx):
    payload = ctx.user_data.pop("start_payload", "")
    if payload.startswith("receipt_"):
        order_id = payload.removeprefix("receipt_")
        await receipt_prompt(update, ctx, order_id)
    else:
        await show_main(update, ctx)


async def cmd_menu(update, ctx):
    if not await access(update, ctx):
        return
    ctx.user_data.clear()
    await show_main(update, ctx)


async def cmd_admin(update, ctx):
    try:
        if await access(update, ctx, admin=True):
            ctx.user_data.clear()
            await admin_route(update, ctx, "home")
    except ShopError as exc:
        await render(update, ctx, f"⛔ {esc(str(exc))}")


async def cmd_section(update, ctx):
    if not await access(update, ctx):
        return
    ctx.user_data.clear()
    command = update.message.text.split()[0].split("@")[0]
    await route(
        update,
        ctx,
        {"/trial": "trial", "/myconfigs": "my_configs", "/orders": "history", "/help": "help"}[command],
    )


async def cmd_cancel(update, ctx):
    if not await access(update, ctx):
        return
    order_id = ctx.user_data.get("awaiting_receipt") or ctx.user_data.get("active_order")
    if order_id:
        try:
            service(ctx).cancel_order(update.effective_user.id, order_id)
        except ShopError:
            pass
    ctx.user_data.clear()
    await show_main(update, ctx)


async def show_main(update, ctx):
    shop = service(ctx)
    user = shop.store.user(update.effective_user.id)
    count = sum(active_config(c) for c in user["configs"])
    rows = [
        [
            b(ctx, "🌐 کانفیگ عادی", "category:regular", style="primary"),
            b(ctx, "🎮 کانفیگ گیمینگ", "category:gaming", style="primary"),
        ],
        [b(ctx, "🎁 تست رایگان یک‌روزه", "trial", style="success")],
        [b(ctx, "📦 کانفیگ‌های من", "my_configs"), b(ctx, "🧾 سفارش‌های من", "history")],
        [b(ctx, "📖 راهنمای اتصال", "help"), b(ctx, "💬 پشتیبانی", "support")],
    ]
    if shop.config.get("webapp_url", "").startswith("https://"):
        rows.insert(
            0,
            [
                b(
                    ctx,
                    "✨ ورود به فروشگاه پینگینو",
                    web_app=WebAppInfo(shop.config["webapp_url"]),
                    style="primary",
                )
            ],
        )
    if shop.is_admin(user["id"]):
        rows.append([b(ctx, "⚙️ پنل مدیریت", "admin:home")])
    await render(
        update,
        ctx,
        f"🐧 <b>سلام {esc(user.get('first_name') or 'دوست من')}!</b>\n\n{esc(shop.config['welcome_message'])}\n\n🟢 کانفیگ فعال: <b>{count}</b>\n\nاز کجا شروع کنیم؟",
        rows,
    )


async def cb_handler(update, ctx):
    q = update.callback_query
    data = str(q.data or "")
    aliases = {
        "back_main": "home",
        "buy_config": "categories",
        "balance": "history",
        "admin_panel": "admin:home",
        "admin_stats": "admin:stats",
        "admin_users": "admin:users",
        "admin_broadcast": "admin:broadcast",
        "cancel_purchase": "home",
    }
    data = aliases.get(data, data)
    # Keep older sent keyboards usable. Remove exactly one prefix, not every
    # occurrence (legacy payment IDs themselves begin with 'pay_').
    for prefix, replacement in (
        ("approve_", "admin:approve:"),
        ("reject_", "admin:reject_confirm:"),
        ("pay_", "receipt:"),
        ("plan_", "plan:"),
    ):
        if data.startswith(prefix):
            data = replacement + data.removeprefix(prefix)
            break
    if data.startswith("admin:") and not service(ctx).is_admin(q.from_user.id):
        await q.answer("⛔ این بخش فقط برای ادمین است.", show_alert=True)
        return
    await q.answer()
    try:
        if not await access(update, ctx, admin=data.startswith("admin:")):
            return
        if data == "check_membership":
            await persistent_menu(update, ctx)
            await resume_start(update, ctx)
            return
        # Every navigation cancels stale input modes; current invoices stay in
        # order history so leaving a screen never loses a payment.
        ctx.user_data.pop("admin_input", None)
        ctx.user_data.pop("broadcast_mode", None)
        ctx.user_data.pop("awaiting_receipt", None)
        if data != "admin:broadcast_send":
            ctx.user_data.pop("broadcast_draft", None)
        if data.startswith("admin:"):
            await admin_route(update, ctx, data.removeprefix("admin:"))
        else:
            await route(update, ctx, data)
    except ShopError as exc:
        await render(
            update,
            ctx,
            f"⚠️ {esc(str(exc))}",
            [back(ctx, "admin:home" if data.startswith("admin:") else "home")],
        )


async def route(update, ctx, data):
    shop = service(ctx)
    uid = update.effective_user.id
    if data == "home":
        ctx.user_data.clear()
        await show_main(update, ctx)
    elif data == "categories":
        await render(
            update,
            ctx,
            "🛍 <b>کدوم اتصال برای توئه؟</b>\n\nپلن‌های عادی و گیمینگ، جدا و متناسب با نیازت.",
            [
                [
                    b(ctx, "🌐 عادی", "category:regular", style="primary"),
                    b(ctx, "🎮 گیمینگ", "category:gaming", style="primary"),
                ],
                back(ctx),
            ],
        )
    elif data.startswith("category:"):
        ctx.user_data.pop("renewal_id", None)
        await show_plans(update, ctx, data.split(":", 1)[1])
    elif data.startswith("plan:"):
        order = shop.new_order(uid, data.split(":", 1)[1], ctx.user_data.get("renewal_id"))
        await show_payment(update, ctx, order)
    elif data.startswith("receipt:"):
        await receipt_prompt(update, ctx, data.split(":", 1)[1])
    elif data.startswith("order:"):
        await show_payment(update, ctx, shop.owned_order(uid, data.split(":", 1)[1]))
    elif data.startswith("cancel:"):
        shop.cancel_order(uid, data.split(":", 1)[1])
        ctx.user_data.clear()
        await render(update, ctx, "سفارش لغو شد. هر وقت خواستی دوباره انتخاب کن 🌱", [back(ctx)])
    elif data == "trial":
        trial = shop.catalog()["trial"]
        user = shop.store.user(uid)
        if user.get("trial_used"):
            await render(
                update,
                ctx,
                "🎁 تست رایگان این حساب قبلاً دریافت شده. لینک تست در «کانفیگ‌های من» باقی می‌ماند.",
                [[b(ctx, "📦 کانفیگ‌های من", "my_configs")], back(ctx)],
            )
        elif not trial["enabled"]:
            await render(update, ctx, "تست رایگان فعلاً غیرفعال است. بعداً سر بزن 🌱", [back(ctx)])
        else:
            await render(
                update,
                ctx,
                f"🎁 <b>اول امتحان کن، بعد انتخاب کن.</b>\n\n⏱ اعتبار: <b>۲۴ ساعت</b> از زمان فعال‌سازی\n📦 حجم: <b>{trial['traffic_gb']} گیگابایت</b>\n💚 کاملاً رایگان، بدون پرداخت\n\nهر حساب تلگرام فقط یک‌بار می‌تواند تست بگیرد.",
                [[b(ctx, "✨ دریافت تست یک‌روزه", "claim_trial", style="success")], back(ctx)],
            )
    elif data == "claim_trial":
        await render(update, ctx, "⏳ داریم تستت رو آماده می‌کنیم…")
        config = await shop.claim_trial(uid)
        if await notify_delivery(ctx.bot, uid, config):
            await render(
                update,
                ctx,
                "✅ تستت آماده شد؛ لینک کانفیگ در یک پیام جدا همین‌جا در تلگرام ارسال شد.",
                [[b(ctx, "📦 مشاهدهٔ کانفیگ تست", f"config:{config['id']}")], back(ctx)],
            )
        else:
            # If sending a fresh message fails, try the existing message. The
            # saved config also remains accessible through /myconfigs.
            await config_view(update, ctx, config)
    elif data == "my_configs":
        await show_my_configs(update, ctx)
    elif data.startswith(("config:", "renew:")):
        action, config_id = data.split(":", 1)
        cfg = shop.owned_config(uid, config_id)
        if action == "config":
            await config_view(update, ctx, cfg)
        else:
            ctx.user_data["renewal_id"] = config_id
            await show_plans(update, ctx, cfg.get("category", "regular"), renewal=True)
    elif data.startswith(("get_link_", "renew_")):
        prefix = "get_link_" if data.startswith("get_link_") else "renew_"
        index = data.removeprefix(prefix)
        cfgs = shop.store.user(uid)["configs"]
        if not index.isdigit() or not 0 <= int(index) < len(cfgs):
            raise ShopError("کانفیگ پیدا نشد.")
        await route(update, ctx, f"{'config' if prefix == 'get_link_' else 'renew'}:{cfgs[int(index)]['id']}")
    elif data == "history":
        orders = shop.store.orders(uid)[:10]
        text = "🧾 <b>سفارش‌های من</b>\n\n" + (
            "هنوز سفارشی ثبت نکردی. اولین اتصال از همین‌جا شروع می‌شه."
            if not orders
            else "۱۰ سفارش آخر؛ برای جزئیات یا ارسال رسید روی سفارش بزن."
        )
        rows = [
            [
                b(
                    ctx,
                    f"{p['plan_name']} · {p['price']:,} ت · {STATUS.get(p['status'], p['status'])}",
                    f"order:{p['id']}",
                )
            ]
            for p in orders
        ]
        await render(update, ctx, text, rows + [back(ctx)])
    elif data == "help":
        await render(
            update,
            ctx,
            "📖 <b>چند قدم تا اتصال</b>\n\n<b>۱. انتخاب</b>\nکانفیگ عادی یا گیمینگ را انتخاب کن؛ قبل از خرید می‌تونی تست یک‌روزه بگیری.\n\n<b>۲. پرداخت</b>\nمبلغ دقیق فاکتور را واریز و عکس رسید را در ربات ارسال کن. فعال‌سازی پس از تأیید ادمین انجام می‌شود.\n\n<b>۳. اتصال</b>\nلینک را از «کانفیگ‌های من» کپی کن. در برنامهٔ سازگار مثل v2rayNG (اندروید)، Hiddify یا Streisand (iOS)، افزودن اشتراک از کلیپ‌بورد را بزن و اشتراک را به‌روز کن.\n\n<b>۴. تمدید</b>\nاز همان کانفیگ دکمهٔ تمدید را بزن؛ لینک قبلی حفظ می‌شود.\n\nکیفیت اتصال و پینگ به اینترنت و مسیر سرور وابسته است. لینک اشتراکت را برای دیگران نفرست.",
            [[b(ctx, "💬 کمک می‌خوام", "support")], back(ctx)],
        )
    elif data == "support":
        username = shop.config.get("support_username")
        rows = (
            [[b(ctx, "💬 گفتگو با پشتیبانی", url=f"https://t.me/{username}", style="primary")]]
            if username
            else []
        )
        await render(
            update,
            ctx,
            "💬 <b>کنارت هستیم.</b>\n\nبرای پیگیری، شناسهٔ سفارش و توضیح مشکل را بفرست؛ هرگز رمز یا اطلاعات کامل کارت را ارسال نکن.\n\n"
            + (
                f"پشتیبانی: @{esc(username)}"
                if username
                else "آدرس پشتیبانی هنوز توسط مدیر ثبت نشده؛ اطلاعیه‌های کانال را بررسی کن."
            ),
            rows + [[b(ctx, "📣 کانال پینگینو", url=shop.config["required_channel_url"])], back(ctx)],
        )
    else:
        await show_main(update, ctx)


async def show_plans(update, ctx, category, renewal=False):
    if category not in CATEGORIES:
        raise ShopError("نوع کانفیگ نامعتبر است.")
    info = CATEGORIES[category]
    plans = {k: p for k, p in service(ctx).catalog()["plans"].items() if p["category"] == category}
    text = f"{info['emoji']} <b>{'تمدید ' if renewal else ''}{info['name']}</b>\n\n{info['description']}\n\n"
    rows = []
    for key, plan in plans.items():
        text += f"{'⭐' if plan.get('featured') else '▫️'} <b>{esc(plan['name'])}</b>\n{plan['traffic_gb']} گیگ · {plan['days']} روز · <b>{plan['price']:,} تومان</b>\n\n"
        rows.append(
            [
                b(
                    ctx,
                    f"انتخاب {plan['name']} · {plan['price']:,} ت",
                    f"plan:{key}",
                    style="primary" if plan.get("featured") else None,
                )
            ]
        )
    if not plans:
        text += "پلن فعالی در این بخش نداریم؛ کمی بعد سر بزن."
    if category == "gaming":
        text += "پینگ به مسیر سرور و اینترنت شما وابسته است؛ قبل از خرید، راهنمای پشتیبانی را ببین."
    await render(update, ctx, text, rows + [back(ctx, "my_configs" if renewal else "home")])


async def show_payment(update, ctx, order):
    service(ctx).owned_order(update.effective_user.id, order["id"])
    config = service(ctx).config
    text = (
        f"🧾 <b>{esc(order['plan_name'])}</b>\n\n"
        f"💰 مبلغ: <b>{order['price']:,} تومان</b>\n"
        f"📦 حجم: {order['traffic_gb']} گیگ · مدت: {order['days']} روز\n"
        f"شناسه: <code>{esc(order['id'])}</code>\n"
        f"وضعیت: {STATUS.get(order['status'], 'در حال بررسی')}\n\n"
    )
    rows = []
    if order["status"] == "awaiting_receipt":
        ctx.user_data["active_order"] = order["id"]
        text += f"مبلغ را به کارت زیر واریز کن:\n<code>{esc(config.get('card_number', ''))}</code>\nبه نام: {esc(config.get('card_name', ''))}\n\nبعد عکس رسید را ارسال کن. سفارش تنها پس از بررسی ادمین فعال می‌شود.\nلینک کانفیگ مستقیماً همین‌جا در تلگرام برایت ارسال می‌شود."
        rows = [
            [b(ctx, "📤 ارسال عکس رسید", f"receipt:{order['id']}", style="success")],
            [b(ctx, "لغو سفارش", f"cancel:{order['id']}", style="danger")],
        ]
    elif order["status"] == "approved":
        rows = [[b(ctx, "📦 دریافت کانفیگ", "my_configs", style="success")]]
    else:
        text += "وضعیت سفارشت از همین بخش قابل پیگیریه."
        rows = [[b(ctx, "💬 پشتیبانی", "support")]]
    await render(update, ctx, text, rows + [back(ctx, "history")])


async def receipt_prompt(update, ctx, order_id):
    order = service(ctx).owned_order(update.effective_user.id, order_id)
    if order["status"] != "awaiting_receipt":
        await show_payment(update, ctx, order)
        return
    ctx.user_data["awaiting_receipt"] = order_id
    await render(
        update,
        ctx,
        f"📤 <b>عکس رسید را همین‌جا بفرست</b>\n\nمبلغ: {order['price']:,} تومان\nسفارش: <code>{esc(order_id)}</code>\n\nعکس واضح باشد و مبلغ و زمان واریز دیده شود. اطلاعات حساس کارت را بپوشان.",
        [[b(ctx, "لغو سفارش", f"cancel:{order_id}", style="danger")], back(ctx, "history")],
    )


async def show_my_configs(update, ctx):
    configs = service(ctx).store.user(update.effective_user.id)["configs"]
    rows = []
    text = "📦 <b>اتصال‌های من</b>\n\n"
    for cfg in reversed(configs[-15:]):
        active = active_config(cfg)
        text += f"{'🟢' if active else '⚪'} {esc(cfg.get('plan_name', 'کانفیگ'))} · {cfg.get('traffic_gb', 0)} گیگ\n"
        rows.append(
            [
                b(
                    ctx,
                    f"🔗 {cfg.get('plan_name', 'کانفیگ')} · {'فعال' if active else 'منقضی'}",
                    f"config:{cfg['id']}",
                )
            ]
        )
    if not configs:
        text += "هنوز کانفیگی نداری؛ با یک تست رایگان شروع کن 🌱"
        rows.append([b(ctx, "🎁 تست یک‌روزه", "trial", style="success")])
    await render(update, ctx, text, rows + [back(ctx)])


async def config_view(update, ctx, cfg):
    expiry = parse_date(cfg["expires_at"]).strftime("%Y-%m-%d %H:%M UTC") if cfg.get("expires_at") else "—"
    text = f"🐧 <b>{esc(cfg.get('plan_name', 'کانفیگ'))}</b>\n\n📦 {cfg.get('traffic_gb', 0)} گیگ\n⏳ انقضا: {expiry}\n\n"
    if cfg.get("config_link"):
        text += f"<code>{esc(cfg['config_link'])}</code>\n\nروی لینک بزن تا کپی بشه؛ بعد در برنامهٔ اتصال واردش کن."
    else:
        text += "لینک هنوز در دسترس نیست؛ برای بررسی با پشتیبانی تماس بگیر."
    rows = [[b(ctx, "📖 راهنمای اتصال", "help")]]
    if cfg.get("panel_uuid"):
        rows.append([b(ctx, "🔄 تمدید همین کانفیگ", f"renew:{cfg['id']}", style="primary")])
    await render(update, ctx, text, rows + [back(ctx, "my_configs")])


async def admin_route(update, ctx, data):
    shop = service(ctx)
    uid = update.effective_user.id
    shop.require_admin(uid)
    parts = data.split(":")
    action = parts[0]
    if action in {"home", "stats"}:
        stats = shop.admin_snapshot(uid)["stats"]
        text = (
            "⚙️ <b>مدیریت پینگینو</b>\n\n"
            f"👥 کاربران: {stats['users']}\n🟢 کانفیگ فعال: {stats['active_configs']}\n"
            f"🧾 در انتظار بررسی: {stats['pending']}\n🎁 تست تحویل‌شده: {stats['trials']}\n"
            f"💰 فروش تأییدشده: {stats['revenue']:,} تومان\n\nقیمت و حجم جدید فقط روی سفارش‌های بعدی اعمال می‌شود."
        )
        rows = [
            [b(ctx, "💎 قیمت و حجم پلن‌ها", "admin:plans", style="primary")],
            [b(ctx, "🧾 بررسی رسیدها", "admin:orders"), b(ctx, "🎁 تنظیمات تست", "admin:trial")],
            [b(ctx, "👥 کاربران", "admin:users"), b(ctx, "📢 ارسال همگانی", "admin:broadcast")],
        ]
        if shop.config.get("webapp_url", "").startswith("https://"):
            rows.append(
                [
                    b(
                        ctx,
                        "✨ داشبورد وب مدیریت",
                        web_app=WebAppInfo(shop.config["webapp_url"].split("#")[0] + "#admin"),
                    )
                ]
            )
        await render(update, ctx, text, rows + [back(ctx)])
    elif action == "plans":
        rows = [
            [
                b(
                    ctx,
                    f"{CATEGORIES.get(p['category'], CATEGORIES['regular'])['emoji']} {p['name']} · {p['price']:,} ت · {p['traffic_gb']} GB {'⏸' if not p['enabled'] else ''}",
                    f"admin:plan:{k}",
                )
            ]
            for k, p in shop.catalog(admin=True)["plans"].items()
        ]
        await render(
            update,
            ctx,
            "💎 <b>مدیریت پلن‌ها</b>\n\nبرای ویرایش قیمت، حجم، مدت یا وضعیت روی پلن بزن.",
            rows + [back(ctx, "admin:home")],
        )
    elif action == "plan" and len(parts) == 2:
        key = parts[1]
        p = shop.catalog(admin=True)["plans"].get(key)
        if not p:
            raise ShopError("پلن پیدا نشد.")
        rows = [
            [
                b(ctx, "💰 تغییر قیمت", f"admin:edit:{key}:price", style="primary"),
                b(ctx, "📦 تغییر حجم", f"admin:edit:{key}:traffic_gb"),
            ],
            [
                b(ctx, "📅 تغییر مدت", f"admin:edit:{key}:days"),
                b(ctx, "✏️ تغییر نام", f"admin:edit:{key}:name"),
            ],
            [
                b(
                    ctx,
                    "غیرفعال کردن" if p["enabled"] else "فعال کردن",
                    f"admin:toggle:{key}",
                    style="danger" if p["enabled"] else "success",
                )
            ],
            back(ctx, "admin:plans"),
        ]
        await render(
            update,
            ctx,
            f"💎 <b>{esc(p['name'])}</b>\n\nقیمت: {p['price']:,} تومان\nحجم: {p['traffic_gb']} گیگ\nمدت: {p['days']} روز\nوضعیت: {'فعال' if p['enabled'] else 'غیرفعال'}",
            rows,
        )
    elif action == "toggle" and len(parts) == 2:
        p = shop.catalog(admin=True)["plans"].get(parts[1])
        if not p:
            raise ShopError("پلن پیدا نشد.")
        shop.edit_plan(uid, parts[1], {"enabled": not p["enabled"]})
        await admin_route(update, ctx, "plan:" + parts[1])
    elif action == "edit" and len(parts) == 3:
        _, key, field = parts
        names = {
            "price": "قیمت جدید به تومان (حداقل ۱۰۰۰)",
            "traffic_gb": "حجم جدید به گیگابایت (حداقل ۰٫۱)",
            "days": "مدت جدید به روز (۱ تا ۳۶۵۰)",
            "name": "نام جدید (۲ تا ۴۰ حرف)",
        }
        if field not in names or key not in shop.catalog(admin=True)["plans"]:
            raise ShopError("ویرایش نامعتبر است.")
        ctx.user_data["admin_input"] = {"type": "plan", "key": key, "field": field}
        await render(
            update,
            ctx,
            f"✏️ <b>{names[field]}</b> را بفرست.\n\nاعداد فارسی و انگلیسی پذیرفته می‌شوند. برای انصراف /cancel را بزن.",
            [back(ctx, "admin:plan:" + key)],
        )
    elif action == "trial":
        t = shop.catalog(admin=True)["trial"]
        await render(
            update,
            ctx,
            f"🎁 <b>تنظیمات تست</b>\n\nاعتبار: همیشه ۲۴ ساعت\nحجم: {t['traffic_gb']} گیگ\nنوع: {CATEGORIES[t['category']]['name']}\nوضعیت: {'فعال' if t['enabled'] else 'غیرفعال'}\n\nهر حساب یک‌بار؛ دریافت‌های قبلی با تغییر تنظیمات ریست نمی‌شوند.",
            [
                [b(ctx, "📦 تغییر حجم تست", "admin:trial_volume", style="primary")],
                [
                    b(
                        ctx,
                        "غیرفعال کردن" if t["enabled"] else "فعال کردن",
                        "admin:trial_toggle",
                        style="danger" if t["enabled"] else "success",
                    ),
                    b(ctx, "تغییر نوع کانفیگ", "admin:trial_category"),
                ],
                back(ctx, "admin:home"),
            ],
        )
    elif action == "trial_volume":
        ctx.user_data["admin_input"] = {"type": "trial"}
        await render(
            update, ctx, "📦 حجم تست را به گیگابایت وارد کن (۰٫۱ تا ۱۰۰۰):", [back(ctx, "admin:trial")]
        )
    elif action in {"trial_toggle", "trial_category"}:
        t = shop.catalog(admin=True)["trial"]
        shop.edit_trial(
            uid,
            {"enabled": not t["enabled"]}
            if action == "trial_toggle"
            else {"category": "gaming" if t["category"] == "regular" else "regular"},
        )
        await admin_route(update, ctx, "trial")
    elif action == "orders":
        orders = [
            p for p in shop.store.orders() if p["status"] in {"review", "provisioning", "needs_review"}
        ][:20]
        rows = [
            [b(ctx, f"{p['user_id']} · {p['price']:,} ت · {STATUS[p['status']]}", f"admin:order:{p['id']}")]
            for p in orders
        ]
        await render(
            update,
            ctx,
            "🧾 <b>صف بررسی رسیدها</b>\n\n"
            + (
                "سفارشی در صف نیست. همه‌چیز مرتبه ✨"
                if not orders
                else "۲۰ درخواست اخیر؛ رسید را قبل از تأیید حتماً ببین."
            ),
            rows + [back(ctx, "admin:home")],
        )
    elif action == "order" and len(parts) == 2:
        order = shop.store.order(parts[1])
        if not order:
            raise ShopError("سفارش پیدا نشد.")
        rows = []
        if order.get("receipt_file_id") or order.get("receipt_path"):
            rows.append([b(ctx, "🧾 مشاهدهٔ تصویر رسید", f"admin:receipt:{order['id']}")])
        if order["status"] == "review":
            rows.append(
                [
                    b(ctx, "✅ تأیید و ساخت", f"admin:approve:{order['id']}", style="success"),
                    b(ctx, "رد رسید", f"admin:reject_confirm:{order['id']}", style="danger"),
                ]
            )
        elif order["status"] in {"needs_review", "provisioning"}:
            rows.append([b(ctx, "🔧 بازیابی کانفیگ موجود", f"admin:recover:{order['id']}")])
        await render(
            update,
            ctx,
            f"🧾 <b>{esc(order['plan_name'])}</b>\n\nکاربر: <code>{order['user_id']}</code>\nمبلغ: {order['price']:,} تومان\nحجم: {order['traffic_gb']} گیگ · {order['days']} روز\nشناسه: <code>{esc(order['id'])}</code>\nوضعیت: {STATUS.get(order['status'], order['status'])}",
            rows + [back(ctx, "admin:orders")],
        )
    elif action == "receipt" and len(parts) == 2:
        order = shop.store.order(parts[1])
        if not order:
            raise ShopError("سفارش پیدا نشد.")
        if order.get("receipt_file_id"):
            await ctx.bot.send_photo(
                chat_id=uid, photo=order["receipt_file_id"], caption=f"رسید {order['id']}"
            )
        elif order.get("receipt_path"):
            # Imported local receipts must remain inside the configured data directory.
            path = await asyncio.to_thread(legacy_receipt_path, shop.config, order)
            if path is None:
                raise ShopError("فایل رسید قدیمی در دسترس نیست.")
            content = await asyncio.to_thread(path.read_bytes)
            await ctx.bot.send_photo(chat_id=uid, photo=content, caption=f"رسید {order['id']}")
        else:
            raise ShopError("تصویر رسید ثبت نشده است.")
    elif action == "approve" and len(parts) == 2:
        cfg = await shop.approve(uid, parts[1])
        order = shop.store.order(parts[1])
        delivered = await notify_delivery(ctx.bot, order["user_id"], cfg)
        await render(
            update,
            ctx,
            "✅ سفارش تأیید و کانفیگ ذخیره شد."
            + (
                "\nپیام برای کاربر ارسال شد."
                if delivered
                else "\nارسال پیام ممکن نشد؛ لینک در «کانفیگ‌های من» کاربر موجود است."
            ),
            [back(ctx, "admin:orders")],
        )
    elif action == "reject_confirm" and len(parts) == 2:
        await render(
            update,
            ctx,
            "این رسید رد شود؟ این کار فقط سفارش در انتظار بررسی را می‌بندد.",
            [
                [b(ctx, "بله، رد رسید", f"admin:reject:{parts[1]}", style="danger")],
                back(ctx, "admin:order:" + parts[1]),
            ],
        )
    elif action == "reject" and len(parts) == 2:
        order = shop.reject(uid, parts[1])
        await notify_rejection(ctx.bot, order)
        await render(update, ctx, "رسید رد شد و وضعیت سفارش به‌روز شد.", [back(ctx, "admin:orders")])
    elif action in {"recover", "recover_trial"} and len(parts) == 2:
        ctx.user_data["admin_input"] = {
            "type": "recover",
            "reference": parts[1],
            "trial": action == "recover_trial",
        }
        await render(
            update,
            ctx,
            "🔧 <b>بازیابی بدون ساخت مجدد</b>\n\nابتدا در HS Panel برچسب کاربر/سفارش، حجم و تاریخ انقضا را بررسی کن. سپس UUID کانفیگ موجود را بفرست.\n\nاین کار فقط لینک موجود را ثبت می‌کند و درخواست ساخت یا تمدید نمی‌فرستد. درخواست در حال پردازش تا ۵ دقیقه قابل بازیابی نیست.",
            [back(ctx, "admin:home")],
        )
    elif action == "users":
        users = shop.admin_snapshot(uid)["users"][:20]
        text = "👥 <b>۲۰ کاربر آخر</b>\n\n"
        rows = []
        for u in users:
            text += f"▫️ {esc(u.get('first_name') or 'بدون نام')} · <code>{u['id']}</code>\n"
            if u.get("trial_status") in {"needs_review", "provisioning"}:
                rows.append([b(ctx, f"🔧 بازیابی تست {u['id']}", f"admin:recover_trial:{u['id']}")])
        await render(update, ctx, text, rows + [back(ctx, "admin:home")])
    elif action == "broadcast":
        ctx.user_data["broadcast_mode"] = "compose"
        await render(
            update,
            ctx,
            "📢 <b>ارسال همگانی</b>\n\nپیام (متن، عکس یا فایل) را بفرست. قبل از ارسال برای همه، تأیید نهایی می‌گیریم.",
            [back(ctx, "admin:home")],
        )
    elif action == "broadcast_send":
        source = ctx.user_data.pop("broadcast_draft", None)
        if not source:
            raise ShopError("پیش‌نویس پیدا نشد؛ پیام را دوباره آماده کن.")
        sent = failed = 0
        for user in shop.store.all("users"):
            try:
                await ctx.bot.copy_message(chat_id=user["id"], from_chat_id=uid, message_id=source)
                sent += 1
            except TelegramError:
                failed += 1
        await render(
            update, ctx, f"📢 ارسال تمام شد.\n✅ موفق: {sent}\n❌ ناموفق: {failed}", [back(ctx, "admin:home")]
        )
    else:
        raise ShopError("دکمه قدیمی یا نامعتبر است؛ منو را دوباره باز کن.")


async def handle_message(update, ctx):
    text = update.effective_message.text or ""
    shop = service(ctx)
    admin_mode = text == "⚙️ پنل ادمین" or bool(
        ctx.user_data.get("admin_input") or ctx.user_data.get("broadcast_mode")
    )
    try:
        if not await access(update, ctx, admin=admin_mode):
            return
        if text in LABELS:
            ctx.user_data.clear()
            destination = LABELS[text]
            if destination.startswith("admin:"):
                await admin_route(update, ctx, "home")
            else:
                # A menu button leaving admin mode must still enforce membership.
                if admin_mode and not await access(update, ctx):
                    return
                await route(update, ctx, destination)
            return
        if ctx.user_data.get("broadcast_mode") == "compose":
            shop.require_admin(update.effective_user.id)
            ctx.user_data.pop("broadcast_mode")
            ctx.user_data["broadcast_draft"] = update.effective_message.message_id
            count = len(shop.store.all("users"))
            await render(
                update,
                ctx,
                f"پیام بالا برای {count} کاربر ارسال شود؟",
                [
                    [b(ctx, "📢 تأیید و ارسال", "admin:broadcast_send", style="primary")],
                    back(ctx, "admin:home"),
                ],
            )
            return
        admin_input = ctx.user_data.get("admin_input")
        if admin_input:
            shop.require_admin(update.effective_user.id)
            if not text:
                raise ShopError("لطفاً مقدار را به صورت متن بفرست.")
            if admin_input["type"] == "plan":
                shop.edit_plan(update.effective_user.id, admin_input["key"], {admin_input["field"]: text})
                target = "plan:" + admin_input["key"]
            elif admin_input["type"] == "trial":
                shop.edit_trial(update.effective_user.id, {"traffic_gb": text})
                target = "trial"
            else:
                reference = admin_input["reference"]
                trial_user = int(reference) if admin_input["trial"] else None
                cfg = await shop.recover(
                    update.effective_user.id, reference, text.strip(), trial_user=trial_user
                )
                owner = trial_user or shop.store.order(reference)["user_id"]
                await notify_delivery(ctx.bot, owner, cfg)
                target = "home"
            ctx.user_data.pop("admin_input", None)
            await update.effective_message.reply_text("✅ تغییرات ذخیره شد.")
            await admin_route(update, ctx, target)
            return
        order_id = ctx.user_data.get("awaiting_receipt")
        if order_id:
            if not update.effective_message.photo:
                await render(
                    update,
                    ctx,
                    "📷 لطفاً رسید را به صورت عکس ارسال کن، نه متن یا فایل. هنوز منتظر عکست هستم.",
                    [back(ctx, "history")],
                )
                return
            order = shop.submit_receipt(
                update.effective_user.id, order_id, update.effective_message.photo[-1].file_id
            )
            ctx.user_data.pop("awaiting_receipt", None)
            ctx.user_data.pop("active_order", None)
            await notify_receipt(ctx.bot, shop.config, order)
            await render(
                update,
                ctx,
                "✅ <b>رسیدت رسید!</b>\n\nپس از تأیید ادمین، لینک کانفیگ همین‌جا برات ارسال می‌شه. از «سفارش‌های من» هم می‌تونی پیگیری کنی.",
                [[b(ctx, "🧾 پیگیری سفارش", "history")], back(ctx)],
            )
            return
        await show_main(update, ctx)
    except ShopError as exc:
        # Invalid input deliberately retains its mode so the user can retry.
        await render(update, ctx, f"⚠️ {esc(str(exc))}", [back(ctx, "admin:home" if admin_mode else "home")])


async def post_init(app):
    shop = app.bot_data["shop"]
    me = await app.bot.get_me()
    shop.config["bot_username"] = me.username
    await app.bot.set_my_commands(
        [
            BotCommand("start", "شروع و بررسی عضویت"),
            BotCommand("menu", "منوی اصلی"),
            BotCommand("trial", "تست رایگان یک‌روزه"),
            BotCommand("myconfigs", "کانفیگ‌های من"),
            BotCommand("orders", "پیگیری سفارش‌ها"),
            BotCommand("help", "راهنمای اتصال"),
            BotCommand("cancel", "لغو عملیات جاری"),
            BotCommand("admin", "پنل مدیریت"),
        ]
    )
    url = shop.config.get("webapp_url", "")
    menu = (
        MenuButtonWebApp(text="🐧 فروشگاه", web_app=WebAppInfo(url))
        if url.startswith("https://")
        else MenuButtonCommands()
    )
    await app.bot.set_chat_menu_button(menu_button=menu)
    logger.info("Pinginoo bot initialized")


async def error_handler(update, ctx):
    # Avoid logging Update/initData/request contents that can contain credentials.
    logger.error("Bot handler failed: %s", type(ctx.error).__name__)
    if isinstance(update, Update) and update.effective_chat:
        try:
            await ctx.bot.send_message(
                update.effective_chat.id,
                "مشکلی پیش اومد؛ چیزی را دوباره پرداخت نکن. از /menu وضعیت سفارشت را بررسی کن یا به پشتیبانی پیام بده.",
            )
        except TelegramError:
            pass


def build_application(config=None, shop=None):
    config = config or load_settings()
    shop = shop or Shop(config)
    proxy = config.get("proxy_url")
    request = HTTPXRequest(connect_timeout=30, read_timeout=30, proxy=proxy)
    polling_request = HTTPXRequest(connect_timeout=30, read_timeout=40, proxy=proxy)
    app = (
        Application.builder()
        .token(config["bot_token"])
        .request(request)
        .get_updates_request(polling_request)
        .post_init(post_init)
        .build()
    )
    app.bot_data["shop"] = shop
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler(["trial", "myconfigs", "orders", "help"], cmd_section))
    # One dispatcher: payment callbacks cannot bypass the membership gate.
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    return app


def main():
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    config = load_settings()
    if not config["bot_token"]:
        raise SystemExit(
            "BOT_TOKEN is missing. Copy config.example.json to config.json and configure the bot, or set BOT_TOKEN in .env."
        )
    build_application(config).run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()

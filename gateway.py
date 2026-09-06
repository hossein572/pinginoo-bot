"""Telegram membership and notification helpers shared by both entry points."""

import logging
from html import escape
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.error import TelegramError

from shop import ShopError

logger = logging.getLogger(__name__)


def button(config, text, callback=None, *, style=None, url=None, web_app=None):
    return InlineKeyboardButton(
        text,
        callback_data=callback,
        url=url,
        web_app=web_app,
        style=style if config.get("colored_buttons", True) else None,
    )


async def check_membership(bot, uid: int, config: dict) -> bool:
    """Fail closed on API/network errors. Telegram requires bot-admin access."""
    if bot is None:
        raise ShopError("اتصال به تلگرام تنظیم نشده است.", "membership_unavailable", 503)
    try:
        member = await bot.get_chat_member(config["required_channel"], uid)
    except TelegramError as exc:
        logger.warning("Channel membership check unavailable (%s)", type(exc).__name__)
        raise ShopError(
            "الان امکان بررسی عضویت نیست. کمی بعد دوباره بزنید؛ مدیر باید ربات را ادمین کانال کند.",
            "membership_unavailable",
            503,
        ) from exc
    return member.status in {
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    } or (member.status == ChatMemberStatus.RESTRICTED and member.is_member)


async def notify_receipt(bot, config: dict, order: dict) -> int:
    if bot is None:
        return 0
    caption = (
        f"🧾 <b>رسید جدید پینگینو</b>\n\n"
        f"کاربر: <code>{order['user_id']}</code>\n"
        f"پلن: {escape(order['plan_name'])}\n"
        f"مبلغ: {order['price']:,} تومان\n"
        f"حجم: {order['traffic_gb']} گیگ · {order['days']} روز\n"
        f"شناسه: <code>{escape(order['id'])}</code>"
    )
    markup = InlineKeyboardMarkup(
        [
            [
                button(config, "تأیید و فعال‌سازی", f"admin:approve:{order['id']}", style="success"),
                button(config, "رد رسید", f"admin:reject_confirm:{order['id']}", style="danger"),
            ]
        ]
    )
    sent = 0
    for admin in config["admin_ids"]:
        try:
            await bot.send_photo(
                chat_id=admin,
                photo=order["receipt_file_id"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=markup,
            )
            sent += 1
        except TelegramError:
            logger.warning("Could not notify admin %s; receipt remains in review queue", admin)
    return sent


async def notify_delivery(bot, uid: int, config: dict) -> bool:
    if bot is None:
        return False
    try:
        await bot.send_message(
            chat_id=uid,
            text=(
                f"✅ <b>کانفیگت آماده است!</b>\n\n"
                f"{escape(config['plan_name'])}\n"
                f"📦 {config['traffic_gb']} گیگ · {config['days']} روز\n\n"
                f"<code>{escape(config['config_link'])}</code>\n\n"
                "لینک را کپی و در برنامهٔ اتصال وارد کن. همیشه از «کانفیگ‌های من» هم در دسترس است."
            ),
            parse_mode="HTML",
        )
        return True
    except TelegramError:
        logger.warning("Delivery notification failed for user %s; config is saved", uid)
        return False


async def notify_rejection(bot, order: dict):
    if bot is None:
        return
    try:
        await bot.send_message(
            chat_id=order["user_id"],
            text=f"❌ رسید سفارش {order['id']} تأیید نشد. برای پیگیری از منوی ربات به پشتیبانی پیام بده.",
        )
    except TelegramError:
        logger.warning("Rejection notification failed for user %s", order["user_id"])


def legacy_receipt_path(config, order):
    """Constrain migrated local files to the original receipts directory."""
    raw = order.get("receipt_path")
    if not raw:
        return None
    root = (Path(config["data_dir"]) / "receipts").resolve()
    path = Path(raw).resolve()
    return path if path.is_relative_to(root) and path.is_file() else None

from html import escape
from unittest.mock import AsyncMock

import pytest
from telegram.error import Forbidden

from gateway import notify_delivery


@pytest.fixture
def subscription():
    return {
        "plan_name": "پلن <تست> & پینگینو",
        "traffic_gb": 1,
        "days": 1,
        "config_link": "https://panel.example.invalid/sub/private?one=1&two=2",
    }


async def test_delivery_sends_actual_link_to_telegram_with_copy_and_help(subscription):
    bot = AsyncMock()
    assert await notify_delivery(bot, 7, subscription) is True
    bot.send_message.assert_awaited_once()
    sent = bot.send_message.call_args.kwargs
    assert sent["chat_id"] == 7
    assert f"<code>{escape(subscription['config_link'])}</code>" in sent["text"]
    assert escape(subscription["plan_name"]) in sent["text"]
    assert "ایمیل" not in sent["text"]
    assert sent["disable_web_page_preview"] is True
    rows = sent["reply_markup"].inline_keyboard
    assert rows[0][0].copy_text.text == subscription["config_link"]
    assert {b.callback_data for b in rows[-1]} == {"my_configs", "help"}


@pytest.mark.parametrize("length,has_copy_button", [(256, True), (257, False)])
async def test_copy_button_length_limit_never_blocks_telegram_delivery(subscription, length, has_copy_button):
    subscription["config_link"] = "https://example.invalid/".ljust(length, "x")
    bot = AsyncMock()
    assert await notify_delivery(bot, 7, subscription) is True
    sent = bot.send_message.call_args.kwargs
    assert subscription["config_link"] in sent["text"]
    assert any(b.copy_text for row in sent["reply_markup"].inline_keyboard for b in row) == has_copy_button


async def test_blocked_bot_reports_failed_delivery_without_email_fallback(subscription):
    bot = AsyncMock()
    bot.send_message.side_effect = Forbidden("bot blocked by user")
    assert await notify_delivery(bot, 7, subscription) is False
    assert bot.send_message.await_count == 1


@pytest.mark.parametrize("link", [None, "", 123])
async def test_missing_link_cannot_report_successful_delivery(subscription, link):
    subscription["config_link"] = link
    bot = AsyncMock()
    assert await notify_delivery(bot, 7, subscription) is False
    bot.send_message.assert_not_awaited()

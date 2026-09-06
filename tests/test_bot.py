from types import SimpleNamespace
from unittest.mock import AsyncMock

from telegram.error import NetworkError

from bot import cb_handler, cmd_start, handle_message
from gateway import button, legacy_receipt_path


def update_context(shop, *, uid=7, data=None, text="hello", joined=True):
    user = SimpleNamespace(id=uid, first_name="<کاربر & تست>", username="example")
    message = SimpleNamespace(text=text, photo=[], message_id=42, reply_text=AsyncMock())
    query = (
        SimpleNamespace(
            data=data, from_user=user, message=message, answer=AsyncMock(), edit_message_text=AsyncMock()
        )
        if data is not None
        else None
    )
    update = SimpleNamespace(
        effective_user=user,
        effective_chat=SimpleNamespace(id=uid, type="private"),
        effective_message=message,
        message=message,
        callback_query=query,
    )
    bot = AsyncMock()
    bot.get_chat_member.return_value = SimpleNamespace(
        status="member" if joined else "left", is_member=joined
    )
    ctx = SimpleNamespace(
        bot=bot, user_data={}, args=[], application=SimpleNamespace(bot_data={"shop": shop})
    )
    return update, ctx


async def test_start_prompts_for_channel_and_verifies_then_menu(shop):
    update, ctx = update_context(shop, joined=False)
    await cmd_start(update, ctx)
    message = ctx.bot.send_message.call_args.kwargs
    assert "عضو" in message["text"]
    buttons = message["reply_markup"].inline_keyboard
    assert buttons[0][0].url == "https://t.me/pingino_org"
    assert buttons[1][0].callback_data == "check_membership"
    update, ctx = update_context(shop, data="check_membership", joined=True)
    await cb_handler(update, ctx)
    ctx.bot.send_message.assert_awaited_once()  # Persistent reply keyboard.
    text = update.callback_query.edit_message_text.call_args.args[0]
    assert "&lt;کاربر &amp; تست&gt;" in text
    assert "کانفیگ فعال" in text


async def test_forged_admin_callback_is_denied_without_listing_data(shop):
    update, ctx = update_context(shop, data="admin:users")
    await cb_handler(update, ctx)
    update.callback_query.answer.assert_awaited_once()
    assert update.callback_query.answer.call_args.kwargs["show_alert"] is True
    update.callback_query.edit_message_text.assert_not_awaited()


async def test_every_user_callback_and_text_input_is_membership_gated(shop, panels):
    for data in ["plan:regular_plus", "claim_trial", "my_configs", "history", "pay_pay_7_123", "renew_-1"]:
        update, ctx = update_context(shop, data=data, joined=False)
        await cb_handler(update, ctx)
        assert "عضو" in update.callback_query.edit_message_text.call_args.args[0]
    assert not shop.store.orders(7)
    assert not panels["regular"].creates
    update, ctx = update_context(shop, joined=False)
    ctx.user_data["awaiting_receipt"] = "ord_fake"
    update.message.photo = [SimpleNamespace(file_id="photo")]
    await handle_message(update, ctx)
    assert "عضو" in ctx.bot.send_message.call_args.kwargs["text"]


async def test_membership_network_failure_shows_retry_not_menu(shop):
    update, ctx = update_context(shop, data="my_configs")
    ctx.bot.get_chat_member.side_effect = NetworkError("offline")
    await cb_handler(update, ctx)
    assert "امکان بررسی عضویت نیست" in update.callback_query.edit_message_text.call_args.args[0]


async def test_menu_buttons_work_without_callback_queries(shop):
    update, ctx = update_context(shop, text="🎮 کانفیگ گیمینگ")
    await handle_message(update, ctx)
    assert "گیمینگ" in ctx.bot.send_message.call_args.kwargs["text"]
    assert "پینگینو سبک" not in ctx.bot.send_message.call_args.kwargs["text"]


async def test_new_and_legacy_config_buttons_have_correct_signature(shop):
    cfg = await shop.claim_trial(7)
    for data in [f"config:{cfg['id']}", "get_link_0", "renew_0"]:
        update, ctx = update_context(shop, data=data)
        await cb_handler(update, ctx)
        text = update.callback_query.edit_message_text.call_args.args[0]
        assert "پیدا نشد" not in text
        assert "<code>" in text or "تمدید" in text


async def test_invalid_photo_keeps_receipt_mode_and_real_photo_is_forwarded(shop):
    order = shop.new_order(7, "regular_plus")
    update, ctx = update_context(shop, text="not a photo")
    ctx.user_data["awaiting_receipt"] = order["id"]
    await handle_message(update, ctx)
    assert ctx.user_data["awaiting_receipt"] == order["id"]
    update.message.photo = [SimpleNamespace(file_id="telegram_receipt_file")]
    await handle_message(update, ctx)
    assert "awaiting_receipt" not in ctx.user_data
    ctx.bot.send_photo.assert_awaited_once()
    assert ctx.bot.send_photo.call_args.kwargs["photo"] == "telegram_receipt_file"
    assert shop.store.order(order["id"])["status"] == "review"


async def test_receipt_deep_link_survives_membership_gate(shop):
    order = shop.new_order(7, "regular_plus")
    update, ctx = update_context(shop, joined=False)
    ctx.args = ["receipt_" + order["id"]]
    await cmd_start(update, ctx)
    assert ctx.user_data["start_payload"] == "receipt_" + order["id"]
    follow, _ = update_context(shop, data="check_membership")
    ctx.bot.get_chat_member.return_value.status = "member"
    await cb_handler(follow, ctx)
    assert ctx.user_data["awaiting_receipt"] == order["id"]


async def test_legacy_double_pay_prefix_only_removed_once(shop):
    order = shop.new_order(7, "regular_plus")
    legacy_id = "pay_7_123"
    with shop.store.transaction() as conn:
        shop.store._put(conn, "orders", legacy_id, {**order, "id": legacy_id})
    update, ctx = update_context(shop, data="pay_" + legacy_id)
    await cb_handler(update, ctx)
    assert ctx.user_data["awaiting_receipt"] == legacy_id


async def test_admin_input_validation_preserves_mode_and_saves(shop):
    update, ctx = update_context(shop, uid=1, text="invalid")
    ctx.user_data["admin_input"] = {"type": "plan", "key": "regular_plus", "field": "price"}
    await handle_message(update, ctx)
    assert ctx.user_data["admin_input"]
    update.message.text = "۲۱۰٬۰۰۰"
    await handle_message(update, ctx)
    assert "admin_input" not in ctx.user_data
    assert shop.catalog()["plans"]["regular_plus"]["price"] == 210000


async def test_back_cancels_broadcast_draft_and_input_modes(shop):
    update, ctx = update_context(shop, uid=1, data="admin:home")
    ctx.user_data.update(
        admin_input={"type": "plan"}, awaiting_receipt="old", broadcast_draft=42, broadcast_mode="compose"
    )
    await cb_handler(update, ctx)
    assert not any(
        k in ctx.user_data for k in ("admin_input", "awaiting_receipt", "broadcast_draft", "broadcast_mode")
    )


def test_telegram_button_styles_and_fallback(config):
    assert button(config, "خرید", "buy", style="primary").to_dict()["style"] == "primary"
    config["colored_buttons"] = False
    assert "style" not in button(config, "خرید", "buy", style="primary").to_dict()


def test_legacy_receipt_cannot_traverse_data_directory(config, tmp_path):
    secret = tmp_path / "config.json"
    secret.write_text('{"bot_token":"private"}')
    assert legacy_receipt_path(config, {"receipt_path": str(secret)}) is None
    receipt = tmp_path / "receipts" / "one.jpg"
    receipt.parent.mkdir()
    receipt.write_bytes(b"jpeg")
    assert legacy_receipt_path(config, {"receipt_path": str(receipt)}) == receipt


async def test_checkout_skips_email_for_new_users_and_old_keyboards(shop):
    update, ctx = update_context(shop, data="plan_regular_plus")
    ctx.user_data.update(awaiting_email=True, pending_plan="regular_plus")
    await cb_handler(update, ctx)
    text = update.callback_query.edit_message_text.call_args.args[0]
    assert "مبلغ" in text and "تلگرام" in text
    assert "ایمیل" not in text
    assert "awaiting_email" not in ctx.user_data and "pending_plan" not in ctx.user_data
    order = shop.store.orders(7)[0]
    assert order["user_id"] == 7 and order["status"] == "awaiting_receipt"
    assert "email" not in order and "email" not in shop.store.user(7)


async def test_pasted_email_is_not_collected_from_old_checkout(shop):
    update, ctx = update_context(shop, text="user@example.invalid")
    ctx.user_data.update(awaiting_email=True, pending_plan="regular_plus")
    await handle_message(update, ctx)
    assert "email" not in shop.store.user(7)
    assert "awaiting_email" not in ctx.user_data
    assert "pending_plan" not in ctx.user_data
    assert not shop.store.orders(7)


async def test_trial_is_delivered_as_a_new_private_telegram_message(shop):
    update, ctx = update_context(shop, data="claim_trial")
    await cb_handler(update, ctx)
    cfg = shop.store.user(7)["configs"][0]
    ctx.bot.send_message.assert_awaited_once()
    sent = ctx.bot.send_message.call_args.kwargs
    assert sent["chat_id"] == 7
    assert cfg["config_link"] in sent["text"]
    assert "پیام جدا" in update.callback_query.edit_message_text.call_args.args[0]


async def test_trial_delivery_failure_keeps_config_and_displays_existing_link(shop, panels):
    update, ctx = update_context(shop, data="claim_trial")
    ctx.bot.send_message.side_effect = NetworkError("telegram unavailable")
    await cb_handler(update, ctx)
    user = shop.store.user(7)
    assert user["trial_used"]
    assert len(user["configs"]) == len(panels["regular"].creates) == 1
    assert user["configs"][0]["config_link"] in update.callback_query.edit_message_text.call_args.args[0]


async def test_payment_approval_sends_config_to_buyer_not_admin(shop):
    order = shop.new_order(7, "gaming_plus")
    shop.submit_receipt(7, order["id"], "receipt_photo")
    update, ctx = update_context(shop, uid=1, data=f"admin:approve:{order['id']}")
    await cb_handler(update, ctx)
    cfg = shop.store.user(7)["configs"][0]
    ctx.bot.send_message.assert_awaited_once()
    sent = ctx.bot.send_message.call_args.kwargs
    assert sent["chat_id"] == 7
    assert cfg["config_link"] in sent["text"]
    assert "ایمیل" not in sent["text"]


async def test_renewal_sends_existing_link_to_buyer_in_telegram(shop, panels):
    previous = await shop.claim_trial(7)
    order = shop.new_order(7, "regular_plus", previous["id"])
    shop.submit_receipt(7, order["id"], "receipt_photo")
    update, ctx = update_context(shop, uid=1, data=f"admin:approve:{order['id']}")
    await cb_handler(update, ctx)
    sent = ctx.bot.send_message.call_args.kwargs
    assert sent["chat_id"] == 7 and previous["config_link"] in sent["text"]
    assert len(panels["regular"].creates) == len(panels["regular"].extensions) == 1

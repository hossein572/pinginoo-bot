"""Validate Telegram Mini App initData on the server, never trust initDataUnsafe."""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from shop import ShopError


def validate_init_data(value: str, token: str, *, max_age=3600, now=None) -> dict:
    if not token or not value or len(value) > 16384:
        raise ShopError("فروشگاه را از داخل ربات تلگرام باز کنید.", "unauthorized", 401)
    try:
        pairs = parse_qsl(value, keep_blank_values=True, strict_parsing=True)
        data = dict(pairs)
        if len(data) != len(pairs):
            raise ValueError("Duplicate keys")
        supplied_hash = data.pop("hash")
        secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
        check = "\n".join(f"{key}={val}" for key, val in sorted(data.items()))
        expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(supplied_hash, expected):
            raise ValueError("Bad signature")
        current = time.time() if now is None else now
        age = current - int(data["auth_date"])
        if age < -30 or age > max_age:
            raise ValueError("Expired")
        user = json.loads(data["user"])
        if isinstance(user.get("id"), bool) or not isinstance(user.get("id"), int) or user["id"] <= 0:
            raise ValueError("Invalid user")
        return user
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ShopError(
            "نشست تلگرام معتبر نیست یا منقضی شده؛ مینی‌اپ را دوباره از ربات باز کنید.", "unauthorized", 401
        ) from exc

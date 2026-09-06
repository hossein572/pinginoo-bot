"""Small transactional store shared by the bot and Mini App.

Legacy JSON files are imported once, untouched. SQLite WAL + BEGIN IMMEDIATE
make claims/edits safe across the two processes; network calls never hold a DB lock.
"""

import copy
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from settings import initial_catalog


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_date(value: str) -> datetime:
    date = datetime.fromisoformat(value)
    return date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date


def active_config(config: dict) -> bool:
    try:
        return config.get("status") == "active" and parse_date(config["expires_at"]) > datetime.now(
            timezone.utc
        )
    except (ValueError, KeyError, TypeError):
        return False


class Store:
    def __init__(self, config: dict, *, demo: bool = False):
        self.config = config
        self.directory = Path(config["data_dir"])
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / ("demo.sqlite3" if demo else "pinginoo.sqlite3")
        with self.connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS records (kind TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(kind, key))"
            )
        self.path.chmod(0o600)
        with self.transaction() as conn:
            if self._get(conn, "meta", "initialized") is None:
                self._put(conn, "settings", "catalog", initial_catalog(config))
                if not demo:
                    self._import_legacy(conn)
                self._put(conn, "meta", "initialized", {"at": now_iso()})

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path, timeout=15)
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    @staticmethod
    def _get(conn, kind: str, key: str):
        row = conn.execute("SELECT value FROM records WHERE kind=? AND key=?", (kind, str(key))).fetchone()
        return json.loads(row[0]) if row else None

    @staticmethod
    def _put(conn, kind: str, key: str, data):
        conn.execute(
            "INSERT INTO records(kind,key,value) VALUES (?,?,?) ON CONFLICT(kind,key) DO UPDATE SET value=excluded.value",
            (kind, str(key), json.dumps(data, ensure_ascii=False)),
        )

    def _import_legacy(self, conn):
        for file, kind in [("users.json", "users"), ("pending_payments.json", "orders")]:
            path = self.directory / file
            if not path.exists():
                continue
            for key, record in json.loads(path.read_text("utf-8")).items():
                if kind == "users":
                    record["id"] = int(key)
                    for cfg in record.get("configs", []):
                        cfg.setdefault("id", uuid4().hex[:12])
                        cfg.setdefault("category", "regular")
                    record.setdefault("trial_used", any(c.get("is_trial") for c in record.get("configs", [])))
                else:
                    record.setdefault("id", key)
                    record.setdefault("category", "regular")
                    if record.get("status") == "pending":
                        record["status"] = "review" if record.get("receipt_path") else "awaiting_receipt"
                self._put(conn, kind, key, record)

    def get(self, kind: str, key: str):
        with self.connection() as conn:
            return self._get(conn, kind, key)

    def all(self, kind: str) -> list:
        with self.connection() as conn:
            return [
                json.loads(row[0]) for row in conn.execute("SELECT value FROM records WHERE kind=?", (kind,))
            ]

    def catalog(self) -> dict:
        return self.get("settings", "catalog")

    def edit_catalog(self, edit):
        with self.transaction() as conn:
            catalog = self._get(conn, "settings", "catalog")
            result = edit(catalog)
            self._put(conn, "settings", "catalog", catalog)
            return result

    def user(self, uid: int, **profile) -> dict:
        with self.transaction() as conn:
            user = self._get(conn, "users", str(uid)) or {
                "id": uid,
                "username": None,
                "first_name": "دوست پینگینویی",
                "configs": [],
                "trial_used": False,
                "created_at": now_iso(),
                "is_active": True,
            }
            # Historical email fields are left untouched, never collected or reused.
            user.update({k: v for k, v in profile.items() if k in {"first_name", "username"}})
            self._put(conn, "users", str(uid), user)
            return user

    def edit_user(self, uid: int, edit):
        self.user(uid)
        with self.transaction() as conn:
            user = self._get(conn, "users", str(uid))
            result = edit(user)
            self._put(conn, "users", str(uid), user)
            return result

    def order(self, order_id: str) -> dict | None:
        return self.get("orders", order_id)

    def orders(self, uid: int | None = None) -> list:
        records = self.all("orders")
        return sorted(
            (p for p in records if uid is None or p["user_id"] == uid),
            key=lambda p: p["created_at"],
            reverse=True,
        )

    def edit_order(self, order_id: str, edit):
        with self.transaction() as conn:
            order = self._get(conn, "orders", order_id)
            if order is None:
                raise KeyError(order_id)
            result = edit(order)
            self._put(conn, "orders", order_id, order)
            return result

    def create_order(self, uid: int, plan_key: str, renewal_id: str | None = None) -> dict:
        self.user(uid)
        with self.transaction() as conn:
            catalog = self._get(conn, "settings", "catalog")
            plan = catalog["plans"].get(plan_key)
            if not plan or not plan.get("enabled", True):
                raise ValueError("این پلن در حال حاضر قابل خرید نیست.")
            user = self._get(conn, "users", str(uid))
            if renewal_id:
                cfg = next((c for c in user["configs"] if c.get("id") == renewal_id), None)
                if not cfg or not cfg.get("panel_uuid"):
                    raise ValueError("کانفیگ قابل تمدید یافت نشد.")
                if cfg.get("category", "regular") != plan["category"]:
                    raise ValueError("نوع پلن تمدید باید با کانفیگ فعلی یکسان باشد.")
                for row in conn.execute("SELECT value FROM records WHERE kind='orders'"):
                    previous = json.loads(row[0])
                    if (
                        previous.get("user_id") == uid
                        and previous.get("renewal_id") == renewal_id
                        and previous["status"] in {"review", "provisioning", "needs_review"}
                    ):
                        raise ValueError("یک درخواست تمدید برای این کانفیگ در حال بررسی است.")
            # Reuse an unsubmitted invoice only if its immutable price/quota match.
            for row in conn.execute("SELECT value FROM records WHERE kind='orders'"):
                previous = json.loads(row[0])
                if (
                    previous.get("user_id") == uid
                    and previous.get("plan_key") == plan_key
                    and previous.get("renewal_id") == renewal_id
                    and previous["status"] == "awaiting_receipt"
                    and all(previous.get(k) == plan[k] for k in ("price", "traffic_gb", "days"))
                ):
                    return previous
            order_id = "ord_" + uuid4().hex[:16]
            order = {
                "id": order_id,
                "user_id": uid,
                "plan_key": plan_key,
                "plan_name": plan["name"],
                "category": plan["category"],
                "price": plan["price"],
                "traffic_gb": plan["traffic_gb"],
                "days": plan["days"],
                "renewal_id": renewal_id,
                "status": "awaiting_receipt",
                "created_at": now_iso(),
            }
            self._put(conn, "orders", order_id, order)
            return copy.deepcopy(order)

    def finish_delivery(self, order_id: str, config: dict, admin_id: int):
        """Persist subscription + approval together, never a paid but missing config."""
        with self.transaction() as conn:
            order = self._get(conn, "orders", order_id)
            if order["status"] != "provisioning":
                raise ValueError("این سفارش قبلاً پردازش شده است.")
            user = self._get(conn, "users", str(order["user_id"]))
            renewal_id = order.get("renewal_id")
            if renewal_id:
                index = next(i for i, c in enumerate(user["configs"]) if c["id"] == renewal_id)
                user["configs"][index] = config
            else:
                user["configs"].append(config)
            order.update(
                status="approved", approved_at=now_iso(), approved_by=admin_id, config_id=config["id"]
            )
            order.pop("delivery_error", None)
            self._put(conn, "users", str(user["id"]), user)
            self._put(conn, "orders", order_id, order)

    def finish_trial(self, uid: int, config: dict):
        with self.transaction() as conn:
            user = self._get(conn, "users", str(uid))
            if user.get("trial_status") != "provisioning" or user.get("trial_used"):
                raise ValueError("تست این حساب قبلاً پردازش شده است.")
            user["configs"].append(config)
            user.update(trial_used=True, trial_status="active", trial_claimed_at=now_iso())
            self._put(conn, "users", str(uid), user)

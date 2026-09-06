"""
HS Panel API Client
Matches the actual HS Panel API endpoints (main.py)
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

import httpx

logger = logging.getLogger(__name__)

BOT_DIR = Path(__file__).parent
CONFIG_FILE = BOT_DIR / "config.json"

def load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        import json
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

CONFIG = load_config()

PANEL_URL = CONFIG.get("panel_url", "http://localhost:8000").rstrip("/")
PANEL_PASSWORD = CONFIG.get("panel_password", "123456")


class PanelAPI:
    """Client for HS Panel REST API"""

    def __init__(self, base_url: str = None, password: str = None):
        self.base = (base_url or PANEL_URL).rstrip("/")
        self.password = password or PANEL_PASSWORD
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
                    text = resp.text.strip()
                    if text:
                        try:
                            return {"status": "ok", "data": resp.json()}
                        except Exception:
                            return {"status": "ok", "data": text}
                    return {"status": "ok"}
                return {"status": "error", "code": resp.status_code, "body": resp.text[:300]}
        except Exception as e:
            logger.error(f"Panel request failed: {method} {path}: {e}")
            return {"status": "error", "detail": str(e)}

    async def login(self) -> bool:
        """Login to panel with password, store token"""
        result = await self._req("POST", "/api/login", json={"password": self.password})
        if result.get("status") == "ok":
            data = result.get("data", {})
            self._token = (
                data.get("token") or
                data.get("access_token") or
                data.get("key") or
                ""
            )
            return bool(self._token)
        return False

    async def ensure_logged_in(self) -> bool:
        """Login if not already authenticated"""
        return await self.login()

    # ─── Subs (main endpoint in HS Panel) ──────────────────────────────

    async def create_sub(self, name: str, traffic: int, days: int,
                          email: str = None, protocol: str = None) -> Dict[str, Any]:
        """Create a subscription on the panel"""
        payload = {
            "name": name,
            "traffic": traffic,  # bytes
            "days": days,
        }
        if email:
            payload["email"] = email
        if protocol:
            payload["protocol"] = protocol
        result = await self._req("POST", "/api/subs", json=payload)
        if result.get("status") != "ok":
            result = await self._req("POST", "/api/links", json=payload)
        return result

    async def list_subs(self) -> List[Dict[str, Any]]:
        """List all subscriptions"""
        result = await self._req("GET", "/api/subs")
        if result.get("status") == "ok":
            data = result.get("data", {})
            if isinstance(data, list):
                return data
            return data.get("subs", data.get("links", []))
        result2 = await self._req("GET", "/api/links")
        if result2.get("status") == "ok":
            d = result2.get("data", {})
            return d if isinstance(d, list) else d.get("links", [])
        return []

    async def get_sub(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get a single subscription"""
        result = await self._req("GET", f"/api/subs/{uid}")
        if result.get("status") == "ok":
            return result.get("data")
        result2 = await self._req("GET", f"/api/links/{uid}")
        if result2.get("status") == "ok":
            return result2.get("data")
        return None

    async def update_sub(self, uid: str, **kwargs) -> Dict[str, Any]:
        """Update subscription (extend days/traffic)"""
        result = await self._req("PATCH", f"/api/subs/{uid}", json=kwargs)
        if result.get("status") != "ok":
            result = await self._req("PATCH", f"/api/links/{uid}", json=kwargs)
        return result

    async def delete_sub(self, uid: str) -> bool:
        """Delete a subscription"""
        result = await self._req("DELETE", f"/api/subs/{uid}")
        if result.get("status") == "ok":
            return True
        result2 = await self._req("DELETE", f"/api/links/{uid}")
        return result2.get("status") == "ok"

    async def get_sub_link(self, uuid_key: str) -> str:
        """Get subscription share link"""
        return f"{self.base}/sub/{uuid_key}"

    # ─── Stats & Health ────────────────────────────────────────────────

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


# Singleton instance
panel = PanelAPI()


async def create_config_for_user(
    email: str,
    user_id: int,
    traffic_gb: int,
    days: int,
    protocol: str = None
) -> Optional[Dict[str, Any]]:
    """Create a config on panel for a user and return result"""
    logged_in = await panel.ensure_logged_in()
    if not logged_in:
        logger.error("Panel login failed")
        return None

    traffic_bytes = traffic_gb * (1024 ** 3)
    label = f"user_{user_id}"

    result = await panel.create_sub(
        name=label,
        traffic=traffic_bytes,
        days=days,
        email=email,
        protocol=protocol
    )

    if result.get("status") == "ok":
        data = result.get("data", {})
        logger.info(f"Config created for user {user_id}: {data.get('uuid', data.get('id', '?'))}")
        return result
    else:
        logger.error(f"Config creation failed: {result}")
        return None


async def extend_user_config(uuid: str, days: int, traffic_gb: int = None) -> bool:
    """Extend an existing config"""
    await panel.ensure_logged_in()
    kwargs = {"days": days}
    if traffic_gb:
        kwargs["traffic"] = traffic_gb * (1024 ** 3)
    result = await panel.update_sub(uuid, **kwargs)
    return result.get("status") == "ok"

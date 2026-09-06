"""HS Panel client. Mutating requests never fall back after an ambiguous failure."""

import logging
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


class PanelAPI:
    def __init__(self, base_url: str, password: str, protocol: str | None = None):
        self.base = base_url.rstrip("/")
        self.password = password
        self.protocol = protocol
        self._token = None

    async def _req(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.request(method, f"{self.base}{path}", headers=headers, **kwargs)
            if 200 <= response.status_code < 300:
                try:
                    data = response.json() if response.content else {}
                except ValueError:
                    data = {}
                return {"status": "ok", "data": data}
            return {
                "status": "error",
                "code": response.status_code,
                "uncertain": response.status_code >= 500 or response.status_code == 408,
            }
        except httpx.HTTPError:
            # Do not log tokens, subscription URLs or a potentially sensitive body.
            logger.warning("HS Panel request failed (%s)", method)
            return {"status": "error", "uncertain": True}

    async def login(self) -> bool:
        self._token = None
        result = await self._req("POST", "/api/login", json={"password": self.password})
        data = result.get("data", {})
        if result["status"] == "ok" and isinstance(data, dict):
            self._token = data.get("token") or data.get("access_token") or data.get("key")
        return bool(self._token)

    async def ensure_logged_in(self) -> bool:
        return await self.login()

    async def _subscription_request(self, method: str, suffix: str = "", **kwargs):
        result = await self._req(method, f"/api/subs{suffix}", **kwargs)
        # Only unsupported endpoints are safe to retry. A timeout/500 may have
        # already created a subscription and must not produce a second one.
        if result.get("code") in (404, 405):
            result = await self._req(method, f"/api/links{suffix}", **kwargs)
        return result

    async def create_sub(self, name: str, traffic: int, days: int, *, protocol: str | None = None) -> dict:
        payload = {"name": name, "traffic": traffic, "days": days}
        if protocol or self.protocol:
            payload["protocol"] = protocol or self.protocol
        return await self._subscription_request("POST", json=payload)

    async def create_link(self, traffic_gb: float, days: int, *, label: str | None = None):
        return await self.create_sub(label or "pinginoo", round(traffic_gb * 1024**3), days)

    async def update_sub(self, uid: str, **kwargs) -> dict:
        return await self._subscription_request("PATCH", "/" + quote(str(uid), safe=""), json=kwargs)

    async def extend_link(self, uid: str, days: int, traffic_gb: float) -> dict:
        return await self.update_sub(uid, days=days, traffic=round(traffic_gb * 1024**3))

    async def get_sub(self, uid: str) -> dict:
        return await self._subscription_request("GET", "/" + quote(str(uid), safe=""))

    async def list_subs(self) -> list:
        result = await self._subscription_request("GET")
        data = result.get("data", {})
        return data if isinstance(data, list) else data.get("subs", data.get("links", []))

    async def delete_sub(self, uid: str) -> bool:
        result = await self._subscription_request("DELETE", "/" + quote(str(uid), safe=""))
        return result["status"] == "ok"

    async def get_sub_link(self, uid: str) -> str:
        return f"{self.base}/sub/{quote(str(uid), safe='')}"

    async def get_stats(self) -> dict:
        result = await self._req("GET", "/stats")
        return result.get("data", {}) if result["status"] == "ok" else {}

    async def health_check(self) -> bool:
        return (await self._req("GET", "/health"))["status"] == "ok"


class DemoPanel(PanelAPI):
    """Explicitly isolated preview adapter: never contacts a real panel."""

    def __init__(self):
        super().__init__("https://example.invalid/pinginoo-demo", "")

    async def ensure_logged_in(self):
        return True

    async def create_link(self, traffic_gb, days, *, label=None):
        return {"status": "ok", "data": {"uuid": "demo_" + label}}

    async def extend_link(self, uid, days, traffic_gb):
        return {"status": "ok", "data": {"uuid": uid}}

    async def get_sub(self, uid):
        return {"status": "ok", "data": {"uuid": uid}}

    async def health_check(self):
        return True

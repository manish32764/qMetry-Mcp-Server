"""
HTTP base client for qMetry REST API.

Handles transport mechanics only: auth headers, base URL, timeouts, and HTTP verbs.
Domain logic lives in the domain-specific mixin modules.
"""

import os
from typing import Any

import httpx


class QMetryBaseClient:
    """HTTP transport layer — owns the httpx.Client and the four verb methods."""

    def __init__(self) -> None:
        api_key = os.environ.get("QMETRY_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("QMETRY_API_KEY environment variable is not set.")

        base_url = (
            os.environ
            .get("QMETRY_BASE_URL", "https://qtmcloud.qmetry.com/rest/api/latest/")
            .rstrip("/") + "/"
        )

        self._http = httpx.Client(
            base_url=base_url,
            headers={
                "apiKey": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "QMetryBaseClient":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    # ------------------------------------------------------------------
    # HTTP verbs — only these should touch self._http
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> Any:
        r = self._http.get(path, params=params)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, body: dict | None = None, params: dict | None = None) -> Any:
        r = self._http.post(path, json=body or {}, params=params)
        r.raise_for_status()
        return r.json()

    def _put(self, path: str, body: dict | None = None) -> Any:
        r = self._http.put(path, json=body or {})
        r.raise_for_status()
        # Some PUT endpoints return 204 with no body
        return r.json() if r.content else {"status": "ok"}

    def _delete(self, path: str, body: dict | None = None) -> Any:
        r = self._http.request("DELETE", path, json=body or {})
        r.raise_for_status()
        return r.json() if r.content else {"status": "ok"}

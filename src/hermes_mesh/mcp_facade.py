"""MCP-facing facade for the local hermes-mesh daemon.

The facade is intentionally thin: automation lives in the daemon, while MCP tools
let Hermes inspect and control that daemon.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from hermes_mesh.sync import JsonTransport, UrllibJsonTransport


@dataclass(frozen=True)
class DaemonClient:
    # @lat: [[interfaces#MCP Facade]]
    base_url: str
    token: str
    timeout: float = 30
    transport: JsonTransport | None = None

    def _transport(self) -> JsonTransport:
        return self.transport or UrllibJsonTransport()

    def health(self) -> dict[str, Any]:
        return self._transport().get_json(f"{self.base_url.rstrip('/')}/health", timeout=self.timeout)

    def node(self) -> dict[str, Any]:
        return self._transport().get_json(f"{self.base_url.rstrip('/')}/node", timeout=self.timeout)

    def list_memory_cards(self, *, state: str | None = None) -> list[dict[str, Any]]:
        suffix = f"?{urlencode({'state': state})}" if state else ""
        result = self._transport().get_json(
            f"{self.base_url.rstrip('/')}/memory/cards{suffix}",
            token=self.token,
            timeout=self.timeout,
        )
        assert isinstance(result, list)
        return result

    def propose_memory_card(self, card: dict[str, Any]) -> dict[str, Any]:
        return self._transport().post_json(
            f"{self.base_url.rstrip('/')}/memory/propose",
            token=self.token,
            payload=card,
            timeout=self.timeout,
        )

    def approve_memory_card(
        self, memory_id: str, *, actor: str, reason: str | None = None
    ) -> dict[str, Any]:
        payload = {"actor": actor}
        if reason:
            payload["reason"] = reason
        return self._transport().post_json(
            f"{self.base_url.rstrip('/')}/memory/cards/{memory_id}/approve",
            token=self.token,
            payload=payload,
            timeout=self.timeout,
        )

    def reject_memory_card(
        self, memory_id: str, *, actor: str, reason: str | None = None
    ) -> dict[str, Any]:
        payload = {"actor": actor}
        if reason:
            payload["reason"] = reason
        return self._transport().post_json(
            f"{self.base_url.rstrip('/')}/memory/cards/{memory_id}/reject",
            token=self.token,
            payload=payload,
            timeout=self.timeout,
        )

    def trigger_sync_once(self) -> dict[str, Any]:
        return self._transport().post_json(
            f"{self.base_url.rstrip('/')}/memory/sync/run-once",
            token=self.token,
            payload={},
            timeout=self.timeout,
        )

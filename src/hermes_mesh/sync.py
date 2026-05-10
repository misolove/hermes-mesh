"""Peer-to-peer memory synchronization helpers."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from hermes_mesh.memory import PromotionState
from hermes_mesh.registry import MemoryRegistry


class JsonTransport(Protocol):
    def post_json(
        self,
        url: str,
        *,
        token: str,
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]: ...


class UrllibJsonTransport:
    """Small dependency-free JSON POST transport for daemon-to-daemon sync."""

    def post_json(
        self,
        url: str,
        *,
        token: str,
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"peer sync failed: HTTP {exc.code}: {detail}") from exc


@dataclass(frozen=True)
class MemorySyncClient:
    base_url: str
    token: str
    timeout: float = 30
    transport: JsonTransport | None = None

    def push_cards(self, cards: list[dict[str, Any]], *, from_node: str) -> dict[str, Any]:
        transport = self.transport or UrllibJsonTransport()
        return transport.post_json(
            f"{self.base_url.rstrip('/')}/memory/sync/push",
            token=self.token,
            payload={"from_node": from_node, "cards": cards},
            timeout=self.timeout,
        )


def sync_approved_to_peer(
    registry: MemoryRegistry,
    client: MemorySyncClient,
    *,
    from_node: str,
) -> dict[str, Any]:
    cards = [
        card.to_json_dict()
        for card in registry.list_cards(state=PromotionState.APPROVED_SHARED)
    ]
    return client.push_cards(cards, from_node=from_node)

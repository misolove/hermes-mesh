"""Peer-to-peer memory synchronization helpers."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from hermes_mesh.memory import MemoryCard, PromotionState
from hermes_mesh.registry import MemoryRegistry


class JsonTransport(Protocol):
    # @lat: [[sync-protocol#Transport Contract]]
    def get_json(
        self,
        url: str,
        *,
        token: str | None = None,
        timeout: float,
    ) -> dict[str, Any]: ...

    def post_json(
        self,
        url: str,
        *,
        token: str,
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]: ...


class UrllibJsonTransport:
    """Small dependency-free JSON transport for daemon-to-daemon sync."""
    # @lat: [[sync-protocol#Transport Contract]]

    def get_json(
        self,
        url: str,
        *,
        token: str | None = None,
        timeout: float,
    ) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(url, method="GET", headers=headers)
        return self._open_json(request, timeout=timeout)

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
        return self._open_json(request, timeout=timeout)

    def _open_json(self, request: urllib.request.Request, *, timeout: float) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"peer request failed: HTTP {exc.code}: {detail}") from exc


@dataclass(frozen=True)
class MemorySyncClient:
    # @lat: [[sync-protocol#Peer Client]]
    base_url: str
    token: str
    timeout: float = 30
    transport: JsonTransport | None = None

    def heartbeat(self, *, from_node: str) -> dict[str, Any]:
        transport = self.transport or UrllibJsonTransport()
        try:
            public_health = transport.get_json(
                f"{self.base_url.rstrip('/')}/health",
                timeout=self.timeout,
            )
            peer_heartbeat = transport.post_json(
                f"{self.base_url.rstrip('/')}/peers/heartbeat",
                token=self.token,
                payload={"from_node": from_node},
                timeout=self.timeout,
            )
            return {**public_health, **peer_heartbeat}
        except Exception as exc:  # noqa: BLE001 - heartbeat should report, not crash sync loop
            return {"ok": False, "error": str(exc)}

    def push_cards(self, cards: list[dict[str, Any]], *, from_node: str) -> dict[str, Any]:
        transport = self.transport or UrllibJsonTransport()
        return transport.post_json(
            f"{self.base_url.rstrip('/')}/memory/sync/push",
            token=self.token,
            payload={"from_node": from_node, "cards": cards},
            timeout=self.timeout,
        )

    def pull_cards(self, *, from_node: str) -> dict[str, Any]:
        transport = self.transport or UrllibJsonTransport()
        query = urllib.parse.urlencode({"from_node": from_node})
        return transport.get_json(
            f"{self.base_url.rstrip('/')}/memory/sync/pull?{query}",
            token=self.token,
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


def import_approved_cards(registry: MemoryRegistry, raw_cards: list[dict[str, Any]]) -> dict[str, list[str]]:
    # @lat: [[sync-protocol#Import Rule]]
    accepted: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []
    for raw_card in raw_cards:
        try:
            card = MemoryCard.model_validate(raw_card)
        except Exception as exc:  # noqa: BLE001 - one bad remote card must not drop the batch
            errors.append(f"unknown: {exc}")
            continue
        if card.promotion.state is not PromotionState.APPROVED_SHARED:
            skipped.append(card.id or "unknown")
            continue
        existing = registry.get(card.id, missing_ok=True)
        if existing is None:
            registry.propose(card)
            accepted.append(card.id or "unknown")
        else:
            skipped.append(card.id or "unknown")
    result = {"accepted": accepted, "skipped": skipped}
    if errors:
        result["errors"] = errors
    return result


def run_sync_once(
    registry: MemoryRegistry,
    clients: list[MemorySyncClient],
    *,
    from_node: str,
) -> dict[str, Any]:
    # @lat: [[sync-protocol#Push Pull Loop]]
    peer_results: list[dict[str, Any]] = []
    for client in clients:
        heartbeat = client.heartbeat(from_node=from_node)
        if heartbeat.get("ok") is False:
            peer_results.append(
                {
                    "peer": client.base_url,
                    "ok": False,
                    "phase": "heartbeat",
                    "heartbeat": heartbeat,
                    "error": heartbeat.get("error", "heartbeat failed"),
                }
            )
            continue
        try:
            push = sync_approved_to_peer(registry, client, from_node=from_node)
            pulled = client.pull_cards(from_node=from_node)
            pull_result = import_approved_cards(registry, pulled.get("cards", []))
        except Exception as exc:  # noqa: BLE001 - one bad peer must not stop the sync loop
            peer_results.append(
                {
                    "peer": client.base_url,
                    "ok": False,
                    "phase": "push_pull",
                    "heartbeat": heartbeat,
                    "error": str(exc),
                }
            )
            continue
        peer_results.append(
            {
                "peer": client.base_url,
                "ok": True,
                "heartbeat": heartbeat,
                "push": push,
                "pull": pull_result,
            }
        )
    return {"peers": peer_results}

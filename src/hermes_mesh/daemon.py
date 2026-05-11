"""Hermes Mesh daemon HTTP API.

The daemon is the always-on sync surface. MCP should wrap this API instead of
being responsible for background synchronization itself.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from hermes_mesh.config import DaemonConfig, load_daemon_config
from hermes_mesh.memory import MemoryCard, PromotionState
from hermes_mesh.registry import MemoryRegistry
from hermes_mesh.sync import MemorySyncClient, import_approved_cards, run_sync_once

DEFAULT_REGISTRY = Path.home() / ".hermes-mesh" / "registry"


def create_app(
    *,
    registry_root: str | Path = DEFAULT_REGISTRY,
    node_id: str = "hermes-mesh-node",
    role: str = "controller",
    token: str | None = None,
    peers: list[MemorySyncClient] | None = None,
    sync_interval_seconds: int = 0,
) -> Starlette:
    # @lat: [[architecture#Daemon First Runtime]]
    # @lat: [[interfaces#Daemon HTTP Surface]]
    registry = MemoryRegistry(registry_root)
    sync_clients = peers or []

    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"ok": True})

    async def node(_: Request) -> JSONResponse:
        return JSONResponse({"node_id": node_id, "role": role})

    async def peer_heartbeat(request: Request) -> JSONResponse:
        if unauthorized(request, token):
            return unauthorized_response()
        payload = await maybe_json(request)
        return JSONResponse(
            {
                "ok": True,
                "node_id": node_id,
                "role": role,
                "from_node": payload.get("from_node"),
            }
        )

    async def propose_memory(request: Request) -> JSONResponse:
        if unauthorized(request, token):
            return unauthorized_response()
        try:
            payload = await request.json()
            card = MemoryCard.model_validate(payload)
            saved = registry.propose(card)
        except (ValidationError, json.JSONDecodeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        return JSONResponse(saved.to_json_dict())

    async def list_memory(request: Request) -> JSONResponse:
        if unauthorized(request, token):
            return unauthorized_response()
        state = request.query_params.get("state")
        cards = [card.to_json_dict() for card in registry.list_cards(state=state)]
        return JSONResponse(cards)

    async def get_memory(request: Request) -> JSONResponse:
        if unauthorized(request, token):
            return unauthorized_response()
        try:
            card = registry.get(request.path_params["memory_id"])
        except (KeyError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=404)
        assert card is not None
        return JSONResponse(card.to_json_dict())

    async def approve_memory(request: Request) -> JSONResponse:
        if unauthorized(request, token):
            return unauthorized_response()
        payload = await maybe_json(request)
        try:
            card = registry.approve(
                request.path_params["memory_id"],
                actor=payload.get("actor", "unknown"),
                reason=payload.get("reason"),
            )
        except (KeyError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        return JSONResponse(card.to_json_dict())

    async def reject_memory(request: Request) -> JSONResponse:
        if unauthorized(request, token):
            return unauthorized_response()
        payload = await maybe_json(request)
        try:
            card = registry.reject(
                request.path_params["memory_id"],
                actor=payload.get("actor", "unknown"),
                reason=payload.get("reason"),
            )
        except (KeyError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        return JSONResponse(card.to_json_dict())

    async def sync_push(request: Request) -> JSONResponse:
        if unauthorized(request, token):
            return unauthorized_response()
        try:
            payload = await request.json()
            result = import_approved_cards(registry, payload.get("cards", []))
        except (ValidationError, json.JSONDecodeError, AttributeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        return JSONResponse(result)

    async def sync_pull(request: Request) -> JSONResponse:
        if unauthorized(request, token):
            return unauthorized_response()
        cards = [
            card.to_json_dict()
            for card in registry.list_cards(state=PromotionState.APPROVED_SHARED)
        ]
        return JSONResponse({"from_node": node_id, "cards": cards})

    async def sync_run_once(request: Request) -> JSONResponse:
        if unauthorized(request, token):
            return unauthorized_response()
        result = await asyncio.to_thread(
            run_sync_once,
            registry,
            sync_clients,
            from_node=node_id,
        )
        return JSONResponse(result)

    routes = [
        Route("/health", health, methods=["GET"]),
        Route("/node", node, methods=["GET"]),
        Route("/peers/heartbeat", peer_heartbeat, methods=["POST"]),
        Route("/memory/propose", propose_memory, methods=["POST"]),
        Route("/memory/cards", list_memory, methods=["GET"]),
        Route("/memory/cards/{memory_id}", get_memory, methods=["GET"]),
        Route("/memory/cards/{memory_id}/approve", approve_memory, methods=["POST"]),
        Route("/memory/cards/{memory_id}/reject", reject_memory, methods=["POST"]),
        Route("/memory/sync/push", sync_push, methods=["POST"]),
        Route("/memory/sync/pull", sync_pull, methods=["GET"]),
        Route("/memory/sync/run-once", sync_run_once, methods=["POST"]),
    ]
    async def periodic_sync() -> None:
        if not sync_clients or sync_interval_seconds <= 0:
            return
        while True:
            await asyncio.to_thread(
                run_sync_once,
                registry,
                sync_clients,
                from_node=node_id,
            )
            await asyncio.sleep(sync_interval_seconds)

    @asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncIterator[None]:
        task: asyncio.Task[None] | None = None
        if sync_clients and sync_interval_seconds > 0:
            task = asyncio.create_task(periodic_sync())
        try:
            yield
        finally:
            if task:
                task.cancel()

    return Starlette(debug=False, routes=routes, lifespan=lifespan)


def create_app_from_config(config: DaemonConfig) -> Starlette:
    # @lat: [[configuration#Loading Config]]
    peers = [
        MemorySyncClient(base_url=peer.url, token=peer.token or "")
        for peer in config.peers
        if peer.enabled
    ]
    return create_app(
        registry_root=config.registry.path,
        node_id=config.node.id,
        role=config.node.role,
        token=config.server.token,
        peers=peers,
        sync_interval_seconds=config.sync.sync_interval_seconds if config.sync.enabled else 0,
    )


def unauthorized(request: Request, token: str | None) -> bool:
    # @lat: [[architecture#Security Boundary]]
    if not token:
        return False
    return request.headers.get("authorization") != f"Bearer {token}"


def unauthorized_response() -> JSONResponse:
    return JSONResponse({"error": "missing or invalid bearer token"}, status_code=401)


async def maybe_json(request: Request) -> dict[str, Any]:
    body = await request.body()
    if not body:
        return {}
    value = json.loads(body)
    if isinstance(value, dict):
        return value
    return {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hermes-mesh-daemon")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8732)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--node-id", default="hermes-mesh-node")
    parser.add_argument("--role", default="controller")
    parser.add_argument("--token")
    args = parser.parse_args(argv)

    import uvicorn

    if args.config:
        config = load_daemon_config(args.config)
        app = create_app_from_config(config)
        uvicorn.run(app, host=config.server.host, port=config.server.port)
        return 0

    app = create_app(
        registry_root=args.registry,
        node_id=args.node_id,
        role=args.role,
        token=args.token,
    )
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

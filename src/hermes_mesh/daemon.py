"""Hermes Mesh daemon HTTP API.

The daemon is the always-on sync surface. MCP should wrap this API instead of
being responsible for background synchronization itself.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from hermes_mesh.memory import MemoryCard, PromotionState
from hermes_mesh.registry import MemoryRegistry

DEFAULT_REGISTRY = Path.home() / ".hermes-mesh" / "registry"


def create_app(
    *,
    registry_root: str | Path = DEFAULT_REGISTRY,
    node_id: str = "hermes-mesh-node",
    role: str = "controller",
    token: str | None = None,
) -> Starlette:
    registry = MemoryRegistry(registry_root)

    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"ok": True})

    async def node(_: Request) -> JSONResponse:
        return JSONResponse({"node_id": node_id, "role": role})

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
        except KeyError as exc:
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
            cards = payload.get("cards", [])
            accepted: list[str] = []
            skipped: list[str] = []
            for raw_card in cards:
                card = MemoryCard.model_validate(raw_card)
                if card.promotion.state is not PromotionState.APPROVED_SHARED:
                    skipped.append(card.id or "unknown")
                    continue
                saved = registry.propose(card)
                accepted.append(saved.id or "unknown")
        except (ValidationError, json.JSONDecodeError, AttributeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        return JSONResponse({"accepted": accepted, "skipped": skipped})

    routes = [
        Route("/health", health, methods=["GET"]),
        Route("/node", node, methods=["GET"]),
        Route("/memory/propose", propose_memory, methods=["POST"]),
        Route("/memory/cards", list_memory, methods=["GET"]),
        Route("/memory/cards/{memory_id}", get_memory, methods=["GET"]),
        Route("/memory/cards/{memory_id}/approve", approve_memory, methods=["POST"]),
        Route("/memory/cards/{memory_id}/reject", reject_memory, methods=["POST"]),
        Route("/memory/sync/push", sync_push, methods=["POST"]),
    ]
    return Starlette(debug=False, routes=routes)


def unauthorized(request: Request, token: str | None) -> bool:
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
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8732)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--node-id", default="hermes-mesh-node")
    parser.add_argument("--role", default="controller")
    parser.add_argument("--token")
    args = parser.parse_args(argv)

    import uvicorn

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

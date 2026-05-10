"""MCP facade for a local hermes-mesh daemon.

Run a daemon for background sync, then expose this MCP server to Hermes as the
agent-facing control surface.
"""

from __future__ import annotations

import os
from typing import Any

from hermes_mesh.mcp_facade import DaemonClient


def make_client() -> DaemonClient:
    return DaemonClient(
        base_url=os.environ.get("HERMES_MESH_DAEMON_URL", "http://127.0.0.1:8732"),
        token=os.environ.get("HERMES_MESH_TOKEN", ""),
    )


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover - environment dependent
        raise SystemExit("mcp package with FastMCP is required to run the MCP facade") from exc

    mcp = FastMCP("hermes-mesh")

    @mcp.tool()
    def mesh_health() -> dict[str, Any]:
        """Return local hermes-mesh daemon health."""
        return make_client().health()

    @mcp.tool()
    def mesh_node() -> dict[str, Any]:
        """Return local hermes-mesh daemon node metadata."""
        return make_client().node()

    @mcp.tool()
    def list_memory_cards(state: str | None = "proposed") -> list[dict[str, Any]]:
        """List source-attributed memory cards from the local daemon."""
        return make_client().list_memory_cards(state=state)

    @mcp.tool()
    def propose_memory_card(card: dict[str, Any]) -> dict[str, Any]:
        """Submit a source-attributed memory card to the local daemon."""
        return make_client().propose_memory_card(card)

    @mcp.tool()
    def approve_memory_card(
        memory_id: str, actor: str = "lerippi", reason: str | None = None
    ) -> dict[str, Any]:
        """Approve a proposed memory card for shared use."""
        return make_client().approve_memory_card(memory_id, actor=actor, reason=reason)

    @mcp.tool()
    def reject_memory_card(
        memory_id: str, actor: str = "lerippi", reason: str | None = None
    ) -> dict[str, Any]:
        """Reject a proposed memory card."""
        return make_client().reject_memory_card(memory_id, actor=actor, reason=reason)

    mcp.run()


if __name__ == "__main__":
    main()

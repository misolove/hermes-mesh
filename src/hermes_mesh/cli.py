"""Command-line interface for Hermes Mesh MVP utilities."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from pydantic import ValidationError

from hermes_mesh.memory import MemoryCard
from hermes_mesh.registry import MemoryRegistry

DEFAULT_REGISTRY = Path.home() / ".hermes-mesh" / "registry"


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValidationError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hermes-mesh")
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help=f"registry root directory (default: {DEFAULT_REGISTRY})",
    )
    subparsers = parser.add_subparsers(dest="resource", required=True)

    memory = subparsers.add_parser("memory", help="manage shared-memory cards")
    memory_sub = memory.add_subparsers(dest="action", required=True)

    propose = memory_sub.add_parser("propose", help="store a proposed memory card from JSON")
    propose.add_argument("--file", type=Path, required=True, help="memory-card JSON file")
    propose.set_defaults(func=cmd_memory_propose)

    list_cmd = memory_sub.add_parser("list", help="list memory cards")
    list_cmd.add_argument("--state", help="filter by promotion state")
    list_cmd.set_defaults(func=cmd_memory_list)

    approve = memory_sub.add_parser("approve", help="approve a memory card for sharing")
    approve.add_argument("memory_id")
    approve.add_argument("--actor", required=True)
    approve.add_argument("--reason")
    approve.set_defaults(func=cmd_memory_approve)

    reject = memory_sub.add_parser("reject", help="reject a memory card")
    reject.add_argument("memory_id")
    reject.add_argument("--actor", required=True)
    reject.add_argument("--reason")
    reject.set_defaults(func=cmd_memory_reject)

    return parser


def cmd_memory_propose(args: argparse.Namespace) -> int:
    payload = json.loads(args.file.read_text(encoding="utf-8"))
    card = MemoryCard.model_validate(payload)
    saved = MemoryRegistry(args.registry).propose(card)
    print_json(saved.to_json_dict())
    return 0


def cmd_memory_list(args: argparse.Namespace) -> int:
    cards = MemoryRegistry(args.registry).list_cards(state=args.state)
    print_json([card.to_json_dict() for card in cards])
    return 0


def cmd_memory_approve(args: argparse.Namespace) -> int:
    card = MemoryRegistry(args.registry).approve(args.memory_id, actor=args.actor, reason=args.reason)
    print_json(card.to_json_dict())
    return 0


def cmd_memory_reject(args: argparse.Namespace) -> int:
    card = MemoryRegistry(args.registry).reject(args.memory_id, actor=args.actor, reason=args.reason)
    print_json(card.to_json_dict())
    return 0


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())

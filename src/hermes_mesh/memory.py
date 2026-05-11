"""Source-attributed shared-memory cards for Hermes Mesh.

The important invariant is that shared memories are never anonymous. Every card
must carry source/provenance so another Hermes does not confuse imported memory
with its own direct observation.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MEMORY_ID_PATTERN = re.compile(r"^mem_[a-f0-9]{16}$")


def validate_memory_id(value: str | None) -> str:
    if not value or not MEMORY_ID_PATTERN.fullmatch(value):
        raise ValueError("memory_id must match mem_<16 lowercase hex chars>")
    return value


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Sensitivity(str, Enum):
    PUBLIC = "public"
    LOW = "low"
    INTERNAL = "internal"
    SECRET = "secret"
    DANGEROUS = "dangerous"


class PromotionState(str, Enum):
    # @lat: [[shared-memory#Promotion Policy]]
    LOCAL_ONLY = "local_only"
    PROPOSED = "proposed"
    SHARED_CANDIDATE = "shared_candidate"
    APPROVED_SHARED = "approved_shared"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Evidence(BaseModel):
    """Redacted pointer to the observation that produced a memory."""

    model_config = ConfigDict(extra="allow")

    type: str
    redacted: bool = True

    @field_validator("type")
    @classmethod
    def require_non_empty_type(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("evidence type must be non-empty")
        return value


class MemorySource(BaseModel):
    """Provenance for a shared memory card."""

    node_id: str
    agent: str
    method: str
    observed_at: datetime
    evidence: list[Evidence] = Field(default_factory=list)

    @field_validator("node_id", "agent", "method")
    @classmethod
    def require_non_empty_source_field(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source fields must be non-empty")
        return value


class Promotion(BaseModel):
    state: PromotionState = PromotionState.PROPOSED
    requires_user_confirmation: bool = True
    approved_by: str | None = None
    rejected_by: str | None = None
    reason: str | None = None
    decided_at: datetime | None = None


class MemoryCard(BaseModel):
    """A durable memory proposal that can be shared between Hermes nodes."""
    # @lat: [[shared-memory#Source Attributed Memory Cards]]

    kind: Literal["memory_card"] = "memory_card"
    id: str | None = None
    subject: str
    title: str
    content: str
    source: MemorySource
    confidence: Confidence = Confidence.MEDIUM
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    promotion: Promotion = Field(default_factory=Promotion)
    scope: dict[str, Any] = Field(default_factory=dict)
    links: dict[str, Any] = Field(default_factory=dict)

    @field_validator("subject", "title", "content")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("memory card text fields must be non-empty")
        return value

    @field_validator("id")
    @classmethod
    def require_safe_memory_id(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_memory_id(value)

    @model_validator(mode="after")
    def fill_stable_id_and_enforce_secret_policy(self) -> MemoryCard:
        if self.id is None:
            self.id = stable_memory_id(self)
        if self.sensitivity in {Sensitivity.SECRET, Sensitivity.DANGEROUS}:
            self.promotion.requires_user_confirmation = True
        return self

    def can_auto_promote(self, *, auto_promote_low_sensitivity: bool = False) -> bool:
        """Return whether policy may promote this card without asking the user."""
        # @lat: [[shared-memory#Promotion Policy]]

        if self.sensitivity in {Sensitivity.SECRET, Sensitivity.DANGEROUS, Sensitivity.INTERNAL}:
            return False
        if self.promotion.requires_user_confirmation and not auto_promote_low_sensitivity:
            return False
        return self.sensitivity in {Sensitivity.PUBLIC, Sensitivity.LOW}

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


def stable_memory_id(card: MemoryCard) -> str:
    """Create a deterministic ID from memory content and provenance."""
    # @lat: [[shared-memory#Local Registry Contract]]

    payload = {
        "kind": card.kind,
        "subject": card.subject,
        "title": card.title,
        "content": card.content,
        "source": card.source.model_dump(mode="json"),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"mem_{digest}"

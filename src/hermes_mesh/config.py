"""Configuration models and YAML loading for hermes-mesh daemons."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class NodeConfig(BaseModel):
    id: str
    role: str = "worker"
    name: str | None = None

    @field_validator("id", "role")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("node fields must be non-empty")
        return value


class ServerConfig(BaseModel):
    # @lat: [[configuration#Server Config]]
    host: str = "127.0.0.1"
    port: int = 8732
    token: str | None = None
    token_env: str | None = None

    @model_validator(mode="after")
    def resolve_token(self) -> ServerConfig:
        if self.token is None and self.token_env:
            self.token = os.environ.get(self.token_env)
        return self


class RegistryConfig(BaseModel):
    path: Path = Path.home() / ".hermes-mesh" / "registry"


class SyncConfig(BaseModel):
    heartbeat_interval_seconds: int = 30
    sync_interval_seconds: int = 60
    enabled: bool = True


class PeerConfig(BaseModel):
    # @lat: [[configuration#Peer Config]]
    id: str
    url: str
    token: str | None = None
    token_env: str | None = None
    role: Literal["controller", "worker", "peer"] = "peer"
    enabled: bool = True

    @field_validator("id", "url")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("peer fields must be non-empty")
        return value.rstrip("/") if value.startswith("http") else value

    @model_validator(mode="after")
    def resolve_token(self) -> PeerConfig:
        if self.token is None and self.token_env:
            self.token = os.environ.get(self.token_env)
        if self.enabled and not self.token:
            raise ValueError(f"peer {self.id} requires token or token_env")
        return self


class DaemonConfig(BaseModel):
    # @lat: [[configuration#Daemon Config Model]]
    node: NodeConfig
    server: ServerConfig = Field(default_factory=ServerConfig)
    registry: RegistryConfig = Field(default_factory=RegistryConfig)
    sync: SyncConfig = Field(default_factory=SyncConfig)
    peers: list[PeerConfig] = Field(default_factory=list)


def load_daemon_config(path: str | Path) -> DaemonConfig:
    # @lat: [[configuration#Loading Config]]
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return DaemonConfig.model_validate(raw)

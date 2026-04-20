"""Data models for solver traces."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    duration_ms: float = 0.0
    timestamp: datetime | None = None


class Message(BaseModel):
    role: str
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    timestamp: datetime | None = None


class AgentTrace(BaseModel):
    messages: list[Message] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    output: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    started_at: datetime | None = None
    finished_at: datetime | None = None

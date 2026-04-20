"""Tests for solver trace models."""

from __future__ import annotations

from datetime import UTC, datetime

from gbr_eval.solvers.models import AgentTrace, Message, ToolCall


class TestToolCall:
    def test_defaults(self) -> None:
        tc = ToolCall(tool_name="search")
        assert tc.tool_name == "search"
        assert tc.arguments == {}
        assert tc.result is None
        assert tc.duration_ms == 0.0

    def test_with_all_fields(self) -> None:
        tc = ToolCall(
            tool_name="onr_query",
            arguments={"matricula": "12345"},
            result={"status": "ok"},
            duration_ms=150.0,
            timestamp=datetime(2026, 4, 20, tzinfo=UTC),
        )
        assert tc.arguments["matricula"] == "12345"
        assert tc.duration_ms == 150.0


class TestMessage:
    def test_defaults(self) -> None:
        msg = Message(role="user")
        assert msg.role == "user"
        assert msg.content == ""
        assert msg.tool_calls == []

    def test_with_tool_calls(self) -> None:
        tc = ToolCall(tool_name="search", arguments={"q": "test"})
        msg = Message(role="assistant", content="let me search", tool_calls=[tc])
        assert len(msg.tool_calls) == 1


class TestAgentTrace:
    def test_defaults(self) -> None:
        trace = AgentTrace()
        assert trace.messages == []
        assert trace.tool_calls == []
        assert trace.output == {}
        assert trace.cost_usd == 0.0
        assert trace.latency_ms == 0.0

    def test_with_output(self) -> None:
        trace = AgentTrace(output={"cpf": "123.456.789-09"})
        assert trace.output["cpf"] == "123.456.789-09"

    def test_serialization_roundtrip(self) -> None:
        tc = ToolCall(tool_name="onr", arguments={"id": "1"}, result="ok")
        msg = Message(role="assistant", tool_calls=[tc])
        trace = AgentTrace(
            messages=[msg],
            tool_calls=[tc],
            output={"result": "pass"},
            cost_usd=0.05,
            latency_ms=2500.0,
            started_at=datetime(2026, 4, 20, tzinfo=UTC),
        )
        data = trace.model_dump(mode="json")
        restored = AgentTrace.model_validate(data)
        assert len(restored.messages) == 1
        assert restored.cost_usd == 0.05
        assert restored.tool_calls[0].tool_name == "onr"

    def test_metadata(self) -> None:
        trace = AgentTrace(metadata={"solver": "agent_v2", "run_id": "abc"})
        assert trace.metadata["solver"] == "agent_v2"

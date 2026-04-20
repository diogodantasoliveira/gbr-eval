"""Tests for OutputRecorder and EvalClient in gbr_eval.harness.client."""

from __future__ import annotations

import io
import json
import socket
import urllib.error
import urllib.request
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from gbr_eval.harness.client import EvalClient, EvalClientError, OutputRecorder

if TYPE_CHECKING:
    from pathlib import Path


class TestOutputRecorder:
    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        recorder = OutputRecorder(record_dir=tmp_path)
        output = {"cpf": "123.456.789-09", "nome": "João Silva", "score": 0.98}

        recorder.save("test.task", 1, output)
        loaded = recorder.load("test.task", 1)

        assert loaded == output

    def test_load_missing_returns_none(self, tmp_path: Path) -> None:
        recorder = OutputRecorder(record_dir=tmp_path)

        result = recorder.load("nonexistent.task", 99)

        assert result is None

    def test_load_all_multiple_cases(self, tmp_path: Path) -> None:
        recorder = OutputRecorder(record_dir=tmp_path)
        outputs = {
            1: {"field": "value_1"},
            2: {"field": "value_2"},
            3: {"field": "value_3"},
        }
        for case_number, output in outputs.items():
            recorder.save("test.task", case_number, output)

        all_cases = recorder.load_all("test.task")

        assert len(all_cases) == 3
        assert all_cases[1] == outputs[1]
        assert all_cases[2] == outputs[2]
        assert all_cases[3] == outputs[3]

    def test_save_creates_directories(self, tmp_path: Path) -> None:
        nested_dir = tmp_path / "deep" / "nested" / "path"
        recorder = OutputRecorder(record_dir=nested_dir)
        output = {"key": "value"}

        saved_path = recorder.save("test.task", 0, output)

        assert saved_path.exists()
        assert saved_path.read_text(encoding="utf-8") != ""

    def test_load_all_empty_task_returns_empty_dict(self, tmp_path: Path) -> None:
        recorder = OutputRecorder(record_dir=tmp_path)

        result = recorder.load_all("nonexistent.task")

        assert result == {}

    def test_save_overwrites_existing(self, tmp_path: Path) -> None:
        recorder = OutputRecorder(record_dir=tmp_path)

        recorder.save("test.task", 1, {"value": "first"})
        recorder.save("test.task", 1, {"value": "second"})
        loaded = recorder.load("test.task", 1)

        assert loaded == {"value": "second"}

    def test_load_all_preserves_case_numbers(self, tmp_path: Path) -> None:
        recorder = OutputRecorder(record_dir=tmp_path)
        recorder.save("test.task", 5, {"case": 5})
        recorder.save("test.task", 10, {"case": 10})

        all_cases = recorder.load_all("test.task")

        assert 5 in all_cases
        assert 10 in all_cases
        assert all_cases[5] == {"case": 5}
        assert all_cases[10] == {"case": 10}

    def test_path_traversal_blocked(self, tmp_path: Path) -> None:
        recorder = OutputRecorder(record_dir=tmp_path)

        with pytest.raises(ValueError, match="path traversal"):
            recorder.save("../../etc/passwd", 1, {})

    def test_path_traversal_blocked_load(self, tmp_path: Path) -> None:
        recorder = OutputRecorder(record_dir=tmp_path)

        with pytest.raises(ValueError, match="path traversal"):
            recorder.load("../../../secret", 1)

    def test_load_all_skips_malformed_json(self, tmp_path: Path) -> None:
        """load_all raises JSONDecodeError for malformed JSON files (documents corrupt data)."""
        recorder = OutputRecorder(record_dir=tmp_path)
        # Save a valid case first
        recorder.save("task1", 1, {"valid": True})
        # Write a malformed JSON file directly into the task directory
        task_dir = tmp_path / "task1"
        (task_dir / "case_002.json").write_text("not valid json{{{", encoding="utf-8")
        # load_all must raise JSONDecodeError — crashing is the correct contract
        # for a recorder used in replay; silent skip would hide corrupt recorded data
        with pytest.raises(json.JSONDecodeError):
            recorder.load_all("task1")

    def test_path_traversal_blocked_load_all(self, tmp_path: Path) -> None:
        """load_all must reject path traversal in task_id."""
        recorder = OutputRecorder(record_dir=tmp_path)
        with pytest.raises(ValueError, match="path traversal"):
            recorder.load_all("../../etc")


class TestEvalClient:
    def test_eval_client_validates_url_scheme(self) -> None:
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            EvalClient(base_url="ftp://bad")

    def test_eval_client_validates_hostname(self) -> None:
        with pytest.raises(ValueError, match="no hostname"):
            EvalClient(base_url="http://")

    def test_eval_client_accepts_http(self) -> None:
        client = EvalClient(base_url="http://localhost:8000", allow_internal=True)
        assert client.base_url == "http://localhost:8000"

    def test_eval_client_accepts_https(self) -> None:
        with patch("socket.gethostbyname", return_value="1.1.1.1"):
            client = EvalClient(base_url="https://staging.api.com")
        assert client.base_url == "https://staging.api.com"

    def test_eval_client_call_success(self) -> None:
        client = EvalClient(base_url="http://localhost:8000", headers={"X-Tenant-ID": "test"}, allow_internal=True)
        response_data = {"cpf": "123.456.789-09", "score": 0.98}
        response_bytes = json.dumps(response_data).encode()

        mock_response = MagicMock()
        mock_response.read.return_value = response_bytes
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            result = client.call("/api/extract", {"skill": "matricula_v1"})

        assert result == response_data
        args, kwargs = mock_urlopen.call_args
        req: urllib.request.Request = args[0]
        assert req.get_header("X-tenant-id") == "test"

    def test_eval_client_call_http_error(self) -> None:
        client = EvalClient(base_url="http://localhost:8000", allow_internal=True)
        http_error = urllib.error.HTTPError(
            url="http://localhost:8000/api/extract",
            code=422,
            msg="Unprocessable Entity",
            hdrs=MagicMock(),  # type: ignore[arg-type]
            fp=io.BytesIO(b"validation error"),
        )

        with patch("urllib.request.urlopen", side_effect=http_error), pytest.raises(EvalClientError, match="HTTP 422"):
            client.call("/api/extract", {})

    def test_eval_client_call_connection_error(self) -> None:
        client = EvalClient(base_url="http://localhost:8000", allow_internal=True)
        url_error = urllib.error.URLError(reason="Connection refused")

        with (
            patch("urllib.request.urlopen", side_effect=url_error),
            pytest.raises(EvalClientError, match="Connection failed"),
        ):
            client.call("/api/extract", {})

    def test_eval_client_call_timeout(self) -> None:
        client = EvalClient(base_url="http://localhost:8000", allow_internal=True)

        with (
            patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")),
            pytest.raises(EvalClientError, match="Timeout"),
        ):
            client.call("/api/extract", {})

    def test_eval_client_call_invalid_json(self) -> None:
        client = EvalClient(base_url="http://localhost:8000", allow_internal=True)

        mock_response = MagicMock()
        mock_response.read.return_value = b"not valid json {{{"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("urllib.request.urlopen", return_value=mock_response),
            pytest.raises(EvalClientError, match="Invalid JSON"),
        ):
            client.call("/api/extract", {})

    def test_blocks_localhost(self) -> None:
        with (
            patch("socket.gethostbyname", return_value="127.0.0.1"),
            pytest.raises(ValueError, match="SSRF protection"),
        ):
            EvalClient(base_url="http://127.0.0.1:8000")

    def test_blocks_private_10(self) -> None:
        with (
            patch("socket.gethostbyname", return_value="10.0.0.1"),
            pytest.raises(ValueError, match="SSRF protection"),
        ):
            EvalClient(base_url="http://10.0.0.1:8000")

    def test_blocks_private_172(self) -> None:
        with (
            patch("socket.gethostbyname", return_value="172.16.0.1"),
            pytest.raises(ValueError, match="SSRF protection"),
        ):
            EvalClient(base_url="http://172.16.0.1:8000")

    def test_blocks_private_192(self) -> None:
        with (
            patch("socket.gethostbyname", return_value="192.168.1.1"),
            pytest.raises(ValueError, match="SSRF protection"),
        ):
            EvalClient(base_url="http://192.168.1.1:8000")

    def test_allows_internal_flag(self) -> None:
        client = EvalClient(base_url="http://127.0.0.1:8000", allow_internal=True)
        assert client.base_url == "http://127.0.0.1:8000"

    def test_allows_public_ip(self) -> None:
        with patch("socket.gethostbyname", return_value="8.8.8.8"):
            client = EvalClient(base_url="http://8.8.8.8:8000")
        assert client.base_url == "http://8.8.8.8:8000"

    def test_dns_rebinding_blocked_at_call_time(self) -> None:
        """DNS rebinding: construction resolves to public IP, call-time resolves to internal IP.

        The __post_init__ check passes (public IP), but call() re-resolves and detects
        the internal IP returned by the rebinding attack, raising EvalClientError.
        """
        # Construction-time: gethostbyname returns public IP — passes __post_init__
        with patch("socket.gethostbyname", return_value="1.2.3.4"):
            client = EvalClient(base_url="http://staging.example.com:8000")

        # Call-time: getaddrinfo returns internal IP — rebinding attack
        internal_addrinfo = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 8000))
        ]
        with (
            patch("socket.getaddrinfo", return_value=internal_addrinfo),
            pytest.raises(EvalClientError, match="SSRF protection \\(call-time\\)"),
        ):
            client.call("/api/extract", {"skill": "matricula_v1"})

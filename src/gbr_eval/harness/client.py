"""HTTP client for online eval against ai-engine staging + output recording."""

from __future__ import annotations

import ipaddress
import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class EvalClientError(Exception):
    """Raised when an eval HTTP call fails."""


def _is_internal_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return True
        # Explicit IPv6 private ranges not always caught by is_private in older Python
        if isinstance(ip, ipaddress.IPv6Address):
            # ::1 loopback, fe80::/10 link-local, fc00::/7 ULA (fc00:: and fd00::)
            ula_range = ipaddress.IPv6Network("fc00::/7")
            if ip in ula_range:
                return True
        return False
    except ValueError:
        return True


@dataclass
class EvalClient:
    """Calls the ai-engine API for online eval."""

    base_url: str
    headers: dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    allow_internal: bool = False

    def __post_init__(self) -> None:
        from urllib.parse import urlparse

        parsed = urlparse(self.base_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid URL scheme: {parsed.scheme!r} (expected http or https)")
        if not parsed.hostname:
            raise ValueError(f"Invalid URL: no hostname in {self.base_url!r}")
        if not self.allow_internal:
            hostname = parsed.hostname
            try:
                resolved_ip = socket.gethostbyname(hostname)
            except socket.gaierror as exc:
                raise ValueError(f"Cannot resolve hostname: {hostname}") from exc
            if _is_internal_ip(resolved_ip):
                raise ValueError(
                    f"SSRF protection: endpoint resolves to internal IP ({resolved_ip}). "
                    f"Use allow_internal=True for local development."
                )

    def call(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(self.base_url)
        hostname = parsed.hostname or ""
        port = parsed.port

        if not self.allow_internal:
            # Re-resolve at call time to prevent DNS rebinding: attacker's DNS
            # returned a public IP at construction, then switches to an internal
            # IP by the time the actual request fires.
            try:
                addrinfos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
            except socket.gaierror as exc:
                raise EvalClientError(f"SSRF check: cannot resolve {hostname!r} at call time: {exc}") from exc

            for addrinfo in addrinfos:
                # addrinfo[4] is the socket address tuple; element [0] is always
                # the IP string for AF_INET and AF_INET6.
                resolved_ip = str(addrinfo[4][0])
                if _is_internal_ip(resolved_ip):
                    raise EvalClientError(
                        f"SSRF protection (call-time): {hostname!r} resolved to internal IP "
                        f"({resolved_ip}). Use allow_internal=True for local development."
                    )

            # Pin the first resolved IP into the URL and preserve the Host header
            # so TLS SNI and virtual hosting still work with the original hostname.
            first_ip = str(addrinfos[0][4][0])
            # For IPv6, the address must be bracketed in the URL
            netloc_ip = f"[{first_ip}]" if ":" in first_ip else first_ip
            if port:
                netloc_ip = f"{netloc_ip}:{port}"
            # Build netloc string and reconstruct URL (urlunparse takes a plain tuple)
            pinned_base = urlunparse((
                parsed.scheme,
                netloc_ip,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            ))
            url = f"{pinned_base.rstrip('/')}{endpoint}"
            host_header = hostname if not port else f"{hostname}:{port}"
        else:
            url = f"{self.base_url.rstrip('/')}{endpoint}"
            host_header = None

        body = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if host_header:
            req.add_header("Host", host_header)
        for k, v in self.headers.items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result: dict[str, Any] = json.loads(resp.read())
                return result
        except urllib.error.HTTPError as e:
            error_body = e.read().decode(errors="replace")
            raise EvalClientError(f"HTTP {e.code} from {url}: {error_body[:500]}") from e
        except urllib.error.URLError as e:
            raise EvalClientError(f"Connection failed to {url}: {e.reason}") from e
        except (TimeoutError, OSError) as e:
            raise EvalClientError(f"Timeout/network error calling {url}: {e}") from e
        except (json.JSONDecodeError, ValueError) as e:
            raise EvalClientError(f"Invalid JSON response from {url}: {e}") from e


@dataclass
class OutputRecorder:
    """Saves and loads eval outputs for record/replay."""

    record_dir: Path

    def _safe_task_dir(self, task_id: str) -> Path:
        task_dir = (self.record_dir / task_id).resolve()
        if not task_dir.is_relative_to(self.record_dir.resolve()):
            raise ValueError(f"Invalid task_id: path traversal detected in {task_id!r}")
        return task_dir

    def save(self, task_id: str, case_number: int, output: dict[str, Any]) -> Path:
        task_dir = self._safe_task_dir(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        path = task_dir / f"case_{case_number:03d}.json"
        path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def load(self, task_id: str, case_number: int) -> dict[str, Any] | None:
        task_dir = self._safe_task_dir(task_id)
        path = task_dir / f"case_{case_number:03d}.json"
        if path.exists():
            result: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            return result
        return None

    def load_all(self, task_id: str) -> dict[int, dict[str, Any]]:
        task_dir = self._safe_task_dir(task_id)
        if not task_dir.is_dir():
            return {}
        results: dict[int, dict[str, Any]] = {}
        for f in sorted(task_dir.glob("case_[0-9]*.json")):
            stem = f.stem.replace("case_", "")
            if stem.isdigit():
                results[int(stem)] = json.loads(f.read_text(encoding="utf-8"))
        return results

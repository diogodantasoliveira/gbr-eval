"""Contract validator — JSON Schema snapshot-based validation without external deps."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

_JSON_TYPE_MAP: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None),
}


@dataclass
class ContractResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    schema_version: str = ""


def _check_type(value: Any, json_type: str) -> bool:
    """Return True if value matches the JSON Schema type string."""
    expected = _JSON_TYPE_MAP.get(json_type)
    if expected is None:
        return True  # unknown type — skip
    # JSON Schema "number" includes integers
    if json_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if json_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, expected)


def _validate_properties(
    response: dict[str, Any],
    properties: dict[str, Any],
    errors: list[str],
) -> None:
    """Validate type constraints for each declared property present in response."""
    for prop_name, prop_schema in properties.items():
        if prop_name not in response:
            continue  # presence enforced by required check
        value = response[prop_name]
        expected_type = prop_schema.get("type")
        if expected_type and not _check_type(value, expected_type):
            errors.append(
                f"Property '{prop_name}': expected type '{expected_type}', "
                f"got '{type(value).__name__}'"
            )
            continue
        # Numeric range constraints
        if expected_type in ("number", "integer"):
            minimum = prop_schema.get("minimum")
            maximum = prop_schema.get("maximum")
            if minimum is not None and value < minimum:
                errors.append(
                    f"Property '{prop_name}': value {value} is below minimum {minimum}"
                )
            if maximum is not None and value > maximum:
                errors.append(
                    f"Property '{prop_name}': value {value} is above maximum {maximum}"
                )


def validate_response(response: dict[str, Any], schema_path: Path) -> ContractResult:
    """Validate a response dict against a JSON Schema snapshot on disk.

    Checks:
    - All "required" fields are present.
    - "type" constraints match for declared properties.
    - Numeric "minimum"/"maximum" constraints are satisfied.

    No external dependencies required.
    """
    raw = schema_path.read_text(encoding="utf-8")
    schema: dict[str, Any] = json.loads(raw)

    schema_version = schema.get("title", schema_path.name)
    errors: list[str] = []

    # Check required fields
    required_fields: list[str] = schema.get("required", [])
    for req_field in required_fields:
        if req_field not in response:
            errors.append(f"Missing required field: '{req_field}'")

    # Validate property types and constraints
    properties: dict[str, Any] = schema.get("properties", {})
    _validate_properties(response, properties, errors)

    return ContractResult(
        valid=len(errors) == 0,
        errors=errors,
        schema_version=schema_version,
    )

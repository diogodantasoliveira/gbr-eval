"""Tests for the scope_check AST-based grader."""

import gbr_eval.graders.scope  # noqa: F401
from gbr_eval.graders.base import grade
from gbr_eval.harness.models import GraderSpec

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

router_with_audit = """
from fastapi import APIRouter
router = APIRouter()

@router.post("/items")
async def create_item(item: ItemCreate, audit: AuditAppender = Depends(get_audit)):
    result = service.create(item)
    await audit.append(action=AuditAction.CREATE, resource_type="item", resource_id=result.id)
    return result
"""

router_without_audit = """
from fastapi import APIRouter
router = APIRouter()

@router.post("/items")
async def create_item(item: ItemCreate):
    result = service.create(item)
    return result

@router.get("/items")
async def list_items():
    return service.list()
"""

router_mixed = """
@router.post("/charge")
async def create_charge(charge: ChargeCreate):
    result = service.create(charge)
    return result

@router.delete("/charge/{id}")
async def delete_charge(id: str, audit: AuditAppender = Depends(get_audit)):
    service.delete(id)
    await audit.append(action=AuditAction.DELETE, resource_type="charge", resource_id=id)
"""

router_with_idempotency = """
from fastapi import APIRouter
router = APIRouter()

@router.post("/payments")
async def create_payment(
    payload: PaymentCreate,
    idempotency_key: str = Header(...),
):
    return service.create(payload, idempotency_key=idempotency_key)
"""

router_without_idempotency = """
from fastapi import APIRouter
router = APIRouter()

@router.post("/payments")
async def create_payment(payload: PaymentCreate):
    return service.create(payload)

@router.put("/payments/{id}")
async def update_payment(id: str, payload: PaymentUpdate):
    return service.update(id, payload)
"""

router_with_forbidden = """
@router.post("/login")
async def login(username: str, password: str):
    print(f"Attempting login with password={password}")
    return auth.login(username, password)
"""

router_without_forbidden = """
@router.post("/login")
async def login(username: str, password: str):
    return auth.login(username, password)
"""

get_only_routes = """
@router.get("/items")
async def list_items():
    return service.list()

@router.get("/items/{id}")
async def get_item(id: str):
    return service.get(id)
"""

router_combined_pass = """
@router.post("/orders")
async def create_order(
    order: OrderCreate,
    idempotency_key: str = Header(...),
    audit: AuditAppender = Depends(get_audit),
):
    result = service.create(order)
    await audit.append(action=AuditAction.CREATE, resource_type="order", resource_id=result.id)
    return result
"""

router_combined_fail = """
@router.post("/orders")
async def create_order(order: OrderCreate):
    result = service.create(order)
    return result
"""

syntax_error_content = """
def broken(:
    pass
"""

empty_content = ""


# ---------------------------------------------------------------------------
# TestScopeCheckAudit — audit coverage scenarios
# ---------------------------------------------------------------------------


class TestScopeCheckAudit:
    def test_post_with_audit_passes(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.(post|put|delete|patch)",
                "required_call": r"audit\.append|create_audit",
            },
        )
        result = grade("scope_check", {"content": router_with_audit}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_post_without_audit_fails(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.(post|put|delete|patch)",
                "required_call": r"audit\.append|create_audit",
            },
        )
        result = grade("scope_check", {"content": router_without_audit}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "required_call" in result.details

    def test_mixed_routes_partial_score(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.(post|put|delete|patch)",
                "required_call": r"audit\.append",
            },
        )
        result = grade("scope_check", {"content": router_mixed}, {}, spec)
        assert not result.passed
        assert 0.0 < result.score < 1.0

    def test_get_only_file_skips_with_no_matches(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.(post|put|delete|patch)",
                "required_call": r"audit\.append",
                "skip_if_no_matches": True,
            },
        )
        result = grade("scope_check", {"content": get_only_routes}, {}, spec)
        assert result.passed
        assert result.score == 1.0
        assert "skip_if_no_matches" in result.details


# ---------------------------------------------------------------------------
# TestScopeCheckIdempotency — idempotency param detection
# ---------------------------------------------------------------------------


class TestScopeCheckIdempotency:
    def test_idempotency_key_in_signature_passes(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "required_param": r"idempotency_key|dedup_key",
            },
        )
        result = grade("scope_check", {"content": router_with_idempotency}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_missing_idempotency_key_fails(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.(post|put)",
                "required_param": r"idempotency_key|dedup_key",
            },
        )
        result = grade("scope_check", {"content": router_without_idempotency}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "required_param" in result.details

    def test_idempotency_in_annotated_type_hint_passes(self):
        code = """
@router.post("/charge")
async def create_charge(
    charge: ChargeCreate,
    key: Annotated[str, Header(alias="Idempotency-Key")] = None,
):
    return service.create(charge, dedup_key=key)
"""
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "required_param": r"dedup_key|Idempotency-Key",
            },
        )
        result = grade("scope_check", {"content": code}, {}, spec)
        assert result.passed
        assert result.score == 1.0


# ---------------------------------------------------------------------------
# TestScopeCheckForbidden — forbidden_call detection
# ---------------------------------------------------------------------------


class TestScopeCheckForbidden:
    def test_forbidden_call_absent_passes(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "forbidden_call": r"print\(.*password",
            },
        )
        result = grade("scope_check", {"content": router_without_forbidden}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_forbidden_call_present_fails(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "forbidden_call": r"print\(.*password",
            },
        )
        result = grade("scope_check", {"content": router_with_forbidden}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "forbidden_call" in result.details

    def test_forbidden_call_details_include_function_name(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "forbidden_call": r"print\(",
            },
        )
        result = grade("scope_check", {"content": router_with_forbidden}, {}, spec)
        assert not result.passed
        assert "login" in result.details


# ---------------------------------------------------------------------------
# TestScopeCheckEdgeCases — edge cases
# ---------------------------------------------------------------------------


class TestScopeCheckEdgeCases:
    def test_syntax_error_fails_with_details(self):
        spec = GraderSpec(
            type="scope_check",
            config={"decorator_pattern": r"@router\.post"},
        )
        result = grade("scope_check", {"content": syntax_error_content}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "SyntaxError" in result.details

    def test_empty_content_skips_when_no_matches(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "skip_if_no_matches": True,
            },
        )
        result = grade("scope_check", {"content": empty_content}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_no_matches_fails_when_skip_false(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "skip_if_no_matches": False,
            },
        )
        result = grade("scope_check", {"content": get_only_routes}, {}, spec)
        assert not result.passed
        assert result.score == 0.0

    def test_no_decorator_pattern_fails(self):
        spec = GraderSpec(
            type="scope_check",
            config={},
        )
        result = grade("scope_check", {"content": router_with_audit}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "decorator_pattern" in result.details

    def test_catastrophic_decorator_pattern_rejected(self):
        spec = GraderSpec(
            type="scope_check",
            config={"decorator_pattern": "(a+)+$"},
        )
        result = grade("scope_check", {"content": router_with_audit}, {}, spec)
        assert not result.passed
        assert "catastrophic" in result.details.lower()

    def test_catastrophic_required_call_rejected(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "required_call": "(a+)+$",
            },
        )
        result = grade("scope_check", {"content": router_with_audit}, {}, spec)
        assert not result.passed
        assert "catastrophic" in result.details.lower()

    def test_no_functions_no_decorators(self):
        code = """
x = 1
y = 2
result = x + y
"""
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "skip_if_no_matches": True,
            },
        )
        result = grade("scope_check", {"content": code}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_custom_file_key(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "required_call": r"audit\.append",
                "file_key": "source",
            },
        )
        result = grade("scope_check", {"source": router_with_audit}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_missing_file_key_skips_gracefully(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "skip_if_no_matches": True,
                "file_key": "content",
            },
        )
        result = grade("scope_check", {}, {}, spec)
        assert result.passed
        assert result.score == 1.0


# ---------------------------------------------------------------------------
# TestScopeCheckCombined — required_call + required_param together
# ---------------------------------------------------------------------------


class TestScopeCheckCombined:
    def test_combined_both_present_passes(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "required_call": r"audit\.append",
                "required_param": r"idempotency_key",
            },
        )
        result = grade("scope_check", {"content": router_combined_pass}, {}, spec)
        assert result.passed
        assert result.score == 1.0

    def test_combined_both_absent_fails(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "required_call": r"audit\.append",
                "required_param": r"idempotency_key",
            },
        )
        result = grade("scope_check", {"content": router_combined_fail}, {}, spec)
        assert not result.passed
        assert result.score == 0.0
        assert "required_call" in result.details
        assert "required_param" in result.details

    def test_details_include_line_number(self):
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "required_call": r"audit\.append",
            },
        )
        result = grade("scope_check", {"content": router_without_audit}, {}, spec)
        assert not result.passed
        assert ":" in result.details

    def test_all_three_checks_combined_pass(self):
        code = """
@router.post("/payments")
async def create_payment(
    payload: PaymentCreate,
    idempotency_key: str = Header(...),
    audit: AuditAppender = Depends(get_audit),
):
    result = service.create(payload)
    await audit.append(action=AuditAction.CREATE, resource_type="payment", resource_id=result.id)
    return result
"""
        spec = GraderSpec(
            type="scope_check",
            config={
                "decorator_pattern": r"@router\.post",
                "required_call": r"audit\.append",
                "required_param": r"idempotency_key",
                "forbidden_call": r"print\(",
            },
        )
        result = grade("scope_check", {"content": code}, {}, spec)
        assert result.passed
        assert result.score == 1.0

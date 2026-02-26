import json

import pytest
from fastapi import Request
from fastapi.responses import Response

from app.enterprise_readiness import (
    authorize_write_request,
    build_enterprise_audit_middleware,
    enterprise_policy_version,
    is_feature_enabled,
    load_capability_rules,
    load_feature_flags,
    redact_sensitive,
    validate_enterprise_runtime_config,
)


def test_feature_flags_support_tenant_and_role_scoping(monkeypatch):
    monkeypatch.setenv(
        "ENTERPRISE_FEATURE_FLAGS_JSON",
        json.dumps(
            {
                "proposal.write": {
                    "tenant-a": {"advisor": True, "*": False},
                    "*": {"*": False},
                }
            }
        ),
    )
    assert is_feature_enabled("proposal.write", "tenant-a", "advisor") is True
    assert is_feature_enabled("proposal.write", "tenant-a", "viewer") is False
    assert is_feature_enabled("proposal.write", "tenant-b", "advisor") is False


def test_redact_sensitive_masks_known_fields():
    payload = {
        "client_email": "user@example.com",
        "details": {"token": "abc", "allowed": "value"},
    }
    redacted = redact_sensitive(payload)
    assert redacted["client_email"] == "***REDACTED***"
    assert redacted["details"]["token"] == "***REDACTED***"
    assert redacted["details"]["allowed"] == "value"


def test_authorize_write_request_enforces_required_headers_when_enabled(monkeypatch):
    monkeypatch.setenv("ENTERPRISE_ENFORCE_AUTHZ", "true")
    allowed, reason = authorize_write_request("POST", "/proposals", {})
    assert allowed is False
    assert reason.startswith("missing_headers:")


def test_authorize_write_request_enforces_capability_rules(monkeypatch):
    monkeypatch.setenv("ENTERPRISE_ENFORCE_AUTHZ", "true")
    monkeypatch.setenv(
        "ENTERPRISE_CAPABILITY_RULES_JSON",
        json.dumps({"POST /proposals": "proposal.write"}),
    )
    headers = {
        "X-Actor-Id": "a1",
        "X-Tenant-Id": "t1",
        "X-Role": "advisor",
        "X-Correlation-Id": "c1",
        "X-Service-Identity": "aea",
        "X-Capabilities": "proposal.read",
    }
    denied, denied_reason = authorize_write_request("POST", "/proposals/123", headers)
    assert denied is False
    assert denied_reason == "missing_capability:proposal.write"

    headers["X-Capabilities"] = "proposal.read,proposal.write"
    allowed, allowed_reason = authorize_write_request("POST", "/proposals/123", headers)
    assert allowed is True
    assert allowed_reason is None


def test_validate_enterprise_runtime_config_reports_rotation_issue(monkeypatch):
    monkeypatch.setenv("ENTERPRISE_SECRET_ROTATION_DAYS", "120")
    issues = validate_enterprise_runtime_config()
    assert "secret_rotation_days_out_of_range" in issues


def test_validate_enterprise_runtime_config_fallback_for_invalid_int(monkeypatch):
    monkeypatch.setenv("ENTERPRISE_SECRET_ROTATION_DAYS", "bad-int")
    issues = validate_enterprise_runtime_config()
    assert issues == []


def test_load_feature_flags_and_capability_rules_ignore_invalid_json(monkeypatch):
    monkeypatch.setenv("ENTERPRISE_FEATURE_FLAGS_JSON", "not-json")
    monkeypatch.setenv("ENTERPRISE_CAPABILITY_RULES_JSON", "[]")
    assert load_feature_flags() == {}
    assert load_capability_rules() == {}


def test_validate_enterprise_runtime_config_can_raise_when_enforced(monkeypatch):
    monkeypatch.setenv("ENTERPRISE_POLICY_VERSION", " ")
    monkeypatch.setenv("ENTERPRISE_SECRET_ROTATION_DAYS", "-1")
    monkeypatch.setenv("ENTERPRISE_ENFORCE_RUNTIME_CONFIG", "true")
    with pytest.raises(RuntimeError, match="enterprise_runtime_config_invalid"):
        validate_enterprise_runtime_config()


def test_validate_enterprise_runtime_config_requires_primary_key_when_authz_enabled(monkeypatch):
    monkeypatch.setenv("ENTERPRISE_ENFORCE_AUTHZ", "true")
    monkeypatch.delenv("ENTERPRISE_PRIMARY_KEY_ID", raising=False)
    issues = validate_enterprise_runtime_config()
    assert "missing_primary_key_id" in issues


def test_authorize_write_request_checks_service_identity(monkeypatch):
    monkeypatch.setenv("ENTERPRISE_ENFORCE_AUTHZ", "true")
    headers = {
        "X-Actor-Id": "a1",
        "X-Tenant-Id": "t1",
        "X-Role": "advisor",
        "X-Correlation-Id": "c1",
    }
    allowed, reason = authorize_write_request("PATCH", "/proposals", headers)
    assert allowed is False
    assert reason == "missing_service_identity"


@pytest.mark.asyncio
async def test_enterprise_middleware_rejects_oversized_write_payload(monkeypatch):
    monkeypatch.setenv("ENTERPRISE_MAX_WRITE_PAYLOAD_BYTES", "1")
    middleware = build_enterprise_audit_middleware()
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/proposals",
        "headers": [(b"content-length", b"4")],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 1234),
        "scheme": "http",
    }
    request = Request(scope)

    async def _call_next(_: Request) -> Response:
        return Response(status_code=200)

    response = await middleware(request, _call_next)
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_enterprise_middleware_sets_policy_header_on_success(monkeypatch):
    monkeypatch.setenv("ENTERPRISE_ENFORCE_AUTHZ", "false")
    monkeypatch.setenv("ENTERPRISE_POLICY_VERSION", "9.9.9")
    middleware = build_enterprise_audit_middleware()
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/health",
        "headers": [],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 1234),
        "scheme": "http",
    }
    request = Request(scope)

    async def _call_next(_: Request) -> Response:
        return Response(status_code=200)

    response = await middleware(request, _call_next)
    assert response.status_code == 200
    assert response.headers["X-Enterprise-Policy-Version"] == enterprise_policy_version()


def test_redact_sensitive_handles_list_values():
    payload = [{"password": "p1"}, {"nested": {"token": "t1"}}, "safe"]
    redacted = redact_sensitive(payload)
    assert redacted[0]["password"] == "***REDACTED***"
    assert redacted[1]["nested"]["token"] == "***REDACTED***"
    assert redacted[2] == "safe"


@pytest.mark.asyncio
async def test_enterprise_middleware_denies_unauthorized_write_and_returns_reason(monkeypatch):
    monkeypatch.setenv("ENTERPRISE_ENFORCE_AUTHZ", "true")
    middleware = build_enterprise_audit_middleware()
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/proposals",
        "headers": [(b"content-length", b"0")],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 1234),
        "scheme": "http",
    }
    request = Request(scope)

    async def _call_next(_: Request) -> Response:
        return Response(status_code=200)

    response = await middleware(request, _call_next)
    assert response.status_code == 403
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["detail"] == "authorization_policy_denied"


@pytest.mark.asyncio
async def test_enterprise_middleware_handles_invalid_content_length(monkeypatch):
    monkeypatch.setenv("ENTERPRISE_ENFORCE_AUTHZ", "false")
    middleware = build_enterprise_audit_middleware()
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/health",
        "headers": [(b"content-length", b"not-an-int")],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 1234),
        "scheme": "http",
    }
    request = Request(scope)

    async def _call_next(_: Request) -> Response:
        return Response(status_code=200)

    response = await middleware(request, _call_next)
    assert response.status_code == 200

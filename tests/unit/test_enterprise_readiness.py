import json

from app.enterprise_readiness import (
    authorize_write_request,
    is_feature_enabled,
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

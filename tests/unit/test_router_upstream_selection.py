from app.routers.platform import _platform_capabilities_service
from app.routers.proposals import _proposal_service
from app.routers.workbench import _workbench_service


def test_proposals_router_targets_advisory_base_url(monkeypatch):
    monkeypatch.setattr(
        "app.routers.proposals.settings.decisioning_service_base_url", "http://advise:8000"
    )
    monkeypatch.setattr(
        "app.routers.proposals.settings.management_service_base_url", "http://manage:8000"
    )
    monkeypatch.setattr("app.routers.proposals.settings.manage_split_enabled", True)

    service = _proposal_service()
    assert service._dpm_client._base_url == "http://advise:8000"


def test_workbench_router_targets_manage_when_split_enabled(monkeypatch):
    monkeypatch.setattr(
        "app.routers.workbench.settings.decisioning_service_base_url", "http://advise:8000"
    )
    monkeypatch.setattr(
        "app.routers.workbench.settings.management_service_base_url", "http://manage:8000"
    )
    monkeypatch.setattr("app.routers.workbench.settings.manage_split_enabled", True)

    service = _workbench_service()
    assert service._dpm_client._base_url == "http://manage:8000"


def test_workbench_router_targets_advisory_when_split_disabled(monkeypatch):
    monkeypatch.setattr(
        "app.routers.workbench.settings.decisioning_service_base_url", "http://advise:8000"
    )
    monkeypatch.setattr(
        "app.routers.workbench.settings.management_service_base_url", "http://manage:8000"
    )
    monkeypatch.setattr("app.routers.workbench.settings.manage_split_enabled", False)

    service = _workbench_service()
    assert service._dpm_client._base_url == "http://advise:8000"


def test_platform_capabilities_manage_client_obeys_split_flag(monkeypatch):
    monkeypatch.setattr("app.routers.platform.settings.manage_split_enabled", True)
    service = _platform_capabilities_service()
    assert service._manage_client is not None

    monkeypatch.setattr("app.routers.platform.settings.manage_split_enabled", False)
    service = _platform_capabilities_service()
    assert service._manage_client is None

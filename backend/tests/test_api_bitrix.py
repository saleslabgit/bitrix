from app import main
from app.main import bitrix_discovery, bitrix_sync_status, run_manual_bitrix_sync


def test_bitrix_api_surfaces_fail_safely_without_credentials(monkeypatch) -> None:
    monkeypatch.setattr(main.settings, "bitrix_webhook_url", None)
    monkeypatch.setattr(main.settings, "bitrix_contact_type_field", None)

    discovery = bitrix_discovery()
    run_status = run_manual_bitrix_sync()
    latest_status = bitrix_sync_status()

    assert discovery.state == "error"
    assert "webhook URL is not configured" in discovery.message
    assert run_status.dataset_kind == "bitrix_manual"
    assert run_status.state == "error"
    assert "webhook URL is not configured" in run_status.message
    assert latest_status.state == "error"

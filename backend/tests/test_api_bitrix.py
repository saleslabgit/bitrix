from app import main
from app.local_database import reset_connection
from app.main import bitrix_discovery, bitrix_sync_status, run_manual_bitrix_sync


def test_bitrix_api_surfaces_fail_safely_without_credentials(monkeypatch, tmp_path) -> None:
    reset_connection()
    monkeypatch.setattr(main.settings, "data_dir", tmp_path)
    monkeypatch.setattr(main.settings, "duckdb_path", tmp_path / "api-bitrix.duckdb")
    monkeypatch.setattr(main.settings, "bitrix_webhook_url", None)
    monkeypatch.setattr(main.settings, "bitrix_contact_type_field", None)

    try:
        discovery = bitrix_discovery()
        run_status = run_manual_bitrix_sync()
        latest_status = bitrix_sync_status()
    finally:
        reset_connection()

    assert discovery.state == "error"
    assert "webhook URL is not configured" in discovery.message
    assert run_status.dataset_kind == "bitrix_manual"
    assert run_status.state == "error"
    assert "webhook URL is not configured" in run_status.message
    assert latest_status.state == "error"

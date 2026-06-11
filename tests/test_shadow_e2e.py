"""End-to-end smoke test — manual trigger of observation runner with a test signal."""

from pathlib import Path

from src.shadow.wiring import build_shadow_stack
from src.config.settings import RuntimeConfig, RiskConfig


def test_shadow_e2e_smoke(tmp_path, monkeypatch):
    """Full smoke test: start observation → process signal → check status → generate summary."""
    monkeypatch.chdir(tmp_path)

    config = RuntimeConfig(
        mode="shadow",
        environment="uat",
        region="US",
        account_ids=["TEST001"],
        confirmation_mode="confirm",
        risk=RiskConfig(
            max_notional_usd=10000,
            max_quantity=1000,
            max_concentration_pct=10.0,
            symbol_whitelist=["AAPL", "TSLA"],
        ),
    )

    stack = build_shadow_stack(
        config,
        ledger_path=str(tmp_path / "runtime" / "shadow_ledger.jsonl"),
        state_db_path=str(tmp_path / "runtime" / "shadow_state.db"),
        incidents_dir=str(tmp_path / "runtime" / "incidents"),
    )

    runner = stack["runner"]
    metrics = stack["metrics"]
    drill = stack["drill"]
    state = stack["state"]

    # Step 1: Start observation period
    obs_id = state.start(config)
    assert obs_id is not None

    # Step 2: Process test signals
    result1 = runner.process_signal("加倉 AAPL 1%", "sig-test-001")
    assert result1.signal_id == "sig-test-001"

    result2 = runner.process_signal("賣出 TSLA 0.5%", "sig-test-002")
    assert result2.signal_id == "sig-test-002"

    # Step 3: Check status
    status = runner.check_status()
    assert status["status"] == "active"
    assert status["signals_processed"] == 2

    # Step 4: Check metrics were recorded
    report = metrics.generate_report()
    assert report.total_signals == 2

    # Step 5: Run alert drill
    drill_result = drill.run_drill()
    assert drill_result.result == "PASS"

    # Step 6: Verify drill gate passes
    assert drill.check_drill_passed() is True

    # Step 7: Generate summary
    summary = runner.generate_summary()
    assert "Shadow Run Summary" in summary
    assert "Go/No-Go Readiness" in summary

    # Step 8: Verify files exist
    assert (tmp_path / "runtime" / "shadow_ledger.jsonl").exists()
    assert (tmp_path / "runtime" / "shadow_state.db").exists()
    assert (tmp_path / "runtime" / "incidents").exists()
    summaries_dir = tmp_path / "runtime" / "shadow_summaries"
    assert summaries_dir.exists()
    assert len(list(summaries_dir.glob("*.md"))) == 1

    # Step 9: Stop observation
    final = state.stop()
    assert final["status"] == "completed"  # insufficient signals but we just stop it

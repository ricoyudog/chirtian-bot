"""Integration tests — full safety flow across all Phase 1 modules."""

import pytest
import yaml

from src.config.settings import RiskConfig, RuntimeConfig
from src.config.validation import compute_config_hash, load_config, validate_startup
from src.safety.idempotency import IdempotencyGuard
from src.safety.runtime_guard import RuntimeGuard
from src.state.ledger import AuditLedger
from src.state.models import AuditEvent
from src.state.queue import DuplicateKeyError, WorkQueue


def _make_config(**overrides):
    defaults = dict(
        mode="offline_replay",
        environment="uat",
        region="US",
        account_ids=["ACC001"],
        confirmation_mode="confirm",
        risk=RiskConfig(
            max_notional_usd=10000, max_quantity=100, max_concentration_pct=5.0
        ),
    )
    defaults.update(overrides)
    return RuntimeConfig(**defaults)


class TestConfigLoadToGuardToAudit:
    def test_config_load_validation_guard_config_hash_in_audit(
        self, tmp_path, sample_config_yaml
    ):
        # Load config
        config = load_config(sample_config_yaml)

        # Validate startup
        validate_startup(config)

        # Run through guard
        guard = RuntimeGuard(config)
        guard.assert_safe_to_run()

        # Compute config hash and record in audit
        config_hash = compute_config_hash(config)
        ledger = AuditLedger(tmp_path / "audit.jsonl")
        ledger.append(AuditEvent(
            event_type="config_loaded",
            config_hash=config_hash,
            source="integration_test",
            data={"mode": config.mode},
        ))

        # Verify audit has the event with correct hash
        events = ledger.query(event_type="config_loaded")
        assert len(events) == 1
        assert events[0].config_hash == config_hash
        assert config_hash.startswith("sha256:")


class TestConfigInvalidFieldsFailsFast:
    def test_invalid_mode_fails(self, tmp_path):
        raw = {
            "runtime": {
                "mode": "invalid_mode",
                "environment": "uat",
                "region": "US",
                "account_ids": ["A"],
                "confirmation_mode": "confirm",
            },
            "risk": {"max_notional_usd": 100, "max_quantity": 10, "max_concentration_pct": 5},
        }
        path = tmp_path / "bad.yaml"
        path.write_text(yaml.dump(raw))

        with pytest.raises(Exception):
            load_config(path)

    def test_missing_risk_section_fails(self, tmp_path):
        raw = {
            "runtime": {
                "mode": "offline_replay",
                "environment": "uat",
                "region": "US",
                "account_ids": ["A"],
                "confirmation_mode": "confirm",
            },
        }
        path = tmp_path / "bad.yaml"
        path.write_text(yaml.dump(raw))

        with pytest.raises(Exception):
            load_config(path)


class TestEnqueueLeaseAuditAck:
    def test_full_queue_lifecycle_with_audit(self, tmp_path, sample_config_yaml):
        config = load_config(sample_config_yaml)
        config_hash = compute_config_hash(config)

        db_path = tmp_path / "queue.db"
        ledger_path = tmp_path / "audit.jsonl"

        queue = WorkQueue(db_path)
        ledger = AuditLedger(ledger_path)

        # Enqueue
        job_id = queue.enqueue("trade", "key-1", {"symbol": "AAPL", "action": "BUY"})
        ledger.append(AuditEvent(
            event_type="job_enqueued",
            config_hash=config_hash,
            source="integration_test",
            data={"job_id": job_id},
        ))

        # Lease
        job = queue.lease("worker-1")
        assert job is not None
        assert job.job_id == job_id
        ledger.append(AuditEvent(
            event_type="job_leased",
            config_hash=config_hash,
            source="integration_test",
            data={"job_id": job_id, "worker": "worker-1"},
        ))

        # Ack
        queue.ack(job_id)
        ledger.append(AuditEvent(
            event_type="job_completed",
            config_hash=config_hash,
            source="integration_test",
            data={"job_id": job_id},
        ))

        # Verify audit trail
        assert len(ledger.query()) == 3
        assert len(ledger.query(event_type="job_enqueued")) == 1
        assert len(ledger.query(event_type="job_completed")) == 1

        # All events have config_hash
        for event in ledger.query():
            assert event.config_hash == config_hash


class TestIdempotencyDuplicateBlocked:
    def test_same_instruction_twice_blocked(self, tmp_path, sample_config_yaml):
        config = load_config(sample_config_yaml)
        config_hash = compute_config_hash(config)

        queue = WorkQueue(tmp_path / "queue.db")
        ledger = AuditLedger(tmp_path / "audit.jsonl")
        guard = IdempotencyGuard(queue)

        # First enqueue succeeds
        guard.check_and_enqueue(
            "trade", "post-1", 1, "BUY", "AAPL", 0.25,
            {"symbol": "AAPL", "action": "BUY"},
        )
        ledger.append(AuditEvent(
            event_type="job_enqueued",
            config_hash=config_hash,
            source="integration_test",
            data={"post_id": "post-1"},
        ))

        # Second enqueue blocked
        with pytest.raises(DuplicateKeyError):
            guard.check_and_enqueue(
                "trade", "post-1", 1, "BUY", "AAPL", 0.25,
                {"symbol": "AAPL", "action": "BUY"},
            )
        ledger.append(AuditEvent(
            event_type="duplicate_blocked",
            config_hash=config_hash,
            source="integration_test",
            data={"post_id": "post-1", "reason": "duplicate idempotency key"},
        ))

        # Audit shows both events
        assert len(ledger.query()) == 2
        assert len(ledger.query(event_type="duplicate_blocked")) == 1


class TestProdAutoFailsAtStartup:
    def test_prod_auto_blocks_everything(self, tmp_path):
        config = _make_config(
            mode="prod_auto", environment="prod", confirmation_mode="auto"
        )

        with pytest.raises(RuntimeError, match="prod environment with auto confirmation"):
            RuntimeGuard(config).assert_safe_to_run()

        # Queue operations should not be attempted, but if they were,
        # mutation would also be blocked
        with pytest.raises(RuntimeError, match="mutation blocked"):
            RuntimeGuard(config).assert_mutation_allowed()


class TestQueueCrashSimulation:
    def test_enqueue_restart_lease_picks_up(self, tmp_path):
        db_path = tmp_path / "queue.db"

        # Simulate first process: enqueue then die
        q1 = WorkQueue(db_path)
        job_id = q1.enqueue("trade", "key-1", {"symbol": "AAPL"})
        del q1  # simulate crash

        # Simulate second process: restart and pick up
        q2 = WorkQueue(db_path)
        job = q2.lease("worker-restart")
        assert job is not None
        assert job.job_id == job_id
        assert job.status == "leased"

        q2.ack(job_id)
        result = q2.get(job_id)
        assert result.status == "completed"


class TestLedgerIntegrityAtStartup:
    def test_corruption_detected(self, tmp_path):
        ledger_path = tmp_path / "audit.jsonl"
        ledger = AuditLedger(ledger_path)
        ledger.append(AuditEvent(
            event_type="startup",
            config_hash="sha256:test",
            source="integration_test",
            data={"status": "ok"},
        ))

        # Corrupt the ledger
        with open(ledger_path, "a") as f:
            f.write("CORRUPTED LINE NOT JSON\n")

        # Startup integrity check should fail
        new_ledger = AuditLedger(ledger_path)
        assert new_ledger.verify_integrity() is False

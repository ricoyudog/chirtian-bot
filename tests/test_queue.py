"""Tests for the durable work queue."""

import time

import pytest

from src.state.queue import DuplicateKeyError, WorkQueue


class TestEnqueueLeaseAck:
    def test_happy_path(self, tmp_db):
        q = WorkQueue(tmp_db)
        job_id = q.enqueue("test_job", "key-1", {"url": "https://example.com"})

        job = q.lease("worker-1")
        assert job is not None
        assert job.job_id == job_id
        assert job.status == "leased"
        assert job.leased_by == "worker-1"

        q.ack(job_id)
        result = q.get(job_id)
        assert result.status == "completed"


class TestRetryAfter:
    def test_lease_retry_lease_ack(self, tmp_db):
        q = WorkQueue(tmp_db)
        job_id = q.enqueue("test_job", "key-1", {"x": 1})

        job = q.lease("worker-1")
        assert job is not None

        q.retry_after(job_id, delay_seconds=0, reason="transient error")

        # Attempt count incremented
        job = q.get(job_id)
        assert job.attempt_count == 1
        assert job.status == "pending"
        assert job.last_error == "transient error"

        # Can lease again and ack
        job2 = q.lease("worker-2")
        assert job2 is not None
        assert job2.job_id == job_id
        q.ack(job_id)

        result = q.get(job_id)
        assert result.status == "completed"


class TestDeadLetter:
    def test_lease_dead_letter(self, tmp_db):
        q = WorkQueue(tmp_db)
        job_id = q.enqueue("test_job", "key-1", {"x": 1})

        job = q.lease("worker-1")
        assert job is not None

        q.dead_letter(job_id, "permanent failure")

        result = q.get(job_id)
        assert result.status == "dead_lettered"
        assert result.last_error == "permanent failure"
        assert result.leased_by is None


class TestDuplicateIdempotencyKey:
    def test_duplicate_key_raises(self, tmp_db):
        q = WorkQueue(tmp_db)
        q.enqueue("test_job", "key-1", {"x": 1})

        with pytest.raises(DuplicateKeyError, match="Duplicate idempotency_key"):
            q.enqueue("test_job", "key-1", {"x": 2})


class TestLeaseNoPending:
    def test_returns_none_when_empty(self, tmp_db):
        q = WorkQueue(tmp_db)
        assert q.lease("worker-1") is None

    def test_returns_none_when_all_leased(self, tmp_db):
        q = WorkQueue(tmp_db)
        q.enqueue("test_job", "key-1", {"x": 1})
        q.lease("worker-1")

        assert q.lease("worker-2") is None


class TestExpiredLease:
    def test_expired_lease_can_be_reclaimed(self, tmp_db):
        q = WorkQueue(tmp_db)
        q.enqueue("test_job", "key-1", {"x": 1})

        # Lease with very short TTL
        job = q.lease("worker-1", ttl_seconds=0)
        assert job is not None
        assert job.leased_by == "worker-1"

        # Wait for lease to expire, then reclaim
        time.sleep(0.1)
        job2 = q.lease("worker-2")
        assert job2 is not None
        assert job2.leased_by == "worker-2"
        assert job2.job_id == job.job_id


class TestAttemptCount:
    def test_increments_on_retry(self, tmp_db):
        q = WorkQueue(tmp_db)
        job_id = q.enqueue("test_job", "key-1", {"x": 1})

        for i in range(3):
            job = q.lease(f"worker-{i}")
            assert job is not None
            q.retry_after(job_id, delay_seconds=0, reason=f"attempt {i}")

        result = q.get(job_id)
        assert result.attempt_count == 3


class TestRetryAfterTerminalGuard:
    def test_retry_after_dead_lettered_raises(self, tmp_db):
        q = WorkQueue(tmp_db)
        job_id = q.enqueue("test_job", "key-1", {"x": 1})
        q.lease("worker-1")
        q.dead_letter(job_id, "permanent failure")

        with pytest.raises(ValueError, match="terminal state"):
            q.retry_after(job_id, delay_seconds=0, reason="should fail")

    def test_retry_after_completed_raises(self, tmp_db):
        q = WorkQueue(tmp_db)
        job_id = q.enqueue("test_job", "key-1", {"x": 1})
        q.lease("worker-1")
        q.ack(job_id)

        with pytest.raises(ValueError, match="terminal state"):
            q.retry_after(job_id, delay_seconds=0, reason="should fail")

    def test_dead_lettered_not_claimable(self, tmp_db):
        q = WorkQueue(tmp_db)
        job_id = q.enqueue("test_job", "key-1", {"x": 1})
        q.lease("worker-1")
        q.dead_letter(job_id, "permanent failure")

        assert q.lease("worker-2") is None


class TestLeaseTtlValidation:
    def test_negative_ttl_raises(self, tmp_db):
        q = WorkQueue(tmp_db)
        q.enqueue("test_job", "key-1", {"x": 1})

        with pytest.raises(ValueError, match="non-negative"):
            q.lease("worker-1", ttl_seconds=-60)

    def test_zero_ttl_accepted(self, tmp_db):
        q = WorkQueue(tmp_db)
        q.enqueue("test_job", "key-1", {"x": 1})

        job = q.lease("worker-1", ttl_seconds=0)
        assert job is not None
        assert job.leased_by == "worker-1"

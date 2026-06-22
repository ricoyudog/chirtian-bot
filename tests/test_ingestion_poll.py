"""Tests for ingestion wiring: signal_detector, seen-store, poll_once."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.analyzer.parser_schema import ParseResult
from src.ingestion.poll import poll_once
from src.ingestion.seen_store import ProcessedPostStore
from src.ingestion.signal_detector import SignalDetector

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeClient:
    """Duck-typed SubstackClient (no network)."""

    def __init__(self, updates, posts):
        self._updates = updates
        self._posts = posts  # url -> {"text": ...}
        self.check_updates_calls: list[dict] = []

    def check_updates(self, publication_ids=None, since=None, limit=10):
        self.check_updates_calls.append(
            {"publication_ids": publication_ids, "limit": limit}
        )
        return self._updates

    def fetch_post(self, url, format="text"):
        return self._posts.get(url, {})

    def close(self):
        pass


class FakeParser:
    """Records parse() call args so we can assert arg order."""

    def __init__(self, result):
        self._result = result
        self.calls: list[tuple] = []

    def parse(self, post_id, raw_text):
        self.calls.append((post_id, raw_text))
        return self._result


def _exec_result(post_id, instructions=None):
    return ParseResult(
        post_id=post_id,
        status="EXECUTABLE",
        instructions=instructions or [],
        confidence=0.9,
    )


# ---------------------------------------------------------------------------
# SignalDetector
# ---------------------------------------------------------------------------


class TestSignalDetector:
    def test_parse_arg_order_is_post_id_then_text(self):
        url = "https://christian1hedge.substack.com/p/2025652"
        client = FakeClient([{"canonicalUrl": url, "title": "t"}], {url: {"text": "买入aapl"}})
        parser = FakeParser(_exec_result("2025652"))

        SignalDetector(client, parser).check_new_signals()

        # Regression: was previously parse(text, post_id) — swapped.
        assert parser.calls == [("2025652", "买入aapl")]

    def test_slug_from_url(self):
        assert SignalDetector._slug_from_url("https://x.substack.com/p/2025652") == "2025652"
        assert SignalDetector._slug_from_url("https://x.substack.com/p/abc/extra") == "abc"
        # no /p/ segment → fall back to full url
        assert SignalDetector._slug_from_url("https://x.substack.com/nope") == (
            "https://x.substack.com/nope"
        )

    def test_skip_not_actionable_filtered(self):
        url = "https://x.substack.com/p/s1"
        client = FakeClient([{"canonicalUrl": url}], {url: {"text": "noop"}})
        parser = FakeParser(ParseResult(post_id="s1", status="SKIP_NOT_ACTIONABLE"))

        signals = SignalDetector(client, parser).check_new_signals()

        assert signals == []

    def test_publication_ids_and_limit_passed_through(self):
        url = "https://x.substack.com/p/s1"
        client = FakeClient([{"canonicalUrl": url}], {url: {"text": "x"}})
        parser = FakeParser(_exec_result("s1"))

        SignalDetector(client, parser).check_new_signals(
            publication_ids=["123"], limit=5,
        )

        assert client.check_updates_calls[0]["publication_ids"] == ["123"]
        assert client.check_updates_calls[0]["limit"] == 5


# ---------------------------------------------------------------------------
# ProcessedPostStore
# ---------------------------------------------------------------------------


class TestProcessedPostStore:
    def test_round_trip_and_persistence(self, tmp_path):
        store = ProcessedPostStore(tmp_path / "seen.json")
        assert store.is_seen("p1") is False

        store.mark_seen("p1", {"title": "t"})

        assert store.is_seen("p1") is True
        # a new instance reading the same file still sees it
        assert ProcessedPostStore(tmp_path / "seen.json").is_seen("p1") is True


# ---------------------------------------------------------------------------
# poll_once
# ---------------------------------------------------------------------------


class TestPollOnce:
    def _setup(self, tmp_path):
        url = "https://x.substack.com/p/s1"
        client = FakeClient(
            [{"canonicalUrl": url, "title": "T"}], {url: {"text": "buy"}},
        )
        parser = FakeParser(_exec_result("s1"))
        pipeline = MagicMock()
        pipeline.process_parse_result.return_value = [MagicMock(outcome="placed")]
        seen = ProcessedPostStore(tmp_path / "seen.json")
        return client, parser, pipeline, seen

    def test_new_post_processed_and_marked_seen(self, tmp_path):
        client, parser, pipeline, seen = self._setup(tmp_path)

        outcomes = poll_once(
            client=client, parser=parser, pipeline=pipeline,
            seen_store=seen, account_id="ACC1",
        )

        assert len(outcomes) == 1
        pipeline.process_parse_result.assert_called_once()
        assert seen.is_seen("s1") is True

    def test_already_seen_post_is_skipped(self, tmp_path):
        client, parser, pipeline, seen = self._setup(tmp_path)
        seen.mark_seen("s1")  # pretend a prior run processed it

        outcomes = poll_once(
            client=client, parser=parser, pipeline=pipeline,
            seen_store=seen, account_id="ACC1",
        )

        assert outcomes == []
        pipeline.process_parse_result.assert_not_called()

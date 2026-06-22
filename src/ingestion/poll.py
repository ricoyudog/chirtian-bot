"""Poll glue: fetch new Substack posts → orchestrator, with seen-state dedup."""

from __future__ import annotations

from typing import Any, Optional

from src.ingestion.signal_detector import SignalDetector


def poll_once(
    *,
    client: Any,
    parser: Any,
    pipeline: Any,
    seen_store: Any,
    account_id: str,
    publication_ids: Optional[list[str]] = None,
    limit: int = 10,
) -> list:
    """Fetch new posts and run each un-seen one through the pipeline.

    For every new post: skip if already seen, otherwise call
    ``pipeline.process_parse_result(parse_result, account_id)`` and mark seen.
    Returns the concatenated list of ``InstructionOutcome`` from processed posts.
    """
    detector = SignalDetector(client, parser)
    signals = detector.check_new_signals(publication_ids=publication_ids, limit=limit)

    outcomes = []
    for sig in signals:
        if seen_store.is_seen(sig.post_id):
            continue
        result = pipeline.process_parse_result(sig.parse_result, account_id)
        seen_store.mark_seen(
            sig.post_id,
            {
                "title": sig.post_title,
                "outcomes": [getattr(o, "outcome", "") for o in result],
            },
        )
        outcomes.extend(result)
    return outcomes

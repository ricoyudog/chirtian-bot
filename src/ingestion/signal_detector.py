"""Signal detector — converts Substack posts into parsed trading signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.analyzer.parser import InstructionParser
from src.analyzer.parser_schema import ParseResult
from src.ingestion.substack_client import SubstackClient


@dataclass
class DetectedSignal:
    post_id: str
    post_url: str
    post_title: str
    published_at: Optional[str]
    raw_text: str
    parse_result: ParseResult


class SignalDetector:
    """Checks for new Substack posts and parses them into trading signals."""

    def __init__(self, client: SubstackClient, parser: InstructionParser):
        self._client = client
        self._parser = parser

    def check_new_signals(
        self,
        publication_ids: Optional[list[str]] = None,
        limit: int = 10,
    ) -> list[DetectedSignal]:
        """Check for new posts and return parsed signals.

        Only returns EXECUTABLE and NEEDS_REVIEW results.
        SKIP_NOT_ACTIONABLE posts are filtered out.
        """
        updates = self._client.check_updates(publication_ids=publication_ids, limit=limit)

        signals = []
        for update in updates:
            url = update.get("canonicalUrl")
            if not url:
                continue

            post = self._client.fetch_post(url)
            text = post.get("text", "")
            if not text:
                continue

            post_id = self._slug_from_url(url)
            parse_result = self._parser.parse(post_id, text)

            if parse_result.status == "SKIP_NOT_ACTIONABLE":
                continue

            signals.append(DetectedSignal(
                post_id=post_id,
                post_url=url,
                post_title=update.get("title", ""),
                published_at=update.get("publishedAt"),
                raw_text=text,
                parse_result=parse_result,
            ))

        return signals

    @staticmethod
    def _slug_from_url(url: str) -> str:
        """Derive a stable post_id (slug) from a Substack canonical URL.

        ``https://christian1hedge.substack.com/p/2025652`` -> ``2025652``.
        Matches the ``christian log/`` archive keying. Falls back to the URL.
        """
        if "/p/" in url:
            slug = url.rstrip("/").split("/p/", 1)[1].split("/", 1)[0]
            if slug:
                return slug
        return url

"""Load christian-trading-language.md as parser reference context."""

from __future__ import annotations

from pathlib import Path

# Default path relative to project root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_REF_PATH = (
    _PROJECT_ROOT / "wiki" / "research" / "christian-trading-language.md"
)


def load_reference_context(path: Path | None = None) -> str:
    """Load the Christian trading language reference document.

    Returns:
        The full text of the reference document.

    Raises:
        FileNotFoundError: If the reference file does not exist.
    """
    ref_path = path or _DEFAULT_REF_PATH
    if not ref_path.exists():
        raise FileNotFoundError(f"Reference context not found: {ref_path}")
    return ref_path.read_text(encoding="utf-8")

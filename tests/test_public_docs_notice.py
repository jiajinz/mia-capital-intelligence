"""Every public document must carry the independent-project notice (AGENTS.md)."""
from pathlib import Path

# The required statement (AGENTS.md). Wording may vary around it; the clause must appear verbatim.
NOTICE = "not affiliated with or endorsed by miami international airport or miami-dade county"
ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DOCS = ["README.md", "docs/SOURCES_AND_METHODS.md", "docs/DATA_UPDATES.md"]


def test_public_documents_state_the_notice():
    for name in PUBLIC_DOCS:
        assert NOTICE in (ROOT / name).read_text(encoding="utf-8").lower(), f"notice missing from {name}"

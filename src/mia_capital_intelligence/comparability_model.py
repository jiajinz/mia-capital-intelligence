"""Source and metric contracts for the local comparability gate."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from hashlib import sha256

CONTRACT_VERSION = "1.0"
SUPPORTED_METRICS = frozenset({"total_estimated_cost_usd", "current_approved_budget_usd"})
EVIDENCE_CATEGORIES = (
    "original_records", "project_identity", "scope",
    "financial_metric", "estimate_basis", "reporting_period",
)


@dataclass(frozen=True)
class SourceDocument:
    """A source version with a declared memo period and page boundary."""

    matter_id: str
    sha256: str
    url: str
    title: str
    period_start: date
    period_end: date
    memo_date: date
    fiscal_caption: str
    exhibit_pages: tuple[int, ...]


@dataclass(frozen=True)
class AmountObservation:
    """An exact amount and the original cell representation."""

    value: Decimal | None
    raw_value: str
    original_header: str
    unit: str = "USD"
    verification_status: str = "machine_cross_checked"


@dataclass(frozen=True)
class SourceRecord:
    """A physical source row whose reference includes the document version."""

    matter_id: str
    document_sha256: str
    exhibit: str
    pdf_page: int
    row_ordinal: int
    project_id: str
    description_raw: str
    metrics: dict[str, AmountObservation]
    bbox: tuple[float, float, float, float] | None = None

    @property
    def source_ref(self) -> str:
        """Return an immutable version/page/row reference."""
        return (
            f"{self.matter_id}:{self.document_sha256}:{self.exhibit}:"
            f"{self.pdf_page}:{self.row_ordinal}"
        )


def candidate_id(earlier_ref: str, later_ref: str) -> str:
    """Identify a version-specific ordered candidate without implying approval."""
    digest = sha256(f"{earlier_ref}\n{later_ref}".encode()).hexdigest()
    return f"pair-{digest}"

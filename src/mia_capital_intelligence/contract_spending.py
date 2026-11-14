"""Validated, read-only access to the owner-authorized contract financial slice."""

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile

from mia_capital_intelligence.financial_sources import ISSUES, check_study, financial_amounts

ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = Path("data/financial/snapshots.v1.json")
REVIEW_PATH = Path("data/financial/review.json")
SCHEMA_VERSION = "1.0"
DEFINITION_VERSION = "contract-expenditures-1.0"
INPUT_SHA256 = "3c90df7ea841061823781be3aa6a388f18c82d51fcf317c3d7f7b261a11622be"
PDF_BASE = "https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/"
DEFINITIONS = {
    "currency": "USD",
    "population": "Four Exhibit B contract rows in each of the three sampled issues",
    "reported_month": "Month printed in the issue's Summary of Changes",
    "adopted_budget_usd": "Fiscal-year adopted budget in Exhibit B",
    "approved_budget_usd": "Current approved budget in Exhibit B",
    "prior_expenditures_usd": "Reported expenditures before the issue's current month",
    "monthly_expenditures_usd": "Current Month Expenditures in Exhibit B",
    "cumulative_expenditures_usd": "Cumulative Expenditures to Date in Exhibit B",
    "ledger_cutoff": None,
    "cash_or_accrual_basis": None,
    "alias": "E20-MDAD--03 in Exhibit B maps to E20-MDAD-03 in each same-issue summary",
    "zero_policy": "Resolve a monthly dash only to an explicit zero in the same-issue contract summary",
}
REVIEW_FIELDS = {
    "schema_version", "decision", "reviewer_name", "reviewed_at", "input_sha256",
    "definition_version", "definitions_accepted", "reviewed_source_refs", "evidence_reference",
}


@dataclass(frozen=True)
class ContractMonth:
    contract_id: str
    reported_month: str
    month_label: str
    source_ref: str
    source_url: str
    financial_page: int
    printed_page: str
    row_ordinal: int
    summary_page: int
    summary_row_ordinal: int
    raw_contract: str
    prior_usd: Decimal
    monthly_usd: Decimal
    cumulative_usd: Decimal
    monthly_dash_corroborated: bool

    @property
    def financial_url(self) -> str:
        return f"{self.source_url}#page={self.financial_page}"

    @property
    def summary_url(self) -> str:
        return f"{self.source_url}#page={self.summary_page}"


@dataclass(frozen=True)
class FinancialInput:
    digest: str
    rows: tuple[ContractMonth, ...]


@dataclass(frozen=True)
class FinancialView:
    status: str
    rows: tuple[ContractMonth, ...] = ()
    local_review: bool = False


def _unique_fields(pairs: list[tuple]) -> dict:
    fields = dict(pairs)
    if len(fields) != len(pairs):
        raise ValueError("Duplicate JSON field")
    return fields


def _read_json(contents: bytes | str) -> dict:
    result = json.loads(contents, object_pairs_hook=_unique_fields)
    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object")
    return result


def _validate_input(payload: dict, pdf_dir: Path | None = None) -> tuple[ContractMonth, ...]:
    if (payload.get("schema_version"), payload.get("definition_version"), payload.get("definitions")) != (
        SCHEMA_VERSION, DEFINITION_VERSION, DEFINITIONS
    ):
        raise ValueError("Unsupported financial schema or definitions")
    check_study(payload, pdf_dir)
    rows = []
    for source in payload["sources"]:
        month = source["report_month_label"]
        url = f"{PDF_BASE}{source['matter_id']}.pdf"
        if source["url"] != url or source["ledger_cutoff"] is not None:
            raise ValueError("Unsupported financial source URL or ledger cutoff")
        for row in source["records"]:
            amounts = financial_amounts(row)
            reference = f"{source['matter_id']}:{source['sha256']}:B:{source['financial_pdf_page']}:{row['row_ordinal']}"
            rows.append(ContractMonth(
                contract_id=row["contract_id"], reported_month=month, month_label=ISSUES[month][3],
                source_ref=reference, source_url=url, financial_page=source["financial_pdf_page"],
                printed_page=source["printed_page"], row_ordinal=row["row_ordinal"],
                summary_page=row["summary_pdf_page"], summary_row_ordinal=row["summary_row_ordinal"],
                raw_contract=row["contract_raw_visual"],
                prior_usd=amounts["prior_expenditures_usd"],
                monthly_usd=amounts["monthly_expenditures_usd"],
                cumulative_usd=amounts["cumulative_expenditures_usd"],
                monthly_dash_corroborated=row["dash_resolution"] == "summary_explicit_zero",
            ))
    return tuple(rows)


def read_financial_input(path: Path) -> FinancialInput:
    """Read the exact prepared artifact whose bytes the reviewer must attest to."""
    contents = path.read_bytes()
    digest = sha256(contents).hexdigest()
    if digest != INPUT_SHA256:
        raise ValueError("Financial input differs from the pinned artifact")
    return FinancialInput(digest, _validate_input(_read_json(contents)))


def build_financial_input(candidate: Path, pdf_dir: Path, output: Path) -> FinancialInput:
    """Revalidate original PDFs before atomically replacing the versioned artifact."""
    payload = _read_json(candidate.read_bytes())
    rows = _validate_input(payload, pdf_dir)
    contents = (json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    digest = sha256(contents).hexdigest()
    if digest != INPUT_SHA256:
        raise ValueError("Candidate differs from the pinned financial artifact")
    temporary = None
    try:
        with NamedTemporaryFile(dir=output.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return FinancialInput(digest, rows)


def review_status(financial: FinancialInput, path: Path, *, review_json: str | None = None) -> str:
    """Validate a privately provisioned human attestation for these exact input bytes."""
    try:
        review = _read_json(path.read_bytes() if review_json is None else review_json)
        if set(review) != REVIEW_FIELDS:
            return "invalid_review"
        if review["schema_version"] != SCHEMA_VERSION or review["decision"] != "approved":
            return "invalid_review"
        for field in ("reviewer_name", "evidence_reference"):
            if not isinstance(review[field], str) or not review[field].strip():
                return "invalid_review"
        reviewed_at = datetime.fromisoformat(review["reviewed_at"])
        if (reviewed_at.utcoffset() is None or reviewed_at > datetime.now(UTC)
                or review["definitions_accepted"] is not True):
            return "invalid_review"
        if review["input_sha256"] != financial.digest or review["definition_version"] != DEFINITION_VERSION:
            return "stale_review"
        refs = review["reviewed_source_refs"]
        expected = {row.source_ref for row in financial.rows}
        if not isinstance(refs, list) or len(refs) != len(expected) or set(refs) != expected:
            return "invalid_review"
        return "approved"
    except FileNotFoundError:
        return "pending_review"
    except (OSError, TypeError, ValueError):
        return "invalid_review"


def financial_view(
    root: Path, *, review_flag: str | None, server_address: str | None, review_json: str | None = None,
) -> FinancialView:
    """Only the process environment and an explicit loopback bind can enable local review."""
    try:
        financial = read_financial_input(root / INPUT_PATH)
    except (OSError, ValueError, TypeError, KeyError):
        return FinancialView("invalid_input")
    status = review_status(financial, root / REVIEW_PATH, review_json=review_json)
    local_review = review_flag == "1" and server_address in {"127.0.0.1", "::1"}
    visible = status == "approved" or local_review
    return FinancialView(status, financial.rows if visible else (), local_review)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "check", "review-fields"])
    parser.add_argument("--input", type=Path, default=ROOT / INPUT_PATH)
    parser.add_argument("--pdf-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        if args.pdf_dir is None or args.output is None:
            parser.error("build requires --pdf-dir and --output")
        financial = build_financial_input(args.input, args.pdf_dir, args.output)
    else:
        financial = read_financial_input(args.input)
    print(json.dumps({
        "input_sha256": financial.digest,
        "definition_version": DEFINITION_VERSION,
        "row_count": len(financial.rows),
        "review_status": review_status(financial, ROOT / REVIEW_PATH),
        **({"reviewed_source_refs": [row.source_ref for row in financial.rows]}
           if args.command == "review-fields" else {}),
    }, indent=2))


if __name__ == "__main__":
    main()

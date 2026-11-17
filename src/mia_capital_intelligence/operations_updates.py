"""Service updates cited to the approved narrative slice and exact registry rows."""

from dataclasses import dataclass

from mia_capital_intelligence.directory_queries import airport_classification
from mia_capital_intelligence.public_registry import PublicRegistry

OPERATIONS_MATTER = "261402"
OPERATIONS_AIRPORT = "MIA"
OPERATIONS_DOCUMENT_SHA256 = "84751b451da8b7d5e06cad6b1c24c870e563de5669c5f07325033c446bbaeb2a"
OPERATING_AREAS = ("Gates & connections", "Security screening", "Baggage systems", "Runways & taxiways")


@dataclass(frozen=True)
class OperationsUpdate:
    """A paraphrase keyed to the project ID heading on a pinned memo page."""

    project_id: str
    area: str
    title: str
    description: str
    memo_page: int
    exhibit_page: int
    exhibit_row: int

    @property
    def source_ref(self) -> str:
        return (f"{OPERATIONS_MATTER}:{OPERATIONS_DOCUMENT_SHA256}:B:"
                f"{self.exhibit_page}:{self.exhibit_row}")


_UPDATES = (
    OperationsUpdate(
        "BA013A", "Security screening", "Security checkpoint equipment replacement",
        "MIA plans to upgrade one checkpoint at a time to keep screening available.", 6, 12, 26,
    ),
    OperationsUpdate(
        "CA004A", "Gates & connections", "Concourse F–H connection",
        "A planned passage inside the secure area would let connecting passengers move between the concourses "
        "without a second screening.", 6, 12, 35,
    ),
    OperationsUpdate(
        "X078A", "Gates & connections", "South Terminal expansion",
        "The report describes six planned new gates at Concourse K to help replace aging gates at Concourse G.",
        7, 13, 39,
    ),
    OperationsUpdate(
        "AB040A", "Baggage systems", "North Terminal baggage screening",
        "The project would replace aging equipment that screens checked baggage.", 6, 12, 12,
    ),
    OperationsUpdate(
        "Y118A", "Runways & taxiways", "Runway safety improvements",
        "The project aims to reduce runway incursion risk where taxiways meet runways.", 5, 13, 43,
    ),
)


def operations_updates(registry: PublicRegistry) -> tuple[OperationsUpdate, ...]:
    """Keep an update attached to its reviewed report version, project and airport."""
    records = {row.source_ref: row for row in registry.records if row.matter_id == OPERATIONS_MATTER}
    return tuple(
        update for update in _UPDATES
        if (record := records.get(update.source_ref)) is not None
        and record.project_id == update.project_id
        and airport_classification(record.description_raw)[0] == OPERATIONS_AIRPORT
    )

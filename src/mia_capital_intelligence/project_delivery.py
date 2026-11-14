"""Dated Board award evidence linked to individual quarterly source rows."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ProjectLead:
    name: str
    memo_page: int


@dataclass(frozen=True)
class ContractAward:
    company: str
    contract_id: str
    scope: str


@dataclass(frozen=True)
class DeliveryEvidence:
    matter_id: str
    adopted_on: date
    lead: ProjectLead | None = None
    award: ContractAward | None = None

    @property
    def board_url(self) -> str:
        return (
            "https://www.miamidade.gov/govaction/matter.asp?file=true&fileAnalysis=false"
            f"&matter={self.matter_id}&yearFolder=Y{self.adopted_on.year}"
        )

    @property
    def packet_url(self) -> str:
        return (
            "https://www.miamidade.gov/govaction/legistarfiles/Matters/"
            f"Y{self.adopted_on.year}/{self.matter_id}.pdf"
        )


_SATELLITE_E = DeliveryEvidence(
    matter_id="252233",
    adopted_on=date(2025, 11, 18),
    lead=ProjectLead("Ricardo Lopez", memo_page=5),
    award=ContractAward("Magnum Construction Management, LLC", "U010D-1", "Chiller plant construction"),
)

_CONCOURSE_K = DeliveryEvidence(
    matter_id="250831",
    adopted_on=date(2025, 5, 20),
    lead=ProjectLead("Joachim Perez", memo_page=5),
    award=ContractAward("Lemartec-NV2A JV, LLC", "DB23AV01", "Concourse K design and construction"),
)

# Each binding uses the exact version, page and row checked in the review packet.
# An award match does not establish identity or estimate comparability across reports.
DELIVERY_BY_SOURCE_REF = {
    "260526:eaf845f4fb746a69940f38fe4655d27b56ab42effdbf9cfdd1dbc746a0fba878:B:11:65": _SATELLITE_E,
    "261402:84751b451da8b7d5e06cad6b1c24c870e563de5669c5f07325033c446bbaeb2a:B:12:66": _SATELLITE_E,
    "260526:eaf845f4fb746a69940f38fe4655d27b56ab42effdbf9cfdd1dbc746a0fba878:B:12:39": _CONCOURSE_K,
    "261402:84751b451da8b7d5e06cad6b1c24c870e563de5669c5f07325033c446bbaeb2a:B:13:39": _CONCOURSE_K,
}

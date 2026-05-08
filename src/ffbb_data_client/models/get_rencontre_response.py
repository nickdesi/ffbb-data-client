from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class GetRencontreResponse:
    id: str
    numero: str | None = None
    numeroJournee: str | None = None
    date_rencontre: datetime | None = None
    date: str | None = None
    horaire: str | None = None
    resultatEquipe1: str | None = None
    resultatEquipe2: str | None = None
    joue: int = 0
    nomEquipe1: str | None = None
    nomEquipe2: str | None = None
    idPoule: str | None = None
    competitionId: Any | None = None
    idOrganismeEquipe1: Any | None = None
    idOrganismeEquipe2: Any | None = None
    idEngagementEquipe1: Any | None = None
    idEngagementEquipe2: Any | None = None
    salle: Any | None = None
    officiels: list[Any] | None = None
    rematch_videos: list[Any] | None = None
    gsId: str | None = None
    etat: str | None = None
    handicap1: Any | None = None
    handicap2: Any | None = None
    pratique: str | None = None
    uniqueKey: str | None = None
    url_competition: str | None = None
    validee: bool | None = None
    remise: bool | None = None
    defautEquipe1: bool | None = None
    defautEquipe2: bool | None = None
    forfaitEquipe1: bool | None = None
    forfaitEquipe2: bool | None = None
    penaliteEquipe1: bool | None = None
    penaliteEquipe2: bool | None = None
    raw_data: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "GetRencontreResponse | None":
        if not data or not isinstance(data, dict):
            return None
        date_str = data.get("date_rencontre")
        date = None
        if date_str:
            try:
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                date = None
        return cls(
            id=str(data.get("id", "")),
            numero=data.get("numero"),
            numeroJournee=data.get("numeroJournee"),
            date_rencontre=date,
            date=data.get("date"),
            horaire=data.get("horaire"),
            resultatEquipe1=data.get("resultatEquipe1"),
            resultatEquipe2=data.get("resultatEquipe2"),
            joue=int(data.get("joue", 0)),
            nomEquipe1=data.get("nomEquipe1"),
            nomEquipe2=data.get("nomEquipe2"),
            idPoule=data.get("idPoule"),
            competitionId=data.get("competitionId"),
            idOrganismeEquipe1=data.get("idOrganismeEquipe1"),
            idOrganismeEquipe2=data.get("idOrganismeEquipe2"),
            idEngagementEquipe1=data.get("idEngagementEquipe1"),
            idEngagementEquipe2=data.get("idEngagementEquipe2"),
            salle=data.get("salle"),
            officiels=data.get("officiels"),
            rematch_videos=data.get("rematch_videos"),
            gsId=data.get("gsId"),
            etat=data.get("etat"),
            handicap1=data.get("handicap1"),
            handicap2=data.get("handicap2"),
            pratique=data.get("pratique"),
            uniqueKey=data.get("uniqueKey"),
            url_competition=data.get("url_competition"),
            validee=data.get("validee"),
            remise=data.get("remise"),
            defautEquipe1=data.get("defautEquipe1"),
            defautEquipe2=data.get("defautEquipe2"),
            forfaitEquipe1=data.get("forfaitEquipe1"),
            forfaitEquipe2=data.get("forfaitEquipe2"),
            penaliteEquipe1=data.get("penaliteEquipe1"),
            penaliteEquipe2=data.get("penaliteEquipe2"),
            raw_data=data,
        )

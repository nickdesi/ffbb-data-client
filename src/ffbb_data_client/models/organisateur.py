from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from ..utils.converter_utils import (
    from_bool,
    from_datetime,
    from_list,
    from_obj,
    from_str,
    from_uuid,
    to_dict_set,
)
from .organisme_id_pere import OrganismeIDPere


@dataclass
class Organisateur:
    adresse: str | None = None
    adresse_club_pro: str | None = None
    cartographie: str | None = None
    code: str | None = None
    commune: str | None = None
    commune_club_pro: str | None = None
    id: str | None = None
    mail: str | None = None
    nom: str | None = None
    nom_club_pro: str | None = None
    organisme_id_pere: OrganismeIDPere | None = None
    salle: str | None = None
    telephone: str | None = None
    type: str | None = None
    type_association: str | None = None
    url_site_web: str | None = None
    logo: UUID | None = None
    nom_simple: str | None = None
    date_affiliation: datetime | None = None
    saison_en_cours: bool | None = None
    entreprise: bool | None = None
    handibasket: bool | None = None
    omnisport: bool | None = None
    hors_association: bool | None = None
    offres_pratiques: list[Any] | None = None
    engagements: list[Any] | None = None
    labellisation: list[Any] | None = None
    membres: list[int] | None = None
    date_created: datetime | None = None
    date_updated: datetime | None = None
    logo_base64: UUID | None = None
    competitions: list[str] | None = None
    organismes_fils: list[int] | None = None

    @staticmethod
    def from_dict(obj: Any) -> Organisateur:
        assert isinstance(obj, dict)
        adresse = from_str(obj, "adresse")
        adresse_club_pro = from_str(obj, "adresseClubPro")
        cartographie = from_str(obj, "cartographie")
        code = from_str(obj, "code")
        commune = from_str(obj, "commune")
        commune_club_pro = from_str(obj, "communeClubPro")
        id = from_str(obj, "id")
        mail = from_str(obj, "mail")
        nom = from_str(obj, "nom")
        nom_club_pro = from_str(obj, "nomClubPro")
        organisme_id_pere = from_obj(
            OrganismeIDPere.from_dict, obj, "organisme_id_pere"
        )
        salle = from_str(obj, "salle")
        telephone = from_str(obj, "telephone")
        type = from_str(obj, "type")
        type_association = from_str(obj, "type_association")
        url_site_web = from_str(obj, "urlSiteWeb")
        logo = from_uuid(obj, "logo")
        nom_simple = from_str(obj, "nom_simple")
        date_affiliation = from_datetime(obj, "dateAffiliation")
        saison_en_cours = from_bool(obj, "saison_en_cours")
        entreprise = from_bool(obj, "entreprise")
        handibasket = from_bool(obj, "handibasket")
        omnisport = from_bool(obj, "omnisport")
        hors_association = from_bool(obj, "horsAssociation")
        offres_pratiques = from_list(lambda x: x, obj, "offresPratiques")
        engagements = from_list(lambda x: x, obj, "engagements")
        labellisation = from_list(lambda x: x, obj, "labellisation")
        membres = from_list(int, obj, "membres")
        date_created = from_datetime(obj, "date_created")
        date_updated = from_datetime(obj, "date_updated")
        logo_base64 = from_uuid(obj, "logo_base64")
        competitions = from_list(str, obj, "competitions")
        organismes_fils = from_list(int, obj, "organismes_fils")
        return Organisateur(
            adresse=adresse,
            adresse_club_pro=adresse_club_pro,
            cartographie=cartographie,
            code=code,
            commune=commune,
            commune_club_pro=commune_club_pro,
            id=id,
            mail=mail,
            nom=nom,
            nom_club_pro=nom_club_pro,
            organisme_id_pere=organisme_id_pere,
            salle=salle,
            telephone=telephone,
            type=type,
            type_association=type_association,
            url_site_web=url_site_web,
            logo=logo,
            nom_simple=nom_simple,
            date_affiliation=date_affiliation,
            saison_en_cours=saison_en_cours,
            entreprise=entreprise,
            handibasket=handibasket,
            omnisport=omnisport,
            hors_association=hors_association,
            offres_pratiques=offres_pratiques,
            engagements=engagements,
            labellisation=labellisation,
            membres=membres,
            date_created=date_created,
            date_updated=date_updated,
            logo_base64=logo_base64,
            competitions=competitions,
            organismes_fils=organismes_fils,
        )

    def to_dict(self) -> dict:
        result: dict = {}
        to_dict_set(result, "adresse", self.adresse)
        to_dict_set(result, "adresseClubPro", self.adresse_club_pro)
        to_dict_set(result, "cartographie", self.cartographie)
        to_dict_set(result, "code", self.code)
        to_dict_set(result, "commune", self.commune)
        to_dict_set(result, "communeClubPro", self.commune_club_pro)
        to_dict_set(result, "id", self.id)
        to_dict_set(result, "mail", self.mail)
        to_dict_set(result, "nom", self.nom)
        to_dict_set(result, "nomClubPro", self.nom_club_pro)
        if self.organisme_id_pere is not None:
            result["organisme_id_pere"] = self.organisme_id_pere.to_dict()
        to_dict_set(result, "salle", self.salle)
        to_dict_set(result, "telephone", self.telephone)
        to_dict_set(result, "type", self.type)
        to_dict_set(result, "type_association", self.type_association)
        to_dict_set(result, "urlSiteWeb", self.url_site_web)
        if self.logo is not None:
            result["logo"] = str(self.logo)
        to_dict_set(result, "nom_simple", self.nom_simple)
        if self.date_affiliation is not None:
            result["dateAffiliation"] = self.date_affiliation.isoformat()
        to_dict_set(result, "saison_en_cours", self.saison_en_cours)
        to_dict_set(result, "entreprise", self.entreprise)
        to_dict_set(result, "handibasket", self.handibasket)
        to_dict_set(result, "omnisport", self.omnisport)
        to_dict_set(result, "horsAssociation", self.hors_association)
        to_dict_set(result, "offresPratiques", self.offres_pratiques)
        to_dict_set(result, "engagements", self.engagements)
        to_dict_set(result, "labellisation", self.labellisation)
        if self.membres is not None:
            result["membres"] = [str(x) for x in self.membres]
        if self.date_created is not None:
            result["date_created"] = self.date_created.isoformat()
        if self.date_updated is not None:
            result["date_updated"] = self.date_updated.isoformat()
        if self.logo_base64 is not None:
            result["logo_base64"] = str(self.logo_base64)
        to_dict_set(result, "competitions", self.competitions)
        if self.organismes_fils is not None:
            result["organismes_fils"] = [str(x) for x in self.organismes_fils]
        return result

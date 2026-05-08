from abc import ABC, abstractmethod

from .competition_fields import CompetitionFields
from .field_set import FieldSet
from .organisme_fields import OrganismeFields
from .poule_fields import PouleFields
from .saison_fields import SaisonFields


class QueryFieldsManager(ABC):
    """Abstract base class for handling query fields across different entity types.

    Subclasses must implement get_fields() to return the appropriate field list.
    Static helper methods remain available for direct use.
    """

    @staticmethod
    def get_organisme_search_fields() -> list[str]:
        """Champs optimisés pour les contextes de recherche/identification
        (31 champs vs 77 pour FieldSet.DEFAULT).
        """
        return OrganismeFields.get_search_fields()

    @abstractmethod
    def get_fields(self) -> list[str]:
        """Return the list of fields for this query."""
        raise NotImplementedError

    @staticmethod
    def get_organisme_fields(field_set: FieldSet = FieldSet.DEFAULT) -> list[str]:
        """Get organisme fields based on field set."""
        if field_set == FieldSet.BASIC:
            return OrganismeFields.get_basic_fields()
        elif field_set == FieldSet.DETAILED:
            return OrganismeFields.get_detailed_fields()
        else:
            return OrganismeFields.get_default_fields()

    @staticmethod
    def get_competition_fields(field_set: FieldSet = FieldSet.DEFAULT) -> list[str]:
        """Get competition fields based on field set."""
        if field_set == FieldSet.BASIC:
            return CompetitionFields.get_basic_fields()
        elif field_set == FieldSet.DETAILED:
            return CompetitionFields.get_detailed_fields()
        else:
            return CompetitionFields.get_default_fields()

    @staticmethod
    def get_poule_fields(field_set: FieldSet = FieldSet.DEFAULT) -> list[str]:
        """Get poule fields based on field set."""
        if field_set == FieldSet.BASIC:
            return PouleFields.get_basic_fields()
        elif field_set == FieldSet.DETAILED:
            return PouleFields.get_detailed_fields()
        else:
            return PouleFields.get_default_fields()

    @staticmethod
    def get_classement_fields() -> list[str]:
        """Get only classement fields for lightweight queries."""
        return PouleFields.get_classement_fields()

    @staticmethod
    def get_equipes_fields() -> list[str]:
        """Get only engagement fields for lightweight queries."""
        return OrganismeFields.get_engagements_fields()

    @staticmethod
    def get_saison_fields(field_set: FieldSet = FieldSet.DEFAULT) -> list[str]:
        """Get saison fields based on field set."""
        if field_set == FieldSet.DETAILED:
            return SaisonFields.get_detailed_fields()
        else:
            return SaisonFields.get_default_fields()

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from httpx import Client

from ..helpers.multi_search_query_helper import generate_queries
from ..models.competitions_multi_search_query import CompetitionsMultiSearchQuery
from ..models.content_multi_search_query import (
    GaleriesMultiSearchQuery,
    NewsMultiSearchQuery,
    RssMultiSearchQuery,
    YoutubeVideosMultiSearchQuery,
)
from ..models.engagements_multi_search_query import EngagementsMultiSearchQuery
from ..models.formations_multi_search_query import FormationsMultiSearchQuery
from ..models.generic_search import (
    GaleriesMultiSearchResult,
    NewsMultiSearchResult,
    RssMultiSearchResult,
    YoutubeVideosMultiSearchResult,
)
from ..models.geo_sort_order import GeoSortOrder
from ..models.multi_search_query import MultiSearchQuery
from ..models.multi_search_result_competitions import CompetitionsMultiSearchResult
from ..models.multi_search_result_engagements import EngagementsMultiSearchResult
from ..models.multi_search_result_formations import FormationsMultiSearchResult
from ..models.multi_search_result_organismes import OrganismesMultiSearchResult
from ..models.multi_search_result_pratiques import PratiquesMultiSearchResult
from ..models.multi_search_result_rencontres import RencontresMultiSearchResult
from ..models.multi_search_result_salles import SallesMultiSearchResult
from ..models.multi_search_result_terrains import TerrainsMultiSearchResult
from ..models.multi_search_result_tournois import TournoisMultiSearchResult
from ..models.multi_search_results import MultiSearchResult
from ..models.multi_search_results_class import MultiSearchResults
from ..models.organismes_multi_search_query import OrganismesMultiSearchQuery
from ..models.pratiques_multi_search_query import PratiquesMultiSearchQuery
from ..models.rencontres_multi_search_query import RencontresMultiSearchQuery
from ..models.salles_multi_search_query import SallesMultiSearchQuery
from ..models.terrains_multi_search_query import TerrainsMultiSearchQuery
from ..models.tournois_multi_search_query import TournoisMultiSearchQuery
from ..utils.input_validation import validate_search_query
from .api_ffbb_app_client import ApiFFBBAppClient
from .meilisearch_ffbb_client import MeilisearchFFBBClient


class _SearchFacade:
    """Facade delegating all Meilisearch search calls to MeilisearchFFBBClient."""

    def __init__(
        self,
        api_ffbb_client: ApiFFBBAppClient,
        meilisearch_ffbb_client: MeilisearchFFBBClient,
    ):
        self._api = api_ffbb_client
        self._meilisearch = meilisearch_ffbb_client

    # ------------------------------------------------------------------
    # Meilisearch — multi-search
    # ------------------------------------------------------------------

    async def multi_search_async(
        self, queries: Sequence[MultiSearchQuery] | None = None
    ) -> MultiSearchResults | None:
        """Performs a smart multi-search asynchronously."""
        return await self._meilisearch.recursive_smart_multi_search_async(queries)

    def multi_search(
        self, name: str | None = None, cached_session: Client | None = None
    ) -> list[MultiSearchResult] | None:
        """
        Perform multi-search across all resource types with input validation.

        Args:
            name (str, optional): Search query string
            cached_session (Client, optional): HTTP cache session

        Returns:
            list[MultiSearchResult]: Search results across all resource types

        Raises:
            ValidationError: If search query is invalid
        """
        validated_name = validate_search_query(name, "name")
        queries = generate_queries(validated_name)
        results = self._meilisearch.recursive_smart_multi_search(
            queries, cached_session=cached_session
        )
        return results.results if results else None

    # ------------------------------------------------------------------
    # Meilisearch — competitions
    # ------------------------------------------------------------------

    def search_competitions(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> CompetitionsMultiSearchResult | None:
        results = self.search_multiple_competitions(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_competitions(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[CompetitionsMultiSearchResult] | None:
        if not names:
            return None
        queries = [
            CompetitionsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self._meilisearch.recursive_smart_multi_search(
            queries, cached_session
        )
        return (
            cast(list[CompetitionsMultiSearchResult], results.results)
            if results
            else None
        )

    async def search_competitions_async(
        self, name: str | None = None
    ) -> CompetitionsMultiSearchResult | None:
        """Search for competitions asynchronously."""
        if not name:
            return None
        queries = [CompetitionsMultiSearchQuery(name)]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(CompetitionsMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_competitions_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[CompetitionsMultiSearchResult] | None:
        """Search for multiple competitions asynchronously."""
        if not names:
            return None
        queries = [
            CompetitionsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(list[CompetitionsMultiSearchResult], results.results)
            if results
            else None
        )

    # ------------------------------------------------------------------
    # Meilisearch — organismes
    # ------------------------------------------------------------------

    def search_organismes(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> OrganismesMultiSearchResult | None:
        results = self.search_multiple_organismes(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_organismes_by_geo(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        q: str = "",
        limit: int | None = 20,
        geo_sort: GeoSortOrder = GeoSortOrder.NEAREST_FIRST,
        cached_session: Client | None = None,
    ) -> OrganismesMultiSearchResult | None:
        return self._meilisearch.search_organismes_by_geo(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            q=q,
            limit=limit,
            geo_sort=geo_sort,
            cached_session=cached_session,
        )

    def search_organismes_by_city(
        self,
        city_name: str,
        q: str = "",
        limit: int = 200,
        cached_session: Client | None = None,
    ) -> OrganismesMultiSearchResult | None:
        return self._meilisearch.search_organismes_by_city(
            city_name, q=q, limit=limit, cached_session=cached_session
        )

    def search_multiple_organismes(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[OrganismesMultiSearchResult] | None:
        if not names:
            return None
        queries = [
            OrganismesMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self._meilisearch.recursive_smart_multi_search(
            queries, cached_session
        )
        return (
            cast(list[OrganismesMultiSearchResult], results.results)
            if results
            else None
        )

    async def search_organismes_async(
        self, name: str | None = None
    ) -> OrganismesMultiSearchResult | None:
        """Search for organismes asynchronously."""
        if not name:
            return None
        queries = [OrganismesMultiSearchQuery(name)]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(OrganismesMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_organismes_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[OrganismesMultiSearchResult] | None:
        """Search for multiple organismes asynchronously."""
        if not names:
            return None
        queries = [
            OrganismesMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(list[OrganismesMultiSearchResult], results.results)
            if results
            else None
        )

    # ------------------------------------------------------------------
    # Meilisearch — pratiques
    # ------------------------------------------------------------------

    def search_pratiques(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> PratiquesMultiSearchResult | None:
        results = self.search_multiple_pratiques(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_pratiques(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[PratiquesMultiSearchResult] | None:
        if not names:
            return None
        queries = [
            PratiquesMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self._meilisearch.recursive_smart_multi_search(
            queries, cached_session
        )
        return (
            cast(list[PratiquesMultiSearchResult], results.results) if results else None
        )

    async def search_pratiques_async(
        self, name: str | None = None
    ) -> PratiquesMultiSearchResult | None:
        """Search for pratiques asynchronously."""
        if not name:
            return None
        queries = [PratiquesMultiSearchQuery(name)]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(PratiquesMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_pratiques_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[PratiquesMultiSearchResult] | None:
        """Search for multiple pratiques asynchronously."""
        if not names:
            return None
        queries = [
            PratiquesMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(list[PratiquesMultiSearchResult], results.results) if results else None
        )

    # ------------------------------------------------------------------
    # Meilisearch — rencontres
    # ------------------------------------------------------------------

    def search_rencontres(
        self,
        name: str | None = None,
        categorie: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> RencontresMultiSearchResult | None:
        results = self.search_multiple_rencontres(
            [name] if name is not None else None,
            categorie,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_rencontres(
        self,
        names: list[str | None] | None = None,
        categorie: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[RencontresMultiSearchResult] | None:
        if not names:
            return None
        queries = [
            RencontresMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self._meilisearch.recursive_smart_multi_search(
            queries, cached_session
        )
        if not results or not results.results:
            return None
        rencontres_results = cast(list[RencontresMultiSearchResult], results.results)
        if categorie:
            for res in rencontres_results:
                if res.hits:
                    filtered_hits = []
                    for hit in res.hits:
                        comp = hit.competition_id
                        cat = comp.categorie if comp else None
                        if (
                            comp
                            and cat
                            and (cat.code == categorie or cat.libelle == categorie)
                        ):
                            filtered_hits.append(hit)
                    res.hits = filtered_hits
                    res.estimated_total_hits = len(filtered_hits)
        return rencontres_results

    async def search_rencontres_async(
        self, name: str | None = None, categorie: str | None = None
    ) -> RencontresMultiSearchResult | None:
        """Search for rencontres asynchronously."""
        if not name:
            return None
        results = await self.search_multiple_rencontres_async([name], categorie)
        return results[0] if results else None

    async def search_multiple_rencontres_async(
        self,
        names: list[str | None] | None = None,
        categorie: str | None = None,
    ) -> list[RencontresMultiSearchResult] | None:
        """Search for multiple rencontres asynchronously."""
        if not names:
            return None
        queries = [RencontresMultiSearchQuery(name) for name in names]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        if not results or not results.results:
            return None
        rencontres_results = cast(list[RencontresMultiSearchResult], results.results)
        if categorie:
            for res in rencontres_results:
                if res.hits:
                    filtered_hits = [
                        hit
                        for hit in res.hits
                        if (comp := hit.competition_id)
                        and (cat := comp.categorie)
                        and (cat.code == categorie or cat.libelle == categorie)
                    ]
                    res.hits = filtered_hits
                    res.estimated_total_hits = len(filtered_hits)
        return rencontres_results

    # ------------------------------------------------------------------
    # Meilisearch — salles
    # ------------------------------------------------------------------

    def search_salles(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> SallesMultiSearchResult | None:
        results = self.search_multiple_salles(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_salles_by_geo(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        q: str = "",
        limit: int | None = 20,
        geo_sort: GeoSortOrder = GeoSortOrder.NEAREST_FIRST,
        cached_session: Client | None = None,
    ) -> SallesMultiSearchResult | None:
        return self._meilisearch.search_salles_by_geo(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            q=q,
            limit=limit,
            geo_sort=geo_sort,
            cached_session=cached_session,
        )

    def search_multiple_salles(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[SallesMultiSearchResult] | None:
        if not names:
            return None
        queries = [
            SallesMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self._meilisearch.recursive_smart_multi_search(
            queries, cached_session
        )
        return cast(list[SallesMultiSearchResult], results.results) if results else None

    async def search_salles_async(
        self, name: str | None = None
    ) -> SallesMultiSearchResult | None:
        """Search for salles asynchronously."""
        if not name:
            return None
        queries = [SallesMultiSearchQuery(name)]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(SallesMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_salles_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[SallesMultiSearchResult] | None:
        """Search for multiple salles asynchronously."""
        if not names:
            return None
        queries = [
            SallesMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return cast(list[SallesMultiSearchResult], results.results) if results else None

    # ------------------------------------------------------------------
    # Meilisearch — terrains
    # ------------------------------------------------------------------

    def search_terrains(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> TerrainsMultiSearchResult | None:
        results = self.search_multiple_terrains(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_terrains(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[TerrainsMultiSearchResult] | None:
        if not names:
            return None
        queries = [
            TerrainsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self._meilisearch.recursive_smart_multi_search(
            queries, cached_session
        )
        return (
            cast(list[TerrainsMultiSearchResult], results.results) if results else None
        )

    async def search_terrains_async(
        self, name: str | None = None
    ) -> TerrainsMultiSearchResult | None:
        """Search for terrains asynchronously."""
        if not name:
            return None
        queries = [TerrainsMultiSearchQuery(name)]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(TerrainsMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_terrains_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[TerrainsMultiSearchResult] | None:
        """Search for multiple terrains asynchronously."""
        if not names:
            return None
        queries = [
            TerrainsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(list[TerrainsMultiSearchResult], results.results) if results else None
        )

    # ------------------------------------------------------------------
    # Meilisearch — tournois
    # ------------------------------------------------------------------

    def search_tournois(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> TournoisMultiSearchResult | None:
        results = self.search_multiple_tournois(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_tournois(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[TournoisMultiSearchResult] | None:
        if not names:
            return None
        queries = [
            TournoisMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self._meilisearch.recursive_smart_multi_search(
            queries, cached_session
        )
        return (
            cast(list[TournoisMultiSearchResult], results.results) if results else None
        )

    async def search_tournois_async(
        self, name: str | None = None
    ) -> TournoisMultiSearchResult | None:
        """Search for tournois asynchronously."""
        if not name:
            return None
        queries = [TournoisMultiSearchQuery(name)]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(TournoisMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_tournois_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[TournoisMultiSearchResult] | None:
        """Search for multiple tournois asynchronously."""
        if not names:
            return None
        queries = [
            TournoisMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(list[TournoisMultiSearchResult], results.results) if results else None
        )

    # ------------------------------------------------------------------
    # Meilisearch — engagements
    # ------------------------------------------------------------------

    def search_engagements(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> EngagementsMultiSearchResult | None:
        results = self.search_multiple_engagements(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_engagements_by_geo(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        q: str = "",
        limit: int | None = 20,
        geo_sort: GeoSortOrder = GeoSortOrder.NEAREST_FIRST,
        cached_session: Client | None = None,
    ) -> EngagementsMultiSearchResult | None:
        return self._meilisearch.search_engagements_by_geo(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            q=q,
            limit=limit,
            geo_sort=geo_sort,
            cached_session=cached_session,
        )

    def search_engagements_filtered(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        q: str = "",
        limit: int | None = 5000,
        sexes: list[str] | None = None,
        niveau_codes: list[str] | None = None,
        cached_session: Client | None = None,
    ) -> EngagementsMultiSearchResult | None:
        return self._meilisearch.search_engagements_filtered(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            q=q,
            limit=limit,
            sexes=sexes,
            niveau_codes=niveau_codes,
            cached_session=cached_session,
        )

    def search_multiple_engagements(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[EngagementsMultiSearchResult] | None:
        if not names:
            return None
        queries = [
            EngagementsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self._meilisearch.recursive_smart_multi_search(
            queries, cached_session
        )
        return (
            cast(list[EngagementsMultiSearchResult], results.results)
            if results
            else None
        )

    async def search_engagements_async(
        self, name: str | None = None
    ) -> EngagementsMultiSearchResult | None:
        """Search for engagements asynchronously."""
        if not name:
            return None
        queries = [EngagementsMultiSearchQuery(name)]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(EngagementsMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_engagements_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[EngagementsMultiSearchResult] | None:
        """Search for multiple engagements asynchronously."""
        if not names:
            return None
        queries = [
            EngagementsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(list[EngagementsMultiSearchResult], results.results)
            if results
            else None
        )

    # ------------------------------------------------------------------
    # Meilisearch — formations
    # ------------------------------------------------------------------

    def search_formations(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> FormationsMultiSearchResult | None:
        results = self.search_multiple_formations(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_formations(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[FormationsMultiSearchResult] | None:
        if not names:
            return None
        queries = [
            FormationsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self._meilisearch.recursive_smart_multi_search(
            queries, cached_session
        )
        return (
            cast(list[FormationsMultiSearchResult], results.results)
            if results
            else None
        )

    async def search_formations_async(
        self, name: str | None = None
    ) -> FormationsMultiSearchResult | None:
        """Search for formations asynchronously."""
        if not name:
            return None
        queries = [FormationsMultiSearchQuery(name)]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(FormationsMultiSearchResult, results.results[0])
            if results and results.results
            else None
        )

    async def search_multiple_formations_async(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
    ) -> list[FormationsMultiSearchResult] | None:
        """Search for multiple formations asynchronously."""
        if not names:
            return None
        queries = [
            FormationsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = await self._meilisearch.recursive_smart_multi_search_async(queries)
        return (
            cast(list[FormationsMultiSearchResult], results.results)
            if results
            else None
        )

    # ------------------------------------------------------------------
    # Meilisearch — content indexes
    # ------------------------------------------------------------------

    def search_news(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> NewsMultiSearchResult | None:
        results = self.search_multiple_news(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_news(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[NewsMultiSearchResult] | None:
        if not names:
            return None
        queries = [
            NewsMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self._meilisearch.recursive_smart_multi_search(
            queries, cached_session
        )
        return cast(list[NewsMultiSearchResult], results.results) if results else None

    def search_youtube_videos(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> YoutubeVideosMultiSearchResult | None:
        results = self.search_multiple_youtube_videos(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_youtube_videos(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[YoutubeVideosMultiSearchResult] | None:
        if not names:
            return None
        queries = [
            YoutubeVideosMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self._meilisearch.recursive_smart_multi_search(
            queries, cached_session
        )
        return (
            cast(list[YoutubeVideosMultiSearchResult], results.results)
            if results
            else None
        )

    def search_rss(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> RssMultiSearchResult | None:
        results = self.search_multiple_rss(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_rss(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[RssMultiSearchResult] | None:
        if not names:
            return None
        queries = [
            RssMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self._meilisearch.recursive_smart_multi_search(
            queries, cached_session
        )
        return cast(list[RssMultiSearchResult], results.results) if results else None

    def search_galeries(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> GaleriesMultiSearchResult | None:
        results = self.search_multiple_galeries(
            [name] if name is not None else None,
            filter=filter,
            sort=sort,
            limit=limit,
            cached_session=cached_session,
        )
        return results[0] if results else None

    def search_multiple_galeries(
        self,
        names: list[str | None] | None = None,
        filter: list[str] | None = None,
        sort: list[str] | None = None,
        limit: int | None = 10,
        cached_session: Client | None = None,
    ) -> list[GaleriesMultiSearchResult] | None:
        if not names:
            return None
        queries = [
            GaleriesMultiSearchQuery(name, limit=limit, filter=filter, sort=sort)
            for name in names
        ]
        results = self._meilisearch.recursive_smart_multi_search(
            queries, cached_session
        )
        return (
            cast(list[GaleriesMultiSearchResult], results.results) if results else None
        )

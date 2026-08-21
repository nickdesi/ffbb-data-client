"""Targeted tests for simple uncovered model/data modules."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch


class TestPackagedDiscoveryArtefacts(unittest.TestCase):
    def test_load_discovery_artefact_reads_packaged_json(self) -> None:
        from ffbb_data_client.data import load_discovery_artefact

        fake_resource = MagicMock()
        fake_resource.joinpath.return_value.read_text.return_value = (
            '{"indexes": ["a"]}'
        )

        with patch(
            "ffbb_data_client.data.resources.files", return_value=fake_resource
        ) as files_mock:
            result = load_discovery_artefact("indexes.json")

        files_mock.assert_called_once_with("ffbb_data_client.data")
        fake_resource.joinpath.assert_called_once_with("indexes.json")
        fake_resource.joinpath.return_value.read_text.assert_called_once_with(
            encoding="utf-8"
        )
        self.assertEqual(result, {"indexes": ["a"]})


class TestGameStatsCompatibilityShim(unittest.TestCase):
    def test_game_stats_models_reexports_game_stats_model(self) -> None:
        import warnings

        from ffbb_data_client.models.game_stats_model import GameStatsModel

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ffbb_data_client.models.game_stats_models import (
                GameStatsModel as Reexported,
            )

        self.assertIs(Reexported, GameStatsModel)


class TestGameStatsModelCoverage(unittest.TestCase):
    def test_from_dict_empty_and_non_dict_return_none(self) -> None:
        from ffbb_data_client.models.game_stats_model import GameStatsModel

        self.assertIsNone(GameStatsModel.from_dict({}))
        self.assertIsNone(GameStatsModel.from_dict("invalid"))

    def test_from_dict_maps_all_scores(self) -> None:
        from ffbb_data_client.models.game_stats_model import GameStatsModel

        data = {
            "matchId": "M1",
            "currentStatus": "LIVE",
            "currentPeriod": "Q2",
            "score_q1_home": 10,
            "score_q2_home": 20,
            "score_q3_home": 30,
            "score_q4_home": 40,
            "score_ot1_home": 5,
            "score_ot2_home": 6,
            "score_q1_out": 9,
            "score_q2_out": 19,
            "score_q3_out": 29,
            "score_q4_out": 39,
            "score_ot1_out": 4,
            "score_ot2_out": 3,
        }

        obj = GameStatsModel.from_dict(data)

        self.assertIsNotNone(obj)
        assert obj is not None
        self.assertEqual(obj.match_id, "M1")
        self.assertEqual(obj.current_status, "LIVE")
        self.assertEqual(obj.current_period, "Q2")
        self.assertEqual(obj.score_q1_home, 10)
        self.assertEqual(obj.score_ot2_out, 3)


class TestNiveauExtractorCoverage(unittest.TestCase):
    def test_extract_niveau_variants(self) -> None:
        from ffbb_data_client.models.categorie_type import CategorieType
        from ffbb_data_client.models.niveau_extractor import NiveauExtractor
        from ffbb_data_client.models.niveau_type import NiveauType

        cases = [
            (
                "Elite Masculin U15",
                NiveauType.ELITE,
                None,
                CategorieType.U15,
                "regional",
            ),
            (
                "Pré National Seniors",
                NiveauType.NATIONAL,
                None,
                CategorieType.SENIORS,
                None,
            ),
            ("Championnat R2 U13", NiveauType.REGIONAL, 2, CategorieType.U13, None),
            (
                "Départementale - Division 3 Vétérans",
                NiveauType.DEPARTEMENTAL,
                3,
                CategorieType.VETERANS,
                None,
            ),
        ]

        for (
            name,
            expected_type,
            expected_division,
            expected_category,
            expected_zone,
        ) in cases:
            with self.subTest(name=name):
                niveau = NiveauExtractor.extract_niveau(name)
                self.assertIsNotNone(niveau)
                assert niveau is not None
                self.assertEqual(niveau.type, expected_type)
                self.assertEqual(niveau.division, expected_division)
                self.assertEqual(niveau.categorie, expected_category)
                self.assertEqual(niveau.zone_geographique, expected_zone)

    def test_extract_niveau_none_and_senior_fallback(self) -> None:
        from ffbb_data_client.models.categorie_type import CategorieType
        from ffbb_data_client.models.niveau_extractor import NiveauExtractor

        self.assertIsNone(NiveauExtractor.extract_niveau(""))
        self.assertIsNone(NiveauExtractor.extract_niveau("Coupe sans marqueur"))

        niveau = NiveauExtractor.extract_niveau("Régionale masculine")
        self.assertIsNotNone(niveau)
        assert niveau is not None
        self.assertEqual(niveau.categorie, CategorieType.SENIOR)

    def test_extract_from_competition_data_uses_nom_then_code(self) -> None:
        from ffbb_data_client.models.niveau_extractor import NiveauExtractor
        from ffbb_data_client.models.niveau_type import NiveauType

        from_nom = NiveauExtractor.extract_from_competition_data(
            {"nom": "N1 U20", "code": "D1"}
        )
        from_code = NiveauExtractor.extract_from_competition_data(
            {"nom": "", "code": "D2 U11"}
        )

        self.assertIsNotNone(from_nom)
        self.assertIsNotNone(from_code)
        assert from_nom is not None
        assert from_code is not None
        self.assertEqual(from_nom.type, NiveauType.NATIONAL)
        self.assertIsNone(from_nom.division)
        self.assertEqual(from_code.type, NiveauType.DEPARTEMENTAL)
        self.assertEqual(from_code.division, 2)

    def test_get_niveau_from_idcompetition(self) -> None:
        from ffbb_data_client.models.niveau_extractor import (
            get_niveau_from_idcompetition,
        )
        from ffbb_data_client.models.niveau_type import NiveauType

        self.assertIsNone(get_niveau_from_idcompetition(None))
        self.assertIsNone(
            get_niveau_from_idcompetition(type("Competition", (), {"nom": ""})())
        )

        niveau = get_niveau_from_idcompetition(
            type("Competition", (), {"nom": "R1 U17"})()
        )
        self.assertIsNotNone(niveau)
        assert niveau is not None
        self.assertEqual(niveau.type, NiveauType.REGIONAL)
        self.assertEqual(niveau.division, 1)


class TestGenericSearchModels(unittest.TestCase):
    def test_generic_hit_accessors_and_query_matching(self) -> None:
        from ffbb_data_client.models.generic_search import GenericSearchHit

        hit = GenericSearchHit.from_dict(
            {"id": 123, "title": "Résumé", "type": 42, "nested": {"text": "Basket"}}
        )

        self.assertEqual(hit.id, 123)
        self.assertEqual(hit.title, "Résumé")
        self.assertEqual(hit.type, "42")
        self.assertEqual(hit.to_dict()["nested"], {"text": "Basket"})
        self.assertTrue(hit.is_valid_for_query("basket"))
        self.assertTrue(hit.is_valid_for_query(""))
        self.assertFalse(hit.is_valid_for_query("football"))

    def test_generic_hit_handles_non_dict_and_null_title_type(self) -> None:
        from ffbb_data_client.models.generic_search import GenericSearchHit

        hit = GenericSearchHit.from_dict("invalid")

        self.assertIsNone(hit.id)
        self.assertIsNone(hit.title)
        self.assertIsNone(hit.type)
        self.assertEqual(hit.to_dict(), {})

    def test_generic_facets_roundtrip_dict_and_non_dict(self) -> None:
        from ffbb_data_client.models.generic_search import (
            GenericFacetDistribution,
            GenericFacetStats,
        )

        self.assertEqual(
            GenericFacetDistribution.from_dict({"a": 1}).to_dict(), {"a": 1}
        )
        self.assertEqual(GenericFacetDistribution.from_dict(None).to_dict(), {})
        self.assertEqual(GenericFacetStats.from_dict({"min": 1}).to_dict(), {"min": 1})
        self.assertEqual(GenericFacetStats.from_dict(None).to_dict(), {})


class TestRankingEngagementCoverage(unittest.TestCase):
    def test_from_dict_empty_returns_none(self) -> None:
        from ffbb_data_client.models.ranking_engagement import RankingEngagement

        self.assertIsNone(RankingEngagement.from_dict({}))

    def test_from_dict_maps_logo_when_dict(self) -> None:
        from ffbb_data_client.models.ranking_engagement import RankingEngagement

        obj = RankingEngagement.from_dict(
            {
                "id": 123,
                "nom": "Team",
                "nomUsuel": "T",
                "codeAbrege": "TM",
                "numeroEqu": "1",
                "numeroEquipe": "2",
                "logo": {"id": 456, "gradient_color": "#fff"},
            }
        )

        self.assertIsNotNone(obj)
        assert obj is not None
        self.assertEqual(obj.id, "123")
        self.assertEqual(obj.nom, "Team")
        self.assertEqual(obj.logo_id, "456")
        self.assertEqual(obj.logo_gradient, "#fff")

    def test_from_dict_ignores_non_dict_logo(self) -> None:
        from ffbb_data_client.models.ranking_engagement import RankingEngagement

        obj = RankingEngagement.from_dict({"id": "1", "nom": "Team", "logo": "bad"})

        self.assertIsNotNone(obj)
        assert obj is not None
        self.assertIsNone(obj.logo_id)
        self.assertIsNone(obj.logo_gradient)


class TestContactExtractionCoverage(unittest.TestCase):
    def test_extract_club_info_none_and_value(self) -> None:
        from ffbb_data_client.models.club_contacts import extract_club_info

        empty = type("Organisme", (), {"telephone": "", "mail": None, "nom": "Club"})()
        self.assertIsNone(extract_club_info(empty))

        organisme = type(
            "Organisme",
            (),
            {"telephone": " 010203 ", "mail": "club@example.org", "nom": "Club"},
        )()
        contact = extract_club_info(organisme)

        self.assertIsNotNone(contact)
        assert contact is not None
        self.assertEqual(contact.telephone, "010203")
        self.assertEqual(contact.email, "club@example.org")
        self.assertEqual(contact.role, "club")

    def test_extract_membres_contacts_filters_and_sanitizes(self) -> None:
        from ffbb_data_client.models.club_contacts import extract_membres_contacts

        membre_empty = type(
            "Membre",
            (),
            {"telephonePortable": None, "telephoneFixe": None, "mail": None},
        )()
        membre = type(
            "Membre",
            (),
            {
                "telephonePortable": " 0600 ",
                "telephoneFixe": None,
                "mail": "membre@example.org",
                "nom": "dupont",
                "prenom": "jean",
                "codeFonction": "PRES",
            },
        )()
        organisme = type("Organisme", (), {"membres": [membre_empty, membre]})()

        contacts = extract_membres_contacts(organisme)

        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].nom, "Dupont")
        self.assertEqual(contacts[0].prenom, "Jean")
        self.assertEqual(contacts[0].telephone, "0600")
        self.assertEqual(contacts[0].role, "PRES")

    def test_extract_correspondant_and_entraineur_contacts(self) -> None:
        from ffbb_data_client.models.engagement_contacts import (
            extract_correspondant,
            extract_entraineur_contact,
        )

        empty_engagement = type("Engagement", (), {})()
        self.assertIsNone(extract_correspondant(empty_engagement))

        engagement = type(
            "Engagement",
            (),
            {
                "telephonePortableCorrespondantEquipe": " 0700 ",
                "emailCorrespondantEquipe": "corr@example.org",
                "nomCorrespondantEquipe": "martin",
                "prenomCorrespondantEquipe": "anne",
            },
        )()
        correspondant = extract_correspondant(engagement)

        self.assertIsNotNone(correspondant)
        assert correspondant is not None
        self.assertEqual(correspondant.nom, "Martin")
        self.assertEqual(correspondant.prenom, "Anne")
        self.assertEqual(correspondant.telephone, "0700")
        self.assertEqual(correspondant.role, "correspondant")

        self.assertIsNone(extract_entraineur_contact(None, "coach"))
        coach = type(
            "Coach",
            (),
            {
                "nom": "durand",
                "prenom": "paul",
                "telephonePortable": None,
                "email": None,
            },
        )()
        coach_contact = extract_entraineur_contact(coach, "coach")
        self.assertIsNotNone(coach_contact)
        assert coach_contact is not None
        self.assertEqual(coach_contact.nom, "Durand")
        self.assertEqual(coach_contact.role, "coach")


class TestFacetDistributionCoverage(unittest.TestCase):
    def test_engagements_facet_distribution_roundtrip(self) -> None:
        from ffbb_data_client.models.engagements_facet_distribution import (
            EngagementsFacetDistribution,
        )

        data = {
            "clubPro": {"true": 1},
            "idCompetition.categorie.code": {"U13": 2},
            "idCompetition.categorie.libelle": {"U13 M": 2},
            "idCompetition.code": {"C": 3},
            "idCompetition.nom": {"Nom": 4},
            "idCompetition.sexe": {"M": 5},
            "idPoule.nom": {"Poule A": 6},
            "niveau.code": {"D1": 7},
            "niveau.libelle": {"Départemental": 8},
        }

        self.assertEqual(EngagementsFacetDistribution.from_dict(data).to_dict(), data)
        with self.assertRaises(TypeError):
            EngagementsFacetDistribution.from_dict(None)

    def test_formations_facet_distribution_roundtrip(self) -> None:
        from ffbb_data_client.models.formations_facet_distribution import (
            FormationsFacetDistribution,
        )

        data = {
            "domain": {"sport": 1},
            "mode": {"online": 2},
            "theme": {"arbitrage": 3},
            "type": {"stage": 4},
            "place": {"Paris": 5},
            "places": {"Lyon": 6},
            "postal_code": {"75000": 7},
            "postal_codes": {"69000": 8},
            "date_start_formatted": {"2026": 9},
            "date_end_formatted": {"2027": 10},
        }

        self.assertEqual(FormationsFacetDistribution.from_dict(data).to_dict(), data)
        with self.assertRaises(TypeError):
            FormationsFacetDistribution.from_dict([])


class TestSaisonsAndNiveauInfoCoverage(unittest.TestCase):
    def test_get_saisons_response_from_dict_and_list(self) -> None:
        from ffbb_data_client.models.get_saisons_response import GetSaisonsResponse

        self.assertIsNone(GetSaisonsResponse.from_dict({}))
        self.assertIsNone(GetSaisonsResponse.from_dict("bad"))
        self.assertIsNone(GetSaisonsResponse.from_dict({"errors": ["boom"]}))
        self.assertEqual(GetSaisonsResponse.from_list([]), [])

        data = {
            "id": 1,
            "nom": "2025-2026",
            "actif": True,
            "debut": "2025-07-01",
            "fin": "2026-06-30",
            "code": "2026",
            "libelle": "Saison 2026",
            "enCours": True,
        }
        saison = GetSaisonsResponse.from_dict(data)
        self.assertIsNotNone(saison)
        assert saison is not None
        self.assertEqual(saison.id, "1")
        self.assertTrue(saison.actif)
        self.assertEqual(GetSaisonsResponse.from_list([{}, data]), [saison])

    def test_niveau_info_properties_and_filters(self) -> None:
        from ffbb_data_client.models.niveau_info import NiveauInfo
        from ffbb_data_client.models.niveau_type import NiveauType

        elite = NiveauInfo(type=NiveauType.ELITE)
        self.assertTrue(elite.is_elite)
        self.assertEqual(elite.zone_effective, "regional")
        self.assertTrue(elite.matches_filter("regional"))
        self.assertFalse(elite.matches_filter("national"))

        regional = NiveauInfo(type=NiveauType.REGIONAL, division=2)
        self.assertFalse(regional.is_elite)
        self.assertEqual(regional.zone_effective, "regional")
        self.assertTrue(regional.matches_filter("REGIONAL", 2))
        self.assertFalse(regional.matches_filter("regional", 1))
        self.assertFalse(
            NiveauInfo(type=NiveauType.REGIONAL).matches_filter("regional", 1)
        )


if __name__ == "__main__":
    unittest.main()

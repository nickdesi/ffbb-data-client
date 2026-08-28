"""Unit tests for normalization helper."""
from ffbb_data_client.helpers.normalization import (
    normalize_apostrophes,
    normalize_query,
    parse_categorie,
    strip_accents,
)


def test_strip_accents():
    assert strip_accents("Éléphant & Maçon") == "Elephant & Macon"
    assert strip_accents("") == ""


def test_normalize_apostrophes():
    assert normalize_apostrophes("l’equipe") == "l'equipe"


def test_normalize_query():
    assert normalize_query("  CLERMONT-FERRAND BASKET  ") == "clermont-ferrand basket"
    assert normalize_query("Étoile de Chamalières (63)") == "etoile de chamalieres 63"


def test_parse_categorie():
    p1 = parse_categorie("U11M1")
    assert p1.categorie == "U11"
    assert p1.sexe == "M"
    assert p1.numero_equipe == 1

    p2 = parse_categorie("Senior Féminine 2")
    assert p2.categorie == "SENIOR"
    assert p2.sexe == "F"
    assert p2.numero_equipe == 2

    p3 = parse_categorie(None)
    assert p3.categorie is None

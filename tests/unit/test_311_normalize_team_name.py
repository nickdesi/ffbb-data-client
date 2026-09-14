import pytest
from ffbb_data_client.api import normalize_team_name


def test_normalize_team_name_masculine():
    assert normalize_team_name("GERZAT BASKET", "Départementale masculine U18") == "U18 M1"
    assert normalize_team_name("STADE CLERMONTOIS - 2", "Départementale masculine U13") == "U13 M2"
    assert normalize_team_name("GERZAT BASKET", "Départementale masculine seniors - Division 3") == "SENIOR M3"


def test_normalize_team_name_feminine():
    assert normalize_team_name("GERZAT BASKET", "Départementale féminine U18") == "U18 F1"
    assert normalize_team_name("GERZAT BASKET", "Départementale féminine U13") == "U13 F1"
    assert normalize_team_name("GERZAT BASKET", "Départementale féminine seniors - Division 2") == "SENIOR F2"
    assert normalize_team_name("GERZAT BASKET", "Amical U13F") == "U13 F1"


def test_normalize_team_name_mixte():
    assert normalize_team_name("GERZAT BASKET", "Départementale mixte U9") == "U9 MIXTE"

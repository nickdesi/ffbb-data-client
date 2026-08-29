"""
Text normalization and category parsing utilities for French basketball data.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from functools import lru_cache
from typing import NamedTuple

_ACCENT_TABLE = {
    i: None
    for i in range(sys.maxunicode)
    if unicodedata.category(chr(i)) in ("Mn", "So")
}

_APOSTROPHES_RE = re.compile(r"[’‘ʼ`´]")
_PUNCT_SPACES_RE = re.compile(r"[^\w\s-]")
_MULTI_SPACES_RE = re.compile(r"\s+")

_CAT_PATTERN = re.compile(r"\bU-?(\d{1,2})\b|U(\d{1,2})", re.IGNORECASE)
_JEUNES_NAMED_MAP = [
    (re.compile(r"\bMINI[\s_-]?POUSSIN(?:ES?|S)?\b", re.IGNORECASE), "U9"),
    (re.compile(r"\bPOUSSIN(?:ES?|S)?\b", re.IGNORECASE), "U11"),
    (re.compile(r"\bBENJAMIN(?:ES?|S)?\b", re.IGNORECASE), "U13"),
    (re.compile(r"\bMINIMES?\b", re.IGNORECASE), "U15"),
    (re.compile(r"\bCADET(?:TES?|S)?\b", re.IGNORECASE), "U17"),
    (re.compile(r"\bESPOIRS?\b", re.IGNORECASE), "U21"),
]
_VETERAN_PATTERN = re.compile(
    r"\b(VETERANS?|VÉTÉRANS?|VET|V35|V40|V45|V50)\b",
    re.IGNORECASE,
)
_SENIOR_PATTERN = re.compile(
    r"\b("
    r"SENIORS?|SEN|SE|SEM\d?|SEF\d?|SM\d?|SF\d?|[RDN][MF]\d?|PN[MF]\d?|PR[MF]\d?|[RDN]\d[MF]|"
    r"PRE[\s-]?NAT(IONALE?)?|PRÉ[\s-]?NAT(IONALE?)?|PRE[\s-]?REG(IONALE?)?|PRÉ[\s-]?RÉG(IONALE?)?|"
    r"REGION(AL|ALE|ALES|AUX)?|RÉGION(AL|ALE|ALES|AUX)?|"
    r"DEPARTEMENT(AL|ALE|ALES|AUX)?|DÉPARTEMENT(AL|ALE|ALES|AUX)?|"
    r"NATION(AL|ALE|ALES|AUX)?|ELITE|ÉLITE"
    r")\b",
    re.IGNORECASE,
)
_M_PATTERN = re.compile(
    r"\bM\b|U\d{1,2}M|\b[RDN]M\d?\b|\bPNM\d?\b|\bPRM\d?\b|\bR\dM\b|\bD\dM\b|\bN\dM\b|"
    r"\bSEM\d?\b|\bSM\d?\b|\bM\d\b|"
    r"\b(MASC|MASCULIN|MASCULINS|MASCULINE|HOMMES?|GARS|GARCONS?|GARÇONS?|MESSIEURS|CADETS?|BENJAMINS?|POUSSINS?)\b",
    re.IGNORECASE,
)
_F_PATTERN = re.compile(
    r"\bF\b|U\d{1,2}F|\b[RDN]F\d?\b|\bPNF\d?\b|\bPRF\d?\b|\bR\dF\b|\bD\dF\b|\bN\dF\b|"
    r"\bSEF\d?\b|\bSF\d?\b|\bF\d\b|"
    r"\b(FÉM|FEM|FEMININ|FÉMININ|FEMININE|FÉMININE|FEMININES|FÉMININES|FILLES?|FEMMES?|DAMES?|CADETTES?|BENJAMINES?|POUSSINES?)\b",
    re.IGNORECASE,
)
_NUM_PATTERN = re.compile(r"(\d+)")


class ParsedCategorie(NamedTuple):
    categorie: str | None
    sexe: str | None
    numero_equipe: int | None


def strip_accents(text: str) -> str:
    """Supprime rapidement les accents et diacritiques."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.translate(_ACCENT_TABLE)


def normalize_apostrophes(text: str) -> str:
    """Normalise les variantes typographiques d'apostrophes."""
    return _APOSTROPHES_RE.sub("'", text)


def normalize_query(query: str) -> str:
    """Normalise une requête libre pour la recherche FFBB."""
    if not query:
        return ""
    q = normalize_apostrophes(query)
    q = strip_accents(q)
    q = _PUNCT_SPACES_RE.sub(" ", q)
    q = _MULTI_SPACES_RE.sub(" ", q)
    return q.strip().lower()


@lru_cache(maxsize=256)
def parse_categorie(raw: str | None) -> ParsedCategorie:
    """Parse une chaîne de catégorie libre en composantes structurées."""
    if not raw:
        return ParsedCategorie(categorie=None, sexe=None, numero_equipe=None)

    s = raw.strip()
    if not s:
        return ParsedCategorie(categorie=None, sexe=None, numero_equipe=None)

    cat_match = _CAT_PATTERN.search(s) if "U" in s.upper() else None
    categorie: str | None = None
    if cat_match:
        val = cat_match.group(1) or cat_match.group(2)
        categorie = f"U{val}"
    else:
        for pat, cat_val in _JEUNES_NAMED_MAP:
            if pat.search(s):
                categorie = cat_val
                break
        if not categorie:
            if _VETERAN_PATTERN.search(s):
                categorie = "VETERAN"
            elif _SENIOR_PATTERN.search(s):
                categorie = "SENIOR"

    sexe: str | None = None
    is_m = bool(_M_PATTERN.search(s))
    is_f = bool(_F_PATTERN.search(s))
    if is_m and not is_f:
        sexe = "M"
    elif is_f and not is_m:
        sexe = "F"

    numero_equipe: int | None = None
    remainder = s
    if cat_match:
        remainder = s[cat_match.end() :]
    elif vet_match := _VETERAN_PATTERN.search(s):
        remainder = s[vet_match.end() :]

    num_match = _NUM_PATTERN.search(remainder)
    if num_match:
        try:
            numero_equipe = int(num_match.group(1))
        except ValueError:
            # Fallback if matched digits cannot be converted to int
            pass

    return ParsedCategorie(categorie=categorie, sexe=sexe, numero_equipe=numero_equipe)

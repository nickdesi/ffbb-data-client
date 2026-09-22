#!/usr/bin/env python3
"""Probe the FFBB Directus *permission policy* with stable canaries.

Shape discovery (``scripts/discover_endpoints.py``) snapshots routes,
collections and schemas — it cannot see role/row/field permission changes:
the OpenAPI spec stays identical while Directus starts returning 403 (or
200 + ``{"data": []}``) for archived-season items or restricted fields.

This script probes a fixed canary matrix through the same token path as the
public client (``TokenManager``: environment first, public endpoint fallback)
and records one outcome per probe: ``ok`` / ``empty`` / ``forbidden_directus``
/ ``blocked_cdn`` / ``error:*``. Outcomes are versioned in
``data/permission_matrix.json`` (plus packaged copy) and diffed run-over-run.
Any flip — including ``ok`` → ``empty`` on a historically non-empty canary
filter — is a permission-drift alert surfaced in
``data/permission_drift_summary.md`` and picked up by CI.

Canary maintenance: ``CANARY_CURRENT_COMPETITION_ID`` belongs to the running
season and must be refreshed at each season rollover. A flip on that probe is
the signal to do so — it means the canary aged, not necessarily that the
policy changed.

Usage:
    python scripts/discover_permissions.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from discover_endpoints import (  # noqa: E402
    _load_json,
    _sync_packaged_artefacts,
    _write_json_if_changed,
)
from ffbb_data_client.config import (  # noqa: E402
    API_FFBB_BASE_URL,
    DEFAULT_USER_AGENT,
    ENDPOINT_COMPETITIONS,
    ENDPOINT_CONFIGURATION,
    ENDPOINT_ENGAGEMENTS,
    ENDPOINT_ORGANISMES,
    ENDPOINT_RENCONTRES,
    ENDPOINT_SAISONS,
    ENV_API_TOKEN,
)
from ffbb_data_client.helpers.http_requests_utils import (  # noqa: E402
    _is_bunnycdn_block,
    http_get,
    url_with_params,
)
from ffbb_data_client.utils.cache_manager import CacheConfig  # noqa: E402
from ffbb_data_client.utils.token_manager import TokenManager  # noqa: E402

DATA_DIR = PROJECT_ROOT / "data"
MATRIX_PATH = DATA_DIR / "permission_matrix.json"
DRIFT_SUMMARY_PATH = DATA_DIR / "permission_drift_summary.md"
CHANGE_SUMMARY_PATH = DATA_DIR / "api_update_summary.md"

# Canaries observed on 2026-09-22 (Directus token key_dh).
CANARY_SEASON = "2026-2027"
CANARY_ARCHIVED_COMPETITION_ID = "200000002872733"
CANARY_CURRENT_COMPETITION_ID = "200000002900744"

OUTCOME_OK = "ok"
OUTCOME_EMPTY = "empty"
OUTCOME_FORBIDDEN_DIRECTUS = "forbidden_directus"
OUTCOME_BLOCKED_CDN = "blocked_cdn"

PERMISSION_SECTION_MARKER = "## Permission matrix drift"


def classify_outcome(response: Any) -> dict[str, Any]:
    """Classify a raw probe response into a stable outcome."""
    try:
        status = int(getattr(response, "status_code", 0) or 0)
    except (TypeError, ValueError):
        status = 0
    try:
        content_type = response.headers.get("content-type", "")
    except Exception:
        content_type = ""
    if status == 403 and _is_bunnycdn_block(response):
        return {"outcome": OUTCOME_BLOCKED_CDN, "status": status}
    if status in (401, 403):
        return {"outcome": OUTCOME_FORBIDDEN_DIRECTUS, "status": status}
    if status != 200:
        return {"outcome": f"error:http-{status}", "status": status or None}
    try:
        payload = json.loads(response.text or "")
    except Exception:
        return {"outcome": OUTCOME_OK, "status": status, "note": "non-JSON 200 body"}
    data = payload.get("data") if isinstance(payload, dict) else payload
    if data is None or data == [] or data == {}:
        return {
            "outcome": OUTCOME_EMPTY,
            "status": status,
            "content_type": str(content_type),
        }
    return {"outcome": OUTCOME_OK, "status": status}


def build_probes() -> list[dict[str, Any]]:
    """Fixed canary matrix: controls, archived vs current, both access paths."""
    base = API_FFBB_BASE_URL
    listing = lambda collection: url_with_params(  # noqa: E731
        f"{base}{collection}", {"limit": "1"}
    )
    archived_filter = url_with_params(
        f"{base}{ENDPOINT_COMPETITIONS}",
        {"filter[id][_eq]": CANARY_ARCHIVED_COMPETITION_ID, "limit": "1"},
    )
    current_filter = url_with_params(
        f"{base}{ENDPOINT_COMPETITIONS}",
        {"filter[id][_eq]": CANARY_CURRENT_COMPETITION_ID, "limit": "1"},
    )
    return [
        {
            "name": "config_noauth",
            "url": f"{base}{ENDPOINT_CONFIGURATION}",
            "auth": False,
            "notes": "Public endpoint sans auth : contrôle BunnyCDN et joignabilité.",
        },
        {
            "name": "saisons_id_field",
            "url": url_with_params(
                f"{base}{ENDPOINT_SAISONS}", {"fields[]": ["id"], "limit": "1"}
            ),
            "auth": True,
            "notes": "Champ contrôle, attendu ok.",
        },
        {
            "name": "saisons_nom_field",
            "url": url_with_params(
                f"{base}{ENDPOINT_SAISONS}", {"fields[]": ["nom"], "limit": "1"}
            ),
            "auth": True,
            "notes": "Champ restreint depuis sept 2026 : 403 Directus attendu.",
        },
        {
            "name": "competitions_listing",
            "url": listing(ENDPOINT_COMPETITIONS),
            "auth": True,
            "notes": "Listing contrôle, attendu ok.",
        },
        {
            "name": "organismes_listing",
            "url": listing(ENDPOINT_ORGANISMES),
            "auth": True,
            "notes": "Listing contrôle, attendu ok.",
        },
        {
            "name": "rencontres_listing",
            "url": listing(ENDPOINT_RENCONTRES),
            "auth": True,
            "notes": "Listing contrôle, attendu ok.",
        },
        {
            "name": "engagements_listing",
            "url": listing(ENDPOINT_ENGAGEMENTS),
            "auth": True,
            "notes": "Listing contrôle, attendu ok.",
        },
        {
            "name": "competition_current_direct",
            "url": f"{base}{ENDPOINT_COMPETITIONS}/{CANARY_CURRENT_COMPETITION_ID}",
            "auth": True,
            "notes": (
                f"Canari saison {CANARY_SEASON} : à rafraîchir à chaque rollover. "
                "Un flip ici signale un canari périmé, pas forcément un changement de politique."
            ),
        },
        {
            "name": "competition_current_filter",
            "url": current_filter,
            "auth": True,
            "notes": "Filtre sur saison courante, attendu ok non vide.",
        },
        {
            "name": "competition_archived_direct",
            "url": f"{base}{ENDPOINT_COMPETITIONS}/{CANARY_ARCHIVED_COMPETITION_ID}",
            "auth": True,
            "notes": "Saison archivée : 403 Directus attendu sur accès direct.",
        },
        {
            "name": "competition_archived_filter",
            "url": archived_filter,
            "auth": True,
            "notes": "Filtre sur archivé : 200 vide attendu (pas une erreur HTTP).",
        },
    ]


def run_probe(
    fetch: Callable[..., Any], probe: dict[str, Any], headers: dict[str, str]
) -> dict[str, Any]:
    """Execute one probe, never raising: transport failures become outcomes."""
    result: dict[str, Any] = {
        "name": probe["name"],
        "url": probe["url"],
        "notes": probe.get("notes", ""),
    }
    try:
        result.update(classify_outcome(fetch(probe["url"], headers, timeout=30)))
    except Exception as exc:
        result.update(
            {
                "outcome": f"error:{type(exc).__name__}",
                "status": None,
                "detail": str(exc)[:200],
            }
        )
    return result


def detect_flips(
    previous: dict[str, str], current: list[dict[str, Any]]
) -> dict[str, list[dict[str, str]]]:
    """Diff current outcomes vs the previous matrix (outcome flips only)."""
    current_by_name = {item["name"]: item["outcome"] for item in current}
    flips = [
        {"probe": name, "before": previous[name], "after": outcome}
        for name, outcome in sorted(current_by_name.items())
        if name in previous and previous[name] != outcome
    ]
    return {
        "flips": flips,
        "added": sorted(set(current_by_name) - set(previous)),
        "removed": sorted(set(previous) - set(current_by_name)),
    }


def render_drift_summary(
    timestamp: str,
    flips: list[dict[str, str]],
    added: list[str],
    removed: list[str],
) -> str:
    """Stable markdown: static when clean (no CI churn), detailed on drift."""
    if not flips and not added and not removed:
        return "# FFBB permission matrix drift\n\nNo permission drift detected.\n"
    lines = [f"# FFBB permission matrix drift — {timestamp}", ""]
    for flip in flips:
        lines.append(f"- FLIP: {flip['probe']}: {flip['before']} -> {flip['after']}")
    for name in added:
        lines.append(f"- FLIP: {name}: probe added")
    for name in removed:
        lines.append(f"- FLIP: {name}: probe removed")
    lines += [
        "",
        "Vérifier la politique de rôles Directus (filtres de saison, champs "
        "restreints) ou rafraîchir les canaris après un rollover de saison.",
        "",
    ]
    return "\n".join(lines)


def sync_permission_section(summary_text: str, flips_present: bool) -> bool:
    """Mirror drift into api_update_summary.md (PR body) — idempotent.

    The section is appended only while flips exist and stripped once they
    resolve, so the shape-discovery file is untouched in the steady state.
    """
    if not CHANGE_SUMMARY_PATH.exists():
        return False
    previous = CHANGE_SUMMARY_PATH.read_text(encoding="utf-8")
    head = previous.split(f"\n{PERMISSION_SECTION_MARKER}\n", 1)[0].rstrip() + "\n"
    if not flips_present:
        if head == previous:
            return False
        CHANGE_SUMMARY_PATH.write_text(head, encoding="utf-8")
        return True
    section = (
        f"\n{PERMISSION_SECTION_MARKER}\n\n"
        "La politique d'autorisation Directus a changé (ou un canari a péri). "
        "Détail : `data/permission_drift_summary.md`.\n"
    )
    updated = head + section
    if updated == previous:
        return False
    CHANGE_SUMMARY_PATH.write_text(updated, encoding="utf-8")
    return True


def build_matrix(
    fetch: Callable[..., Any],
    headers_auth: dict[str, str],
    headers_noauth: dict[str, str],
    previous: dict[str, Any] | None,
    token_source: str,
) -> dict[str, Any]:
    """Run every probe and diff outcomes against the previous matrix."""
    probes = [
        run_probe(fetch, probe, headers_auth if probe["auth"] else headers_noauth)
        for probe in build_probes()
    ]
    previous_outcomes = (
        {item["name"]: item["outcome"] for item in previous.get("probes", [])}
        if isinstance(previous, dict)
        else {}
    )
    drift = detect_flips(previous_outcomes, probes)
    return {
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "api_base_url": API_FFBB_BASE_URL,
            "token_source": token_source,
            "canary_season": CANARY_SEASON,
            "archived_competition_id": CANARY_ARCHIVED_COMPETITION_ID,
            "current_competition_id": CANARY_CURRENT_COMPETITION_ID,
        },
        "probes": probes,
        "drift": drift,
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    previous = _load_json(MATRIX_PATH)

    tokens = TokenManager.get_tokens(cache_config=CacheConfig(enabled=False))
    headers_auth = {
        "Authorization": f"Bearer {tokens.api_token}",
        "user-agent": DEFAULT_USER_AGENT,
    }
    headers_noauth = {"user-agent": DEFAULT_USER_AGENT}
    token_source = "env" if os.environ.get(ENV_API_TOKEN) else "public-fallback"

    matrix = build_matrix(
        http_get, headers_auth, headers_noauth, previous, token_source
    )
    flips = matrix["drift"]["flips"]
    added = matrix["drift"]["added"]
    removed = matrix["drift"]["removed"]

    matrix_changed = _write_json_if_changed(MATRIX_PATH, matrix)
    packaged_changed = _sync_packaged_artefacts([MATRIX_PATH])

    summary = render_drift_summary(
        matrix["metadata"]["timestamp"], flips, added, removed
    )
    summary_changed = False
    if DRIFT_SUMMARY_PATH.exists():
        summary_changed = DRIFT_SUMMARY_PATH.read_text(encoding="utf-8") != summary
    else:
        summary_changed = True
    if summary_changed:
        DRIFT_SUMMARY_PATH.write_text(summary, encoding="utf-8")

    section_changed = sync_permission_section(summary, bool(flips or added or removed))

    print(f"Probes: {len(matrix['probes'])}, flips: {len(flips)}")
    for flip in flips:
        print(f"FLIP: {flip['probe']}: {flip['before']} -> {flip['after']}")
    print(f"Matrix written to: {MATRIX_PATH} (changed={matrix_changed})")
    print(f"Drift summary: {DRIFT_SUMMARY_PATH} (changed={summary_changed})")
    if packaged_changed:
        print(
            "Packaged artefacts updated: " + ", ".join(str(p) for p in packaged_changed)
        )
    if section_changed:
        print(f"Change summary section synced: {CHANGE_SUMMARY_PATH}")


if __name__ == "__main__":
    main()

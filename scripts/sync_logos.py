#!/usr/bin/env python3
"""Synchronise les logos officiels des clubs et adversaires dans data/logos/.

Usage:
    uv run python scripts/sync_logos.py
    uv run python scripts/sync_logos.py --clubs ARA0063074 ARA0063029
    uv run python scripts/sync_logos.py --proxy http://127.0.0.1:8888
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent
LOGOS_DIR = ROOT_DIR / "data" / "logos"
DEFAULT_HOOPS63_LOGOS_DIR = ROOT_DIR.parent / "hoops63-workflow" / "assets" / "logos"

MEILISEARCH_URL = os.getenv(
    "MEILISEARCH_URL", "https://meilisearch-prod.ffbb.app"
).rstrip("/")
MEILISEARCH_TOKEN = os.getenv(
    "MEILISEARCH_BEARER_TOKEN",
    "98f07e4d3869853c218a0f65edce2ae56cc670728d9bcb8b035a5107ce1b55dc",
)
DIRECTUS_BASE_URL = os.getenv("API_FFBB_BASE_URL", "https://api.ffbb.com").rstrip("/")

DEFAULT_CLUB_CODES = ("ARA0063074", "ARA0063029", "ARA0063062")
# 12 départements de la ligue Auvergne-Rhône-Alpes (codes FFBB ARA0001..ARA0074)
REGION_DEPTS: dict[str, tuple[str, ...]] = {
    "ARA": ("01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"),
}
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

# Mapping explicite slug local (hoops63-workflow) -> UUID Directus si le nom diffère
KNOWN_LOCAL_ALIASES: dict[str, str] = {
    "7c41db49-46b9-4a67-a443-8485ceb43955": "bc_lempdes-badge.webp",
}


def detect_image_ext(data: bytes) -> str | None:
    """Retourne l'extension réelle d'après les magic bytes, ou None si invalide (ex: HTML 403)."""
    if len(data) < 12:
        return None
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data.lstrip().startswith((b"<svg", b"<?xml")):
        return ".svg"
    return None


def fetch_needed_logos(club_codes: list[str]) -> dict[str, str]:
    """Interroge Meilisearch pour collecter tous les UUIDs de logos (clubs + adversaires)."""
    headers = {
        "Authorization": f"Bearer {MEILISEARCH_TOKEN}",
        "Content-Type": "application/json",
    }
    needed: dict[str, str] = {}
    with httpx.Client(timeout=15.0) as client:
        for code in club_codes:
            resp = client.post(
                f"{MEILISEARCH_URL}/indexes/ffbbserver_rencontres/search",
                headers=headers,
                json={
                    "q": "",
                    "filter": (
                        f'idOrganismeEquipe1.code = "{code}" '
                        f'OR idOrganismeEquipe2.code = "{code}"'
                    ),
                    "limit": 500,
                    "attributesToRetrieve": [
                        "idOrganismeEquipe1.logo",
                        "idOrganismeEquipe2.logo",
                        "nomEquipe1",
                        "nomEquipe2",
                    ],
                },
            )
            resp.raise_for_status()
            for hit in resp.json().get("hits", []):
                for side, team_key in (
                    ("idOrganismeEquipe1", "nomEquipe1"),
                    ("idOrganismeEquipe2", "nomEquipe2"),
                ):
                    org: Any = hit.get(side)
                    if not isinstance(org, dict):
                        continue
                    logo = org.get("logo")
                    lid = (
                        logo.get("id")
                        if isinstance(logo, dict)
                        else (logo if isinstance(logo, str) else None)
                    )
                    if not lid:
                        continue
                    clean_id = str(lid).strip().lower()
                    if UUID_RE.match(clean_id) and clean_id not in needed:
                        team_name = (
                            str(hit.get(team_key) or "?").split(" - ")[0].strip()
                        )
                        needed[clean_id] = team_name
    return needed


def fetch_region_logos(region_prefix: str) -> dict[str, str]:
    """Interroge Meilisearch ffbbserver_organismes pour tous les clubs d'une région (ex: ARA)."""
    headers = {
        "Authorization": f"Bearer {MEILISEARCH_TOKEN}",
        "Content-Type": "application/json",
    }
    prefix = region_prefix.upper().strip()
    depts = REGION_DEPTS.get(prefix, ("",))
    queries = [f"{prefix}00{d}" if d else prefix for d in depts]
    needed: dict[str, str] = {}

    with httpx.Client(timeout=15.0) as client:
        for q_str in queries:
            resp = client.post(
                f"{MEILISEARCH_URL}/indexes/ffbbserver_organismes/search",
                headers=headers,
                json={
                    "q": q_str,
                    "attributesToSearchOn": ["code"],
                    "limit": 1000,
                    "attributesToRetrieve": ["id", "nom", "code", "logo"],
                },
            )
            resp.raise_for_status()
            for hit in resp.json().get("hits", []):
                code = str(hit.get("code") or "")
                if not code.startswith(prefix):
                    continue
                logo = hit.get("logo")
                lid = (
                    logo.get("id")
                    if isinstance(logo, dict)
                    else (logo if isinstance(logo, str) else None)
                )
                if not lid:
                    continue
                clean_id = str(lid).strip().lower()
                if UUID_RE.match(clean_id) and clean_id not in needed:
                    needed[clean_id] = str(hit.get("nom") or "?").strip()
    return needed


def existing_logo_uuids(logos_dir: Path) -> set[str]:
    if not logos_dir.exists():
        return set()
    return {
        p.stem.lower()
        for p in logos_dir.iterdir()
        if p.is_file() and UUID_RE.match(p.stem.lower())
    }


def try_import_local(uuid: str, local_dir: Path | None, dest_dir: Path) -> Path | None:
    if not local_dir or not local_dir.exists():
        return None
    filename = KNOWN_LOCAL_ALIASES.get(uuid)
    if not filename:
        return None
    src = local_dir / filename
    if not src.is_file():
        return None
    ext = detect_image_ext(src.read_bytes())
    if not ext:
        return None
    dest = dest_dir / f"{uuid}{ext}"
    shutil.copy2(src, dest)
    return dest


def try_download_directus(
    client: httpx.Client, uuid: str, dest_dir: Path
) -> tuple[bool, int | str]:
    url = f"{DIRECTUS_BASE_URL}/assets/{uuid}"
    headers = {
        "User-Agent": "FFBB/2.4.1 (Linux; U; Android 14; com.ffbb.ffbb; Build/2412)",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Referer": "https://competitions.ffbb.com/",
    }
    try:
        resp = client.get(url, headers=headers)
        if resp.status_code != 200:
            return False, resp.status_code
        ext = detect_image_ext(resp.content)
        if not ext:
            return False, f"invalid_body({resp.headers.get('content-type', '?')})"
        dest = dest_dir / f"{uuid}{ext}"
        dest.write_bytes(resp.content)
        return True, len(resp.content)
    except Exception as exc:
        return False, type(exc).__name__


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync FFBB club logos into data/logos/"
    )
    parser.add_argument(
        "--clubs",
        nargs="+",
        default=list(DEFAULT_CLUB_CODES),
        help="Codes clubs FFBB à scanner dans Meilisearch",
    )
    parser.add_argument(
        "--region",
        default=None,
        help="Préfixe ligue FFBB à synchroniser intégralement (ex: ARA pour Auvergne-Rhône-Alpes)",
    )
    parser.add_argument(
        "--proxy",
        default=os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY") or None,
        help="Proxy HTTP/SOCKS5 optionnel pour contourner le WAF BunnyCDN",
    )
    parser.add_argument(
        "--local-dir",
        type=Path,
        default=DEFAULT_HOOPS63_LOGOS_DIR,
        help="Répertoire local de logos existants (fallback)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Lister les logos manquants sans écrire sur disque",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-télécharger même les logos déjà présents dans data/logos/",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Retourner 0 même si certains logos restent bloqués en 403",
    )
    args = parser.parse_args()

    LOGOS_DIR.mkdir(parents=True, exist_ok=True)
    needed = (
        fetch_region_logos(args.region)
        if args.region
        else fetch_needed_logos(args.clubs)
    )
    present = existing_logo_uuids(LOGOS_DIR)
    missing = (
        needed if args.force else {k: v for k, v in needed.items() if k not in present}
    )

    print(
        f"Logos nécessaires: {len(needed)} | Déjà présents: {len(present & set(needed))} | À traiter: {len(missing)}"
    )
    if not missing:
        print("Tous les logos sont déjà présents dans data/logos/.")
        return 0

    if args.dry_run:
        for uuid, club in sorted(missing.items(), key=lambda x: x[1]):
            print(f"  [MISSING] {uuid} ({club})")
        return 0

    imported = 0
    downloaded = 0
    blocked: list[tuple[str, str, int | str]] = []

    with httpx.Client(timeout=15.0, proxy=args.proxy, follow_redirects=True) as client:
        for uuid, club in sorted(missing.items(), key=lambda x: x[1]):
            local_path = try_import_local(uuid, args.local_dir, LOGOS_DIR)
            if local_path is not None:
                print(f"  [LOCAL]      {uuid} ({club}) -> {local_path.name}")
                imported += 1
                continue

            ok, info = try_download_directus(client, uuid, LOGOS_DIR)
            if ok:
                print(f"  [DOWNLOADED] {uuid} ({club}) ({info} bytes)")
                downloaded += 1
            else:
                print(f"  [BLOCKED]    {uuid} ({club}) -> {info}")
                blocked.append((uuid, club, info))

    print(
        f"\nRésumé: {imported} importé(s) localement, {downloaded} téléchargé(s), {len(blocked)} bloqué(s)."
    )
    if blocked:
        print(
            "Astuce: relancez avec un VPN hors-FR ou `--proxy <http/socks5>` si BunnyCDN WAF renvoie 403."
        )
        return 0 if args.allow_partial else 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

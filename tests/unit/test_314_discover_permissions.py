"""Unit tests for the permission-policy discovery script.

Mirrors ``test_310_discover_endpoints.py``: the script is loaded via importlib
and only pure helpers plus the matrix builder (with an injected fake fetch)
are exercised — no network calls.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
from httpx import Request, Response

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "discover_permissions.py"


@pytest.fixture(scope="module")
def perm() -> ModuleType:
    """Load the permission discovery script as an importable module."""
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("discover_permissions", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resp(
    status: int, content_type: str, body: bytes, perm: ModuleType | None = None
) -> Response:
    del perm
    req = Request("GET", "https://api.ffbb.app/items/x")
    return Response(
        status, request=req, headers={"content-type": content_type}, content=body
    )


class TestClassifyOutcome:
    def test_ok_direct_item(self, perm: ModuleType) -> None:
        r = _resp(200, "application/json", b'{"data": {"id": "1", "nom": "X"}}')
        out = perm.classify_outcome(r)
        assert out["outcome"] == "ok"
        assert out["status"] == 200

    def test_ok_filter_hits(self, perm: ModuleType) -> None:
        r = _resp(200, "application/json", b'{"data": [{"id": "1"}]}')
        assert perm.classify_outcome(r)["outcome"] == "ok"

    def test_empty_filter_list(self, perm: ModuleType) -> None:
        r = _resp(200, "application/json", b'{"data": []}')
        assert perm.classify_outcome(r)["outcome"] == "empty"

    def test_empty_null_data(self, perm: ModuleType) -> None:
        r = _resp(200, "application/json", b'{"data": null}')
        assert perm.classify_outcome(r)["outcome"] == "empty"

    def test_forbidden_directus_json(self, perm: ModuleType) -> None:
        r = _resp(
            403,
            "application/json",
            b'{"errors": [{"message": "You don\'t have permission."}]}',
        )
        out = perm.classify_outcome(r)
        assert out["outcome"] == "forbidden_directus"

    def test_blocked_bunnycdn_html(self, perm: ModuleType) -> None:
        r = _resp(403, "text/html", b"<html><body>BunnyCDN-FR1 blocked</body></html>")
        assert perm.classify_outcome(r)["outcome"] == "blocked_cdn"

    def test_unauthorized_is_directus(self, perm: ModuleType) -> None:
        r = _resp(401, "application/json", b'{"errors": []}')
        assert perm.classify_outcome(r)["outcome"] == "forbidden_directus"

    def test_server_error(self, perm: ModuleType) -> None:
        r = _resp(500, "text/plain", b"boom")
        assert perm.classify_outcome(r)["outcome"] == "error:http-500"

    def test_non_json_200_is_ok(self, perm: ModuleType) -> None:
        r = _resp(200, "text/plain", b"not-json")
        out = perm.classify_outcome(r)
        assert out["outcome"] == "ok"


class TestDetectFlips:
    def test_flip_and_stable(self, perm: ModuleType) -> None:
        previous = {"a": "ok", "b": "ok"}
        current = [
            {"name": "a", "outcome": "forbidden_directus"},
            {"name": "b", "outcome": "ok"},
        ]
        drift = perm.detect_flips(previous, current)
        assert drift["flips"] == [
            {"probe": "a", "before": "ok", "after": "forbidden_directus"}
        ]
        assert drift["added"] == [] and drift["removed"] == []

    def test_ok_to_empty_is_a_flip(self, perm: ModuleType) -> None:
        """The sneaky Directus case: 200 + [] must alert, not stay green."""
        drift = perm.detect_flips(
            {"competition_archived_filter": "ok"},
            [{"name": "competition_archived_filter", "outcome": "empty"}],
        )
        assert drift["flips"] == [
            {
                "probe": "competition_archived_filter",
                "before": "ok",
                "after": "empty",
            }
        ]

    def test_added_removed(self, perm: ModuleType) -> None:
        drift = perm.detect_flips({"old": "ok"}, [{"name": "new", "outcome": "ok"}])
        assert drift["added"] == ["new"]
        assert drift["removed"] == ["old"]
        assert drift["flips"] == []


class TestBuildMatrix:
    def test_outcomes_and_auth_routing(self, perm: ModuleType) -> None:
        seen: dict[str, dict[str, str]] = {}

        def fake_fetch(
            url: str, headers: dict[str, str], timeout: int = 30
        ) -> Response:
            seen[url] = dict(headers)
            if "configuration" in url:
                return _resp(200, "application/json", b'{"data": {"k": 1}}')
            return _resp(200, "application/json", b'{"data": []}')

        matrix = perm.build_matrix(
            fake_fetch,
            {"Authorization": "Bearer t", "user-agent": "okhttp/4.12.0"},
            {"user-agent": "okhttp/4.12.0"},
            previous=None,
            token_source="env",
        )
        by_name = {p["name"]: p for p in matrix["probes"]}
        assert by_name["config_noauth"]["outcome"] == "ok"
        assert by_name["competition_archived_filter"]["outcome"] == "empty"
        assert matrix["drift"]["flips"] == []
        assert matrix["drift"]["removed"] == []
        # First run (no previous matrix): every probe is reported as added.
        assert sorted(matrix["drift"]["added"]) == sorted(by_name)
        assert matrix["metadata"]["token_source"] == "env"
        # No-auth probe must not leak the bearer token.
        config_url = by_name["config_noauth"]["url"]
        assert "Authorization" not in seen[config_url]

        # Second run with identical outcomes: no drift at all.
        previous = {"probes": matrix["probes"]}
        rerun = perm.build_matrix(
            fake_fetch,
            {"Authorization": "Bearer t", "user-agent": "okhttp/4.12.0"},
            {"user-agent": "okhttp/4.12.0"},
            previous=previous,
            token_source="env",
        )
        assert rerun["drift"] == {"flips": [], "added": [], "removed": []}

    def test_transport_error_becomes_outcome(self, perm: ModuleType) -> None:
        def boom(url: str, headers: dict[str, str], timeout: int = 30) -> Response:
            raise RuntimeError("dns down")

        matrix = perm.build_matrix(
            boom, {"Authorization": "Bearer t"}, {}, previous=None, token_source="env"
        )
        assert all(p["outcome"] == "error:RuntimeError" for p in matrix["probes"])


class TestRenderDriftSummary:
    def test_clean_summary_is_static(self, perm: ModuleType) -> None:
        summary = perm.render_drift_summary("2026-09-22T00:00:00+00:00", [], [], [])
        assert "No permission drift detected" in summary
        assert "FLIP" not in summary
        assert "2026-09-22" not in summary

    def test_flip_summary_lists_flips(self, perm: ModuleType) -> None:
        summary = perm.render_drift_summary(
            "2026-09-22T00:00:00+00:00",
            [
                {
                    "probe": "saisons_nom_field",
                    "before": "ok",
                    "after": "forbidden_directus",
                }
            ],
            [],
            [],
        )
        assert "- FLIP: saisons_nom_field: ok -> forbidden_directus" in summary

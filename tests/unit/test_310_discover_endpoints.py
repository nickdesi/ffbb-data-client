"""Unit tests for the FFBB API discovery script (``scripts/discover_endpoints.py``).

The script is a standalone module (not part of the installable package), so it is
loaded dynamically via :mod:`importlib`. Only the pure, side-effect-free helpers
are exercised here; network calls are mocked.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "discover_endpoints.py"


@pytest.fixture(scope="module")
def disc() -> ModuleType:
    """Load the discovery script as an importable module."""
    spec = importlib.util.spec_from_file_location("discover_endpoints", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestDiffLists:
    def test_added_removed_unchanged(self, disc: ModuleType) -> None:
        result = disc._diff_lists(["a", "b", "c"], ["b", "c", "d"])
        assert result == {
            "added": ["d"],
            "removed": ["a"],
            "unchanged": ["b", "c"],
        }

    def test_empty_inputs(self, disc: ModuleType) -> None:
        assert disc._diff_lists([], []) == {
            "added": [],
            "removed": [],
            "unchanged": [],
        }

    def test_results_are_sorted(self, disc: ModuleType) -> None:
        result = disc._diff_lists(["z", "a"], ["a", "m", "b"])
        assert result["added"] == ["b", "m"]
        assert result["removed"] == ["z"]


class TestStripVolatileMetadata:
    def test_strips_volatile_keys(self, disc: ModuleType) -> None:
        payload = {
            "timestamp": "2026-06-17T00:00:00Z",
            "openapi_version": "abc",
            "openapi_sha256": "deadbeef",
            "openapi_snapshot_sha256": "cafe",
            "stable": "keep",
        }
        assert disc._strip_volatile_metadata(payload) == {"stable": "keep"}

    def test_strips_nested_info_version(self, disc: ModuleType) -> None:
        payload = {"info": {"version": "v1", "title": "FFBB"}, "x": 1}
        assert disc._strip_volatile_metadata(payload) == {
            "info": {"title": "FFBB"},
            "x": 1,
        }

    def test_recurses_into_lists(self, disc: ModuleType) -> None:
        payload = {"items": [{"timestamp": "t", "v": 1}, {"v": 2}]}
        assert disc._strip_volatile_metadata(payload) == {"items": [{"v": 1}, {"v": 2}]}

    def test_passthrough_scalars(self, disc: ModuleType) -> None:
        assert disc._strip_volatile_metadata("x") == "x"
        assert disc._strip_volatile_metadata(42) == 42


class TestWriteJsonIfChanged:
    def test_writes_when_absent(self, disc: ModuleType, tmp_path: Path) -> None:
        target = tmp_path / "out.json"
        assert disc._write_json_if_changed(target, {"a": 1}) is True
        assert json.loads(target.read_text(encoding="utf-8")) == {"a": 1}

    def test_no_write_when_only_volatile_changes(
        self, disc: ModuleType, tmp_path: Path
    ) -> None:
        target = tmp_path / "out.json"
        disc._write_json(target, {"timestamp": "t1", "data": [1, 2]})
        changed = disc._write_json_if_changed(
            target, {"timestamp": "t2", "data": [1, 2]}
        )
        assert changed is False

    def test_writes_when_structural_change(
        self, disc: ModuleType, tmp_path: Path
    ) -> None:
        target = tmp_path / "out.json"
        disc._write_json(target, {"data": [1, 2]})
        assert disc._write_json_if_changed(target, {"data": [1, 2, 3]}) is True


class TestExtractItemCollections:
    def test_extracts_and_dedupes(self, disc: ModuleType) -> None:
        openapi = {
            "paths": {
                "/items/teams": {},
                "/items/teams/{id}": {},
                "/items/players": {},
                "/assets": {},
                "/items/clubs/{id}": {},
            }
        }
        assert disc._extract_item_collections(openapi) == [
            "clubs",
            "players",
            "teams",
        ]

    def test_empty(self, disc: ModuleType) -> None:
        assert disc._extract_item_collections({"paths": {}}) == []


class TestExtractItemPaths:
    def test_maps_paths_to_sorted_operations(self, disc: ModuleType) -> None:
        openapi = {
            "paths": {
                "/items/teams": {"get": {}, "post": {}},
                "/items/teams/{id}": {"patch": {}, "get": {}},
                "/assets": {"get": {}},
            }
        }
        result = disc._extract_item_paths(openapi)
        assert result == {
            "items/teams": ["get", "post"],
            "items/teams/{id}": ["get", "patch"],
        }


class TestBuildOpenapiSnapshot:
    def test_keeps_only_relevant_paths_and_schemas(self, disc: ModuleType) -> None:
        openapi = {
            "openapi": "3.0.0",
            "info": {"version": "v1"},
            "servers": [{"url": "https://api"}],
            "paths": {
                "/items/teams": {"get": {}},
                "/assets": {"get": {}},
                "/files": {"get": {}},
                "/unrelated": {"get": {}},
            },
            "components": {
                "schemas": {
                    "ItemsTeams": {"properties": {}},
                    "Files": {"properties": {}},
                    "OtherSchema": {"properties": {}},
                }
            },
        }
        snapshot = disc._build_openapi_snapshot(openapi)
        assert set(snapshot["paths"]) == {"/items/teams", "/assets", "/files"}
        assert set(snapshot["components"]["schemas"]) == {"ItemsTeams", "Files"}
        assert snapshot["openapi"] == "3.0.0"


class TestDiffOpenapiSchemas:
    def test_added_removed_modified(self, disc: ModuleType) -> None:
        before = {
            "components": {
                "schemas": {
                    "ItemsX": {
                        "properties": {
                            "old": {"type": "string"},
                            "chg": {"type": "string"},
                        }
                    },
                    "ItemsGone": {"properties": {}},
                }
            }
        }
        after = {
            "components": {
                "schemas": {
                    "ItemsX": {
                        "properties": {
                            "new": {"type": "integer"},
                            "chg": {"type": "integer"},
                        }
                    },
                    "ItemsNew": {"properties": {}},
                }
            }
        }
        drift = disc._diff_openapi_schemas(before, after)
        assert drift["added_schemas"] == ["ItemsNew"]
        assert drift["removed_schemas"] == ["ItemsGone"]
        mod = drift["modified_schemas"]["ItemsX"]
        assert mod["added_properties"] == ["new"]
        assert mod["removed_properties"] == ["old"]
        assert mod["modified_properties"] == {
            "chg": {"before": "string", "after": "integer"}
        }

    def test_no_drift_when_identical(self, disc: ModuleType) -> None:
        schema = {"components": {"schemas": {"ItemsX": {"properties": {}}}}}
        drift = disc._diff_openapi_schemas(schema, schema)
        assert drift["added_schemas"] == []
        assert drift["removed_schemas"] == []
        assert drift["modified_schemas"] == {}

    def test_ref_and_nullable_type_summary(self, disc: ModuleType) -> None:
        before = {
            "components": {
                "schemas": {
                    "ItemsX": {
                        "properties": {"rel": {"$ref": "#/components/schemas/Foo"}}
                    }
                }
            }
        }
        after = {
            "components": {
                "schemas": {
                    "ItemsX": {
                        "properties": {"rel": {"type": "string", "nullable": True}}
                    }
                }
            }
        }
        drift = disc._diff_openapi_schemas(before, after)
        assert drift["modified_schemas"]["ItemsX"]["modified_properties"]["rel"] == {
            "before": "Foo",
            "after": "string | None",
        }

    def test_returns_empty_on_non_dict(self, disc: ModuleType) -> None:
        assert disc._diff_openapi_schemas(None, {}) == {}


class TestDiffMeiliAttributes:
    def test_added_removed(self, disc: ModuleType) -> None:
        before = {"indexes": [{"indexUid": "idx", "sampleKeys": ["a", "b"]}]}
        after = {"indexes": [{"indexUid": "idx", "sampleKeys": ["b", "c"]}]}
        assert disc._diff_meili_attributes(before, after) == {
            "idx": {"added": ["c"], "removed": ["a"]}
        }

    def test_no_drift_when_identical(self, disc: ModuleType) -> None:
        payload = {"indexes": [{"indexUid": "idx", "sampleKeys": ["a"]}]}
        assert disc._diff_meili_attributes(payload, payload) == {}

    def test_reads_nested_meilisearch_key(self, disc: ModuleType) -> None:
        before = {"meilisearch": {"indexes": [{"indexUid": "i", "sampleKeys": ["a"]}]}}
        after = {
            "meilisearch": {"indexes": [{"indexUid": "i", "sampleKeys": ["a", "z"]}]}
        }
        assert disc._diff_meili_attributes(before, after) == {
            "i": {"added": ["z"], "removed": []}
        }

    def test_returns_empty_on_non_dict(self, disc: ModuleType) -> None:
        assert disc._diff_meili_attributes([], {}) == {}


class TestPreviousAccessors:
    def test_previous_collections_variants(self, disc: ModuleType) -> None:
        assert disc._previous_collections({"collections": ["a"]}) == ["a"]
        assert disc._previous_collections({"directus": {"collections": ["b"]}}) == ["b"]
        assert disc._previous_collections(["c"]) == ["c"]
        assert disc._previous_collections(None) == []

    def test_previous_indexes_variants(self, disc: ModuleType) -> None:
        assert disc._previous_indexes({"available_indexes": ["a"]}) == ["a"]
        assert disc._previous_indexes(
            {"meilisearch": {"available_indexes": ["b"]}}
        ) == ["b"]
        assert disc._previous_indexes(["c"]) == ["c"]
        assert disc._previous_indexes(None) == []


class TestProbeMeiliIndexes:
    def test_marks_available_and_unavailable(self, disc: ModuleType) -> None:
        def fake_post(url, headers, data, timeout):  # noqa: ANN001
            index_uid = data["queries"][0]["indexUid"]
            if index_uid == disc.MEILI_CANDIDATE_INDEXES[0]:
                return {
                    "results": [
                        {
                            "hits": [{"k1": 1, "k2": 2}],
                            "estimatedTotalHits": 5,
                        }
                    ]
                }
            raise RuntimeError("boom")

        with patch.object(disc, "http_post_json", side_effect=fake_post):
            result = disc._probe_meili_indexes("tok")

        by_uid = {item["indexUid"]: item for item in result}
        first = by_uid[disc.MEILI_CANDIDATE_INDEXES[0]]
        assert first["available"] is True
        assert first["sampleKeys"] == ["k1", "k2"]
        assert first["estimatedTotalHits"] == 5

        # Every other candidate raised -> not available
        others = [v for k, v in by_uid.items() if k != disc.MEILI_CANDIDATE_INDEXES[0]]
        assert others, "expected additional candidate indexes"
        assert all(item["available"] is False for item in others)


class TestBuildChangeSummary:
    def _report(self) -> dict:
        return {
            "metadata": {
                "timestamp": "2026-06-17T00:00:00Z",
                "api_base_url": "https://api.ffbb.app/",
                "meilisearch_base_url": "https://meilisearch-prod.ffbb.app/",
                "openapi_version": "v1",
                "openapi_sha256": "sha",
            }
        }

    def test_clean_summary_has_no_added_removed_brackets(
        self, disc: ModuleType
    ) -> None:
        summary = disc._build_change_summary(
            previous_report=None,
            previous_collections={"collections": ["teams"]},
            previous_indexes={"available_indexes": ["idx"]},
            previous_openapi_snapshot={"paths": {"/items/teams": {}}},
            report=self._report(),
            collections_payload={"collections": ["teams"]},
            indexes_payload={"available_indexes": ["idx"], "indexes": []},
            openapi_snapshot={"paths": {"/items/teams": {}}, "components": {}},
        )
        # No structural change -> CI detection grep must yield nothing.
        for line in summary.splitlines():
            assert not line.startswith("- Added: [")
            assert not line.startswith("- Removed: [")
        assert "drift" not in summary

    def test_summary_reports_added_collection(self, disc: ModuleType) -> None:
        summary = disc._build_change_summary(
            previous_report=None,
            previous_collections={"collections": ["teams"]},
            previous_indexes={"available_indexes": []},
            previous_openapi_snapshot={"paths": {}},
            report=self._report(),
            collections_payload={"collections": ["teams", "clubs"]},
            indexes_payload={"available_indexes": [], "indexes": []},
            openapi_snapshot={"paths": {}, "components": {}},
        )
        assert "- Added: ['clubs']" in summary

    def test_summary_path_label_is_accurate(self, disc: ModuleType) -> None:
        summary = disc._build_change_summary(
            previous_report=None,
            previous_collections={"collections": []},
            previous_indexes={"available_indexes": []},
            previous_openapi_snapshot={"paths": {}},
            report=self._report(),
            collections_payload={"collections": []},
            indexes_payload={"available_indexes": [], "indexes": []},
            openapi_snapshot={
                "paths": {"/items/teams": {}, "/assets": {}, "/files": {}},
                "components": {},
            },
        )
        assert "## OpenAPI paths (items, assets, files)" in summary
        assert "- Total: `3`" in summary

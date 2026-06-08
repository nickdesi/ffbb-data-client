#!/usr/bin/env python3
"""Check that FFBBDataClient wrapper exposes all methods from inner clients."""

import ast
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLIENTS = ROOT / "src" / "ffbb_data_client" / "clients"

# Methods / names intentionally excluded from the parity check
EXCLUDED = {
    "__init__",
    "__repr__",
    "__str__",
    # Singleton-factory classmethod on the wrapper itself
    "create",
}


def get_public_methods(path: Path) -> set[str]:
    """Return all public method names defined in the first class of a file.

    Skips:
    - dunder methods
    - names listed in EXCLUDED
    - @property decorated functions (they are attributes, not callable methods)
    - @staticmethod / @classmethod that are internal helpers
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    methods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                name = item.name
                if name.startswith("_") or name in EXCLUDED:
                    continue
                # Skip @property decorated functions
                is_property = any(
                    (isinstance(d, ast.Name) and d.id == "property")
                    or (isinstance(d, ast.Attribute) and d.attr == "property")
                    for d in item.decorator_list
                )
                if is_property:
                    continue
                methods.add(name)
            break  # only first class
    return methods


def write_summary(text: str) -> None:
    """Append text to the GitHub Actions step summary if available."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(text + "\n")


def main() -> int:
    api_methods = get_public_methods(CLIENTS / "api_ffbb_app_client.py")
    ms_methods = get_public_methods(CLIENTS / "meilisearch_ffbb_client.py")

    # Collect wrapper methods from the main file AND any facade files.
    # After the v2.1.0 refactor, methods live in _rest_facade.py and
    # _search_facade.py; the thin ffbb_data_client.py delegates via setattr.
    wrapper_files = [
        CLIENTS / "ffbb_data_client.py",
        CLIENTS / "_rest_facade.py",
        CLIENTS / "_search_facade.py",
    ]
    wrapper_methods: set[str] = set()
    for wf in wrapper_files:
        if wf.exists():
            wrapper_methods |= get_public_methods(wf)

    all_inner = api_methods | ms_methods
    missing = sorted(all_inner - wrapper_methods)

    if not missing:
        msg = "## ✅ Wrapper parity OK\n\nAll public methods from inner clients are exposed in `FFBBDataClient` (including facade files)."
        print(msg)
        write_summary(msg)
        return 0

    # Build markdown report
    missing_detail = " ".join(
        [
            "The following methods exist in inner clients but are **not exposed**",
            "in `FFBBDataClient` or its facade files:",
        ]
    )
    fix_detail = " ".join(
        [
            "Add the missing method(s) to",
            "`src/ffbb_data_client/clients/ffbb_data_client.py` or one of its",
            "facade files (`_rest_facade.py`, `_search_facade.py`)",
            "so they delegate to the appropriate inner client.",
        ]
    )

    lines = [
        "## ⚠️ Wrapper parity check failed",
        "",
        missing_detail,
        "",
        "| Method | Source client |",
        "|---|---|",
    ]
    for m in missing:
        source = []
        if m in api_methods:
            source.append("`ApiFFBBAppClient`")
        if m in ms_methods:
            source.append("`MeilisearchFFBBClient`")
        lines.append(f"| `{m}` | {', '.join(source)} |")

    lines += [
        "",
        "### How to fix",
        fix_detail,
    ]

    report = "\n".join(lines)
    Path("parity_report.md").write_text(report, encoding="utf-8")
    print(report)
    write_summary(report)

    print(f"\n❌ {len(missing)} missing method(s) found — failing build.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

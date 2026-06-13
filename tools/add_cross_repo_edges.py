#!/usr/bin/env python3
"""Add cross-repo edges (imports_from) to the merged graph.

Analyzes imports from the FFBB MCP server toward ffbb-data-client and
creates corresponding ``imports_from`` edges in the merged graph so
that cross-repository dependencies are visible.

Usage:
    python tools/add_cross_repo_edges.py [OPTIONS]

Examples:
    # Default: use graphify-cross-repo.json config
    python tools/add_cross_repo_edges.py

    # Custom graph path
    python tools/add_cross_repo_edges.py --graph /path/to/merged-graph.json

    # Dry-run (show edges without saving)
    python tools/add_cross_repo_edges.py --dry-run
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ── Configuration ────────────────────────────────────────────────────

DEFAULT_CONFIG = Path("graphify-cross-repo.json")
DEFAULT_GRAPH = Path("graphify-out/merged-graph.json")
SOURCE_REPO = "FFBB MCP server"
TARGET_REPO = "ffbb-data-client"


@dataclass
class ImportRecord:
    """A single import statement parsed from source code."""

    source_file: str
    line: int
    module: str
    names: list[str] = field(default_factory=list)
    is_from_import: bool = False


@dataclass
class EdgeCandidate:
    """An edge to be added to the merged graph."""

    source_node: str
    target_node: str
    source_file: str
    line: int
    confidence: str = "ANALYZED"


@dataclass
class CrossRepoEdgeStats:
    """Resolution statistics for computed cross-repo edges."""

    imports_seen: int = 0
    imports_in_scope: int = 0
    source_unresolved: int = 0
    target_unresolved: int = 0
    edges_added: int = 0
    duplicate_edges: int = 0
    resolved_targets: dict[str, int] = field(default_factory=dict)


# ── AST parser ───────────────────────────────────────────────────────


def parse_imports(file_path: Path, repo_root: Path) -> list[ImportRecord]:
    """Parse a Python file and extract all import statements."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return []

    records: list[ImportRecord] = []
    rel_path = str(file_path.relative_to(repo_root))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                records.append(
                    ImportRecord(
                        source_file=rel_path,
                        line=node.lineno,
                        module=alias.name,
                        names=[alias.asname or alias.name],
                        is_from_import=False,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = [a.name for a in node.names]
            records.append(
                ImportRecord(
                    source_file=rel_path,
                    line=node.lineno,
                    module=module,
                    names=names,
                    is_from_import=True,
                )
            )
    return records


# ── Graph helpers ────────────────────────────────────────────────────


def load_graph(path: Path) -> dict[str, Any]:
    """Load the merged graph JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_graph(graph: dict[str, Any], path: Path) -> None:
    """Write the merged graph JSON back to disk."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)
        f.write("\n")


def build_node_index(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build a lookup from node id -> node dict."""
    return {n["id"]: n for n in graph.get("nodes", [])}


def build_existing_edge_set(graph: dict[str, Any]) -> set[tuple[str, str, str]]:
    """Return set of (source, target, relation) already present in the graph."""
    edges = graph.get("links", graph.get("edges", []))
    return {(e["source"], e["target"], e["relation"]) for e in edges}


# ── Core logic ───────────────────────────────────────────────────────


def collect_cross_repo_imports(
    mcp_root: Path,
) -> list[ImportRecord]:
    """Scan all .py files under the MCP server repo for ffbb_data_client imports."""
    all_imports: list[ImportRecord] = []
    for py_file in sorted(mcp_root.rglob("*.py")):
        # Skip virtualenvs, __pycache__, .git
        parts = py_file.parts
        if any(
            p in parts
            for p in (".git", "__pycache__", ".tox", "node_modules", ".venv", "venv")
        ):
            continue
        all_imports.extend(parse_imports(py_file, mcp_root))
    return all_imports


def _is_definition_node(node: dict[str, Any]) -> bool:
    """Return True if the node represents a source-code definition."""
    if node.get("file_type") != "code":
        return False
    label = (node.get("label") or "").lower()
    nid = (node.get("id") or "").lower()
    source_file = (node.get("source_file") or "").lower()
    if (
        source_file.startswith(("docs/", "build/", "tests/"))
        or "/tests/" in source_file
    ):
        return False
    if "test_" in nid or "test_" in label:
        return False
    return True


def _is_mcp_node(node: dict[str, Any]) -> bool:
    """Check if a node belongs to the MCP server repo based on ID prefix."""
    nid = node.get("id", "")
    # MCP server nodes have ID format: ffbb-data-client::FFBB MCP server::...
    # or contain ffbb_mcp in the path
    return "FFBB MCP server" in nid or "ffbb_mcp" in nid


def _is_client_node(node: dict[str, Any]) -> bool:
    """Check if a node belongs to ffbb-data-client repo based on ID prefix."""
    nid = node.get("id", "")
    # Client nodes have ID format: ffbb-data-client::ffbb-data-client::...
    # or contain ffbb_data_client in the path
    return "ffbb_data_client" in nid or (
        "ffbb-data-client::" in nid and "FFBB MCP server" not in nid
    )


def resolve_target_nodes(
    imp: ImportRecord,
    node_index: dict[str, dict[str, Any]],
) -> list[str]:
    """Map an import record to target node IDs in the graph.

    For ``from ffbb_data_client import X``, finds the canonical definition
    node for X in the ffbb-data-client repo.  For constants (e.g.
    ``MEILISEARCH_INDEX_*``), falls back to the config module file node.
    """
    targets: list[str] = []
    seen: set[str] = set()

    module_parts = imp.module.split(".")
    module_key = "_".join(module_parts)

    resolved_names: set[str] = set()

    # ── Pass 1: exact norm_label match ────────────────────────────────
    for name in imp.names:
        name_lower = name.lower()
        candidates: list[tuple[str, dict[str, Any]]] = []

        for nid, node in node_index.items():
            if not _is_client_node(node):
                continue
            if not _is_definition_node(node):
                continue
            norm = (node.get("norm_label") or "").lower()
            if norm == name_lower or norm == f"{module_key}_{name_lower}":
                candidates.append((nid, node))

        if len(candidates) > 1:
            candidates.sort(
                key=lambda c: module_key in c[0].lower(),
                reverse=True,
            )
        for nid, _ in candidates[:1]:
            if nid not in seen:
                targets.append(nid)
                seen.add(nid)
            resolved_names.add(name_lower)

    # ── Pass 2: nid-fragment match for unmatched names ────────────────
    for name in imp.names:
        name_lower = name.lower()
        if name_lower in resolved_names:
            continue

        for nid, node in node_index.items():
            if not _is_client_node(node):
                continue
            if not _is_definition_node(node):
                continue
            nid_parts = nid.lower().split("::")
            if name_lower in nid_parts:
                if nid not in seen:
                    targets.append(nid)
                    seen.add(nid)
                resolved_names.add(name_lower)
                break

    # ── Pass 3: fallback for unmatched names — module file node ───────
    # For names that couldn't be resolved (e.g. MEILISEARCH_INDEX_*
    # constants), create an edge to the module file node so the
    # cross-repo dependency is still visible.
    unresolved = [n for n in imp.names if n.lower() not in resolved_names]
    if unresolved:
        module_last = module_parts[-1]  # e.g. "config"
        for nid, node in node_index.items():
            if not _is_client_node(node):
                continue
            norm = (node.get("norm_label") or "").lower()
            if (
                norm == module_key
                or norm == module_last
                or norm == f"{module_last}.py"
                or norm.endswith(f"_{module_key}")
            ):
                if node.get("file_type") == "code":
                    if nid not in seen:
                        targets.append(nid)
                        seen.add(nid)
                    break

    return targets


def find_source_node(
    imp: ImportRecord,
    node_index: dict[str, dict[str, Any]],
) -> str | None:
    """Find the source (MCP server) file node in the graph."""
    rel = imp.source_file
    fname = Path(rel).stem  # e.g. "client"
    fname_py = Path(rel).name  # e.g. "client.py"

    # Strategy 1: exact source_file match
    for nid, node in node_index.items():
        if not _is_mcp_node(node):
            continue
        if node.get("source_file") == rel:
            return nid

    # Strategy 2: norm_label matches filename (file node)
    for nid, node in node_index.items():
        if not _is_mcp_node(node):
            continue
        if node.get("file_type") != "code":
            continue
        norm = node.get("norm_label", "")
        if norm == fname or norm == fname_py:
            return nid

    # Strategy 3: id contains normalized path fragments
    # e.g. "FFBB MCP server::ffbb_mcp_client" for "src/ffbb_mcp/client.py"
    parts = rel.replace(".py", "").replace("/", "_").split("_")
    for nid, node in node_index.items():
        if not _is_mcp_node(node):
            continue
        if node.get("file_type") != "code":
            continue
        nid_lower = nid.lower()
        # Check if all significant parts are in the id
        if all(p.lower() in nid_lower for p in parts if p and p != "py"):
            return nid

    return None


def add_cross_repo_edges(
    graph: dict[str, Any],
    mcp_root: Path,
    dry_run: bool = False,
    stats: CrossRepoEdgeStats | None = None,
) -> int:
    """Main function: parse MCP imports, create edges, update graph.

    Returns the number of edges added.
    """
    node_index = build_node_index(graph)
    existing = build_existing_edge_set(graph)
    imports = collect_cross_repo_imports(mcp_root)

    if stats is None:
        stats = CrossRepoEdgeStats()
    stats.imports_seen = len(imports)

    new_edges: list[dict[str, Any]] = []

    for imp in imports:
        # Only care about ffbb_data_client imports
        if not imp.module.startswith("ffbb_data_client"):
            continue
        stats.imports_in_scope += 1

        # Find source node (the MCP file doing the import)
        src_node = find_source_node(imp, node_index)
        if src_node is None:
            stats.source_unresolved += 1
            continue

        # Find target nodes (the imported symbols in ffbb-data-client)
        target_nodes = resolve_target_nodes(imp, node_index)
        if not target_nodes:
            stats.target_unresolved += 1

        for tgt_node in target_nodes:
            edge_key = (src_node, tgt_node, "imports_from")
            if edge_key in existing:
                stats.duplicate_edges += 1
                continue

            edge: dict[str, Any] = {
                "source": src_node,
                "target": tgt_node,
                "relation": "imports_from",
                "context": "import",
                "confidence": "ANALYZED",
                "source_file": imp.source_file,
                "source_location": f"L{imp.line}",
                "weight": 1.0,
                "confidence_score": 0.95,
            }
            new_edges.append(edge)
            existing.add(edge_key)
            target_file = node_index.get(tgt_node, {}).get("source_file") or tgt_node
            stats.resolved_targets[target_file] = (
                stats.resolved_targets.get(target_file, 0) + 1
            )

    stats.edges_added = len(new_edges)

    if not dry_run:
        graph.setdefault("links", graph.get("edges", []))
        graph["links"].extend(new_edges)
        # Remove legacy 'edges' key if present and different from 'links'
        if "edges" in graph and graph["edges"] is not graph["links"]:
            del graph["edges"]

    return len(new_edges)


# ── CLI ──────────────────────────────────────────────────────────────


def resolve_mcp_root(config_path: Path | None = None) -> Path:
    """Resolve the MCP server root from config or default."""
    cfg = config_path or DEFAULT_CONFIG
    if cfg.exists():
        with open(cfg, encoding="utf-8") as f:
            data = json.load(f)
        for repo in data.get("cross_repo", {}).get("repos", []):
            if repo.get("name") == SOURCE_REPO:
                return Path(repo["path"])
    # Fallback: sibling directory
    return Path("/Volumes/HomeExt/Users/Nicolas/Documents/Repo GIT/FFBB MCP server")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add cross-repo imports_from edges to the merged graph"
    )
    parser.add_argument(
        "--graph",
        type=Path,
        default=None,
        help="Path to merged-graph.json (default: graphify-out/merged-graph.json)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to graphify-cross-repo.json (for MCP server path)",
    )
    parser.add_argument(
        "--mcp-root",
        type=Path,
        default=None,
        help="Explicit path to MCP server repo (overrides config)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show edges without writing the graph",
    )

    args = parser.parse_args()

    # Resolve paths
    graph_path = args.graph or DEFAULT_GRAPH
    if not graph_path.exists():
        print(f"✗ Fichier introuvable: {graph_path}", file=sys.stderr)
        return 1

    mcp_root = args.mcp_root or resolve_mcp_root(args.config)
    if not mcp_root.exists():
        print(f"✗ MCP server introuvable: {mcp_root}", file=sys.stderr)
        return 1

    print("╔══════════════════════════════════════════╗")
    print("║   Cross-Repo Edge Builder (imports_from) ║")
    print("╚══════════════════════════════════════════╝")
    print()

    # Load graph
    graph = load_graph(graph_path)
    num_nodes = len(graph.get("nodes", []))
    num_edges_before = len(graph.get("links", graph.get("edges", [])))
    print(f"📊 Graph chargé: {num_nodes} nœuds, {num_edges_before} arêtes")
    print(f"   MCP server: {mcp_root}")
    print()

    # Add edges
    stats = CrossRepoEdgeStats()
    num_added = add_cross_repo_edges(graph, mcp_root, dry_run=args.dry_run, stats=stats)

    # Summary
    print(f"✅ Arêtes cross-repo ajoutées: {num_added}")
    print(
        "   Imports ffbb_data_client: "
        f"{stats.imports_in_scope} "
        f"({stats.source_unresolved} sources non résolues, "
        f"{stats.target_unresolved} cibles non résolues, "
        f"{stats.duplicate_edges} doublons)"
    )
    if stats.resolved_targets:
        print("   Top cibles:")
        for target, count in sorted(
            stats.resolved_targets.items(), key=lambda item: item[1], reverse=True
        )[:5]:
            print(f"   - {count}× {target}")
    if not args.dry_run:
        num_edges_after = len(graph.get("links", []))
        print(f"   Total arêtes: {num_edges_before} → {num_edges_after}")
        save_graph(graph, graph_path)
        print(f"   Fichier mis à jour: {graph_path}")
    else:
        print("   (dry-run — aucun changement sauvegardé)")

    return 0


if __name__ == "__main__":
    sys.exit(main())

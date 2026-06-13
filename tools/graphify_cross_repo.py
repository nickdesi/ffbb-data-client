#!/usr/bin/env python3
"""Graphify Cross-Repo: Merge and analyze multiple repositories.

Usage:
    python tools/graphify_cross_repo.py [OPTIONS]

Examples:
    # Default: merge ffbb-data-client and FFBB MCP server
    python tools/graphify_cross_repo.py

    # Custom repos
    python tools/graphify_cross_repo.py --repos /path/to/repo1 /path/to/repo2

    # Skip individual repo updates (use cached graphs)
    python tools/graphify_cross_repo.py --skip-update

    # Output merged graph to custom location
    python tools/graphify_cross_repo.py --output /path/to/merged-graph.json

    # Use configuration file
    python tools/graphify_cross_repo.py --config graphify-cross-repo.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import add_cross_repo_edges as cross_repo_edges


@dataclass
class RepoConfig:
    """Configuration for a single repository."""

    path: Path
    name: str
    description: str = ""
    graph_path: Path = field(init=False)
    exists: bool = field(init=False)

    def __post_init__(self) -> None:
        self.exists = self.path.exists() and (self.path / ".git").exists()
        self.graph_path = self.path / "graphify-out" / "graph.json"

    @property
    def has_graph(self) -> bool:
        return self.exists and self.graph_path.exists()

    @property
    def head_commit(self) -> str:
        if not self.exists:
            return "n/a"
        returncode, stdout, _ = run_command(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=self.path,
        )
        return stdout.strip() if returncode == 0 else "n/a"

    @property
    def dirty_status(self) -> str:
        if not self.exists:
            return "n/a"
        returncode, stdout, _ = run_command(
            ["git", "status", "--short"],
            cwd=self.path,
        )
        if returncode != 0:
            return "n/a"
        return "dirty" if stdout.strip() else "clean"


@dataclass
class MergeResult:
    """Result of a graph merge operation."""

    success: bool
    merged_path: Path
    nodes: int = 0
    edges: int = 0
    communities: int = 0
    cross_repo_edges_added: int = 0
    cross_repo_edge_stats: cross_repo_edges.CrossRepoEdgeStats | None = None
    duration: float = 0.0
    errors: list[str] = field(default_factory=list)


@dataclass
class CrossRepoConfig:
    """Configuration for cross-repo analysis."""

    repos: list[RepoConfig]
    output_dir: str = "graphify-out"
    merged_filename: str = "merged-graph.json"
    auto_update: bool = True
    auto_cluster: bool = True
    auto_cross_repo_edges: bool = True
    parallel_update: bool = True
    timeout_per_repo: int = 600
    force_rebuild: bool = False
    generate_report: bool = True

    @classmethod
    def from_file(cls, config_path: Path) -> CrossRepoConfig:
        """Load configuration from JSON file."""
        with open(config_path) as f:
            data = json.load(f)

        cross_repo = data.get("cross_repo", {})
        settings = data.get("settings", {})

        repos = []
        for repo_data in cross_repo.get("repos", []):
            repo_path = _resolve_config_path(repo_data["path"], config_path.parent)
            repos.append(
                RepoConfig(
                    path=repo_path,
                    name=repo_data["name"],
                    description=repo_data.get("description", ""),
                )
            )

        output_dir = _resolve_config_path(
            cross_repo.get("output_dir", "graphify-out"),
            config_path.parent,
        )

        return cls(
            repos=repos,
            output_dir=str(output_dir),
            merged_filename=cross_repo.get("merged_filename", "merged-graph.json"),
            auto_update=cross_repo.get("auto_update", True),
            auto_cluster=cross_repo.get("auto_cluster", True),
            auto_cross_repo_edges=cross_repo.get("auto_cross_repo_edges", True),
            parallel_update=settings.get("parallel_update", True),
            timeout_per_repo=settings.get("timeout_per_repo", 600),
            force_rebuild=settings.get("force_rebuild", False),
            generate_report=settings.get("generate_report", True),
        )


def _resolve_config_path(value: str, base_dir: Path) -> Path:
    """Resolve env/user/relative paths from a config file."""
    path = Path(os.path.expandvars(value)).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = 300,
    capture_output: bool = True,
) -> tuple[int, str, str]:
    """Execute a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            timeout=timeout,
            capture_output=capture_output,
            text=True,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return 1, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return 1, "", str(e)


def check_graphify_installed() -> bool:
    """Check if graphify is installed and accessible."""
    returncode, _, _ = run_command(["graphify", "--help"])
    return returncode == 0


def update_repo_graph(
    repo: RepoConfig,
    force: bool = False,
    timeout: int = 600,
) -> tuple[RepoConfig, bool, str]:
    """Update graph for a single repository. Returns (repo, success, message)."""
    cmd = ["graphify", "update", str(repo.path)]
    if force:
        cmd.append("--force")

    returncode, stdout, stderr = run_command(cmd, timeout=timeout)

    if returncode == 0:
        return repo, True, "✓"
    else:
        error_msg = stderr[:200] if stderr else "Unknown error"
        return repo, False, f"✗ {error_msg}"


def merge_graphs(
    repos: list[RepoConfig],
    output: Path,
    skip_cluster: bool = False,
    timeout: int = 300,
    add_cross_repo_edges: bool = True,
) -> MergeResult:
    """Merge multiple repository graphs into one."""
    start_time = time.time()

    # Filter repos with valid graphs
    valid_repos = [r for r in repos if r.has_graph]
    if len(valid_repos) < 2:
        return MergeResult(
            success=False,
            merged_path=output,
            errors=[
                f"Besoin d'au moins 2 repos avec des graphs, trouvé {len(valid_repos)}"
            ],
        )

    # Build merge command
    graph_paths = [str(r.graph_path) for r in valid_repos]
    cmd = ["graphify", "merge-graphs"] + graph_paths + ["--out", str(output)]

    returncode, stdout, stderr = run_command(cmd, timeout=timeout)

    if returncode != 0:
        return MergeResult(
            success=False,
            merged_path=output,
            errors=[f"Échec fusion: {stderr}"],
        )

    # Parse merge stats from stdout
    # Format: "Merged 2 graphs -> 6951 nodes, 17400 edges"
    nodes, edges = 0, 0
    for line in stdout.split("\n"):
        if "nodes" in line and "edges" in line:
            # Extract nodes: "6951 nodes"
            if "nodes" in line:
                try:
                    nodes_part = line.split("->")[1].split("nodes")[0].strip()
                    nodes = int(nodes_part.replace(",", ""))
                except (IndexError, ValueError):
                    pass
            # Extract edges: "17400 edges"
            if "edges" in line:
                try:
                    edges_part = line.split("edges")[0].split(",")[-1].strip()
                    edges = int(edges_part.replace(",", ""))
                except (IndexError, ValueError):
                    pass

    # Run clustering unless skipped
    communities = 0
    if not skip_cluster:
        cluster_cmd = [
            "graphify",
            "cluster-only",
            str(output.parent.parent),
            "--graph",
            str(output),
        ]
        returncode, stdout, stderr = run_command(cluster_cmd, timeout=timeout)

        if returncode == 0:
            for line in stdout.split("\n"):
                if "communities" in line:
                    parts = line.split("-")
                    if len(parts) > 1:
                        try:
                            communities = int(parts[-1].split("communities")[0].strip())
                        except (ValueError, IndexError):
                            pass

    cross_edges_added = 0
    cross_edge_stats: cross_repo_edges.CrossRepoEdgeStats | None = None
    if add_cross_repo_edges:
        mcp_repo = next(
            (r for r in repos if r.name == cross_repo_edges.SOURCE_REPO), None
        )
        if mcp_repo and mcp_repo.exists:
            try:
                graph = cross_repo_edges.load_graph(output)
                cross_edge_stats = cross_repo_edges.CrossRepoEdgeStats()
                cross_edges_added = cross_repo_edges.add_cross_repo_edges(
                    graph,
                    mcp_repo.path,
                    stats=cross_edge_stats,
                )
                if cross_edges_added:
                    cross_repo_edges.save_graph(graph, output)
                    edges += cross_edges_added
            except Exception as e:
                return MergeResult(
                    success=False,
                    merged_path=output,
                    nodes=nodes,
                    edges=edges,
                    communities=communities,
                    errors=[f"Échec ajout arêtes cross-repo: {e}"],
                )

    duration = time.time() - start_time

    return MergeResult(
        success=True,
        merged_path=output,
        nodes=nodes,
        edges=edges,
        communities=communities,
        cross_repo_edges_added=cross_edges_added,
        cross_repo_edge_stats=cross_edge_stats,
        duration=duration,
    )


def generate_report(
    repos: list[RepoConfig],
    merge_result: MergeResult,
) -> str:
    """Generate a summary report."""
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    lines = [
        "# Graphify Cross-Repo Report",
        "",
        f"Generated: `{generated_at}`",
        "",
        "## Repositories",
        "",
    ]

    for repo in repos:
        status = "✓" if repo.has_graph else "✗"
        desc = f" — {repo.description}" if repo.description else ""
        lines.append(
            f"- {status} {repo.name}: `{repo.path}`{desc} "
            f"(HEAD `{repo.head_commit}`, {repo.dirty_status})"
        )

    lines.extend(
        [
            "",
            "## Merge Result",
            "",
            f"- **Status**: {'Succès' if merge_result.success else 'Échec'}",
            f"- **Nodes**: {merge_result.nodes:,}",
            f"- **Edges**: {merge_result.edges:,}",
            f"- **Cross-repo edges added**: {merge_result.cross_repo_edges_added:,}",
            f"- **Communities**: {merge_result.communities}",
            f"- **Duration**: {merge_result.duration:.1f}s",
            f"- **Output**: `{merge_result.merged_path}`",
        ]
    )

    if merge_result.errors:
        lines.extend(["", "## Errors", ""])
        for error in merge_result.errors:
            lines.append(f"- {error}")

    if merge_result.cross_repo_edge_stats:
        stats = merge_result.cross_repo_edge_stats
        lines.extend(
            [
                "",
                "## Cross-Repo Resolution",
                "",
                f"- **Imports scanned**: {stats.imports_seen:,}",
                f"- **ffbb_data_client imports**: {stats.imports_in_scope:,}",
                f"- **Edges added**: {stats.edges_added:,}",
                f"- **Duplicate edges skipped**: {stats.duplicate_edges:,}",
                f"- **Unresolved source files**: {stats.source_unresolved:,}",
                f"- **Unresolved targets**: {stats.target_unresolved:,}",
            ]
        )
        if stats.resolved_targets:
            lines.extend(["", "### Top resolved targets", ""])
            for target, count in sorted(
                stats.resolved_targets.items(), key=lambda item: item[1], reverse=True
            )[:10]:
                lines.append(f"- {count}× `{target}`")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Graphify Cross-Repo: Merge and analyze multiple repositories"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to configuration file (graphify-cross-repo.json)",
    )
    parser.add_argument(
        "--repos",
        nargs="+",
        type=Path,
        default=None,
        help="List of repository paths to merge (overrides config)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for merged graph (overrides config)",
    )
    parser.add_argument(
        "--skip-update",
        action="store_true",
        help="Skip individual repo graph updates",
    )
    parser.add_argument(
        "--skip-cluster",
        action="store_true",
        help="Skip clustering step",
    )
    parser.add_argument(
        "--skip-cross-repo-edges",
        action="store_true",
        help="Skip computed imports_from edges between repositories",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force graph rebuild even if fewer nodes",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate and print report",
    )
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel repo updates",
    )

    args = parser.parse_args()

    # Check graphify is installed
    if not check_graphify_installed():
        print("✗ graphify n'est pas installé ou accessible", file=sys.stderr)
        return 1

    print("╔══════════════════════════════════════════╗")
    print("║      Graphify Cross-Repo Analysis       ║")
    print("╚══════════════════════════════════════════╝")
    print()

    # Load configuration
    config: CrossRepoConfig
    if args.config and args.config.exists():
        print(f"📋 Chargement de la config: {args.config}")
        config = CrossRepoConfig.from_file(args.config)
    else:
        # Default configuration
        config = CrossRepoConfig(
            repos=[
                RepoConfig(
                    path=Path(
                        "/Volumes/HomeExt/Users/Nicolas/Documents/Repo GIT/ffbb-data-client"
                    ),
                    name="ffbb-data-client",
                    description="SDK Python pour l'API FFBB",
                ),
                RepoConfig(
                    path=Path(
                        "/Volumes/HomeExt/Users/Nicolas/Documents/Repo GIT/FFBB MCP server"
                    ),
                    name="FFBB MCP server",
                    description="Serveur MCP pour l'API FFBB",
                ),
            ]
        )

    # Override with CLI arguments
    if args.repos:
        config.repos = [RepoConfig(path=r.resolve(), name=r.name) for r in args.repos]
    if args.output:
        config.merged_filename = args.output.name
        config.output_dir = str(args.output.parent)
    if args.skip_update:
        config.auto_update = False
    if args.skip_cluster:
        config.auto_cluster = False
    if args.skip_cross_repo_edges:
        config.auto_cross_repo_edges = False
    if args.force:
        config.force_rebuild = True
    if args.report:
        config.generate_report = True
    if args.no_parallel:
        config.parallel_update = False

    # Print repo status
    for repo in config.repos:
        status = "✓" if repo.exists else "✗ (non trouvé)"
        print(f"📦 {repo.name}: {status}")

    print()

    # Check all repos exist
    missing = [r for r in config.repos if not r.exists]
    if missing:
        print("✗ Repos manquants:", file=sys.stderr)
        for r in missing:
            print(f"  - {r.path}", file=sys.stderr)
        return 1

    # Update graphs unless skipped
    if config.auto_update:
        print("═══ Mise à jour des graphs ═══")

        if config.parallel_update and len(config.repos) > 1:
            # Parallel update
            print(f"  → Mise à jour parallèle de {len(config.repos)} repos...")
            with ThreadPoolExecutor(max_workers=len(config.repos)) as executor:
                futures = {
                    executor.submit(
                        update_repo_graph,
                        repo,
                        config.force_rebuild,
                        config.timeout_per_repo,
                    ): repo
                    for repo in config.repos
                }

                for future in as_completed(futures):
                    repo, success, message = future.result()
                    print(f"  {repo.name}: {message}")
        else:
            # Sequential update
            for repo in config.repos:
                _, success, message = update_repo_graph(
                    repo,
                    config.force_rebuild,
                    config.timeout_per_repo,
                )
                print(f"  {repo.name}: {message}")

        print()

    # Determine output path
    output = Path(config.output_dir) / config.merged_filename
    output.parent.mkdir(parents=True, exist_ok=True)

    # Merge graphs
    print("═══ Fusion des graphs ═══")
    merge_result = merge_graphs(
        config.repos,
        output=output,
        skip_cluster=not config.auto_cluster,
        timeout=config.timeout_per_repo,
        add_cross_repo_edges=config.auto_cross_repo_edges,
    )
    print()

    # Print summary
    if merge_result.success:
        print("✅ Fusion réussie!")
        print(
            f"   {merge_result.nodes:,} nœuds, {merge_result.edges:,} arêtes, {merge_result.communities} communautés"
        )
        print(f"   Durée: {merge_result.duration:.1f}s")
        print(f"   Fichier: {output}")
    else:
        print("❌ Échec de la fusion", file=sys.stderr)
        for error in merge_result.errors:
            print(f"   {error}", file=sys.stderr)
        return 1

    # Generate report if requested
    if config.generate_report:
        print()
        print("═══ Rapport ═══")
        report = generate_report(config.repos, merge_result)
        print(report)

        # Save report to file
        report_path = output.parent / "CROSS_REPO_REPORT.md"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"\n📄 Rapport sauvegardé: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

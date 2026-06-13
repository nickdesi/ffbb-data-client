#!/bin/bash
# Graphify Cross-Repo: Wrapper script for easy usage
#
# Usage:
#   ./tools/graphify-cross-repo.sh              # Default: merge both repos
#   ./tools/graphify-cross-repo.sh --skip-update # Skip repo updates
#   ./tools/graphify-cross-repo.sh --report      # Generate report
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default repos (relative to this project)
DEFAULT_REPOS=(
    "/Volumes/HomeExt/Users/Nicolas/Documents/Repo GIT/ffbb-data-client"
    "/Volumes/HomeExt/Users/Nicolas/Documents/Repo GIT/FFBB MCP server"
)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}✓${NC} $*"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $*"; }
log_error() { echo -e "${RED}✗${NC} $*" >&2; }

# Check dependencies
check_deps() {
    if ! command -v graphify &>/dev/null; then
        log_error "graphify n'est pas installé"
        exit 1
    fi
    if ! command -v python3 &>/dev/null; then
        log_error "python3 n'est pas installé"
        exit 1
    fi
}

# Main
main() {
    check_deps

    # Build repo arguments
    REPO_ARGS=()
    for repo in "${DEFAULT_REPOS[@]}"; do
        if [[ -d "$repo" ]]; then
            REPO_ARGS+=("$repo")
        else
            log_warn "Repo non trouvé: $repo"
        fi
    done

    # Run the Python script with all arguments
    if [[ ${#REPO_ARGS[@]} -gt 0 ]]; then
        "${PYTHON:-python3}" "$SCRIPT_DIR/graphify_cross_repo.py" --repos "${REPO_ARGS[@]}" "$@"
    else
        "${PYTHON:-python3}" "$SCRIPT_DIR/graphify_cross_repo.py" "$@"
    fi
}

main "$@"

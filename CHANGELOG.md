# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.4.5] - 2026-08-29

### Security & Hardening (CodeQL / SSRF Pipeline Unification)
- **SSRF Elimination (CWE-918)**: Unification de l'ensemble des requêtes HTTP (sync & async) au travers de `make_http_request_with_retry` et élimination des appels directs non encapsulés à `session.get()` / `session.post()`.

## [2.4.4] - 2026-08-29

### Security & Hardening (CodeQL / SSRF Resolution)
- **SSRF Elimination (CWE-918)**: Découpage et reconstruction sûre des composants d'URL (`scheme`, `netloc`, `path`, `query`) pour casser le graphe de propagation de données non fiables dans `http_requests_utils.py` et `retry_utils.py`.

## [2.4.3] - 2026-08-29

### Security & Hardening (CodeQL / CWE-117 & CWE-918)
- **Log Injection (CWE-117)**: Neutralisation stricte des séquences CRLF dans `secure_logging.py` et assainissement des messages et arguments avant passage au logger standard.
- **SSRF Hardening (CWE-918)**: Validation stricte des protocoles (HTTP/HTTPS) et des cibles URL dans `http_requests_utils.py` et `retry_utils.py`.
- **FastAPI Input Validation**: Validation des bornes et expressions régulières des paramètres d'URL (IDs organismes et poules) dans `api.py`.
- **Explanatory Fallbacks**: Documentation explicite des clauses `except` de fallback dans `api.py` et `normalization.py`.

## [2.4.2] - 2026-08-29

### Security & Hardening (CodeQL / CWE-117 & CWE-918)
- **Log Injection (CWE-117)**: Neutralisation des injections de logs par assainissement des sauts de ligne (CRLF) dans `secure_logging.py`.
- **SSRF Hardening (CWE-918)**: Validation stricte des protocoles (HTTP/HTTPS) et des domaines cibles dans `http_requests_utils.py`.
- **CodeQL Empty Excepts**: Ajout de commentaires explicatifs documentés dans les blocs `except` de `api.py` et `normalization.py`.

## [2.4.1] - 2026-08-29

### Fixed
- **CI / Linters & Typage**: Correction des erreurs de typage MyPy/Pyright dans `api.py`, découpage des lignes d'expressions régulières dans `normalization.py` et configuration des extras de typage.

## [2.4.0] - 2026-08-29

### Added
- **Serveur FastAPI & REST API**: Serveur FastAPI intégré avec support CORS, documentation OpenAPI/Swagger et routes optimisées pour les matchs de clubs.
- **Résolution d'adresses précises des salles**: Résolution automatique de l'adresse de voirie exacte des gymnases pour l'ensemble des rencontres (domicile & extérieur).
- **Gestion du cycle de vie async (`aclose`)**: Support natif de la fermeture asynchrone des sessions et mutualisation des pools de connexions HTTP.

### Fixed & Maintenance
- **Imports des modèles**: Correction des chemins d'accès aux modèles `CategorieType` et `Niveau`.
- **Conventions d'architecture**: Documentation des règles d'immutabilité des packages PyPI et des directives d'imports de modèles dans `AGENTS.md`.

## [2.3.4] - 2026-08-19

### Fixed
- **Security**: Masquage complet des tokens d'authentification dans les messages et arguments de formatage de logs (`CWE-532` / alertes CodeQL).
- **Directus 403**: Retrait du champ `nom` obsolète dans `SaisonFields` pour prévenir les erreurs de permissions sur l'endpoint des saisons.

### Added & Changed
- **Website & Documentation**: Refonte de la landing page avec design spatial et support mobile 100% responsive (tiroir de navigation hamburger, protection contre le CSS grid blowout, typographie fluide).
- **PyPI & Docs**: Correction des liens relatifs dans le README pour un affichage propre sur PyPI.


## [2.3.3] - 2026-08-10

### Added
- **Recherche parallèle**: `search_many` / `search_many_async` exécutent plusieurs recherches Meilisearch indépendantes concurrentement (`asyncio.gather`) et renvoient les résultats dans l'ordre. Chaque `SearchSpec` est dispatché vers la méthode `search_multiple_<resource>_async` correspondante.
- **Keepalive CI**: nouveau workflow `keep-ffbb-api-discovery-alive` garantissant une exécution quotidienne de la discovery automatique des artefacts API (relance si aucun run depuis 22 h).
- **Unit tests** pour le script de discovery FFBB API (`scripts/discover_endpoints.py`).

### Changed
- **Performance**: `recursive_smart_multi_search` / `recursive_smart_multi_search_async`
  exécutent désormais la pagination Meilisearch en **parallèle** (lots de 10 pages,
  `asyncio.gather` en async / `ThreadPoolExecutor` en sync) au lieu d'enchaîner les
  allers-retours réseau un par un — divisant la latence de pagination par le nombre de pages.
- Les requêtes de pagination sont désormais **clonées** (`dataclasses.replace`) au lieu de
  muter les objets `MultiSearchQuery` du caller, supprimant une fuite d'état entre appels.
- **Refactor**: `api_ffbb_app_client.py` découpé en mixins (2408 → 113 lignes).
- **Performance**: réutilisation des connexions HTTP, wheel allégée et déduplication des recherches Meilisearch.
- **CI**: migration du AI PR reviewer (`.js` → `.cjs`), pagination et retry; simplification de la résolution de conflits de PR.

### Fixed
- Incohérences de la codebase : collision `HitType`, imports `_models` dépréciés remplacés par les sous-modules directs.
- CI : exécution uniquement de l'environnement tox correspondant à la matrice dans le job de test.
- Alertes CodeQL (imports) et ordre d'imports isort dans `http_requests_utils`.

## [2.3.2] - 2026-06-13

### Fixed
- Résolution du cycle d'imports du token manager et alignement des fichiers d'outillage (`fix: resolve token manager import cycle and sync tooling files`).
- Alertes CodeQL (imports et `empty-except`).
- Corrections pre-commit appliquées pour passer la CI.

## [2.3.1] - 2026-06-13

### Added
- **AI Pull Request Reviewer**: workflow d'analyse automatique des PR (analyse statique, commentaires automatiques, résolution de conflits `bolt.md`).

### Changed
- **Performance**: suppression de `TypeAdapter` de Pydantic au profit des parseurs natifs; optimisation de la réutilisation des connexions HTTP et du cache warming parallèle.
- **CI**: cache pip et tox dans la pipeline GitHub Actions; opt-in Node.js 24 pour toutes les actions JavaScript; upgrade `actions/checkout` (4→6), `actions/setup-node` (4→6), `upload-artifact`/`download-artifact` (v7/v8), `github/codeql-action` (4.35.5→4.36.x); permission `workflows: write` ajoutée puis revertée sur `release-after-discovery-merge`.

### Fixed
- Alertes de code scanning (`md5`, variables globales inutilisées, faux positifs Ruff S105).
- Cycle d'imports entre `token_manager` et `http_requests_utils`.
- Ordre d'imports (isort) et corrections flake8 pour le pre-commit de mise à jour des artefacts.

## [2.3.0] - 2026-05-24

### Added
- **API Schema Drift Detection**: Automated detection of changes inside Directus OpenAPI schemas (added/removed/modified properties, nested types, and nullability changes)
- **Meilisearch Attributes Drift Detection**: Automated detection of changes inside Meilisearch index schemas (`sampleKeys`) with robust sampling over 20 hits
- **CI/CD Pull Request Automation**: Pre-commit hooks and GitHub Actions workflow automatically open a Pull Request when any API property or index drift is detected
- Detailed Schema Drift reporting in `data/api_update_summary.md` and `report["drift"]` payload

### Fixed
- Robust Meilisearch sampling: index keys are now aggregated across 20 hits instead of 1, preventing false positives on optional null fields
- Pre-commit & flake8 E501 line too long violations in `tools/update_agents_md.py`
- Formatted `AGENTS.md` spacing and line wrapping for flawless agent ingestion

## [2.2.0] - 2026-05-17

### Changed
- **REFACTOR**: `FFBBDataClient` (2865 → 272 lines) split into modular facades — `_RestFacade` (1592 lines) and `_SearchFacade` (1020 lines)
- Public API remains 100% backward-compatible — all 167 methods accessible directly on `FFBBDataClient`
- `check_wrapper_parity.py` updated to scan facade files in addition to the main client

### Added
- `pytest_asyncio_mode = "auto"` in `pyproject.toml` for pytest-asyncio compatibility
- `isolated_build = True` in `tox.ini` for proper PEP 517 builds

### Fixed
- `CacheManager` docstring corrected — Redis backend marked as "planned" (not implemented)
- `readme_renderer[md]` moved from `install_requires` to `testing` extras (build-time only dependency)

### Removed
- Orphaned `src/ffbb_api_client_v3/` directory (residual from v2.1.0 cleanup)
- Orphaned `.coverage` file at project root
- `benchmark_search_organisme.py` moved from root to `scripts/`

## [2.1.0] - 2026-05-17

### Changed
- **BREAKING (internal)**: Sync methods now delegate to async counterparts via `_run_async()` helper, eliminating ~604 lines of duplication
- Sync and async share a single source of truth — async methods are canonical
- `ThreadPoolExecutor` fallback handles nested event loops gracefully

### Added
- **NEW**: Pre-push hook for type-check (mypy + pyright) — catches type errors before push
- **NEW**: CodeQL security scanning in CI
- **NEW**: Dependabot for automated dependency updates (GitHub Actions + pip)
- **NEW**: `SECURITY.md` security policy

### Fixed
- SQLite cache concurrency: sync uses `http_cache.db`, async uses `http_cache_async.db` (prevents `database is locked`)
- CI type check failures with proper generic typing for `_run_async(coro: Awaitable[T]) -> T`
- `FFBBDataClient` wrapper parity — added 8 missing async method delegations

### Removed
- Dead `invalidate_pattern()` from `CacheManager` and related tests
- `ffbb_api_client_v3` shim, dead scripts, and backward-compat alias

### Security
- CI supply chain hardened with pinned action versions and trusted publishers

## [2.0.2] - 2026-05-17

### Changed
- README version updated to v2.0.2

## [1.6.1] - 2026-04-29

### Changed
- Migrated test suite from `requests` to `httpx` to align with the core project dependencies.

### Fixed
- Fixed bug in `FFBBDataClient.multi_search` that could improperly mutate optional arguments when initialized as `None`.
- Fixed CI formatting errors and resolved Coveralls code coverage report upload issues by correcting `.coveragerc` path omission rules.

## [1.6.0] - 2026-04-24

### Added
- **NEW**: `get_configuration()` / `get_configuration_async()` exposed in `FFBBDataClient` wrapper
- **NEW**: `list_competitions()` / `list_competitions_async()` exposed in `FFBBDataClient` wrapper
- **NEW**: `search_multiple_competitions_async()` exposed in `FFBBDataClient` wrapper
- **NEW**: `search_multiple_organismes_async()` exposed in `FFBBDataClient` wrapper
- **NEW**: `search_multiple_pratiques_async()` exposed in `FFBBDataClient` wrapper
- **NEW**: `search_multiple_salles_async()` exposed in `FFBBDataClient` wrapper
- **NEW**: `search_multiple_terrains_async()` exposed in `FFBBDataClient` wrapper
- **NEW**: `search_multiple_tournois_async()` exposed in `FFBBDataClient` wrapper
- **NEW**: `search_multiple_engagements_async()` exposed in `FFBBDataClient` wrapper
- **NEW**: `search_multiple_formations_async()` exposed in `FFBBDataClient` wrapper
- **NEW**: GitHub Actions workflow `check_wrapper_parity.yml` — automated weekly CI check (every Monday 06:00 UTC) that fails if any public method from inner clients is missing from the wrapper
- **NEW**: `.github/scripts/check_wrapper_parity.py` — AST-based parity script with `@property` exclusion and GitHub Step Summary output

### Fixed
- Wrapper `FFBBDataClient` was silently missing 10 methods previously only accessible via inner clients directly

## [1.5.5] - 2026-04-20

### Added
- **NEW**: SEO-optimized landing page, `sitemap.xml`, `robots.txt` and updated `og:url`
- **NEW**: Added test coverage for `result_from_list` exceptions and `get_classement` delegation

### Changed
- **PERFORMANCE**: Pre-compile regex patterns and optimize SENIOR category deduction in `NiveauExtractor`
- **PERFORMANCE**: Replace O(n²) list operations with O(n) comprehensions in `filter_result` (`MultiSearchQuery`)
- **PERFORMANCE**: Optimize URL parameter encoding and datetime parsing
- Extracted normalization logic from `RencontresHit.__post_init__`
- Rewrote README with PAS framework and content strategy

### Fixed
- Error path in `OrganismesHit.from_dict`
- Trailing whitespace and end-of-file formatting
- CI action failures related to date validation

## [1.5.0] - 2026-04-04

### Added
- **NEW**: `search_engagements` / `search_formations` — two new Meilisearch search methods (sync + async) covering the `ffbbserver_engagements` and `ffbbserver_formations` indexes
- **NEW**: `EngagementsHit`, `FormationsHit`, `FormationSession` models with full field mapping
- **NEW**: `EngagementsMultiSearchQuery`, `FormationsMultiSearchQuery` query classes
- **NEW**: `EngagementsMultiSearchResult`, `FormationsMultiSearchResult` result types
- **NEW**: Facet distribution and stats classes for engagements and formations
- **NEW**: `filter`, `sort`, and `limit` parameters on all `search_*` and `search_multiple_*` methods (Meilisearch native filtering)
- **NEW**: Unit tests for search_engagements, search_formations, filter/sort/limit params (`test_v2_backport_search.py`, `test_123_v2_backport.py`)

### Changed
- `QueryFieldsManager` now inherits from `ABC` with abstract `get_fields()` method
- `FieldSet.BASIC` and `FieldSet.DETAILED` are now aliases for `FieldSet.DEFAULT` (simplified to a single field set)
- `generate_queries()` in `multi_search_query_helper.py` now includes engagements and formations (9 indexes total)

## [1.4.0] - 2026-04-03

### Added
- **NEW**: Sync with upstream v1.4.0 model updates (`organisme_fields`, `team_ranking`, `commune`)

### Improved
- **PERFORMANCE**: Improved async session reuse and HTTP robustness in the main client
- Enhanced data conversion utilities (`converter_utils`) to safely handle edge cases
- Better HTTP fallback logic and session management

### Fixed
- Cherry-picked critical fixes from upstream for Data Models to prevent deserialization errors on null/missing fields
- Type mismatches and formatting edge cases affecting data ingestion

## [1.2.0] - 2025-02-05

### Added
- **NEW**: `TokenManager` class for automatic token resolution
  - Fetches tokens from environment variables or FFBB API
  - Uses HTTP-level caching via `CacheManager` for configuration requests
  - `FFBBTokens` dataclass for type-safe token handling
- **NEW**: Centralized configuration module (`config.py`)
  - `API_FFBB_BASE_URL`, `MEILISEARCH_BASE_URL` constants
  - `DEFAULT_USER_AGENT` constant
  - `ENV_API_TOKEN`, `ENV_MEILISEARCH_TOKEN` environment variable names
  - API endpoint path constants (`ENDPOINT_CONFIGURATION`, `ENDPOINT_LIVES`, etc.)
  - Meilisearch endpoint path constants (`MEILISEARCH_ENDPOINT_MULTI_SEARCH`)
- New tests: `test_019_config.py`, `test_020_token_manager.py`

### Changed
- **BREAKING**: `TokenManager.get_tokens()` signature changed: `use_cache` parameter replaced by `cache_config`
- API clients now use centralized endpoint constants from `config.py`
- Simplified Quick Start examples using TokenManager
- Updated all example scripts to demonstrate TokenManager usage

### Removed
- `TokenManager.clear_cache()` method (use `get_cache_manager().clear()` instead)
- `TokenManager._cached_tokens` class variable (HTTP caching is now used)

### Improved
- No more manual token management required for basic usage
- Environment variable handling is now optional (tokens can be auto-fetched)

## [1.1.1] - 2025-09-16

### Fixed
- Fixed flake8 line length errors that prevented CI workflow from completing
- Updated maximum line length configuration to be compatible with Black formatting
- Improved code formatting consistency across the codebase

## [1.1.0] - 2025-09-16

### Added
- Comprehensive data models with automatic validation (`GetOrganismeResponse`, `GetCompetitionResponse`, `GetSaisonsResponse`, `GetPouleResponse`)
- Centralized query fields management with `QueryFieldsManager` and `FieldSet` enums
- 28 comprehensive unit tests with 100% pass rate
- Enhanced integration tests with real API validation
- Automatic environment variable loading from `.env` files
- Pre-commit hooks for code quality enforcement (Black, Flake8, isort)
- Advanced usage examples in documentation
- API reference documentation
- **NEW**: Team ranking analysis example (`examples/team_ranking_analysis.py`)
- **NEW**: Input validation utilities with secure token handling
- **NEW**: Retry mechanisms with exponential backoff for improved reliability
- **NEW**: Caching system for performance optimization

### Changed
- **BREAKING**: API methods now return strongly-typed model objects instead of dictionaries
- **BREAKING**: Field management now uses centralized `QueryFieldsManager` class
- All API methods use default fields automatically when fields parameter is None
- Improved error handling with automatic invalid data filtering
- Enhanced documentation with comprehensive examples
- Better API response parsing with `{"data": {...}}` wrapper handling
- **SECURITY**: Enhanced secure token logging and validation
- **PERFORMANCE**: Modernized Python code to use Python 3.9+ features (union operators, improved type hints)
- **QUALITY**: Applied comprehensive code formatting (Black, isort, pyupgrade) and linting (flake8)

### Fixed
- API response parsing issues with nested data structures
- Environment variable loading in test environments
- **CLEANUP**: Removed development scripts, temporary files, and redundant documentation
- **CONSISTENCY**: Consolidated CHANGELOG files (removed duplicate .rst version)

### Removed
- Temporary development scripts (`analyze_senas_ranking.py`, `find_pelissanne_*.py`, etc.)
- Cache files and temporary directories (`http_cache/`, `http_cache.db`, etc.)
- Redundant documentation files (Pelissanne analysis docs, duplicate parameters files)
- Duplicate CHANGELOG.rst file in favor of unified CHANGELOG.md

## [1.0.1] - 2025-08-12

### Added
- Basic integration tests and enhanced testing framework
- Improved API client functionality

### Fixed
- Various bug fixes and stability improvements

## [1.0.0.1] - Previous Release

### Added
- Basic FFBB API client functionality
- Search capabilities across multiple resource types
- Request caching support
- Meilisearch integration for search functionality
- Multi-search across all resource types

### Features
- Access to FFBB API endpoints (competitions, organismes, lives, etc.)
- Search functionality for clubs, competitions, matches, venues
- Basic data models and response handling
- PyScaffold-based project structure
- Apache 2.0 licensing

---

## Migration Guide

### From v1.0.x to v1.1.0

**API Response Changes:**
```python
# Before
organisme = client.get_organisme(123)
name = organisme['nom']  # Dictionary access

# After
organisme = client.get_organisme(123)
name = organisme.nom  # Object attribute access
```

**Field Selection:**
```python
# Before
fields = ["id", "nom", "code"]

# After
from ffbb_data_client.models.query_fields import QueryFieldsManager, FieldSet
fields = QueryFieldsManager.get_organisme_fields(FieldSet.BASIC)
```

**Error Handling:**
```python
# After - Automatic error handling
organisme = client.get_organisme(999999)
if organisme is None:
    print("Organization not found or error occurred")
```

[Unreleased]: https://github.com/nickdesi/ffbb-data-client/compare/v2.3.3...master
[2.3.3]: https://github.com/nickdesi/ffbb-data-client/compare/v2.3.2...v2.3.3
[2.3.2]: https://github.com/nickdesi/ffbb-data-client/compare/v2.3.1...v2.3.2
[2.3.1]: https://github.com/nickdesi/ffbb-data-client/compare/v2.3.0...v2.3.1
[2.3.0]: https://github.com/nickdesi/ffbb-data-client/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/nickdesi/ffbb-data-client/compare/v2.1.0...v2.2.0

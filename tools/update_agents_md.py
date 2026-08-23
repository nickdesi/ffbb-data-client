#!/usr/bin/env python3
"""Génère AGENTS.md pour le dépôt ffbb-data-client."""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FFBB_DATA_CLIENT_PY = (
    ROOT / "src" / "ffbb_data_client" / "clients" / "ffbb_data_client.py"
)
REST_FACADE_PY = ROOT / "src" / "ffbb_data_client" / "clients" / "_rest_facade.py"
SEARCH_FACADE_PY = ROOT / "src" / "ffbb_data_client" / "clients" / "_search_facade.py"
AGENTS_MD = ROOT / "AGENTS.md"


def extract_facade_methods() -> tuple[list[str], list[str]]:
    """Parse ffbb_data_client.py et extrait les listes _REST_METHODS et _SEARCH_METHODS."""
    if not FFBB_DATA_CLIENT_PY.exists():
        return [], []
    tree = ast.parse(FFBB_DATA_CLIENT_PY.read_text())
    rest_methods = []
    search_methods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "_REST_METHODS" and isinstance(
                        node.value, ast.List
                    ):
                        rest_methods = [
                            str(elt.value)
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant)
                        ]
                    elif target.id == "_SEARCH_METHODS" and isinstance(
                        node.value, ast.List
                    ):
                        search_methods = [
                            str(elt.value)
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant)
                        ]
    return rest_methods, search_methods


def extract_method_summaries(filepath: Path) -> dict[str, str]:
    """Parse un fichier facade et extrait les docstrings des méthodes publiques."""
    if not filepath.exists():
        return {}
    tree = ast.parse(filepath.read_text())
    summaries = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            docstring = ast.get_docstring(node) or ""
            first_line = docstring.strip().split("\n")[0] if docstring else ""
            summaries[node.name] = first_line.strip().rstrip(".")
    return summaries


def count_lines(filepath: Path) -> int:
    if not filepath.exists():
        return 0
    return len(filepath.read_text().splitlines())


def count_dir_lines(directory: Path) -> int:
    """Compte récursivement le nombre de lignes de tous les fichiers .py du dossier."""
    total = 0
    if not directory.exists():
        return 0
    for py_file in directory.rglob("*.py"):
        total += len(py_file.read_text().splitlines())
    return total


def generate_agents_md() -> str:
    rest_methods, search_methods = extract_facade_methods()
    rest_summaries = extract_method_summaries(REST_FACADE_PY)
    search_summaries = extract_method_summaries(SEARCH_FACADE_PY)

    # Lignes par composants
    clients_lines = count_dir_lines(ROOT / "src" / "ffbb_data_client" / "clients")
    models_lines = count_dir_lines(ROOT / "src" / "ffbb_data_client" / "models")
    utils_lines = count_dir_lines(ROOT / "src" / "ffbb_data_client" / "utils")
    helpers_lines = count_dir_lines(ROOT / "src" / "ffbb_data_client" / "helpers")
    total_lines = clients_lines + models_lines + utils_lines + helpers_lines

    # Construction du tableau REST
    rest_rows = []
    for name in rest_methods:
        summary = rest_summaries.get(name, "Méthode de récupération de données")
        rest_rows.append(f"- `{name}` : {summary}")

    # Construction du tableau Search
    search_rows = []
    for name in search_methods:
        summary = search_summaries.get(name, "Méthode de recherche de données")
        search_rows.append(f"- `{name}` : {summary}")

    NL = "\n"

    content = f"""# FFBB Data Client SDK

> ⚠️ **Fichier auto-généré** par `tools/update_agents_md.py` — ne pas modifier manuellement.
> Dernière mise à jour : ffbb-data-client | SDK total : ~{total_lines} lignes de code
> (clients: {clients_lines}, models: {models_lines}, utils: {utils_lines}, helpers: {helpers_lines})

## Langue
Tous les documents de travail (walkthrough.md, implementation_plan.md) DOIVENT être en français.

## Persona
Expert en basketball français et intégration technique.
Accès au SDK Python de bas niveau `ffbb-data-client` connecté à l'API et au Meilisearch officiel de la FFBB.

## Méthodes REST du Client (Exemples importants)
Le SDK expose les méthodes directes de récupération de données suivantes via `FFBBDataClient` :
{NL.join(rest_rows)}

## Méthodes de Recherche Meilisearch (Exemples importants)
Le SDK expose également des méthodes de recherche optimisées avec facettes, géolocalisation et filtres via Meilisearch :
{NL.join(search_rows)}

## Variables d'environnement
Le SDK résout automatiquement les jetons de sécurité via les variables d'environnement suivantes
ou interroge l'API publique en cache en cas d'absence :

| Variable | Défaut | Usage |
|----------|--------|-------|
| `API_FFBB_APP_BEARER_TOKEN` | — | Jeton Bearer de sécurité pour requêter directement l'API FFBB (api.ffbb.app) |
| `MEILISEARCH_BEARER_TOKEN` | — | Jeton Bearer de sécurité pour interroger le moteur Meilisearch (meilisearch-prod.ffbb.app) |

## Règles de comportement des agents
- **RTK OBLIGATOIRE** : Utilisez TOUJOURS le préfixe `rtk` pour toutes les commandes terminal
  exécutées sur la machine de l'utilisateur (ex: `rtk pytest`, `rtk tox`, etc.).
- **Tox & Pytest** : Privilégiez l'exécution des tests via `pytest` local ou `tox` pour valider
  les évolutions du SDK sur les différentes versions de Python prises en charge.
- **Modèles typés** : Respectez scrupuleusement la déclaration des types Pydantic de `ffbb_data_client.models`.
  Tout nouveau modèle ou modification de champ doit correspondre aux spécifications de l'API FFBB.
- **Réponses en français** : Communiquez et expliquez toujours vos changements ou vos analyses en langue française.
- **Génération et mises à jour autonomes** : Effectuez systématiquement toutes les régénérations de
  documentation (`AGENTS.md`), de site/landing page ou autres tâches de synchronisation de
  manière autonome. Si vous estimez qu'une mise à jour automatique est pertinente ou non, prenez
  la décision par vous-même sans attendre la validation explicite de l'utilisateur.
- **Validation pre-commit systématique (Zéro échec de CI)** : Pour éviter tout échec de build ou de formatage en CI,
  exécutez systématiquement la validation complète locale via `rtk pre-commit run --all-files` avant de pousser
  tout commit vers origin. Résolvez toutes les alertes (formatage, imports `isort`, typage) localement.


## Karpathy Guidelines (Règles de développement)
Ces directives inspirées d'Andrej Karpathy visent à éliminer les erreurs de codage courantes en privilégiant la simplicité et la rigueur :

### 1. Penser avant de coder (Think Before Coding)
- **Ne pas assumer, ne pas cacher la confusion, expliciter les compromis.**
- Avant d'implémenter :
  - Déclarez vos hypothèses de manière explicite. En cas d'incertitude, demandez.
  - S'il existe plusieurs interprétations, présentez-les — ne choisissez pas en silence.
  - Si une approche plus simple existe, proposez-la. Argumentez contre la complexité inutile si nécessaire.
  - Si quelque chose n'est pas clair, arrêtez-vous. Nommez ce qui vous perturbe et demandez confirmation.

### 2. La simplicité d'abord (Simplicity First)
- **Le minimum de code nécessaire pour résoudre le problème. Rien de spéculatif.**
- Pas de fonctionnalités au-delà de ce qui est explicitement demandé.
- Pas d'abstractions pour du code à usage unique.
- Pas de "flexibilité" ou de "configurabilité" non requise.
- Pas de gestion d'erreurs pour des scénarios impossibles.
- Si vous écrivez 200 lignes alors que 50 suffiraient, réécrivez-le.
- Posez-vous toujours la question : "Est-ce qu'un développeur senior validerait cette implémentation comme simple et directe ?"

## Architecture du SDK
```
src/ffbb_data_client/
├── __init__.py            # Point d'entrée du SDK, expose FFBBDataClient et FFBBTokens
├── clients/               # Clients d'API (REST et Meilisearch) et façades (≈{clients_lines} lignes)
├── config.py              # Configuration centralisée (URLs, Headers, Endpoints, Facettes)
├── data/                  # Ressources et données statiques
├── helpers/               # Méthodes utilitaires pour requêtes HTTP et mapping (≈{helpers_lines} lignes)
├── models/                # Modèles de données Pydantic type-safe (≈{models_lines} lignes)
├── py.typed               # Marqueur pour la compatibilité avec mypy
└── utils/                 # Gestionnaires transversaux (cache, jetons de sécurité, validation) (≈{utils_lines} lignes)
```

## Conventions de code
- **Modèles Pydantic** : Tous les modèles héritent de `pydantic.BaseModel` et fournissent une validation stricte.
  Chaque modèle possède son propre fichier source dédié en `snake_case` (ex: `categorie_type.py`, `niveau_info.py`).
  Les imports internes et dans les tests doivent cibler précisément le fichier dédié ou le namespace racine `models`.
- **Async/Sync en parallèle** : Le SDK implémente systématiquement la double interface synchrone (`get_x`)
  et asynchrone (`get_x_async`) pour un maximum de flexibilité d'intégration.
- **Cache HTTP** : Utilisation d'`hishel` pour le cache de requêtes HTTP asynchrones et d'un cache local
  configurable pour optimiser les appels et respecter les quotas FFBB.
- **Validation** : Les paramètres passés à `FFBBDataClient.create` sont strictement validés
  via les utilitaires de validation robustes de `utils/input_validation.py`.

## Commandes courantes
- Lancer les tests locaux : `rtk pytest`
- Lancer la suite d'intégration Tox : `rtk tox`
- Vérifier les types : `rtk mypy src`
- Formater et vérifier le style : `rtk ruff format . && rtk ruff check .`

## Push / Tag / Release Gate
⚠️ OBLIGATION STRICTE : Toutes ces commandes DOIVENT être préfixées par 'rtk' dans le terminal
(ex: 'rtk pytest'). Ne jamais exécuter de commande nue sans 'rtk'.
Avant push/tag/release :
1. `rtk ruff format --check .`
2. `rtk ruff check .`
3. `rtk mypy src`
4. `rtk pytest`
5. `rtk pre-commit run --all-files`

⚠️ Note Release PyPI : Les releases sur PyPI sont immuables. Ne jamais réassigner ou forcer un tag
déjà publié sur PyPI. Tout correctif requiert un bump de version (ex: v2.3.6).
"""
    return content


def main():
    """Génère AGENTS.md et retourne 0 si le fichier a changé, 1 sinon."""
    new_content = generate_agents_md()
    existing = AGENTS_MD.read_text() if AGENTS_MD.exists() else ""

    if new_content == existing:
        print("AGENTS.md — aucun changement détecté.")
        return 0

    AGENTS_MD.write_text(new_content)
    print("AGENTS.md — mis à jour avec succès.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

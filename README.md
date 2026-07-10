<div align="center">

# 🏀 FFBB Data Client

**SDK Python moderne, typé et asynchrone pour exploiter les données publiques FFBB : clubs, compétitions, rencontres, classements, salles, officiels et recherche Meilisearch.**

[![PyPI](https://img.shields.io/pypi/v/ffbb-data-client?color=blue&label=PyPI&logo=python&logoColor=white)](https://pypi.org/project/ffbb-data-client/)
[![Python](https://img.shields.io/pypi/pyversions/ffbb-data-client?logo=python&logoColor=white)](https://pypi.org/project/ffbb-data-client/)
[![CI](https://github.com/nickdesi/ffbb-data-client/actions/workflows/ci.yml/badge.svg)](https://github.com/nickdesi/ffbb-data-client/actions/workflows/ci.yml)
[![Coverage](https://coveralls.io/repos/github/nickdesi/ffbb-data-client/badge.svg?branch=master)](https://coveralls.io/github/nickdesi/ffbb-data-client?branch=master)
[![License](https://img.shields.io/pypi/l/ffbb-data-client?color=green)](LICENSE.txt)
[![MCP-Ready](https://img.shields.io/badge/MCP-Ready-orange.svg?logo=modelcontextprotocol&logoColor=white)](https://github.com/nickdesi/FFBB-MCP-Server)
[![Security Policy](https://img.shields.io/badge/Security-Policy-blue.svg)](SECURITY.md)
[![Stars](https://img.shields.io/github/stars/nickdesi/ffbb-data-client?style=social)](https://github.com/nickdesi/ffbb-data-client/stargazers)
[![Last Commit](https://img.shields.io/github/last-commit/nickdesi/ffbb-data-client)](https://github.com/nickdesi/ffbb-data-client/commits/master)
[![Issues](https://img.shields.io/github/issues/nickdesi/ffbb-data-client)](https://github.com/nickdesi/ffbb-data-client/issues)
[![PRs](https://img.shields.io/github/issues-pr/nickdesi/ffbb-data-client)](https://github.com/nickdesi/ffbb-data-client/pulls)

[Installation](#-installation) •
[Démarrage rapide](#-démarrage-rapide) •
[Fonctionnalités](#-fonctionnalités) •
[Recherche](#-recherche-meilisearch) •
[Async](#-utilisation-asynchrone) •
[Développement](#-développement-local)

</div>

---

## 📌 À propos

`ffbb_data_client` simplifie l'accès aux API FFBB et à leurs index Meilisearch avec :

- une façade unique : `FFBBDataClient` ;
- des modèles Pydantic v2 typés ;
- une API utilisable en synchrone ou en `async/await` ;
- une gestion automatique des tokens via `TokenManager` ;
- du cache HTTP configurable via `hishel` ;
- des helpers prêts pour l'intégration MCP / agents IA.

---

## 🚀 Version v2.3.1 — Juin 2026

Principales évolutions récentes :

- **détection de drift API** : surveillance des changements de schéma Directus (propriétés/types/nullabilité) ;
- **détection de drift Meilisearch** : agrégation robuste des attributs (`sampleKeys`) sur plusieurs hits ;
- **automatisation CI/CD** : ouverture automatique de PR lorsqu'un drift est détecté ;
- **fiabilité outillage** : alignement pyupgrade/isort/pre-commit pour des runs CI reproductibles ;
- **qualité/sécurité** : corrections CodeQL et nettoyage des alertes d'analyse statique.

Voir aussi : [CHANGELOG.md](https://github.com/nickdesi/ffbb-data-client/blob/master/CHANGELOG.md) et [RELEASE_NOTES.md](https://github.com/nickdesi/ffbb-data-client/blob/master/RELEASE_NOTES.md).

---

## 📦 Installation

```bash
pip install ffbb-data-client
```

Pour contribuer ou exécuter les tests :

```bash
git clone https://github.com/nickdesi/ffbb-data-client.git
cd ffbb-data-client
pip install -e ".[testing]"
```

Prérequis : Python `>=3.10`.

---

## ⚡ Démarrage rapide

```python
from ffbb_data_client import FFBBDataClient

client = FFBBDataClient.create()

# Recherche globale sur les index FFBB
results = client.multi_search("Pau Orthez")

for result in results or []:
    print(result.index_uid, len(result.hits or []))

# Lives en cours
lives = client.get_lives()
```

`FFBBDataClient.create()` résout automatiquement les tokens si aucun token n'est passé explicitement.

---

## ✨ Fonctionnalités

| Domaine | Capacités |
|---|---|
| API FFBB | clubs, compétitions, organismes, saisons, poules, classements, rencontres, lives |
| Entités additionnelles | EDF (matches, joueurs, rosters, équipes), Genius Sport, Rematch Videos |
| Recherche | organismes, compétitions, rencontres, salles, terrains, pratiques, tournois, engagements et formations |
| REST typé | récupération de ressources individuelles avec modèles Pydantic v2 |
| Async | méthodes `*_async()` — source de vérité ; sync délègue via `_run_async()` |
| Cache | cache HTTP `hishel`, sessions `httpx` réutilisées, retries configurables, SQLite séparés sync/async |
| Sécurité | masquage des tokens dans les logs, CodeQL scanning, Dependabot |
| IA / MCP | structure compatible avec des wrappers MCP et agents IA |

---

## 🔍 Recherche Meilisearch

### Recherche globale

```python
results = client.multi_search("Clermont")
```

### Recherche ciblée

```python
organismes = client.search_organismes(
    "Clermont",
    filter=['codePostal = "63000"'],
    sort=["nom:asc"],
    limit=10,
)

rencontres = client.search_rencontres("N1M", limit=20)
salles = client.search_salles("Maison des Sports", limit=5)
engagements = client.search_engagements("U15M", limit=20)
```

### Recherche géographique

```python
clubs = client.search_organismes_by_geo(
    lat=45.7772,
    lng=3.0870,
    radius_km=20,
    limit=20,
)
```

### Principales méthodes exposées

| Ressource | Méthode sync | Méthode async |
|---|---|---|
| Recherche globale | `multi_search()` | `multi_search_async()` |
| Clubs / organismes | `search_organismes()` | `search_organismes_async()` |
| Compétitions | `search_competitions()` | `search_competitions_async()` |
| Rencontres | `search_rencontres()` | `search_rencontres_async()` |
| Salles | `search_salles()` | `search_salles_async()` |
| Terrains | `search_terrains()` | `search_terrains_async()` |
| Pratiques | `search_pratiques()` | `search_pratiques_async()` |
| Tournois | `search_tournois()` | `search_tournois_async()` |
| Engagements | `search_engagements()` | `search_engagements_async()` |
| Formations | `search_formations()` | `search_formations_async()` |

---

## 🧱 Accès REST typé

```python
# Ressources principales
organisme = client.get_organisme(12345)
competition = client.get_competition(67890)
poule = client.get_poule(11111)

# Ressources ajoutées récemment
rencontre = client.get_rencontre(22222)
officiel = client.get_officiel(33333)
entraineur = client.get_entraineur(44444)
```

Les assets Directus et autres collections peuvent être exploités via les méthodes REST/listing dédiées exposées par le client lorsque disponibles.

Les réponses sont converties en modèles Pydantic lorsque le schéma est connu, ce qui apporte validation, autocomplétion et sérialisation propre.

---

## 🧵 Utilisation asynchrone

```python
import asyncio
from ffbb_data_client import FFBBDataClient

async def main() -> None:
    client = FFBBDataClient.create()

    results = await client.search_organismes_async("ASVEL")
    lives = await client.get_lives_async()

    print(results.estimated_total_hits if results else 0)
    print(len(lives or []))

asyncio.run(main())
```

---

## 🔐 Tokens et configuration

Par défaut, le client utilise `TokenManager.get_tokens()` au moment de la création :

```python
from ffbb_data_client import FFBBDataClient, TokenManager

tokens = TokenManager.get_tokens()

client = FFBBDataClient.create(
    api_bearer_token=tokens.api_token,
    meilisearch_bearer_token=tokens.meilisearch_token,
)
```

Il est donc possible de laisser le client résoudre les tokens automatiquement ou de les fournir explicitement selon le contexte d'exécution.

---

## 🏗 Architecture

```text
src/ffbb_data_client/
├── clients/
│   ├── ffbb_data_client.py       # Façade publique (272 lignes, delegation)
│   ├── _rest_facade.py           # Façade REST API (Directus)
│   ├── _search_facade.py         # Façade recherche Meilisearch
│   ├── api_ffbb_app_client.py    # Client REST FFBB (async source of truth)
│   └── meilisearch_ffbb_client.py # Client recherche Meilisearch
├── helpers/                       # Requêtes HTTP, multi-search, conversions
├── models/                        # Modèles Pydantic v2
├── utils/                         # cache (sync/async séparés), tokens, logging sécurisé
└── data/                          # schémas et métadonnées embarqués
```

> **Architecture sync/async** : Depuis v2.1.0, les méthodes asynchrones sont la source de vérité. Les méthodes synchrones délèguent via `_run_async()`, un helper qui gère les event loops imbriqués avec `ThreadPoolExecutor`.
>
> **Architecture facades** : Depuis v2.2.0, `FFBBDataClient` est une fine coquille qui compose `_RestFacade` et `_SearchFacade`. L'API publique reste identique — `client.get_organisme(123)` fonctionne comme avant.

---

## 🧪 Développement local

```bash
pip install -e ".[testing]"
pytest tests/
```

Commandes utiles :

```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/ --cov=src
tox -e type          # mypy + pyright
```

Hooks automatiques :
- **pre-push** : exécute mypy + pyright avant chaque push
- **pre-commit** : black, isort, flake8, trailing-whitespace

Documentation complémentaire :

- [`LOCAL_CI_GUIDE.md`](LOCAL_CI_GUIDE.md)
- [`docs/testing_conventions.md`](docs/testing_conventions.md)
- [`docs/architecture.rst`](docs/architecture.rst)

---

## 🛠️ Découverte d'API et Détection de Drift (Schema Drift)

Le projet intègre un système robuste de surveillance quotidienne de l'API de production de la FFBB (Directus & Meilisearch) afin de détecter immédiatement l'apparition de nouvelles ressources, de nouveaux champs ou de changements de types.

### 1. Fonctionnement
* **Script de découverte** : `scripts/discover_endpoints.py` interroge dynamiquement l'OpenAPI spec Directus de la FFBB, extrait toutes les collections, sonde les index Meilisearch (via un échantillonnage agrégé sur 20 hits) et calcule les différences structurelles avec les fichiers locaux.
* **Détection de dérive** : Le script compare les structures internes de chaque modèle (propriétés ajoutées, supprimées ou types modifiés) ainsi que les attributs Meilisearch, et génère un rapport consolidé dans `data/api_update_summary.md`.

### 2. Automatisation CI/CD
Un workflow quotidien (`update-ffbb-api-discovery.yml`) s'exécute chaque matin à 5h17 UTC pour :
1. Télécharger l'OpenAPI spec et sonder Meilisearch en production.
2. Analyser les dérives structurelles.
3. Si un changement structurel est détecté (ajout de collection, de propriétés ou d'index), le workflow ouvre automatiquement une **Pull Request** sur GitHub contenant un résumé des modifications pour permettre aux développeurs de mettre à jour les modèles Pydantic.

### 3. Exécution locale
Pour lancer manuellement la découverte d'API et mettre à jour les fichiers de schémas locaux :
```bash
python scripts/discover_endpoints.py
```

---

## 🤖 Intégration IA / MCP

Le client sert de base au serveur MCP FFBB et expose une API stable pour construire des outils agent-friendly : recherche de clubs, récupération de poules, classements, lives, calendriers et détails de rencontres.

Projet associé : [FFBB-MCP-Server](https://github.com/nickdesi/FFBB-MCP-Server)

---

## 🤝 Contribuer

Les contributions sont bienvenues :

- ouvrez une [issue](https://github.com/nickdesi/ffbb-data-client/issues) pour un bug ;
- proposez une évolution via les [discussions](https://github.com/nickdesi/ffbb-data-client/discussions) ;
- lancez les tests localement avant une pull request.

---

## 📄 Licence

Distribué sous licence Apache-2.0. Voir [`LICENSE.txt`](LICENSE.txt).

---

## 📌 Recommandations GitHub

**Description suggérée :**

> 🏀 Modern async & typed Python SDK for FFBB public data (clubs, competitions, standings, lives) and Meilisearch search — the data layer behind the FFBB MCP Server.

**Topics suggérés (≤ 20) :**

`python` · `api-client` · `ffbb` · `open-data` · `basketball` · `mcp` · `model-context-protocol` · `async` · `pydantic` · `meilisearch` · `sdk` · `ai` · `llm` · `sports` · `rest-api` · `httpx` · `france` · `data` · `cache` · `typed`

---

<div align="center">

**Si ce projet vous aide, une étoile est appréciée. ⭐**

[![GitHub stars](https://img.shields.io/github/stars/nickdesi/ffbb-data-client?style=social)](https://github.com/nickdesi/ffbb-data-client/stargazers)

</div>

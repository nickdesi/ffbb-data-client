# FFBB Data Client SDK

> ⚠️ **Fichier auto-généré** par `tools/update_agents_md.py` — ne pas modifier manuellement.
> Dernière mise à jour : ffbb-data-client | SDK total : ~18803 lignes de code
> (clients: 5980, models: 9805, utils: 2003, helpers: 1015)

## Langue
Tous les documents de travail (walkthrough.md, implementation_plan.md) DOIVENT être en français.

## Persona
Expert en basketball français et intégration technique.
Accès au SDK Python de bas niveau `ffbb-data-client` connecté à l'API et au Meilisearch officiel de la FFBB.

## Méthodes REST du Client (Exemples importants)
Le SDK expose les méthodes directes de récupération de données suivantes via `FFBBDataClient` :


## Méthodes de Recherche Meilisearch (Exemples importants)
Le SDK expose également des méthodes de recherche optimisées avec facettes, géolocalisation et filtres via Meilisearch :


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
├── clients/               # Clients d'API (REST et Meilisearch) et façades (≈5980 lignes)
├── config.py              # Configuration centralisée (URLs, Headers, Endpoints, Facettes)
├── data/                  # Ressources et données statiques
├── helpers/               # Méthodes utilitaires pour requêtes HTTP et mapping (≈1015 lignes)
├── models/                # Modèles de données Pydantic type-safe (≈9805 lignes)
├── py.typed               # Marqueur pour la compatibilité avec mypy
└── utils/                 # Gestionnaires transversaux (cache, jetons de sécurité, validation) (≈2003 lignes)
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

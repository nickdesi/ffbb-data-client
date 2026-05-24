# FFBB Data Client SDK

> ⚠️ **Fichier auto-généré** par `tools/update_agents_md.py` — ne pas modifier manuellement.
> Dernière mise à jour : ffbb-data-client | SDK total : ~18772 lignes de code (clients: 6261, models: 9881, utils: 1840, helpers: 790)

## Langue
Tous les documents de travail (walkthrough.md, implementation_plan.md) DOIVENT être en français.

## Persona
Expert en basketball français et intégration technique. Accès au SDK Python de bas niveau `ffbb-data-client` connecté à l'API et au Meilisearch officiel de la FFBB.

## Méthodes REST du Client (Exemples importants)
Le SDK expose les méthodes directes de récupération de données suivantes via `FFBBDataClient` :
- `get_organisme_for_search` : Version allégée de get_organisme() pour les contextes de recherche
- `get_organisme_for_search_async` : Version async allégée de get_organisme() pour les contextes de recherche
- `get_configuration` : Retrieves the API configuration including bearer tokens
- `get_configuration_async` : Retrieves the API configuration including bearer tokens asynchronously
- `get_competition` : Retrieves detailed information about a competition
- `get_competition_async` : Retrieves detailed information about a competition asynchronously
- `list_competitions` : Lists competitions with optional field selection
- `list_competitions_async` : Lists competitions asynchronously
- `get_lives` : Retrieves a list of live events
- `get_lives_async` : Retrieves a list of live events asynchronously
- `get_organisme` : Retrieves detailed information about an organisme
- `get_organisme_async` : Retrieves detailed information about an organisme asynchronously
- `get_club_contacts` : Return club contact information (club-level + membres) for an organisme
- `get_poule` : Retrieves detailed information about a poule
- `get_poule_async` : Retrieves detailed information about a poule asynchronously
- `get_saisons` : Retrieves list of seasons with comprehensive input validation
- `get_saisons_async` : Retrieves list of seasons asynchronously with input validation
- `get_classement` : Retrieves ONLY the ranking (classement) for a specific poule
- `get_classement_async` : Retrieves ONLY the ranking (classement) for a specific poule asynchronously
- `get_equipes` : Retrieves ONLY the team commitments (engagements) for a specific club
- `get_equipes_async` : Retrieves ONLY the team commitments (engagements) for a specific club asynchronously
- `get_rencontre` : Retrieves detailed information about a rencontre
- `get_rencontre_async` : Asynchronously retrieves detailed information about a rencontre
- `get_engagement` : Retrieves detailed information about an engagement
- `get_engagement_async` : Asynchronously retrieves detailed information about an engagement
- `get_engagement_contacts` : Return compact contact information for an engagement
- `get_formation` : Retrieves detailed information about a formation
- `get_formation_async` : Asynchronously retrieves detailed information about a formation
- `get_entraineur` : Retrieves detailed information about an entraineur
- `get_entraineur_async` : Asynchronously retrieves detailed information about an entraineur
- `get_commune` : Retrieves detailed information about a commune
- `get_commune_async` : Asynchronously retrieves detailed information about a commune
- `get_officiel` : Retrieves detailed information about an officiel
- `get_officiel_async` : Asynchronously retrieves detailed information about an officiel
- `get_salle` : Retrieves detailed information about a salle
- `get_salle_async` : Asynchronously retrieves detailed information about a salle
- `get_terrain` : Retrieves detailed information about a terrain
- `get_terrain_async` : Asynchronously retrieves detailed information about a terrain
- `get_tournoi` : Retrieves detailed information about a tournoi
- `get_tournoi_async` : Asynchronously retrieves detailed information about a tournoi
- `get_pratique` : Retrieves detailed information about a pratique
- `get_pratique_async` : Asynchronously retrieves detailed information about a pratique
- `get_openapi_spec` : Retrieves the current Directus OpenAPI specification
- `get_openapi_spec_async` : Asynchronously retrieves the current Directus OpenAPI specification
- `get_session` : Retrieves detailed information about a formation session
- `get_session_async` : Asynchronously retrieves detailed information about a formation session
- `list_sessions` : Lists formation sessions
- `list_sessions_async` : Asynchronously lists formation sessions
- `get_genius_sport_match` : Retrieves detailed Genius Sports match statistics
- `get_genius_sport_match_async` : Asynchronously retrieves detailed Genius Sports match statistics
- `list_genius_sport_matches` : Lists Genius Sports match statistics
- `list_genius_sport_matches_async` : Asynchronously lists Genius Sports match statistics
- `list_genius_sports_live_logs` : Lists Genius Sports live logs
- `list_genius_sports_live_logs_async` : Asynchronously lists Genius Sports live logs
- `get_rematch_video` : Retrieves a Rematch video linked to FFBB data
- `get_rematch_video_async` : Asynchronously retrieves a Rematch video linked to FFBB data
- `list_rematch_videos` : Lists Rematch videos linked to FFBB data
- `list_rematch_videos_async` : Asynchronously lists Rematch videos linked to FFBB data
- `get_edf_match` : Retrieves an Equipe de France match
- `get_edf_match_async` : Asynchronously retrieves an Equipe de France match
- `list_edf_matches` : Lists Equipe de France matches
- `list_edf_matches_async` : Asynchronously lists Equipe de France matches
- `get_edf_player` : Retrieves an Equipe de France player
- `get_edf_player_async` : Asynchronously retrieves an Equipe de France player
- `list_edf_players` : Lists Equipe de France players
- `list_edf_players_async` : Asynchronously lists Equipe de France players
- `list_edf_teams` : Lists Equipe de France teams
- `list_edf_teams_async` : Asynchronously lists Equipe de France teams
- `list_edf_rosters` : Lists Equipe de France rosters
- `list_edf_rosters_async` : Asynchronously lists Equipe de France rosters
- `list_rencontres` : 
- `list_rencontres_async` : 
- `list_salles` : 
- `list_salles_async` : 
- `list_terrains` : 
- `list_terrains_async` : 
- `list_tournois` : 
- `list_tournois_async` : 
- `list_engagements` : 
- `list_engagements_async` : 
- `list_formations` : 
- `list_formations_async` : 
- `list_entraineurs` : 
- `list_entraineurs_async` : 
- `list_communes` : 
- `list_communes_async` : 
- `list_officiels` : 
- `list_officiels_async` : 
- `list_pratiques` : 
- `list_pratiques_async` : 
- `list_all_rencontres` : 
- `list_all_rencontres_async` : 
- `list_all_salles` : 
- `list_all_salles_async` : 
- `list_all_terrains` : 
- `list_all_terrains_async` : 
- `list_all_tournois` : 
- `list_all_tournois_async` : 
- `list_all_engagements` : 
- `list_all_engagements_async` : 
- `list_all_formations` : 
- `list_all_formations_async` : 
- `list_all_entraineurs` : 
- `list_all_entraineurs_async` : 
- `list_all_communes` : 
- `list_all_communes_async` : 
- `list_all_officiels` : 
- `list_all_officiels_async` : 
- `list_all_pratiques` : 
- `list_all_pratiques_async` : 
- `list_engagements_by_ids` : 
- `list_engagements_by_poule` : 
- `list_engagements_by_poules` : 
- `list_rencontres_by_poule` : 
- `list_rencontres_by_poules` : 
- `list_entraineurs_by_ids` : 

## Méthodes de Recherche Meilisearch (Exemples importants)
Le SDK expose également des méthodes de recherche optimisées avec facettes, géolocalisation et filtres via Meilisearch :
- `multi_search` : Perform multi-search across all resource types with input validation
- `multi_search_async` : Performs a smart multi-search asynchronously
- `search_competitions` : 
- `search_multiple_competitions` : 
- `search_competitions_async` : Search for competitions asynchronously
- `search_multiple_competitions_async` : Search for multiple competitions asynchronously
- `search_organismes` : 
- `search_organismes_by_geo` : 
- `search_organismes_by_city` : 
- `search_multiple_organismes` : 
- `search_organismes_async` : Search for organismes asynchronously
- `search_multiple_organismes_async` : Search for multiple organismes asynchronously
- `search_pratiques` : 
- `search_multiple_pratiques` : 
- `search_pratiques_async` : Search for pratiques asynchronously
- `search_multiple_pratiques_async` : Search for multiple pratiques asynchronously
- `search_rencontres` : 
- `search_multiple_rencontres` : 
- `search_rencontres_async` : Search for rencontres asynchronously
- `search_multiple_rencontres_async` : Search for multiple rencontres asynchronously
- `search_salles` : 
- `search_salles_by_geo` : 
- `search_multiple_salles` : 
- `search_salles_async` : Search for salles asynchronously
- `search_multiple_salles_async` : Search for multiple salles asynchronously
- `search_terrains` : 
- `search_multiple_terrains` : 
- `search_terrains_async` : Search for terrains asynchronously
- `search_multiple_terrains_async` : Search for multiple terrains asynchronously
- `search_tournois` : 
- `search_multiple_tournois` : 
- `search_tournois_async` : Search for tournois asynchronously
- `search_multiple_tournois_async` : Search for multiple tournois asynchronously
- `search_engagements` : 
- `search_engagements_by_geo` : 
- `search_engagements_filtered` : 
- `search_multiple_engagements` : 
- `search_engagements_async` : Search for engagements asynchronously
- `search_multiple_engagements_async` : Search for multiple engagements asynchronously
- `search_formations` : 
- `search_multiple_formations` : 
- `search_formations_async` : Search for formations asynchronously
- `search_multiple_formations_async` : Search for multiple formations asynchronously
- `search_news` : 
- `search_multiple_news` : 
- `search_youtube_videos` : 
- `search_multiple_youtube_videos` : 
- `search_rss` : 
- `search_multiple_rss` : 
- `search_galeries` : 
- `search_multiple_galeries` : 

## Variables d'environnement
Le SDK résout automatiquement les jetons de sécurité via les variables d'environnement suivantes ou interroge l'API publique en cache en cas d'absence :

| Variable | Défaut | Usage |
|----------|--------|-------|
| `API_FFBB_APP_BEARER_TOKEN` | — | Jeton Bearer de sécurité pour requêter directement l'API FFBB (api.ffbb.app) |
| `MEILISEARCH_BEARER_TOKEN` | — | Jeton Bearer de sécurité pour interroger le moteur Meilisearch (meilisearch-prod.ffbb.app) |

## Règles de comportement des agents
- **RTK OBLIGATOIRE** : Utilisez TOUJOURS le préfixe `rtk` pour toutes les commandes terminal exécutées sur la machine de l'utilisateur (ex: `rtk pytest`, `rtk tox`, etc.).
- **Tox & Pytest** : Privilégiez l'exécution des tests via `pytest` local ou `tox` pour valider les évolutions du SDK sur les différentes versions de Python prises en charge.
- **Modèles typés** : Respectez scrupuleusement la déclaration des types Pydantic de `ffbb_data_client.models`. Tout nouveau modèle ou modification de champ doit correspondre aux spécifications de l'API FFBB.
- **Réponses en français** : Communiquez et expliquez toujours vos changements ou vos analyses en langue française.

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
├── clients/               # Clients d'API (REST et Meilisearch) et façades (≈6261 lignes)
├── config.py              # Configuration centralisée (URLs, Headers, Endpoints, Facettes)
├── data/                  # Ressources et données statiques
├── helpers/               # Méthodes utilitaires pour requêtes HTTP et mapping (≈790 lignes)
├── models/                # Modèles de données Pydantic type-safe (≈9881 lignes)
├── py.typed               # Marqueur pour la compatibilité avec mypy
└── utils/                 # Gestionnaires transversaux (cache, jetons de sécurité, validation) (≈1840 lignes)
```

## Conventions de code
- **Modèles Pydantic** : Tous les modèles héritent de `pydantic.BaseModel` et fournissent une validation stricte.
- **Async/Sync en parallèle** : Le SDK implémente systématiquement la double interface synchrone (`get_x`) et asynchrone (`get_x_async`) pour un maximum de flexibilité d'intégration.
- **Cache HTTP** : Utilisation d'`hishel` pour le cache de requêtes HTTP asynchrones et d'un cache local configurable pour optimiser les appels et respecter les quotas FFBB.
- **Validation** : Les paramètres passés à `FFBBDataClient.create` sont strictement validés via les utilitaires de validation robustes de `utils/input_validation.py`.

## Commandes courantes
- Lancer les tests locaux : `rtk pytest`
- Lancer la suite d'intégration Tox : `rtk tox`
- Vérifier les types : `rtk mypy src`
- Formater et vérifier le style : `rtk ruff format . && rtk ruff check .`

## Push / Tag / Release Gate
⚠️ OBLIGATION STRICTE : Toutes ces commandes DOIVENT être préfixées par 'rtk' dans le terminal (ex: 'rtk pytest'). Ne jamais exécuter de commande nue sans 'rtk'.
Avant push/tag/release :
1. `rtk ruff format --check .`
2. `rtk ruff check .`
3. `rtk mypy src`
4. `rtk pytest`

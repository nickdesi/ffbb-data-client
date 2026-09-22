<div align="center">

<img src="https://raw.githubusercontent.com/nickdesi/ffbb-data-client/master/website/assets/logo.webp" alt="FFBB Data Client Logo" width="160" style="margin-bottom: 12px; border-radius: 20px; box-shadow: 0 8px 24px rgba(255, 107, 0, 0.25);" />

# 🏀 FFBB Data Client
### L'API Officielle du Basket Français en Python & Recherche Meilisearch

**Le SDK Python moderne, ultra-rapide, asynchrone et typé pour exploiter l'API de la Fédération Française de BasketBall (FFBB) : clubs, compétitions nationales & régionales, scores en direct (lives), classements, calendriers, gymnases/salles et détection de niveau.**

*Alternative officielle, haute performance et maintenue aux anciens packages obsolètes `ffbb-api-client` et `ffbb-api-client-v2`.*

<p align="center">
  <a href="https://pypi.org/project/ffbb-data-client/"><img src="https://img.shields.io/pypi/v/ffbb-data-client?color=ff6b00&label=PyPI%20Release&logo=python&logoColor=white&style=for-the-badge" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/ffbb-data-client/"><img src="https://img.shields.io/pypi/pyversions/ffbb-data-client?logo=python&logoColor=white&style=for-the-badge&color=238636" alt="Python versions" /></a>
  <a href="https://github.com/nickdesi/ffbb-data-client/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/nickdesi/ffbb-data-client/ci.yml?branch=master&label=CI%20Build&logo=github&style=for-the-badge" alt="CI Status" /></a>
  <a href="https://coveralls.io/github/nickdesi/ffbb-data-client?branch=master"><img src="https://img.shields.io/coveralls/github/nickdesi/ffbb-data-client/master?style=for-the-badge&logo=coveralls" alt="Coverage" /></a>
</p>

<p align="center">
  <a href="https://github.com/nickdesi/FFBB-MCP-Server"><img src="https://img.shields.io/badge/MCP-Ready-0969da.svg?logo=modelcontextprotocol&logoColor=white&style=flat-square" alt="MCP Ready" /></a>
  <a href="https://github.com/nickdesi/ffbb-data-client/blob/master/LICENSE.txt"><img src="https://img.shields.io/badge/License-Apache--2.0-blue.svg?style=flat-square" alt="License" /></a>
  <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/Code%20Style-Black-000000.svg?style=flat-square" alt="Code Style: Black" /></a>
  <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/badge/Fast%20Packaging-uv-de5fe9.svg?style=flat-square" alt="Packaged with uv" /></a>
  <a href="https://github.com/nickdesi/ffbb-data-client/stargazers"><img src="https://img.shields.io/github/stars/nickdesi/ffbb-data-client?style=flat-square&color=gold" alt="GitHub Stars" /></a>
  <a href="https://ffbb-api.desimone.fr/"><img src="https://img.shields.io/badge/Web-ffbb--api.desimone.fr-blue?style=flat-square&logo=googlechrome&logoColor=white" alt="API Website" /></a>
</p>

---

[⚡ Démarrage Rapide](#-démarrage-rapide-30-secondes) •
[📍 Recherche Géo & Clubs](#-recherche-géographique--clubs-de-france) •
[🔥 Cas d'Usage](#-recettes--cas-dusage-concrets) •
[🧵 Streaming Async](#-haute-performance--streaming-asynchrone) •
[🤖 Intégration IA / MCP](#-ia-agents--mcp-server) •
[🌐 API REST](#-serveur-rest-fastapi-embarqué) •
[📖 Documentation](https://nickdesi.github.io/ffbb-data-client/)

</div>

<!-- DISCOVERY_METRICS:START -->
> 🔄 **Cartographie API synchronisée** : `162` collections Directus OpenAPI cartographiées, `13` index Meilisearch surveillés.
<!-- DISCOVERY_METRICS:END -->

---

## 🏆 Pourquoi choisir `ffbb-data-client` ?

| Fonctionnalité | Ancien client (`ffbb-api-client`) | **`ffbb-data-client` (v2.4+)** |
| :--- | :---: | :---: |
| **Bypass WAF BunnyCDN** (anti-403) | ❌ Bloqué en 403 Forbidden | ✅ **Garanti (okhttp/4.12.0 emulated)** |
| **Architecture Asynchrone Native** | ❌ 100% bloquant / synchrone | ✅ **Async native (`async/await` + `aiter`)** |
| **Modèles de Données & Typage** | ❌ Dictionnaires bruts sans type | ✅ **Dataclasses & Pydantic v2 validés** |
| **Recherche Meilisearch Instantanée** | ❌ Partielle ou absente | ✅ **Multi-index (Clubs, Salles, Poules, 3x3)** |
| **Recherche Géographique par GPS** | ❌ Non disponible | ✅ **Rayon kilométrique autour de coordonnées** |
| **Streaming de Masse (Pagination auto)** | ❌ Manuelle, risque d'OOM | ✅ **Générateurs streaming `aiter_all_*`** |
| **Résolution d'Adresses de Salles** | ❌ Nom brut souvent vide | ✅ **Résolution physique complète (Gymnase, Rue, CP, Ville)** |
| **Compatibilité IA & Agents MCP** | ❌ Incompatible | ✅ **Connecteur natif Model Context Protocol** |
| **Couverture de Tests & Fiabilité** | ⚠️ < 30% | ✅ **680+ tests unitaires & 100% Zero-Red CI** |

---

## 📦 Installation

Installez la dernière version stable via `pip` ou `uv` :

```bash
# Via pip standard
pip install ffbb-data-client

# Via uv (recommandé pour la rapidité)
uv add ffbb-data-client
```

### Options supplémentaires

```bash
# Avec le serveur d'API REST FastAPI intégré
pip install "ffbb-data-client[server]"

# Pour le développement local et la suite de tests complète
pip install "ffbb-data-client[testing]"
```

*Prérequis : Python `>=3.10`.*

---

## ⚡ Démarrage Rapide (30 secondes)

Aucun compte développeur ni clé d'API compliquée : `FFBBDataClient.create()` résout et rafraîchit automatiquement les tokens publics nécessaires :

```python
from ffbb_data_client import FFBBDataClient

# Initialisation en une seule ligne (zéro configuration requise)
client = FFBBDataClient.create()

# 1. Rechercher un club de basket en France
clubs = client.search_organismes("Clermont", limit=3)
for club in clubs.hits:
    print(f"🏀 {club.nom} ({club.codePostal} {club.commune}) - ID: {club.id}")

# 2. Consulter les scores et matchs en direct (Lives FFBB)
lives = client.get_lives()
print(f"Matchs suivis en direct : {len(lives)}")

# 3. Explorer les rencontres d'une compétition (ex: Nationale 1 Masculine)
rencontres = client.search_rencontres("NM1", limit=5)
for m in rencontres.hits:
    print(f"📅 {m.date_rencontre} : {m.equipe1} vs {m.equipe2}")
```

---

## 📍 Recherche Géographique & Clubs de France

Idéal pour concevoir des applications mobiles, des cartes interactives ou des annuaires de basketball :

### 🌍 Trouver tous les clubs autour d'un point GPS

```python
# Exemple : Clubs dans un rayon de 20 km autour de Lyon / Clermont-Ferrand
clubs = client.search_organismes_by_geo(
    lat=45.7772,
    lng=3.0870,
    radius_km=20,
    limit=15,
)

for club in clubs.hits:
    print(f"📍 {club.nom} à {club.commune} [{club.geo}]")
```

### 🔍 Recherche ciblée par Code Postal, Ville ou Catégorie

```python
# Filtrer par département ou code postal
organismes = client.search_organismes(
    "Basket",
    filter=['codePostal = "63000"'],
    sort=["nom:asc"],
    limit=10,
)
```

---

## 🔥 Recettes & Cas d'Usage Concrets

<details>
<summary><b>1. Suivre les classements et résultats d'une poule</b></summary>

```python
from ffbb_data_client import FFBBDataClient

client = FFBBDataClient.create()

# Récupération complète d'une poule de championnat
poule = client.get_poule(11111)

print(f"Championnat : {poule.nom}")
for rk in poule.classement or []:
    print(f"#{rk.position} {rk.organisme_nom} - {rk.points} pts ({rk.victoires}V - {rk.defaites}D)")
```
</details>

<details>
<summary><b>2. Résoudre l'adresse complète et exacte d'un gymnase</b></summary>

```python
# Fini les adresses partielles : résolution déterministe certifiée FFBB
salles = client.search_salles("Maison des Sports", limit=3)
for salle in salles.hits:
    print(f"🏟️ {salle.nom} : {salle.adresse}, {salle.codePostal} {salle.ville}")
```
</details>

<details>
<summary><b>3. Détection automatique du niveau et de la catégorie (U13, R1, D2...)</b></summary>

```python
from ffbb_data_client import NiveauExtractor, NiveauType

# Détection intelligente du niveau hiérarchique
niveau = NiveauExtractor.extract_niveau("RÉGIONALE MASCULINE SENIORS - DIVISION 2")
print(niveau.type)       # NiveauType.REGIONAL
print(niveau.division)   # 2
```
</details>

<details>
<summary><b>4. Extraire les contacts d'un club (Président, Correspondant, Email)</b></summary>

```python
# Contacts administratifs officiels
contacts = client.get_club_contacts(organisme_id=9326)
if contacts:
    print(f"Club : {contacts.club_contact.nom}")
    print(f"Email : {contacts.club_contact.email}")
    for membre in contacts.membres:
        print(f" - {membre.role} : {membre.prenom} {membre.nom} ({membre.email})")
```
</details>

---

## 🧵 Haute Performance & Streaming Asynchrone

Pour traiter de gros volumes de données sans saturer la mémoire vive ni bloquer la boucle d'événements :

```python
import asyncio
from ffbb_data_client import FFBBDataClient

async def main():
    client = FFBBDataClient.create()

    # Streaming asynchrone mémoire-constant (aiter)
    count = 0
    async for rencontre in client.aiter_all_rencontres(page_size=100, max_items=500):
        count += 1
        if count % 100 == 0:
            print(f"Traitement du match #{count} : {rencontre.id}")

    # Recherche asynchrone non-bloquante
    results = await client.search_organismes_async("ASVEL")
    print(f"Résultats trouvés : {results.estimated_total_hits}")

asyncio.run(main())
```

---

## 🤖 IA, Agents & MCP Server

Le SDK `ffbb-data-client` est le moteur officiel du serveur **Model Context Protocol (MCP)** pour le basket français.

Il permet aux LLMs (**Claude**, **ChatGPT**, **Cursor**, **Gemini**, **Antigravity**) d'interagir nativement avec les championnats de basket :

* 💬 *"Quels sont les prochains matchs du SCBA ce week-end ?"*
* 💬 *"Donne-moi le classement de la Poule Haute U13M2."*
* 💬 *"Quelle est l'adresse exacte de la salle pour le match de samedi ?"*

👉 Découvrez le projet dédié : **[FFBB-MCP-Server](https://github.com/nickdesi/FFBB-MCP-Server)**

---

## 🌐 Serveur REST FastAPI Embarqué

Besoin d'une API web pour votre application React, Vue, Next.js ou mobile ? `ffbb-data-client` intègre une API FastAPI prête à l'emploi :

```bash
# Démarrer le serveur API local
uvicorn ffbb_data_client.api:app --host 0.0.0.0 --port 8000 --reload
```

Accédez ensuite à la documentation Swagger interactive sur `http://localhost:8000/docs` !

*Endpoints phares :*
- `GET /health` : Statut de santé et horodatage UTC.
- `GET /api/v1/club/{id}/matches` : Calendrier optimisé du club avec adresses de salles résolues.
- `GET /api/v1/lives` : Matchs en direct agrégés.

---

## 📚 Référence des Méthodes (Sync & Async)

> 💡 **Pattern standard** : Toutes les méthodes existent en version synchrone (`nom()`) et asynchrone (`nom_async()`).

| Domaine | Méthodes (Sync & Async) | Description |
| :--- | :--- | :--- |
| **🌐 Multi-Search** | `multi_search()`<br>`multi_search_async()` | Recherche globale simultanée sur tous les index Meilisearch |
| **🏀 Clubs & Organismes** | `search_organismes()`<br>`search_organismes_async()` | Recherche par nom, commune, département ou code postal |
| **📍 Géo-Localisation** | `search_organismes_by_geo()`<br>`search_organismes_by_geo_async()` | Recherche de clubs par rayon GPS (lat/lng, km) |
| **👤 Contacts Club** | `get_club_contacts()`<br>`get_club_contacts_async()` | Fiche contacts officielle (président, correspondants, emails) |
| **📅 Rencontres & Matchs** | `search_rencontres()`<br>`search_rencontres_async()` | Calendriers, résultats de matchs et scores |
| **⚡ Streaming Continu** | `aiter_all_rencontres()` | Générateur asynchrone paginé en streaming (`aiter`) |
| **🏟️ Salles & Gymnases** | `search_salles()`<br>`search_salles_async()` | Adresses physiques complètes, gymnases et coordonnées |
| **🏆 Compétitions** | `search_competitions()`<br>`search_competitions_async()` | Championnats nationaux (NM1, LF2...), régionaux, départ. |
| **📊 Poules & Classement** | `get_poule()`<br>`get_poule_async()` | Classement officiel complet (V/D, pts) et matchs de poule |
| **⚡ Scores en Direct** | `get_lives()`<br>`get_lives_async()` | Flux officiel des scores en temps réel (Lives FFBB) |
| **🎯 Tournois 3x3** | `search_tournois()`<br>`search_tournois_async()` | Tournois officiels homologués 3x3 FFBB |

---

## 🛠️ Robustesse, CI/CD & Découverte Quotidienne

* **Protection BunnyCDN** : User-Agent garanti `okhttp/4.12.0` pour éviter tout blocage WAF 403.
* **Découverte Quotidienne du Schéma** : Un cron GitHub Actions analyse chaque matin à 5h17 UTC l'OpenAPI spec officielle de la FFBB et détecte automatiquement tout nouveau champ ou collection Directus.
* **Cache Intelligent Sécurisé** : Gestionnaire de cache HTTP `hishel` avec SQLite distinct pour les flux synchrones et asynchrones.
* **CodeQL & Zéro Dette** : Conformité aux normes de sécurité, zéro alerte d'injection de log, 100% typé.

---

## 🤝 Contribuer

Les contributions, signalements de bugs et suggestions sont les bienvenus !

1. **Forkez** le projet.
2. Créez une branche (`git checkout -b feat/ma-nouvelle-fonctionnalite`).
3. Installez l'environnement de développement : `pip install -e ".[testing]"`.
4. Vérifiez que tous les tests passent : `pytest tests/` et `pre-commit run --all-files`.
5. Ouvrez une **Pull Request** claire et documentée.

---

## 📄 Licence

Distribué sous la licence **Apache-2.0**. Voir [`LICENSE.txt`](LICENSE.txt) pour plus de détails.

---

<div align="center">

**Développé avec passion pour la communauté du basketball français. 🇫🇷🏀**

Si cette bibliothèque vous est utile, n'hésitez pas à **ajouter une étoile ⭐** sur GitHub pour encourager le projet !

[![GitHub stars](https://img.shields.io/github/stars/nickdesi/ffbb-data-client?style=social)](https://github.com/nickdesi/ffbb-data-client/stargazers)

</div>

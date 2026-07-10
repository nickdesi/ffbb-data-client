# Politique de sécurité

## Versions supportées

Les correctifs de sécurité ciblent la **dernière version publiée sur PyPI** et la branche `master` courante.

| Version | Supportée |
| --- | --- |
| Dernière release (PyPI) | ✅ |
| `master` | ✅ |
| Versions antérieures | ❌ |

## Signaler une vulnérabilité

**Ne publiez jamais** une vulnérabilité dans une issue ou une pull request publique.

Méthode recommandée : utilisez **GitHub Security Advisories / Private Vulnerability Reporting** (onglet *Security → Report a vulnerability* du dépôt) si disponible.

À défaut, contactez le mainteneur via les coordonnées indiquées dans `setup.cfg` en incluant :

- une description claire du problème ;
- les versions ou commits concernés ;
- les étapes minimales de reproduction ;
- l'impact potentiel ;
- toute mitigation connue.

N'attendez pas de divulguer publiquement tant qu'un correctif ou une mitigation n'a pas été publié.

## Périmètre

**Données sensibles** : n'incluez jamais de tokens bearer FFBB, de tokens Meilisearch, de logs contenant des identifiants, ou des données personnelles dans vos rapports. Si ces données sont nécessaires à la reproduction, **anonymisez-les** au préalable.

Sont principalement dans le périmètre :

- exécution de code non attendue ;
- fuite de secrets ou de données sensibles (tokens, logs) ;
- vulnérabilités liées au client HTTP / cache (`hishel`, `httpx`) ;
- contournement de limites de sécurité documentées ;
- dépendances vulnérables impactant l'exécution du client.

Hors périmètre sauf impact démontré :

- indisponibilité ou erreurs provenant directement de l'API FFBB amont ;
- scraping agressif ou abus des services tiers ;
- problèmes nécessitant déjà un accès administrateur à l'hôte.

## Bonnes pratiques d'utilisation sûre

- Stockez les tokens (`api_bearer_token`, `meilisearch_bearer_token`) dans des variables d'environnement ou un gestionnaire de secrets, jamais en clair dans le code.
- Ne committez jamais de `.env` ou de fichier de credentials (voir `.gitignore`).
- Le client masque les tokens dans les logs ; ne désactivez pas ce comportement en production.
- Évitez d'exposer le cache SQLite (`hishel`) contenant d'éventuelles réponses sur un stockage partagé.
- Tenez les dépendances à jour (`pip install -U ffbb-data-client`, Dependabot actif).

## 📝 Description

Fournissez une description claire des modifications proposées dans cette Pull Request et de leurs motivations.

> Résout : # (indiquez l'issue associée ici, ex: #123)

---

## 🛠️ Type de changement

Veuillez cocher l'option qui s'applique à votre Pull Request :

- [ ] 🐛 Correction de bug (changement non bloquant qui résout un dysfonctionnement)
- [ ] ✨ Nouvelle fonctionnalité (changement non bloquant qui ajoute une fonctionnalité)
- [ ] 💥 Changement majeur / breaking change (correction ou fonctionnalité qui modifie le comportement existant)
- [ ] ⚙️ Refactoring / Amélioration de code (optimisation du code sans changement de fonctionnalité)
- [ ] 📖 Documentation (modification ou ajout à la documentation ou aux commentaires de code)
- [ ] 🚨 Tests (ajout ou mise à jour de la couverture de tests)

---

## 🔍 Comment cela a-t-il été testé ?

Veuillez détailler les tests effectués pour valider vos modifications (ex: tests unitaires ajoutés, tests d'intégration, ou vérification manuelle).

*Exemple :*
- [ ] Test unitaire `tests/unit/clients/test_xyz.py` exécuté et validé.
- [ ] Validation complète de la suite via Tox.

---

## ✅ Checklist de validation

Avant de soumettre cette Pull Request, veuillez vérifier et cocher les points suivants :

- [ ] Mon code respecte le style et les règles de conception décrits dans les directives du projet.
- [ ] J'ai documenté les nouvelles fonctionnalités ou modifications dans le code (docstrings, typage Pydantic).
- [ ] J'ai ajouté des tests couvrant mes modifications.
- [ ] Tous les tests existants et nouveaux passent avec succès (`rtk pytest`).
- [ ] J'ai exécuté le formatage et le linter localement (`rtk ruff format . && rtk ruff check .`).
- [ ] J'ai vérifié la conformité des types statiques avec `rtk mypy src`.
- [ ] La validation `rtk pre-commit run --all-files` s'exécute localement sans aucune erreur.
- [ ] Je n'ai pas modifié manuellement le fichier `AGENTS.md` (qui est géré de manière autonome par les scripts).

> ⚠️ **Rappel crucial** : Toutes les commandes exécutées localement dans votre terminal doivent obligatoirement être préfixées par **`rtk`** (ex: `rtk pytest`, `rtk tox`, etc.).

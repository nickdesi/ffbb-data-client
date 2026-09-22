.. _data_dictionary:

========================================
Dictionnaire de Données & Cartographie
========================================

Ce document présente la cartographie des index de recherche Meilisearch et des collections Directus
ainsi que la définition des champs et attributs de l'écosystème FFBB.

.. note::

    Ce fichier est synchronisé automatiquement par ``scripts/discover_endpoints.py`` lors des phases de découverte.

Index Meilisearch Surveillés
============================

Index ``ffbbnational_galeries``
-------------------------------

- **Nombre d'enregistrements estimés** : ``98``

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Attribut
     - Catégorie
     - Description & Usage
   * - ``count``
     - ``statistique``
     - Nombre total d'éléments (photos, items, participants) associés.
   * - ``cover``
     - ``media``
     - URL ou identifiant de l'image de couverture / affiche.
   * - ``creator``
     - ``metadonnees``
     - Auteur ou créateur de la ressource dans le CMS Directus FFBB.
   * - ``date``
     - ``temporel``
     - Date de l'événement, de la rencontre ou de la publication.
   * - ``date_created``
     - ``metadonnees``
     - Date de création initiale de l'enregistrement dans la base Directus.
   * - ``date_published``
     - ``temporel``
     - Date de mise en ligne ou publication publique de l'article/contenu.
   * - ``date_timestamp``
     - ``temporel``
     - Timestamp Unix de la date principale pour tri numérique rapide.
   * - ``date_updated``
     - ``metadonnees``
     - Date de dernière mise à jour de l'enregistrement dans la base Directus.
   * - ``id``
     - ``identification``
     - Identifiant numérique unique de la ressource dans le système Directus FFBB.
   * - ``images``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``surtitle``
     - ``contenu``
     - Surtitre ou chapeau introductif de l'article ou de la galerie.
   * - ``tags``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``thumbnail``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``title``
     - ``contenu``
     - Titre officiel du contenu, événement ou entité.
   * - ``type``
     - ``statut``
     - Typologie administrative de l'organisme (Club, Comité départemental, Ligue régionale, Groupement, etc.).

Index ``ffbbnational_pratiques``
--------------------------------

- **Nombre d'enregistrements estimés** : ``515``

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Attribut
     - Catégorie
     - Description & Usage
   * - ``_geo``
     - ``geographie``
     - Coordonnées géographiques de localisation (latitude, longitude) au format standard Meilisearch.
   * - ``action``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``adresse``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``adresse_salle``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``adresse_structure``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``affiche``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``assurance``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``cartographie``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``code``
     - ``identification``
     - Code fédéral unique attribué par la FFBB (ex: ARA0063062 pour un club, 063 pour un comité).
   * - ``code_structure``
     - ``identification``
     - Code identifiant de la structure organisatrice ou hôte.
   * - ``cp_salle``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``date_created``
     - ``metadonnees``
     - Date de création initiale de l'enregistrement dans la base Directus.
   * - ``date_debut``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``date_debut_timestamp``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``date_demande``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``date_fin``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``date_fin_timestamp``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``date_inscription``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``date_updated``
     - ``metadonnees``
     - Date de dernière mise à jour de l'enregistrement dans la base Directus.
   * - ``date_validation_ffbb``
     - ``statut``
     - Date à laquelle la FFBB a formellement validé l'élément ou l'offre de pratique.
   * - ``date_validation_ffbb_timestamp``
     - ``statut``
     - Timestamp Unix de la date de validation FFBB.
   * - ``description``
     - ``contenu``
     - Texte descriptif détaillé de la ressource.
   * - ``email``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``engagement``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``facebook``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``horaires_seances``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``id``
     - ``identification``
     - Identifiant numérique unique de la ressource dans le système Directus FFBB.
   * - ``inscriptions``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``jours``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``label``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``latitude``
     - ``geographie``
     - Coordonnée de latitude géographique.
   * - ``longitude``
     - ``geographie``
     - Coordonnée de longitude géographique.
   * - ``mail_demandeur``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``mail_structure``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nom_demandeur``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nom_salle``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nom_structure``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nombre_personnes``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nombre_seances``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``objectif``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``prenom_demandeur``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``public``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``site_web``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``telephone``
     - ``contact``
     - Numéro de téléphone de contact officiel de l'organisme.
   * - ``thumbnail``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``titre``
     - ``contenu``
     - Titre du contenu ou de l'actualité en français.
   * - ``twitter``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``type``
     - ``statut``
     - Typologie administrative de l'organisme (Club, Comité départemental, Ligue régionale, Groupement, etc.).
   * - ``ville_salle``
     - ``général``
     - Attribut exposé dans l'index.

Index ``ffbbnational_rss``
--------------------------

- **Nombre d'enregistrements estimés** : ``4296``

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Attribut
     - Catégorie
     - Description & Usage
   * - ``categories``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``chapo``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``cover``
     - ``media``
     - URL ou identifiant de l'image de couverture / affiche.
   * - ``creator``
     - ``metadonnees``
     - Auteur ou créateur de la ressource dans le CMS Directus FFBB.
   * - ``date``
     - ``temporel``
     - Date de l'événement, de la rencontre ou de la publication.
   * - ``date_created``
     - ``metadonnees``
     - Date de création initiale de l'enregistrement dans la base Directus.
   * - ``date_timestamp``
     - ``temporel``
     - Timestamp Unix de la date principale pour tri numérique rapide.
   * - ``date_updated``
     - ``metadonnees``
     - Date de dernière mise à jour de l'enregistrement dans la base Directus.
   * - ``highlight``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``id``
     - ``identification``
     - Identifiant numérique unique de la ressource dans le système Directus FFBB.
   * - ``img``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``img_credits``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``img_legend``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``link``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``match_id``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``surtitle``
     - ``contenu``
     - Surtitre ou chapeau introductif de l'article ou de la galerie.
   * - ``tags``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``text``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``texte``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``thumbnail``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``title``
     - ``contenu``
     - Titre officiel du contenu, événement ou entité.
   * - ``type``
     - ``statut``
     - Typologie administrative de l'organisme (Club, Comité départemental, Ligue régionale, Groupement, etc.).

Index ``ffbbserver_competitions``
---------------------------------

- **Nombre d'enregistrements estimés** : ``2442``

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Attribut
     - Catégorie
     - Description & Usage
   * - ``age``
     - ``sportif``
     - Tranche d'âge de la compétition (Seniors, U20, U18, U15, U13, etc.).
   * - ``categorie``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``code``
     - ``identification``
     - Code fédéral unique attribué par la FFBB (ex: ARA0063062 pour un club, 063 pour un comité).
   * - ``codeComite``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``codeLigue``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``compare_old_site``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``competition_origine``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``competition_origine_niveau``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``competition_origine_nom``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``creationEnCours``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``date_created``
     - ``metadonnees``
     - Date de création initiale de l'enregistrement dans la base Directus.
   * - ``date_updated``
     - ``metadonnees``
     - Date de dernière mise à jour de l'enregistrement dans la base Directus.
   * - ``emarqueV2``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``etat``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``id``
     - ``identification``
     - Identifiant numérique unique de la ressource dans le système Directus FFBB.
   * - ``idCompetitionPere``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``liveStat``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``logo``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``niveau``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``niveau_nb``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nom``
     - ``identification``
     - Nom officiel de l'entité (organisme, compétition, salle, officiel, terrain).
   * - ``ordre``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``organisateur``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``participants``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``phase_code``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``phases``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``poules``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``pro``
     - ``sportif``
     - Indicateur booléen signalant si la rencontre ou la compétition concerne le secteur professionnel (LNB, LFB, etc.).
   * - ``publicationInternet``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``saison``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``sexe``
     - ``sportif``
     - Genre de la compétition ou de l'équipe (Masculin, Féminin, Mixte).
   * - ``slug``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``thumbnail``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``toUpdate``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``typeCompetition``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``typeCompetitionGenerique``
     - ``sportif``
     - Niveau générique de compétition (Championnat de France, Régional, Départemental, Coupe, Tournoi).

Index ``ffbbserver_engagements``
--------------------------------

- **Nombre d'enregistrements estimés** : ``5000``

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Attribut
     - Catégorie
     - Description & Usage
   * - ``_geo``
     - ``geographie``
     - Coordonnées géographiques de localisation (latitude, longitude) au format standard Meilisearch.
   * - ``age``
     - ``sportif``
     - Tranche d'âge de la compétition (Seniors, U20, U18, U15, U13, etc.).
   * - ``categorie``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``clubPro``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``codeAbrege``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``codeClub``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``codeComite``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``codeLigue``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``competitionsUrl``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``gradient_color``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``id``
     - ``identification``
     - Identifiant numérique unique de la ressource dans le système Directus FFBB.
   * - ``idCompetition``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``idPoule``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``logo``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``niveau``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nom``
     - ``identification``
     - Nom officiel de l'entité (organisme, compétition, salle, officiel, terrain).
   * - ``nomClub``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nomClubPro``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nomComite``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nomCtc``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nomEquipe``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nomLigue``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nomOfficiel``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nomOrganisme``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nomUsuel``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``numeroEquipe``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``sexe``
     - ``sportif``
     - Genre de la compétition ou de l'équipe (Masculin, Féminin, Mixte).
   * - ``thumbnail``
     - ``général``
     - Attribut exposé dans l'index.

Index ``ffbbserver_formations``
-------------------------------

- **Nombre d'enregistrements estimés** : ``144``

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Attribut
     - Catégorie
     - Description & Usage
   * - ``certification``
     - ``formation``
     - Type de diplôme ou brevet délivré par une session de formation (ex: CQP, Brevet Fédéral).
   * - ``content``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``description``
     - ``contenu``
     - Texte descriptif détaillé de la ressource.
   * - ``domain``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``duration_hours``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``files``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``goals``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``id``
     - ``identification``
     - Identifiant numérique unique de la ressource dans le système Directus FFBB.
   * - ``id_origin_hash``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``image``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``level``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``modalities``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``mode``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``mode_hidden``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``pedagogy``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``places``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``postal_codes``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``prerequisites``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``programIdFbi``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``public``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``reference``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``results``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``sessions``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``theme``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``thumbnail``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``title``
     - ``contenu``
     - Titre officiel du contenu, événement ou entité.
   * - ``type``
     - ``statut``
     - Typologie administrative de l'organisme (Club, Comité départemental, Ligue régionale, Groupement, etc.).

Index ``ffbbserver_organismes``
-------------------------------

- **Nombre d'enregistrements estimés** : ``5000``

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Attribut
     - Catégorie
     - Description & Usage
   * - ``_geo``
     - ``geographie``
     - Coordonnées géographiques de localisation (latitude, longitude) au format standard Meilisearch.
   * - ``adresse``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``adresseClubPro``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``cartographie``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``code``
     - ``identification``
     - Code fédéral unique attribué par la FFBB (ex: ARA0063062 pour un club, 063 pour un comité).
   * - ``code_emploi``
     - ``statut``
     - Code de conventionnement ou statut employeur/PSF de l'organisme auprès de la FFBB (suivi des postes aidés ANS/PSF et structuration salariée).
   * - ``commune``
     - ``geographie``
     - Nom de la commune de rattachement ou de localisation.
   * - ``communeClubPro``
     - ``geographie``
     - Commune de rattachement de la section professionnelle d'un club.
   * - ``dateAffiliation``
     - ``statut``
     - Date d'affiliation officielle de l'organisme auprès de la fédération.
   * - ``engagements_codes``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``engagements_noms``
     - ``sportif``
     - Noms textuels des équipes engagées par le club dans les championnats.
   * - ``id``
     - ``identification``
     - Identifiant numérique unique de la ressource dans le système Directus FFBB.
   * - ``labellisation``
     - ``sportif``
     - Labels fédéraux obtenus par le club (École Française de MiniBasket, Club Formateur, Basket Santé, Citoyen, etc.).
   * - ``logo``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``mail``
     - ``contact``
     - Adresse email de contact officiel de l'organisme ou du correspondant.
   * - ``nom``
     - ``identification``
     - Nom officiel de l'entité (organisme, compétition, salle, officiel, terrain).
   * - ``nomClubPro``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nom_simple``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``offresPratiques``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``organisme_id_pere``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``saison``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``saison_en_cours``
     - ``statut``
     - Indicateur booléen signalant si l'organisme est actif sur la saison sportive courante.
   * - ``telephone``
     - ``contact``
     - Numéro de téléphone de contact officiel de l'organisme.
   * - ``thumbnail``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``type``
     - ``statut``
     - Typologie administrative de l'organisme (Club, Comité départemental, Ligue régionale, Groupement, etc.).
   * - ``type_association``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``urlSiteWeb``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``url_competition``
     - ``général``
     - Attribut exposé dans l'index.

Index ``ffbbserver_rencontres``
-------------------------------

- **Nombre d'enregistrements estimés** : ``5000``

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Attribut
     - Catégorie
     - Description & Usage
   * - ``_geo``
     - ``geographie``
     - Coordonnées géographiques de localisation (latitude, longitude) au format standard Meilisearch.
   * - ``competitionId``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``creation_timestamp``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``date``
     - ``temporel``
     - Date de l'événement, de la rencontre ou de la publication.
   * - ``dateSaisieResultat_timestamp``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``date_rencontre``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``date_rencontre_timestamp``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``date_timestamp``
     - ``temporel``
     - Timestamp Unix de la date principale pour tri numérique rapide.
   * - ``gsId``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``handicap1``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``handicap2``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``id``
     - ``identification``
     - Identifiant numérique unique de la ressource dans le système Directus FFBB.
   * - ``idEngagementEquipe1``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``idEngagementEquipe2``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``idOrganismeEquipe1``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``idOrganismeEquipe2``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``idPoule``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``joue``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``modification_timestamp``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``niveau``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``niveau_nb``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nomEquipe1``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nomEquipe2``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``numeroJournee``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``officiels``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``officiels_string``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``organisateur``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``pratique``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``rematch_videos``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``resultatEquipe1``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``resultatEquipe2``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``saison``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``salle``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``thumbnail``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``uniqueKey``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``url_competition``
     - ``général``
     - Attribut exposé dans l'index.

Index ``ffbbserver_salles``
---------------------------

- **Nombre d'enregistrements estimés** : ``5000``

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Attribut
     - Catégorie
     - Description & Usage
   * - ``_geo``
     - ``geographie``
     - Coordonnées géographiques de localisation (latitude, longitude) au format standard Meilisearch.
   * - ``adresse``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``adresseComplement``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``capaciteSpectateur``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``cartographie``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``commune``
     - ``geographie``
     - Nom de la commune de rattachement ou de localisation.
   * - ``date_created``
     - ``metadonnees``
     - Date de création initiale de l'enregistrement dans la base Directus.
   * - ``date_updated``
     - ``metadonnees``
     - Date de dernière mise à jour de l'enregistrement dans la base Directus.
   * - ``id``
     - ``identification``
     - Identifiant numérique unique de la ressource dans le système Directus FFBB.
   * - ``libelle``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``libelle2``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``mail``
     - ``contact``
     - Adresse email de contact officiel de l'organisme ou du correspondant.
   * - ``numero``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``telephone``
     - ``contact``
     - Numéro de téléphone de contact officiel de l'organisme.
   * - ``thumbnail``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``type``
     - ``statut``
     - Typologie administrative de l'organisme (Club, Comité départemental, Ligue régionale, Groupement, etc.).
   * - ``type_association``
     - ``général``
     - Attribut exposé dans l'index.

Index ``ffbbserver_terrains``
-----------------------------

- **Nombre d'enregistrements estimés** : ``5000``

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Attribut
     - Catégorie
     - Description & Usage
   * - ``_geo``
     - ``geographie``
     - Coordonnées géographiques de localisation (latitude, longitude) au format standard Meilisearch.
   * - ``accesLibre``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``cartographie``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``commune``
     - ``geographie``
     - Nom de la commune de rattachement ou de localisation.
   * - ``date_created``
     - ``metadonnees``
     - Date de création initiale de l'enregistrement dans la base Directus.
   * - ``date_updated``
     - ``metadonnees``
     - Date de dernière mise à jour de l'enregistrement dans la base Directus.
   * - ``id``
     - ``identification``
     - Identifiant numérique unique de la ressource dans le système Directus FFBB.
   * - ``largeur``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``longueur``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``natureSol``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nom``
     - ``identification``
     - Nom officiel de l'entité (organisme, compétition, salle, officiel, terrain).
   * - ``numero``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``rue``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``thumbnail``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``type``
     - ``statut``
     - Typologie administrative de l'organisme (Club, Comité départemental, Ligue régionale, Groupement, etc.).

Index ``ffbbserver_tournois``
-----------------------------

- **Nombre d'enregistrements estimés** : ``3``

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Attribut
     - Catégorie
     - Description & Usage
   * - ``_geo``
     - ``geographie``
     - Coordonnées géographiques de localisation (latitude, longitude) au format standard Meilisearch.
   * - ``adresse``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``adresseComplement``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``ageMax``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``ageMin``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``cartographie``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``categorieChampionnat3x3Id``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``categorieChampionnat3x3Libelle``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``code``
     - ``identification``
     - Code fédéral unique attribué par la FFBB (ex: ARA0063062 pour un club, 063 pour un comité).
   * - ``commune``
     - ``geographie``
     - Nom de la commune de rattachement ou de localisation.
   * - ``date_created``
     - ``metadonnees``
     - Date de création initiale de l'enregistrement dans la base Directus.
   * - ``date_updated``
     - ``metadonnees``
     - Date de dernière mise à jour de l'enregistrement dans la base Directus.
   * - ``debut``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``debut_timestamp``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``description``
     - ``contenu``
     - Texte descriptif détaillé de la ressource.
   * - ``document_flyer``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``fin``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``fin_timestamp``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``id``
     - ``identification``
     - Identifiant numérique unique de la ressource dans le système Directus FFBB.
   * - ``mailOrganisateur``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nbParticipantPrevu``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``nom``
     - ``identification``
     - Nom officiel de l'entité (organisme, compétition, salle, officiel, terrain).
   * - ``nomOrganisateur``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``sexe``
     - ``sportif``
     - Genre de la compétition ou de l'équipe (Masculin, Féminin, Mixte).
   * - ``siteChoisi``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``tarifOrganisateur``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``telephoneOrganisateur``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``thumbnail``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``tournoiType``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``tournoiTypes3x3``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``urlOrganisateur``
     - ``général``
     - Attribut exposé dans l'index.

Index ``ffbbsite_news``
-----------------------

- **Nombre d'enregistrements estimés** : ``6301``

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Attribut
     - Catégorie
     - Description & Usage
   * - ``author``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``categories``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``category``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``category_2``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``content``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``date_published``
     - ``temporel``
     - Date de mise en ligne ou publication publique de l'article/contenu.
   * - ``featured``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``featured_mobile``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``filters_3x3``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``headline``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``id``
     - ``identification``
     - Identifiant numérique unique de la ressource dans le système Directus FFBB.
   * - ``image``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``link``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``match_id``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``permalink``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``push_newsletter``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``surtitle``
     - ``contenu``
     - Surtitre ou chapeau introductif de l'article ou de la galerie.
   * - ``tags``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``thumbnail``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``title``
     - ``contenu``
     - Titre officiel du contenu, événement ou entité.
   * - ``type``
     - ``statut``
     - Typologie administrative de l'organisme (Club, Comité départemental, Ligue régionale, Groupement, etc.).

Index ``youtube_videos``
------------------------

- **Nombre d'enregistrements estimés** : ``1863``

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Attribut
     - Catégorie
     - Description & Usage
   * - ``channelId``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``channelTitle``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``commentCount``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``date``
     - ``temporel``
     - Date de l'événement, de la rencontre ou de la publication.
   * - ``date_created``
     - ``metadonnees``
     - Date de création initiale de l'enregistrement dans la base Directus.
   * - ``date_published``
     - ``temporel``
     - Date de mise en ligne ou publication publique de l'article/contenu.
   * - ``date_updated``
     - ``metadonnees``
     - Date de dernière mise à jour de l'enregistrement dans la base Directus.
   * - ``description``
     - ``contenu``
     - Texte descriptif détaillé de la ressource.
   * - ``display_image``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``duration``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``duration_seconds``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``id``
     - ``identification``
     - Identifiant numérique unique de la ressource dans le système Directus FFBB.
   * - ``likeCount``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``snippet``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``tags``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``thumbnail``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``thumbnailDefaultUrl``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``thumbnailHighUrl``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``thumbnailMaxresUrl``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``thumbnailMediumUrl``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``thumbnailStandardUrl``
     - ``général``
     - Attribut exposé dans l'index.
   * - ``title``
     - ``contenu``
     - Titre officiel du contenu, événement ou entité.
   * - ``type``
     - ``statut``
     - Typologie administrative de l'organisme (Club, Comité départemental, Ligue régionale, Groupement, etc.).
   * - ``viewCount``
     - ``général``
     - Attribut exposé dans l'index.

Champs & Attributs de Référence
===============================

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Champ
     - Catégorie
     - Description & Rôle Métier
   * - ``_geo``
     - ``geographie``
     - Coordonnées géographiques de localisation (latitude, longitude) au format standard Meilisearch.
   * - ``age``
     - ``sportif``
     - Tranche d'âge de la compétition (Seniors, U20, U18, U15, U13, etc.).
   * - ``capacite``
     - ``infrastructure``
     - Capacité d'accueil en nombre de places assises / spectateurs de la salle ou tribune.
   * - ``certification``
     - ``formation``
     - Type de diplôme ou brevet délivré par une session de formation (ex: CQP, Brevet Fédéral).
   * - ``code``
     - ``identification``
     - Code fédéral unique attribué par la FFBB (ex: ARA0063062 pour un club, 063 pour un comité).
   * - ``code_emploi``
     - ``statut``
     - Code de conventionnement ou statut employeur/PSF de l'organisme auprès de la FFBB (suivi des postes aidés ANS/PSF et structuration salariée).
   * - ``code_postal``
     - ``geographie``
     - Code postal de localisation.
   * - ``code_structure``
     - ``identification``
     - Code identifiant de la structure organisatrice ou hôte.
   * - ``commune``
     - ``geographie``
     - Nom de la commune de rattachement ou de localisation.
   * - ``communeClubPro``
     - ``geographie``
     - Commune de rattachement de la section professionnelle d'un club.
   * - ``count``
     - ``statistique``
     - Nombre total d'éléments (photos, items, participants) associés.
   * - ``cover``
     - ``media``
     - URL ou identifiant de l'image de couverture / affiche.
   * - ``creator``
     - ``metadonnees``
     - Auteur ou créateur de la ressource dans le CMS Directus FFBB.
   * - ``date``
     - ``temporel``
     - Date de l'événement, de la rencontre ou de la publication.
   * - ``dateAffiliation``
     - ``statut``
     - Date d'affiliation officielle de l'organisme auprès de la fédération.
   * - ``date_affiliation``
     - ``statut``
     - Date d'affiliation officielle de l'organisme auprès de la fédération (format snake_case).
   * - ``date_created``
     - ``metadonnees``
     - Date de création initiale de l'enregistrement dans la base Directus.
   * - ``date_published``
     - ``temporel``
     - Date de mise en ligne ou publication publique de l'article/contenu.
   * - ``date_timestamp``
     - ``temporel``
     - Timestamp Unix de la date principale pour tri numérique rapide.
   * - ``date_updated``
     - ``metadonnees``
     - Date de dernière mise à jour de l'enregistrement dans la base Directus.
   * - ``date_validation_ffbb``
     - ``statut``
     - Date à laquelle la FFBB a formellement validé l'élément ou l'offre de pratique.
   * - ``date_validation_ffbb_timestamp``
     - ``statut``
     - Timestamp Unix de la date de validation FFBB.
   * - ``description``
     - ``contenu``
     - Texte descriptif détaillé de la ressource.
   * - ``engagements_noms``
     - ``sportif``
     - Noms textuels des équipes engagées par le club dans les championnats.
   * - ``horaire``
     - ``temporel``
     - Heure programmée de la rencontre (format HH:MM).
   * - ``id``
     - ``identification``
     - Identifiant numérique unique de la ressource dans le système Directus FFBB.
   * - ``labellisation``
     - ``sportif``
     - Labels fédéraux obtenus par le club (École Française de MiniBasket, Club Formateur, Basket Santé, Citoyen, etc.).
   * - ``latitude``
     - ``geographie``
     - Coordonnée de latitude géographique.
   * - ``longitude``
     - ``geographie``
     - Coordonnée de longitude géographique.
   * - ``mail``
     - ``contact``
     - Adresse email de contact officiel de l'organisme ou du correspondant.
   * - ``nom``
     - ``identification``
     - Nom officiel de l'entité (organisme, compétition, salle, officiel, terrain).
   * - ``nom_club_pro``
     - ``identification``
     - Dénomination officielle de la structure professionnelle (SASP / SAOS) rattachée à l'association.
   * - ``offres_pratiques``
     - ``sportif``
     - Types de pratiques basket proposées (5x5, 3x3, Micro-Basket, Basket Santé, Basket Inclusif, etc.).
   * - ``pro``
     - ``sportif``
     - Indicateur booléen signalant si la rencontre ou la compétition concerne le secteur professionnel (LNB, LFB, etc.).
   * - ``saison_en_cours``
     - ``statut``
     - Indicateur booléen signalant si l'organisme est actif sur la saison sportive courante.
   * - ``sexe``
     - ``sportif``
     - Genre de la compétition ou de l'équipe (Masculin, Féminin, Mixte).
   * - ``status``
     - ``statut``
     - État de publication de l'enregistrement dans Directus (published, draft, archived).
   * - ``surtitle``
     - ``contenu``
     - Surtitre ou chapeau introductif de l'article ou de la galerie.
   * - ``telephone``
     - ``contact``
     - Numéro de téléphone de contact officiel de l'organisme.
   * - ``title``
     - ``contenu``
     - Titre officiel du contenu, événement ou entité.
   * - ``titre``
     - ``contenu``
     - Titre du contenu ou de l'actualité en français.
   * - ``type``
     - ``statut``
     - Typologie administrative de l'organisme (Club, Comité départemental, Ligue régionale, Groupement, etc.).
   * - ``typeCompetitionGenerique``
     - ``sportif``
     - Niveau générique de compétition (Championnat de France, Régional, Départemental, Coupe, Tournoi).
   * - ``type_salle``
     - ``infrastructure``
     - Catégorisation technique de l'équipement sportif (Gymnase, Palais des Sports, Complexe, Terrain extérieur 3x3).
   * - ``type_sol``
     - ``infrastructure``
     - Revêtement du terrain (Parquet, Synthétique, Résine, Bitume, etc.).
   * - ``url_site_web``
     - ``contact``
     - URL du site internet officiel ou de la page de l'organisme.
   * - ``ville``
     - ``geographie``
     - Nom de la ville de localisation.

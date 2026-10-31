# FFBB permission matrix drift — 2026-10-31T10:56:40.789952+00:00

- FLIP: competition_archived_direct: blocked_cdn -> forbidden_directus
- FLIP: competition_archived_filter: blocked_cdn -> empty
- FLIP: competition_current_direct: blocked_cdn -> ok
- FLIP: competition_current_filter: blocked_cdn -> ok
- FLIP: competitions_listing: blocked_cdn -> ok
- FLIP: config_noauth: blocked_cdn -> ok
- FLIP: config_noauth_ipv4: blocked_cdn -> ok
- FLIP: config_tripwire_okhttp_ipv4: blocked_cdn -> ok
- FLIP: engagements_listing: blocked_cdn -> ok
- FLIP: organismes_listing: blocked_cdn -> ok
- FLIP: relational_nested_expand: blocked_cdn -> ok
- FLIP: rencontres_listing: blocked_cdn -> ok
- FLIP: saisons_id_field: blocked_cdn -> ok
- FLIP: saisons_nom_field: blocked_cdn -> forbidden_directus

Vérifier la politique de rôles Directus (filtres de saison, champs restreints) ou rafraîchir les canaris après un rollover de saison.

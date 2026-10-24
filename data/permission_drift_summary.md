# FFBB permission matrix drift — 2026-10-24T11:43:45.501709+00:00

- FLIP: competition_archived_direct: forbidden_directus -> blocked_cdn
- FLIP: competition_archived_filter: empty -> blocked_cdn
- FLIP: competition_current_direct: ok -> blocked_cdn
- FLIP: competition_current_filter: ok -> blocked_cdn
- FLIP: competitions_listing: ok -> blocked_cdn
- FLIP: config_noauth: ok -> blocked_cdn
- FLIP: config_noauth_ipv4: ok -> blocked_cdn
- FLIP: config_noauth_ipv6: error:ConnectError -> blocked_cdn
- FLIP: config_tripwire_okhttp_ipv4: ok -> blocked_cdn
- FLIP: engagements_listing: ok -> blocked_cdn
- FLIP: organismes_listing: ok -> blocked_cdn
- FLIP: relational_nested_expand: ok -> blocked_cdn
- FLIP: rencontres_listing: ok -> blocked_cdn
- FLIP: saisons_id_field: ok -> blocked_cdn
- FLIP: saisons_nom_field: forbidden_directus -> blocked_cdn

Vérifier la politique de rôles Directus (filtres de saison, champs restreints) ou rafraîchir les canaris après un rollover de saison.

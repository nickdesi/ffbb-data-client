========
Migration
========

This guide helps you migrate from older versions to the latest version of the FFBB API Client V2.

Public API Migration (No Changes Required)
==========================================

**Good News**: If you were using the public API, **no changes are required**!

The following imports continue to work exactly as before:

.. code-block:: python

    # These imports are unchanged and fully supported
    from ffbb_data_client import FFBBDataClient, ApiFFBBAppClient
    from ffbb_data_client import MeilisearchClient, MeilisearchFFBBClient
    from ffbb_data_client import MultiSearchQuery, Live
    from ffbb_data_client import MeilisearchClientExtension
    from ffbb_data_client import generate_queries

Your existing code should work without any modifications!

Migration from v1.0.x to v1.1.0
=============================

**Breaking Changes**: API methods now return model objects instead of dictionaries.

**Before (v1.0.x):**

.. code-block:: python

    from ffbb_data_client import FFBBDataClient

    client = FFBBDataClient.create(api_token, meilisearch_token)

    # Returns dictionary
    organisme = client.get_organisme(123)
    name = organisme['nom']  # Dictionary access
    type_info = organisme['type']

**After (v1.1.0+):**

.. code-block:: python

    from ffbb_data_client import FFBBDataClient

    client = FFBBDataClient.create(api_token, meilisearch_token)

    # Returns strongly-typed model object
    organisme = client.get_organisme(123)
    name = organisme.nom  # Object attribute access
    type_info = organisme.type

**Migration Steps:**

1. Replace dictionary access with object attributes
2. Update error handling - methods return None on error instead of raising exceptions
3. Import model types if you need type hints

**Common Patterns:**

.. code-block:: python

    # Before
    competitions = client.search_competitions("basketball")
    for comp in competitions.hits:
        comp_data = comp.source  # Dictionary
        name = comp_data['nom']
        season = comp_data['saison']

    # After
    competitions = client.search_competitions("basketball")
    for comp in competitions.hits:
        comp_data = comp.source  # Model object
        name = comp_data.nom
        season = comp_data.saison

Migration from v1.1.x to v1.2.0 (Upcoming)
=======================================

**Breaking Changes**: TokenManager API updated for better caching control.

**Before (v1.1.x):**

.. code-block:: python

    from ffbb_data_client import TokenManager

    tokens = TokenManager.get_tokens(use_cache=False)
    TokenManager.clear_cache()

**After (v1.2.0+):**

.. code-block:: python

    from ffbb_data_client import TokenManager
    from ffbb_data_client.utils.cache_manager import CacheManager

    # Updated signature
    tokens = TokenManager.get_tokens(use_cache=False)

    # Use CacheManager directly for cache operations
    CacheManager().clear_cache()

**Migration Steps:**

1. Update TokenManager.get_tokens() calls to use cache_config parameter
2. Replace TokenManager.clear_cache() with CacheManager().clear_cache()
3. Import CacheManager from ffbb_data_client.utils.cache_manager

---

**Migration Guide from v1.0.x to v1.1.0**

API Response Objects
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Before v1.1.0
    organisme = client.get_organisme(123)
    name = organisme['nom']  # Dictionary access

    # After v1.1.0
    organisme = client.get_organisme(123)
    name = organisme.nom  # Object attribute access

Field Selection
~~~~~~~~~~~~~~~

.. code-block:: python

    # Before v1.1.0
    fields = ["id", "nom", "code"]  # Manual field lists

    # After v1.1.0
    from ffbb_data_client.models.query_fields import QueryFieldsManager, FieldSet
    fields = QueryFieldsManager.get_organisme_fields(FieldSet.BASIC)

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

    # After v1.1.0 - Models handle errors automatically
    organisme = client.get_organisme(999999)  # Non-existent ID
    if organisme is None:
        print("Organization not found")

---

**Migration Guide from v1.1.x to v1.2.0 (Upcoming)**

Token Management Updates
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Before v1.2.0
    tokens = TokenManager.get_tokens(use_cache=False)
    TokenManager.clear_cache()

    # After v1.2.0
    tokens = TokenManager.get_tokens(use_cache=False)
    from ffbb_data_client.utils.cache_manager import CacheManager
    CacheManager().clear_cache()

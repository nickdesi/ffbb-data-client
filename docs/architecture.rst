============
Architecture
============

Package Structure
==================

The FFBB API Client V2 library has been reorganized for better maintainability and clarity. The new package structure follows domain-driven design principles:

.. code-block::

    ffbb_data_client/
    ├── clients/          # API client classes
    │   ├── api_ffbb_app_client.py
    │   ├── ffbb_data_client.py
    │   ├── meilisearch_client.py
    │   └── meilisearch_ffbb_client.py
    ├── helpers/          # Class extensions and utility helpers
    │   ├── http_requests_helper.py
    │   ├── http_requests_utils.py
    │   ├── meilisearch_client_extension.py
    │   └── multi_search_query_helper.py
    ├── models/           # Data models and structures
    │   ├── lives.py
    │   ├── external_id.py
    │   ├── multi_search_query.py
    │   ├── MultiSearchResults.py
    │   └── ... (50+ model files)
    └── utils/            # Data conversion utilities
        └── converter_utils.py

Clients Package
===============

The **clients/** package contains all API client classes responsible for interacting with FFBB services:

- **ApiFFBBAppClient**: Direct client for FFBB App API endpoints
- **FFBBDataClient**: Main aggregator client that combines multiple services
- **MeilisearchClient**: Base client for Meilisearch operations
- **MeilisearchFFBBClient**: Specialized Meilisearch client for FFBB data

Usage:

.. code-block:: python

    from ffbb_data_client import FFBBDataClient, ApiFFBBAppClient

    # Use the main aggregator client (recommended)
    client = FFBBDataClient.create(meilisearch_token, api_token)

    # Or use specific clients directly
    api_client = ApiFFBBAppClient(api_token)

Models Package
==============

The **models/** package contains all data structures and entities returned by the API:

- **Data Models**: Live games, competitions, organizations, etc.
- **Search Models**: Multi-search queries and results
- **Enumerations**: Status codes, types, categories

Usage:

.. code-block:: python

    from ffbb_data_client import MultiSearchQuery
    from ffbb_data_client.models import CompetitionType, Live

    # Create search queries
    query = MultiSearchQuery("basketball")

    # Work with live game data
    lives = client.get_lives()
    for live in lives:
        print(f"Match: {live.team_name_home} vs {live.team_name_out}")

Helpers Package
===============

The **helpers/** package provides class extensions and utility helpers:

- **HTTP Helpers**: Request handling, caching, error management
- **Client Extensions**: Enhanced functionality for base clients
- **Query Helpers**: Search query generation and manipulation

Usage:

.. code-block:: python

    from ffbb_data_client import MeilisearchClientExtension

    # Use extended client with additional features
    extended_client = MeilisearchClientExtension(token, url)
    results = extended_client.smart_multi_search(queries)

Utils Package
=============

The **utils/** package contains data conversion and utility functions:

- **Converter Utilities**: Type conversion, serialization, validation

Usage:

.. code-block:: python

    from ffbb_data_client.utils import converter_utils

    # Convert data types (internal usage)
    date_obj = converter_utils.from_datetime(date_string)

Migration Guide
===============

If you were using internal imports from the old structure, update them as follows:

.. code-block:: python

    # Old imports (deprecated)
    from ffbb_data_client.api_ffbb_app_client import ApiFFBBAppClient
    from ffbb_data_client.converters import from_datetime
    from ffbb_data_client.meilisearch_client_extension import MeilisearchClientExtension

    # New imports (recommended)
    from ffbb_data_client import ApiFFBBAppClient, MeilisearchClientExtension
    from ffbb_data_client.utils.converter_utils import from_datetime

The main public API remains unchanged, so most existing code should continue to work without modifications.

Dependency Tree
===============

The package dependencies follow a clear hierarchy:

- **Clients** depend on **Helpers** and **Models**
- **Helpers** depend on **Utils** and **Models**
- **Models** depend on **Utils**
- **Utils** have minimal external dependencies

This structure ensures:

- Clear separation of concerns
- Minimal circular dependencies
- Easy testing and maintenance
- Logical code organization

"""
Benchmark de latence ffbb-data-client.

Usage :
- Lance : python benchmark_search_organisme.py
"""

import statistics
import time

from ffbb_data_client import FFBBDataClient, TokenManager

N_RUNS = 10
SEARCH_QUERY = "Gerzat Basket"

CLIENT_CLASS = FFBBDataClient
token_getter = TokenManager.get_tokens


def main():
    print(
        f"Benchmark FFBBApiClient ({CLIENT_CLASS.__name__}) — Recherche organisme '{SEARCH_QUERY}'"
    )
    tokens = token_getter()
    client = CLIENT_CLASS.create(
        api_bearer_token=tokens.api_token,
        meilisearch_bearer_token=tokens.meilisearch_token,
    )
    times = []
    for i in range(N_RUNS):
        t0 = time.perf_counter()
        res = client.search_organismes(SEARCH_QUERY)
        t1 = time.perf_counter()
        times.append(t1 - t0)
        n_hits = len(res.hits) if res and hasattr(res, "hits") and res.hits else 0
        print(f"Run {i + 1:2d}: {times[-1]:.3f}s — {n_hits} résultats")
    print("\nRésumé:")
    print(f"  Moyenne : {statistics.mean(times):.3f}s")
    print(f"  Médiane : {statistics.median(times):.3f}s")
    print(f"  Min     : {min(times):.3f}s")
    print(f"  Max     : {max(times):.3f}s")
    print(f"  Écart-type : {statistics.stdev(times):.3f}s")


if __name__ == "__main__":
    main()

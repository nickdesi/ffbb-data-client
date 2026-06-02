"""
Tests pour les outils de concurrence.
"""

import asyncio
import unittest
from ffbb_data_client.utils.concurrency_utils import gather_with_concurrency


class TestConcurrencyUtils(unittest.TestCase):
    """Test cases for concurrency utility functions."""

    def test_gather_with_concurrency(self):
        """Test gather_with_concurrency works correctly and limits concurrency."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        active_tasks = 0
        max_seen_concurrency = 0

        async def worker(val: int):
            nonlocal active_tasks, max_seen_concurrency
            active_tasks += 1
            if active_tasks > max_seen_concurrency:
                max_seen_concurrency = active_tasks
            await asyncio.sleep(0.01)
            active_tasks -= 1
            return val * 2

        try:
            # 5 tâches avec une concurrence max de 2
            coros = [worker(i) for i in range(5)]
            results = loop.run_until_complete(gather_with_concurrency(2, *coros))

            self.assertEqual(results, [0, 2, 4, 6, 8])
            self.assertTrue(max_seen_concurrency <= 2, f"Expected concurrency <= 2, got {max_seen_concurrency}")
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()

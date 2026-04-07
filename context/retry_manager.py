"""
context/retry_manager.py

Tracks retry attempts per test and per locator.
Used by Agent 3 (self_heal_agent) and Agent 4 (failure_analysis_agent)
to detect flaky patterns before quarantining a test.

Usage:
    tc = TestContext()
    tc.retry.record("test_property_search")
    tc.retry.record("test_property_search")

    if tc.retry.is_flaky("test_property_search"):
        # quarantine or send to self-heal agent
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List


class RetryManager:
    """
    Records retry attempts and classifies tests as flaky
    when they exceed the configured threshold.

    Thresholds:
        flaky_threshold  — number of retries before a test is
                           considered flaky (default: 2)
        heal_threshold   — number of locator failures before
                           self-heal is triggered (default: 1)
    """

    FLAKY_THRESHOLD = 2
    HEAL_THRESHOLD  = 1

    def __init__(self):
        # test_id → list of failure reasons
        self._retries: Dict[str, List[str]] = defaultdict(list)

        # locator_key → failure count
        self._locator_failures: Dict[str, int] = defaultdict(int)

    # ── test retry tracking ───────────────────────────────────────

    def record(self, test_id: str, reason: str = "unknown") -> None:
        """
        Record one retry attempt for a test.

        Args:
            test_id: pytest node ID or behave scenario name
            reason:  short description — "timeout", "assertion", etc.
        """
        self._retries[test_id].append(reason)

    def retry_count(self, test_id: str) -> int:
        """Return how many times a test has been retried."""
        return len(self._retries[test_id])

    def is_flaky(self, test_id: str) -> bool:
        """
        True when a test has been retried more than FLAKY_THRESHOLD times.
        These tests get quarantined (@pytest.mark.flaky) and sent to
        Agent 4 for analysis.
        """
        return self.retry_count(test_id) >= self.FLAKY_THRESHOLD

    def flaky_tests(self) -> List[str]:
        """Return all test IDs currently classified as flaky."""
        return [
            test_id
            for test_id in self._retries
            if self.is_flaky(test_id)
        ]

    # ── locator failure tracking ──────────────────────────────────

    def record_locator_failure(self, locator_key: str) -> None:
        """
        Record a locator failure (TimeoutError on a selector).
        When count >= HEAL_THRESHOLD, Agent 3 self-heal is triggered.

        Args:
            locator_key: the key from the locators dict, e.g. "search_box"
        """
        self._locator_failures[locator_key] += 1

    def locator_failure_count(self, locator_key: str) -> int:
        return self._locator_failures[locator_key]

    def needs_healing(self, locator_key: str) -> bool:
        """
        True when a locator has failed enough times to trigger Agent 3.
        """
        return self._locator_failures[locator_key] >= self.HEAL_THRESHOLD

    def broken_locators(self) -> List[str]:
        """Return all locator keys that need healing."""
        return [
            key
            for key in self._locator_failures
            if self.needs_healing(key)
        ]

    # ── summary ───────────────────────────────────────────────────

    def summary(self) -> dict:
        """
        Return a summary dict written into failures.json by the logger.
        Read by Agent 4 (failure_analysis_agent) for classification.
        """
        return {
            "flaky_tests":     self.flaky_tests(),
            "broken_locators": self.broken_locators(),
            "retry_counts": {
                test_id: self.retry_count(test_id)
                for test_id in self._retries
            },
        }

    def reset(self) -> None:
        """Clear all state — called between behave scenarios."""
        self._retries.clear()
        self._locator_failures.clear()

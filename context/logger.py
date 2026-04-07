"""
context/logger.py

Structured JSON logger for the test framework.
Writes to reports/failures.json on every failure.
Read by Agent 4 (failure_analysis_agent) for root-cause classification.
Read by capture/ci_failure_capture.py for CI artifact generation.

Usage:
    tc = TestContext()
    tc.log.failure(
        test_id   = "tests/test_property.py::test_search",
        error     = "TimeoutError: selector 'input.search' not found",
        category  = "locator",
        trace_path = "reports/traces/test_search.zip"
    )
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ── stdlib logger for console output ─────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

_console = logging.getLogger("ai-test-framework")


class Logger:
    """
    Dual-output logger:
      - Console: human-readable via stdlib logging
      - File:    structured JSON appended to reports/failures.json

    The JSON output is what agents read — never parse console logs.
    """

    FAILURES_FILE = Path("reports/failures.json")

    # ── failure categories (matches Agent 4 classification) ───────
    CATEGORIES = ("locator", "logic", "environment", "flaky", "unknown")

    def __init__(self):
        self.FAILURES_FILE.parent.mkdir(parents=True, exist_ok=True)

    # ── structured failure logging ────────────────────────────────

    def failure(
        self,
        test_id:        str,
        error:          str,
        category:       str = "unknown",
        trace_path:     Optional[str] = None,
        screenshot_path: Optional[str] = None,
        locator_key:    Optional[str] = None,
        broken_selector: Optional[str] = None,
        browser:        Optional[str] = None,
        retry_count:    int = 0,
    ) -> None:
        """
        Append one failure record to reports/failures.json.

        Args:
            test_id:         pytest node ID or behave scenario name
            error:           exception message (first 500 chars)
            category:        one of locator/logic/environment/flaky/unknown
            trace_path:      path to .zip trace file
            screenshot_path: path to on-failure screenshot
            locator_key:     the locators dict key that failed
            broken_selector: the CSS/role selector string that timed out
            browser:         chromium / firefox / webkit
            retry_count:     how many times the test was retried
        """
        if category not in self.CATEGORIES:
            category = "unknown"

        record = {
            "timestamp":       datetime.now(timezone.utc).isoformat(),
            "test_id":         test_id,
            "error":           error[:500],
            "category":        category,
            "trace_path":      trace_path,
            "screenshot_path": screenshot_path,
            "locator_key":     locator_key,
            "broken_selector": broken_selector,
            "browser":         browser,
            "retry_count":     retry_count,
            "ci_run":          os.getenv("GITHUB_RUN_NUMBER"),
            "branch":          os.getenv("GITHUB_REF_NAME"),
        }

        self._append(record)
        _console.error(
            f"FAILURE [{category.upper()}] {test_id} — {error[:120]}"
        )

    # ── convenience console loggers ───────────────────────────────

    def info(self, msg: str) -> None:
        _console.info(msg)

    def debug(self, msg: str) -> None:
        _console.debug(msg)

    def warning(self, msg: str) -> None:
        _console.warning(msg)

    # ── read helpers (used by Agent 4) ────────────────────────────

    def read_failures(self) -> list[dict]:
        """
        Return all failure records from reports/failures.json.
        Returns empty list if file does not exist or is empty.
        """
        if not self.FAILURES_FILE.exists():
            return []
        try:
            content = self.FAILURES_FILE.read_text(encoding="utf-8").strip()
            if not content:
                return []
            # file is newline-delimited JSON (one record per line)
            return [
                json.loads(line)
                for line in content.splitlines()
                if line.strip()
            ]
        except (json.JSONDecodeError, OSError):
            return []

    def failures_by_category(self) -> dict[str, list[dict]]:
        """
        Group failures by category.
        Used by Agent 4 to route: locator → Agent 3, logic → fix plan.
        """
        grouped: dict[str, list[dict]] = {c: [] for c in self.CATEGORIES}
        for record in self.read_failures():
            cat = record.get("category", "unknown")
            grouped.setdefault(cat, []).append(record)
        return grouped

    def clear(self) -> None:
        """
        Clear the failures file.
        Call at the start of a full test run to avoid stale data.
        """
        self.FAILURES_FILE.write_text("", encoding="utf-8")

    # ── internal ──────────────────────────────────────────────────

    def _append(self, record: dict) -> None:
        """Append one JSON record as a new line."""
        with open(self.FAILURES_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

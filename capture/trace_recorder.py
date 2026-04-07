"""
capture/trace_recorder.py

Playwright Trace configuration and recording helpers.
Wired into conftest.py — never called directly from tests.

Trace files saved to reports/traces/{test_name}.zip on every run.
On CI failure, uploaded as artifacts and read by MCPAnalyser.

TRACE_MODE env var:
    always   — save every trace (capture pipeline / Windsurf input)
    failure  — save only on failure (default)
    never    — disable tracing
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from playwright.sync_api import BrowserContext


class TraceRecorder:
    """
    Thin wrapper around Playwright's tracing API.
    Keeps conftest.py clean — all trace config lives here.
    """

    TRACE_DIR = Path("reports/traces")

    @classmethod
    def start(cls, context: BrowserContext) -> None:
        """Start recording immediately after context creation."""
        cls.TRACE_DIR.mkdir(parents=True, exist_ok=True)
        context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True,
        )

    @classmethod
    def stop(
        cls,
        context: BrowserContext,
        test_name: str,
        save: bool = True,
    ) -> Optional[str]:
        """
        Stop recording and optionally save.

        Returns:
            Path to saved .zip, or None if not saved.
        """
        safe_name = cls._sanitise(test_name)
        trace_path = cls.TRACE_DIR / f"{safe_name}.zip"

        if save:
            context.tracing.stop(path=str(trace_path))
            return str(trace_path)

        context.tracing.stop()
        return None

    @staticmethod
    def should_save(passed: bool) -> bool:
        """
        Returns True when the trace should be saved to disk.
        Controlled by TRACE_MODE env var.
        """
        mode = os.getenv("TRACE_MODE", "failure").lower()
        if mode == "always":
            return True
        if mode == "never":
            return False
        return not passed   # "failure" — save only when test failed

    @staticmethod
    def _sanitise(name: str) -> str:
        return (
            name.replace("::", "__")
                .replace("/", "_")
                .replace("\\", "_")
                .replace(" ", "_")
        )

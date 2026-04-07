"""
capture/mcp_analyser.py

Sends a Playwright trace to the Playwright MCP server and
returns a structured MCPAnalysis.

MCP server is TypeScript/Node.js — runs as a subprocess.
Your Python framework connects via subprocess (Phase 1)
or HTTP/SSE (Phase 2 when Windsurf integration is active).

Phase 1 — subprocess (current):
    python -m capture.mcp_analyser --trace reports/traces/test_x.zip

Phase 2 — HTTP (set MCP_SERVER_URL in .env):
    MCP_SERVER_URL=http://localhost:3001

Output (MCPAnalysis dataclass) feeds into:
    - WindsurfExporter  → test generation
    - SelfHealAgent     → role-based locator suggestion
    - Agent 4           → failure root-cause context
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import httpx


@dataclass
class MCPAnalysis:
    """
    Structured output from the MCP Intent Engine.

    intent:      what the user was trying to do
                 e.g. "property_search_and_filter"

    causality:   ordered chain of events
                 e.g. ["click search_box",
                        "GET /api/search → 200",
                        "DOM update: results list rendered"]

    role_map:    locator key → role-based selector
                 e.g. {"search_box": "input[aria-label='Search']"}

    auth_apis:   endpoints that set up session / tokens
                 e.g. ["/oauth/token", "/api/session"]

    flaky_risk:  "high" | "medium" | "low"

    raw:         full MCP server response (for debugging)
    """
    intent:     str = "unknown"
    causality:  list[str] = field(default_factory=list)
    role_map:   dict[str, str] = field(default_factory=dict)
    auth_apis:  list[str] = field(default_factory=list)
    flaky_risk: str = "unknown"
    raw:        dict = field(default_factory=dict)


class MCPAnalyser:
    """
    Connects to the Playwright MCP server and analyses a trace.

    Connection mode is determined by MCP_SERVER_URL env var:
        not set  → subprocess mode (Phase 1)
        set      → HTTP mode (Phase 2)
    """

    MCP_CMD = ["npx", "@playwright/mcp@latest"]

    def __init__(self):
        self.server_url = os.getenv("MCP_SERVER_URL")

    def analyse(self, trace_path: str) -> MCPAnalysis:
        """
        Analyse a Playwright trace file.

        Args:
            trace_path: path to .zip trace file

        Returns:
            MCPAnalysis dataclass
        """
        if not Path(trace_path).exists():
            raise FileNotFoundError(f"Trace not found: {trace_path}")

        if self.server_url:
            return self._analyse_http(trace_path)
        return self._analyse_subprocess(trace_path)

    # ── Phase 1: subprocess ───────────────────────────────────────

    def _analyse_subprocess(self, trace_path: str) -> MCPAnalysis:
        """
        Spawns the MCP server as a child process.
        Works with zero server management — Node.js must be installed.
        """
        try:
            result = subprocess.run(
                self.MCP_CMD + ["analyse", "--trace", trace_path],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                print(f"[MCPAnalyser] MCP error: {result.stderr[:200]}")
                return MCPAnalysis()

            raw = json.loads(result.stdout)
            return self._parse(raw)

        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
            print(f"[MCPAnalyser] subprocess failed: {e}")
            return MCPAnalysis()

    # ── Phase 2: HTTP/SSE ─────────────────────────────────────────

    def _analyse_http(self, trace_path: str) -> MCPAnalysis:
        """
        Calls a running MCP server over HTTP.
        Used when Windsurf is active or in Phase 2 CI setup.
        """
        try:
            response = httpx.post(
                f"{self.server_url}/analyse",
                json={"trace": trace_path},
                timeout=60,
            )
            response.raise_for_status()
            return self._parse(response.json())
        except (httpx.HTTPError, json.JSONDecodeError) as e:
            print(f"[MCPAnalyser] HTTP failed: {e}")
            return MCPAnalysis()

    # ── parse ─────────────────────────────────────────────────────

    @staticmethod
    def _parse(raw: dict) -> MCPAnalysis:
        return MCPAnalysis(
            intent     = raw.get("intent", "unknown"),
            causality  = raw.get("causality", []),
            role_map   = raw.get("role_map", {}),
            auth_apis  = raw.get("auth_apis", []),
            flaky_risk = raw.get("flaky_risk", "unknown"),
            raw        = raw,
        )


# ── CLI entry point ───────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyse a Playwright trace")
    parser.add_argument("--trace", required=True, help="Path to .zip trace file")
    parser.add_argument("--output", default=None, help="Save analysis JSON here")
    args = parser.parse_args()

    analyser = MCPAnalyser()
    analysis = analyser.analyse(args.trace)

    result = {
        "intent":     analysis.intent,
        "causality":  analysis.causality,
        "role_map":   analysis.role_map,
        "auth_apis":  analysis.auth_apis,
        "flaky_risk": analysis.flaky_risk,
    }

    print(json.dumps(result, indent=2))

    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2))
        print(f"\nSaved → {args.output}")

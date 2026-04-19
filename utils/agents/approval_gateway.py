"""
utils/agents/approval_gateway.py

ApprovalGateway — The Agentic Orchestrator ("The Brain")

Reads failures.json after every test run and decides what happens next:

  Category      Decision
  ──────────    ──────────────────────────────────────────────
  locator     → Agent 3: XPath self-heal, diff shown, APPROVE/REJECT per locator
  api_timeout → Retry strategy recommendation + config guidance
  logic       → Agent 4: AI root-cause analysis → fix plan file
  flaky       → Agent 4: quarantine plan + flaky registry
  environment → Escalation report for infra/DevOps
  unknown     → Agent 4: open analysis

Design principle:
  The orchestrator DECIDES automatically.
  Humans APPROVE before any file is patched.
  Read-only actions (reports, plans) run without prompting.

Auto mode (fires at end of pytest session):
  Set AUTO_HEAL=true in .env — wired via conftest.py pytest_sessionfinish

Manual mode:
  python -m utils.agents.approval_gateway
  python -m utils.agents.approval_gateway --file reports/failures.json
"""

from __future__ import annotations

import argparse
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from context.logger import Logger


# ── terminal colours ──────────────────────────────────────────────────────────

class _C:
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    GREEN  = "\033[92m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"


def _header(text: str) -> str:
    bar = "═" * 64
    return f"\n{_C.BOLD}{bar}\n  {text}\n{bar}{_C.RESET}"


def _section(label: str) -> str:
    dashes = "─" * max(0, 56 - len(label))
    return f"\n{_C.CYAN}── {label} {dashes}{_C.RESET}"


# ── orchestrator ──────────────────────────────────────────────────────────────

class ApprovalGateway:
    """
    The Orchestrator — coordinates Agents 3 and 4 after a test run.

    Decision matrix
    ───────────────
    locator      → Agent 3 (SelfHealAgent)  — one diff per broken XPath
    api_timeout  → Retry/mock recommendation — written to fix_plans/
    logic        → Agent 4 (FailureAnalysisAgent) — fix plan file
    flaky        → Agent 4 + flaky registry — quarantine recommendation
    environment  → Escalation report — for infra / DevOps
    unknown      → Agent 4 open analysis

    Every patch to a source file requires human APPROVE.
    Reports and recommendations are written automatically (read-only).
    """

    FIX_PLANS_DIR  = Path("reports/fix_plans")
    ESCALATION_LOG = Path("reports/escalations.txt")
    FLAKY_REGISTRY = Path("reports/flaky_registry.txt")

    # locator files the orchestrator can guess from test IDs
    _LOCATOR_MAP = [
        ("trademe", "property_search", "locators/trademe_property_search_locators.py"),
        ("trademe", "results",         "locators/trademe_results_locators.py"),
        ("trademe", "listing",         "locators/trademe_listing_locators.py"),
    ]

    def __init__(self):
        self.log     = Logger()
        self._results: dict[str, str] = {}   # category → human-readable outcome

    # ══════════════════════════════════════════════════════════════════════════
    # PUBLIC ENTRY POINT
    # ══════════════════════════════════════════════════════════════════════════

    def run(self, failures_file: str = "reports/failures.json") -> None:
        """
        Main orchestration loop.

        Steps:
          1. Load failures.json
          2. Print intake table (what was received, what will happen)
          3. Route each category to the right handler
          4. Print summary outcome table
        """
        print(_header("APPROVAL GATEWAY — Agentic Orchestrator"))

        failures = self.log.read_failures()
        if not failures:
            print(f"\n{_C.GREEN}✓  No failures found — all tests passed!{_C.RESET}\n")
            return

        grouped = self.log.failures_by_category()
        active  = {k: v for k, v in grouped.items() if v}
        total   = sum(len(v) for v in active.values())

        print(f"\n  Loaded {_C.BOLD}{total}{_C.RESET} failure(s) "
              f"across {len(active)} category/categories\n")
        self._print_intake_table(active)

        # ── route ────────────────────────────────────────────────────────────
        if active.get("locator"):
            self._handle_locator(active["locator"])

        if active.get("api_timeout"):
            self._handle_api_timeout(active["api_timeout"])

        if active.get("logic"):
            self._handle_logic(active["logic"])

        if active.get("flaky"):
            self._handle_flaky(active["flaky"])

        if active.get("environment"):
            self._handle_environment(active["environment"])

        if active.get("unknown"):
            self._handle_unknown(active["unknown"])

        self._print_summary_table()

    # ══════════════════════════════════════════════════════════════════════════
    # HANDLERS
    # ══════════════════════════════════════════════════════════════════════════

    def _handle_locator(self, failures: list[dict]) -> None:
        """
        Locator failures → Agent 3 self-heal.

        Deduplicates by broken_selector — same broken XPath appearing in
        multiple tests is healed once, not once per test.
        Pulls HTML from the Playwright trace zip if available.
        """
        print(_section(f"LOCATOR  ({len(failures)} failure(s))"))
        print("  Decision  →  Agent 3: XPath self-heal")

        try:
            from utils.agents.self_heal_agent import SelfHealAgent
            healer = SelfHealAgent()
        except Exception as exc:
            print(f"  {_C.RED}Could not load Agent 3: {exc}{_C.RESET}")
            self._results["locator"] = "Agent 3 unavailable"
            return

        healed  = 0
        skipped = 0
        seen:   set[str] = set()

        for f in failures:
            selector    = f.get("broken_selector") or ""
            locator_key = f.get("locator_key")     or "unknown_key"
            test_id     = f.get("test_id", "?")

            print(f"\n  Test:      {test_id}")
            print(f"  Selector:  {selector or '(not captured)'}")

            # ── guard: selector must be known ────────────────────────────────
            if not selector or selector == "unknown":
                print(f"  {_C.YELLOW}↳ Broken selector not captured. "
                      f"Re-run the test to get it into the error message.{_C.RESET}")
                skipped += 1
                continue

            # ── guard: deduplicate ───────────────────────────────────────────
            if selector in seen:
                print(f"  {_C.YELLOW}↳ Already healed this session — skipping duplicate{_C.RESET}")
                skipped += 1
                continue
            seen.add(selector)

            page_html    = self._html_from_trace(f.get("trace_path"))
            locator_file = self._guess_locator_file(test_id)

            healer.run(
                broken_locator=selector,
                locator_key=locator_key,
                page_html=page_html,
                locator_file=locator_file,
            )
            healed += 1

        self._results["locator"] = f"{healed} healed, {skipped} skipped"

    def _handle_api_timeout(self, failures: list[dict]) -> None:
        """
        API timeout failures → Retry / mock-mode recommendation.
        Writes a structured guidance file.  No code is auto-patched.
        """
        print(_section(f"API TIMEOUT  ({len(failures)} failure(s))"))
        print("  Decision  →  Retry strategy recommendation")

        lines = [
            f"API TIMEOUT RECOMMENDATION",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
        ]
        for f in failures:
            lines.append(f"\nTest:    {f.get('test_id', '?')}")
            lines.append(f"Error:   {f.get('error', '')[:300]}")
            lines.append(f"Browser: {f.get('browser', '?')}")
            lines.append(f"CI run:  {f.get('ci_run', 'local')}")
            lines.append("─" * 40)

        lines += [
            "",
            "RECOMMENDED ACTIONS (in priority order):",
            "  1. Verify API endpoint is reachable from CI runner (VPN/firewall/allowlist)",
            "  2. Increase timeout in api/rest_client.py  (current default → try 60 s)",
            "  3. Enable MOCK_MODE=true to decouple UI tests from API availability",
            "     e.g.  MOCK_MODE=true pytest tests/api/ -v",
            "  4. Add  @pytest.mark.flaky(reruns=2)  to affected tests as a short-term fix",
            "  5. Check if Azure AKS egress rules block outbound calls to the API host",
        ]

        outfile = self._write_plan("api_timeout", "\n".join(lines))
        print(f"\n  {_C.YELLOW}Recommendation saved → {outfile}{_C.RESET}")

        print("\n  Quick actions:")
        print("    MOCK_MODE=true pytest tests/api/ -v")
        print("    # or increase timeout in api/rest_client.py")

        self._results["api_timeout"] = f"Guidance → {outfile}"

    def _handle_logic(self, failures: list[dict]) -> None:
        """
        Logic (assertion) failures → Agent 4 AI root-cause analysis.
        Fix plan saved to reports/fix_plans/.
        """
        print(_section(f"LOGIC  ({len(failures)} failure(s))"))
        print("  Decision  →  Agent 4: AI root-cause analysis + fix plan")

        try:
            from utils.agents.failure_analysis_agent import FailureAnalysisAgent
            report  = FailureAnalysisAgent().analyse_failures(failures)
            outfile = self._write_plan("logic", report)
            print(f"\n  {_C.GREEN}Fix plan → {outfile}{_C.RESET}")
            print("\n  PREVIEW (first 10 lines):")
            print("  " + "\n  ".join(report.splitlines()[:10]))
            self._results["logic"] = f"Fix plan → {outfile}"
        except Exception as exc:
            print(f"  {_C.RED}Agent 4 error: {exc}{_C.RESET}")
            self._results["logic"] = f"Agent 4 error: {exc}"

    def _handle_flaky(self, failures: list[dict]) -> None:
        """
        Flaky failures → Agent 4 quarantine plan + flaky registry update.
        Flaky registry lists test IDs for @pytest.mark.flaky tagging.
        """
        print(_section(f"FLAKY  ({len(failures)} failure(s))"))
        print("  Decision  →  Agent 4: quarantine plan + flaky registry")

        try:
            from utils.agents.failure_analysis_agent import FailureAnalysisAgent
            report  = FailureAnalysisAgent().analyse_failures(failures)
            outfile = self._write_plan("flaky", report)
        except Exception as exc:
            outfile = f"(Agent 4 error: {exc})"
            report  = ""

        flaky_ids = [f.get("test_id", "") for f in failures if f.get("test_id")]
        self._update_flaky_registry(flaky_ids)

        print(f"\n  {_C.YELLOW}Quarantine plan → {outfile}{_C.RESET}")
        print(f"  Flaky registry  → {self.FLAKY_REGISTRY}")
        print("\n  Add  @pytest.mark.flaky(reruns=2)  to these tests:")
        for tid in flaky_ids:
            print(f"    • {tid}")

        self._results["flaky"] = f"{len(failures)} quarantined → {outfile}"

    def _handle_environment(self, failures: list[dict]) -> None:
        """
        Environment failures (network, Docker, AKS) → escalation report.
        Written to reports/escalations.txt — needs human/infra investigation.
        """
        print(_section(f"ENVIRONMENT  ({len(failures)} failure(s))"))
        print("  Decision  →  Escalate to infrastructure / DevOps")

        lines = [
            f"ESCALATION REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Environment failures: {len(failures)}",
            "=" * 60,
        ]
        for f in failures:
            lines.append(f"\nTest:    {f.get('test_id', '?')}")
            lines.append(f"Error:   {f.get('error', '')[:300]}")
            lines.append(f"Browser: {f.get('browser', '?')}")
            lines.append(f"CI run:  {f.get('ci_run', 'local')}")
            lines.append(f"Branch:  {f.get('branch', 'local')}")
            lines.append("─" * 40)

        lines += [
            "",
            "SUGGESTED INVESTIGATION CHECKLIST:",
            "  [ ] Docker image browser version matches installed playwright version",
            "  [ ] Network connectivity: CI runner → test environment (VPN, firewall)",
            "  [ ] Secrets / environment variables present in CI pipeline",
            "  [ ] AKS node has sufficient CPU and memory for test pods",
            "  [ ] Database / backend services are running in test environment",
        ]

        self.ESCALATION_LOG.parent.mkdir(parents=True, exist_ok=True)
        # append (don't overwrite — preserve history across CI runs)
        with open(self.ESCALATION_LOG, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n\n")

        print(f"\n  {_C.RED}Escalation report → {self.ESCALATION_LOG}{_C.RESET}")
        print("  Needs infrastructure / DevOps investigation — not an automated fix.")

        self._results["environment"] = f"{len(failures)} escalated → {self.ESCALATION_LOG}"

    def _handle_unknown(self, failures: list[dict]) -> None:
        """Unknown failures → Agent 4 open analysis."""
        print(_section(f"UNKNOWN  ({len(failures)} failure(s))"))
        print("  Decision  →  Agent 4: classify and recommend")

        try:
            from utils.agents.failure_analysis_agent import FailureAnalysisAgent
            report  = FailureAnalysisAgent().analyse_failures(failures)
            outfile = self._write_plan("unknown", report)
            print(f"\n  Analysis → {outfile}")
            self._results["unknown"] = f"Analysis → {outfile}"
        except Exception as exc:
            print(f"  {_C.RED}Agent 4 error: {exc}{_C.RESET}")
            self._results["unknown"] = f"Agent 4 error: {exc}"

    # ══════════════════════════════════════════════════════════════════════════
    # DISPLAY HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _print_intake_table(self, grouped: dict[str, list[dict]]) -> None:
        """Print what the orchestrator received and what it will do."""
        decisions = {
            "locator":     "Agent 3 — XPath self-heal",
            "api_timeout": "Retry / mock-mode recommendation",
            "logic":       "Agent 4 — AI fix plan",
            "flaky":       "Agent 4 — quarantine plan",
            "environment": "Escalate to infrastructure",
            "unknown":     "Agent 4 — open analysis",
        }
        colour_map = {
            "locator":     _C.RED,
            "api_timeout": _C.YELLOW,
            "logic":       _C.RED,
            "flaky":       _C.YELLOW,
            "environment": _C.RED,
            "unknown":     _C.YELLOW,
        }
        print(f"  {'Category':<16} {'Count':>5}  Decision")
        print(f"  {'─'*16} {'─'*5}  {'─'*38}")
        for cat, items in grouped.items():
            col      = colour_map.get(cat, _C.RESET)
            decision = decisions.get(cat, "analyse")
            print(f"  {col}{cat:<16}{_C.RESET} {len(items):>5}  {decision}")

    def _print_summary_table(self) -> None:
        """Print orchestration outcomes after all handlers have run."""
        print(_header("ORCHESTRATION COMPLETE"))
        print(f"  {'Category':<16}  Outcome")
        print(f"  {'─'*16}  {'─'*46}")
        for cat, outcome in self._results.items():
            col = _C.GREEN if any(w in outcome for w in ("healed", "plan", "Guidance")) \
                  else _C.YELLOW
            print(f"  {col}{cat:<16}{_C.RESET}  {outcome}")
        print()

    # ══════════════════════════════════════════════════════════════════════════
    # FILE HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _write_plan(self, category: str, content: str) -> str:
        """Write any plan / recommendation to reports/fix_plans/ with timestamp."""
        self.FIX_PLANS_DIR.mkdir(parents=True, exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.FIX_PLANS_DIR / f"{ts}_{category}.txt"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def _update_flaky_registry(self, test_ids: list[str]) -> None:
        """Append flaky test IDs to the registry file."""
        self.FLAKY_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(self.FLAKY_REGISTRY, "a", encoding="utf-8") as fh:
            fh.write(f"\n# Session: {ts}\n")
            for tid in test_ids:
                fh.write(f"{tid}\n")

    def _html_from_trace(self, trace_path: Optional[str]) -> str:
        """
        Extract the last HTML snapshot from a Playwright trace zip.
        Returns a fallback string if the trace is missing — Agent 3 can
        still suggest a fix from the broken selector string alone.
        """
        if not trace_path:
            return (
                "HTML snapshot not available (no trace path). "
                "Suggest the most likely correct XPath based on the broken "
                "selector string and common patterns for this type of site."
            )

        path = Path(trace_path)
        if not path.exists():
            return f"Trace file not found: {trace_path}"

        try:
            with zipfile.ZipFile(str(path), "r") as zf:
                html_files = sorted(n for n in zf.namelist() if n.endswith(".html"))
                if html_files:
                    raw = zf.read(html_files[-1]).decode("utf-8", errors="ignore")
                    return raw[:5000]   # 5 KB is enough context for the AI
        except Exception as exc:
            return f"Could not read trace {trace_path}: {exc}"

        return f"No HTML snapshots found in trace: {trace_path}"

    def _guess_locator_file(self, test_id: str) -> str:
        """
        Derive the most likely locator file from a test node ID.
        Falls back to 'locators/' so Agent 3 can ask the user to pick.
        """
        lower = (test_id or "").lower()
        for app, screen, locator_file in self._LOCATOR_MAP:
            if app in lower and screen in lower:
                return locator_file
        # check single-word app match
        for app, _, locator_file in self._LOCATOR_MAP:
            if app in lower:
                return locator_file
        return "locators/"


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ApprovalGateway — agentic orchestrator for ai-test-framework"
    )
    parser.add_argument(
        "--file",
        default="reports/failures.json",
        help="Path to failures.json (default: reports/failures.json)",
    )
    args = parser.parse_args()
    ApprovalGateway().run(failures_file=args.file)


if __name__ == "__main__":
    main()

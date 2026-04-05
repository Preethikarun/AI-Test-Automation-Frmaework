"""
Agent 4 — Failure Analysis (closes the loop)
Reads reports/failures.json after a test run.
Classifies failures, identifies root causes,
suggests fixes, and outputs a plain-English report.

No approval gate — read-only analysis.
Locator failures are routed back to Agent 3.

Usage: python -m agents.failure_analysis_agent
"""
import json
from pathlib import Path
from datetime import datetime
from agents.base_agent import BaseAgent

MOCK_MODE = True  # set False when API key is ready


class FailureAnalysisAgent(BaseAgent):

    SYSTEM_PROMPT = """You are an expert test automation engineer
specialising in root cause analysis of test failures.
You analyse structured failure data and produce clear,
actionable fix plans that a junior engineer can follow."""

    def load_failures(
        self,
        filepath: str = "reports/failures.json"
    ) -> list:
        """Load failures from JSON log."""
        path = Path(filepath)
        if not path.exists():
            print(f"  No failures log found at {filepath}")
            print("  Run your tests first to generate failures.")
            return []

        with open(path, "r", encoding="utf-8") as f:
            failures = json.load(f)

        print(f"  Loaded {len(failures)} failure(s) from {filepath}")
        return failures

    def analyse_failures(self, failures: list) -> str:
        """Send failures to AI for root cause analysis."""
        if not failures:
            return "No failures to analyse."

        if MOCK_MODE:
            print("  [mock mode] generating failure analysis")
            return self._mock_analysis(failures)

        # format failures for the prompt
        failure_summary = json.dumps(failures, indent=2)

        prompt = f"""Analyse these test failures and produce a structured fix plan.

For each failure provide:
FAILURE: [test name]
CATEGORY: [locator | logic | flaky | environment]
ROOT CAUSE: [one sentence — why did this fail?]
FIX: [concrete steps to resolve it]
PRIORITY: [high | medium | low]
---

Failures to analyse:
{failure_summary}

End with a SUMMARY section covering:
- Total failures by category
- Most critical fix needed first
- Any patterns suggesting systemic issues"""

        return self.call_claude(prompt, self.SYSTEM_PROMPT)

    def _mock_analysis(self, failures: list) -> str:
        """Generate realistic mock analysis from actual failures."""
        lines = []
        lines.append("FAILURE ANALYSIS REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Total failures: {len(failures)}")
        lines.append("=" * 50)

        for i, f in enumerate(failures, 1):
            category = f.get("category", "unknown")
            test = f.get("test", "unknown test")
            error = f.get("error_message", "")[:100]

            lines.append(f"\nFAILURE {i}: {test}")
            lines.append(f"CATEGORY: {category}")

            if category == "locator":
                lines.append(
                    "ROOT CAUSE: CSS selector no longer matches "
                    "an element on the page — likely a UI change."
                )
                lines.append(
                    "FIX: Run Agent 3 self-heal to get an "
                    "AI-suggested replacement selector. "
                    "Check if the app was recently updated."
                )
                lines.append("PRIORITY: high")

            elif category == "logic":
                lines.append(
                    "ROOT CAUSE: Assertion failed — the page "
                    "state did not match the expected value."
                )
                lines.append(
                    "FIX: Review the test assertion and confirm "
                    "the expected value matches current app behaviour. "
                    "Check if a recent feature change affected this flow."
                )
                lines.append(
                    "FIX: Review the test assertion and confirm "
                    "the expected value matches current app behaviour. "
                    "Check if a recent feature change affected this flow."
                )
                lines.append("PRIORITY: high")

            elif category == "flaky":
                lines.append(
                    "ROOT CAUSE: Test passed on some runs but "
                    "failed on others — likely a timing or "
                    "async issue."
                )
                lines.append(
                    "FIX: Add explicit wait_for_load_state() or "
                    "expect() assertion before the failing action. "
                    "Consider adding @pytest.mark.flaky for quarantine."
                )
                lines.append("PRIORITY: medium")

            else:
                lines.append(
                    f"ROOT CAUSE: {error}"
                )
                lines.append(
                    "FIX: Check environment setup — network, "
                    "browser version, and dependencies."
                )
                lines.append("PRIORITY: low")

            lines.append("---")

        # summary
        categories = [f.get("category", "unknown")
                    for f in failures]
        lines.append("\nSUMMARY")
        lines.append(
            f"Locator failures:     {categories.count('locator')}"
        )
        lines.append(
            f"Logic failures:       {categories.count('logic')}"
        )
        lines.append(
            f"Flaky failures:       {categories.count('flaky')}"
        )
        lines.append(
            f"Environment failures: {categories.count('environment')}"
        )

        if categories.count("locator") > 0:
            lines.append(
                "\nRECOMMENDATION: Run Agent 3 self-heal on "
                "all locator failures first — "
                "these are fastest to fix."
            )

        return "\n".join(lines)

    def route_locator_failures(self, failures: list):
        """
        Route locator failures back to Agent 3.
        For each unhealed locator failure, offer to self-heal.
        """
        locator_failures = [
            f for f in failures
            if f.get("category") == "locator"
            and not f.get("healed", False)
        ]

        if not locator_failures:
            return

        print(f"\n  {len(locator_failures)} unhealed locator "
            f"failure(s) — route to Agent 3?")
        decision = input("  Route to Agent 3? (Y/N) > ").upper()

        if decision == "Y":
            from agents.self_heal_agent import SelfHealAgent
            healer = SelfHealAgent()
            for failure in locator_failures:
                locator = failure.get("broken_locator", "unknown")
                print(f"\n  Healing: {failure['test']}")
                healer.run(
                    broken_locator=locator,
                    locator_key="unknown_key",
                    page_html="Re-run tests to capture HTML",
                    locator_file="locators/todo_locators.py"
                )

    def run(
        self,
        failures_file: str = "reports/failures.json"
    ):
        """
        Full analysis run.
        Plan: load → analyse → report → route locator failures
        """
        print("\nAgent 4 — failure analysis starting...")

        # Step 1: load failures
        failures = self.load_failures(failures_file)
        if not failures:
            print("  Nothing to analyse — all tests passing!")
            return

        # Step 2: analyse
        print(f"  Analysing {len(failures)} failure(s)...")
        report = self.analyse_failures(failures)

        # Step 3: print report
        print("\n" + "="*60)
        print("AGENT 4 — FAILURE ANALYSIS REPORT")
        print("="*60)
        print(report)
        print("="*60)

        # Step 4: save report
        self.save_output(report, "reports/failure_report.txt")

        # Step 5: route locator failures to Agent 3
        self.route_locator_failures(failures)

        print("\nAnalysis complete.")
        print("See reports/failure_report.txt for full report.")


def main():
    agent = FailureAnalysisAgent()
    agent.run()


if __name__ == "__main__":
    main()

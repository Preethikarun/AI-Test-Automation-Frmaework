"""
utils/agents/test_reader_agent.py  —  Agent 1 (Mode 1)

Reads manual test cases from Excel, CSV, or text files.
Converts them to structured plain-English test cases.
Output feeds directly into Agent 2 (bdd_generator_agent).

Plan mode runs first — agent shows what it will generate
before writing any files. Nothing is saved until you approve.

Workflow:
  1. You provide Excel / CSV / text with manual test cases
  2. Agent 1 reads and converts to structured text
  3. You review the output
  4. You approve → saved to reports/test_cases.txt
  5. Agent 2 reads reports/test_cases.txt → generates BDD

CLI:
  python -m utils.agents.test_reader_agent \\
      --source intake/trademe_test_cases.xlsx \\
      --app trademe \\
      --screen property_search

  python -m utils.agents.test_reader_agent \\
      --source intake/my_tests.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from utils.agents.base_agent import BaseAgent


SYSTEM_PROMPT = """
You are an expert test analyst for a Python Playwright BDD test automation framework.

Your job is to read manual test cases and convert each one into a structured format
using this EXACT template:

TEST CASE: [clear descriptive name]
GIVEN: [starting state or precondition — passive, not an action]
WHEN: [action the user performs — active voice]
THEN: [expected result — what the user sees]
TAGS: [from: smoke, regression, ui, api, e2e, filter, detail, search]
SCREEN: [snake_case screen name e.g. property_search, results, listing_detail]
PRIORITY: [High / Medium / Low]
DATA:
  key: "exact value from input"
  key: "exact value from input"
---

CRITICAL DATA RULES — these are the most important rules:
1. The DATA block MUST contain every concrete value mentioned in the input
   (search terms, prices, URLs, usernames, quantities, dates, filter values, etc.)
2. Copy values VERBATIM from the input — do NOT paraphrase, round, or invent values
3. If the input says "$500,000" write "$500,000" — not "500000" or "five hundred thousand"
4. If no concrete value is given for a field, write: FILL_ME (in uppercase, no quotes)
5. Keys must be snake_case. Values must be double-quoted strings.
6. Every parameter that will appear in a Gherkin step MUST be in the DATA block

GENERAL RULES:
- Extract EVERY test case — do not skip any
- GIVEN is a state, not an action: "the property search page is open" not "I open..."
- WHEN uses active voice: "I search for...", "I apply...", "I select..."
- THEN is a state: "results appear showing...", "the price filter shows..."
- TAGS from this list only: smoke, regression, ui, api, e2e, filter, detail, search
- SCREEN must be snake_case: property_search, results, listing_detail
- Separate each test case with exactly one line containing: ---
- Output ONLY the structured test cases — no preamble, no explanations

EXAMPLE — correct output for "search for Auckland apartments under $600k":

TEST CASE: Search for Auckland apartments under $600,000
GIVEN: the Trade Me property search page is open
WHEN: I search for "Auckland apartments" and apply a max price of "$600,000"
THEN: results appear showing apartments in Auckland priced under $600,000
TAGS: smoke, ui, search
SCREEN: property_search
PRIORITY: High
DATA:
  search_term: "Auckland apartments"
  max_price: "$600,000"
  expected_region: "Auckland"
---
""".strip()


class TestReaderAgent(BaseAgent):
    """
    Agent 1 — reads manual test cases and converts to structured format.

    Plan mode (default ON):
      Shows a preview of the first 3 test cases before saving anything.
      User must type APPROVE to save, or REJECT to abort.
    """

    OUTPUT_FILE = "reports/test_cases.txt"

    def run(
        self,
        source_path: str,
        app:         str = "app",
        screen:      str = "",
        plan_mode:   bool = True,
    ) -> str:
        """
        Read source file and convert test cases to structured format.

        Args:
            source_path: path to Excel, CSV, or text file
            app:         app name for context (e.g. "trademe")
            screen:      optional screen filter (e.g. "property_search")
            plan_mode:   if True, show preview and wait for approval

        Returns:
            structured test cases as plain text string
        """
        print(f"\nAgent 1 — Test Reader")
        print(f"Source: {source_path}")
        print(f"App:    {app}  Screen: {screen or 'all'}\n")

        # ── read input ────────────────────────────────────────────
        raw_content = self.read_input(source_path)
        print(f"Read {len(raw_content.splitlines())} lines from source.\n")

        # ── build prompt ──────────────────────────────────────────
        screen_hint = (
            f"\nFocus only on test cases for the '{screen}' screen."
            if screen else ""
        )
        prompt = (
            f"App under test: {app}\n"
            f"{screen_hint}\n\n"
            f"Convert ALL of these manual test cases to structured format:\n\n"
            f"{raw_content}"
        )

        # ── call AI ───────────────────────────────────────────────
        print("Sending to AI for conversion...")
        result = self.call_claude(prompt, SYSTEM_PROMPT)

        # ── plan mode: preview before saving ─────────────────────
        if plan_mode:
            approved = self._plan_mode_review(result)
            if not approved:
                print("Rejected. Nothing saved.")
                return ""

        # ── save output ───────────────────────────────────────────
        self.save_output(result, self.OUTPUT_FILE)
        count = result.count("TEST CASE:")
        print(f"\nAgent 1 complete — {count} test cases saved to {self.OUTPUT_FILE}")
        print("Next: run Agent 2 to generate BDD feature files and steps.\n")
        return result

    # ── plan mode ─────────────────────────────────────────────────

    def _plan_mode_review(self, result: str) -> bool:
        """
        Show first 3 test cases as a preview.
        Wait for APPROVE or REJECT from the user.
        """
        cases  = result.split("---")
        preview = "---".join(cases[:3])

        print("=" * 60)
        print("PLAN MODE — Preview (first 3 test cases)")
        print("=" * 60)
        print(preview.strip())
        print("=" * 60)
        print(f"Total test cases found: {result.count('TEST CASE:')}")
        print("=" * 60)
        print("\nType APPROVE to save all test cases.")
        print("Type REJECT to abort without saving.")

        while True:
            decision = input("\nDecision: ").strip().upper()
            if decision == "APPROVE":
                print("Approved.")
                return True
            elif decision == "REJECT":
                return False
            print("Please type APPROVE or REJECT.")


# ── CLI ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Agent 1: Convert manual test cases to structured format"
    )
    parser.add_argument(
        "--source", required=True,
        help="Path to test case file (.xlsx, .csv, .txt, .md)"
    )
    parser.add_argument(
        "--app", default="app",
        help="App name for context (e.g. trademe)"
    )
    parser.add_argument(
        "--screen", default="",
        help="Optional: filter to specific screen (e.g. property_search)"
    )
    parser.add_argument(
        "--no-plan", action="store_true",
        help="Skip plan mode approval and save immediately"
    )
    args = parser.parse_args()

    agent  = TestReaderAgent()
    result = agent.run(
        source_path = args.source,
        app         = args.app,
        screen      = args.screen,
        plan_mode   = not args.no_plan,
    )

    if not result:
        sys.exit(1)


if __name__ == "__main__":
    main()

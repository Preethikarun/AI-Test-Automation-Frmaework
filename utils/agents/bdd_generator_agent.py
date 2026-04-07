"""
utils/agents/bdd_generator_agent.py  —  Agent 2 (Mode 2 + Mode 3)

Reads structured test cases from Agent 1 output and generates:
  1. Gherkin .feature file
  2. Python step definitions (calls Facade — never PageObjects directly)
  3. Locator skeleton file (empty strings for tester to fill from DevTools)

Plan mode runs first — shows what files will be created and their
content before writing anything. Nothing is saved until you approve.

Workflow:
  Agent 1 output (reports/test_cases.txt)
        ↓
  Agent 2 reads and generates:
        ├── features/{app}_{screen}.feature
        ├── steps/{app}_steps.py
        └── locators/{app}_{screen}_locators.py   ← skeleton only

CLI:
  python -m utils.agents.bdd_generator_agent \\
      --source reports/test_cases.txt \\
      --app trademe \\
      --screen property_search \\
      --facade TradeMeFacade

  # Skip plan mode (useful for CI):
  python -m utils.agents.bdd_generator_agent \\
      --source reports/test_cases.txt \\
      --app trademe --no-plan
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

from utils.agents.base_agent import BaseAgent


# ── system prompts ────────────────────────────────────────────────

FEATURE_SYSTEM = """
You are an expert BDD test automation engineer for a Python Playwright framework.

Generate a complete Gherkin .feature file from the structured test cases provided.

Rules:
- Feature title must describe the screen or functionality being tested
- Use Background for preconditions shared across all scenarios
- Every Scenario must map to exactly one TEST CASE from the input
- Use Scenario Outline with Examples table for data-driven tests
- Tags must match those in the input: @smoke @regression @filter @detail @search @e2e @api
- Use double-quoted parameters in steps: When I search for "Wellington homes"
- Steps must be written so they can be implemented by calling a Facade method
- Do NOT use first-person "I" in Given steps — use passive: "the search page is open"
- Use "I" in When steps: "When I search for..."
- Use "the" in Then steps: "Then the results page shows..."
- Output ONLY the .feature file content — no explanation, no markdown fences
""".strip()

STEPS_SYSTEM = """
You are an expert Python test automation engineer for a Playwright BDD framework.

Generate Python step definitions for a behave BDD framework.

Framework rules (MUST follow):
1. Steps ONLY call the Facade — never PageObjects directly
2. No Playwright calls in steps
3. Use context.tc (TestContext) to pass state between steps
4. Import pattern: from facade.{app}_facade import {Facade}
5. Helper function at top: def _facade(context): return {Facade}(context.page, context.tc)
6. Assertions go in Facade assert_* helpers — never inline assert in steps
   EXCEPTION: simple not-None or not-empty checks are OK inline
7. Store intermediate results on context: context.results, context.listing
8. Every step function name must be unique and snake_case

Output format:
- Full Python file with all imports at top
- Group steps: GIVEN → WHEN → THEN
- Docstring on each step explaining the BDD line it implements
- Output ONLY the Python file content — no explanation, no markdown fences
""".strip()

LOCATOR_SYSTEM = """
You are an expert Python test automation engineer.

Generate a locator skeleton file for a Playwright Page Object Model framework.

Rules:
- Output a single Python dict named {DICT_NAME}
- Dict name = ALL CAPS version of the file name (e.g. TRADEME_SEARCH_LOCATORS)
- Every key is a snake_case string describing what the element does
- Every value is an empty string "" — the tester fills these from DevTools
- Add an inline comment on each key: # inspect: description of where to find it
- Group keys by function with section comments
- Include ALL selectors implied by the test cases
- Selector priority comment at top (data-testid > aria-label > name > CSS class)
- Output ONLY the Python file content — no explanation, no markdown fences
""".strip()


class GeneratedFiles(NamedTuple):
    feature_path:  str
    steps_path:    str
    locator_path:  str
    feature_text:  str
    steps_text:    str
    locator_text:  str


class BDDGeneratorAgent(BaseAgent):
    """
    Agent 2 — generates BDD feature file, steps, and locator skeleton
    from structured test cases produced by Agent 1.
    """

    def run(
        self,
        source_path: str,
        app:         str = "app",
        screen:      str = "screen",
        facade_name: str = "",
        plan_mode:   bool = True,
    ) -> GeneratedFiles | None:
        """
        Generate all three output files from test cases.

        Args:
            source_path:  path to reports/test_cases.txt (Agent 1 output)
            app:          app name slug (e.g. "trademe")
            screen:       screen name slug (e.g. "property_search")
            facade_name:  Facade class name (e.g. "TradeMeFacade")
                          auto-derived from app name if not provided
            plan_mode:    show preview and wait for approval before saving

        Returns:
            GeneratedFiles namedtuple, or None if rejected
        """
        print(f"\nAgent 2 — BDD Generator")
        print(f"Source: {source_path}")
        print(f"App: {app}  Screen: {screen}\n")

        # ── derive names ──────────────────────────────────────────
        if not facade_name:
            facade_name = self._derive_facade_name(app)

        feature_path = f"features/{app}_{screen}.feature"
        steps_path   = f"steps/{app}_steps.py"
        locator_path = f"locators/{app}_{screen}_locators.py"
        dict_name    = f"{app.upper()}_{screen.upper()}_LOCATORS"

        # ── read test cases ───────────────────────────────────────
        test_cases = self.read_input(source_path)
        print(f"Read {test_cases.count('TEST CASE:')} test cases from source.\n")

        # ── generate all three files ──────────────────────────────
        print("Generating Gherkin feature file...")
        feature_text = self._generate_feature(
            test_cases, app, screen
        )

        print("Generating step definitions...")
        steps_text = self._generate_steps(
            test_cases, app, screen, facade_name, feature_text
        )

        print("Generating locator skeleton...")
        locator_text = self._generate_locators(
            test_cases, app, screen, dict_name
        )

        files = GeneratedFiles(
            feature_path = feature_path,
            steps_path   = steps_path,
            locator_path = locator_path,
            feature_text = feature_text,
            steps_text   = steps_text,
            locator_text = locator_text,
        )

        # ── plan mode: preview before saving ─────────────────────
        if plan_mode:
            approved = self._plan_mode_review(files)
            if not approved:
                print("Rejected. Nothing saved.")
                return None

        # ── save all three files ──────────────────────────────────
        self.save_output(feature_text, feature_path)
        self.save_output(steps_text,   steps_path)
        self.save_output(locator_text, locator_path)

        print(f"\nAgent 2 complete — 3 files generated:")
        print(f"  {feature_path}")
        print(f"  {steps_path}")
        print(f"  {locator_path}")
        print(f"\nNext steps:")
        print(f"  1. Fill selector values in {locator_path}")
        print(f"     Open DevTools on your app and inspect each element.")
        print(f"  2. Run: pytest testCases/ -v --headed -m smoke")
        return files

    # ── generators ────────────────────────────────────────────────

    def _generate_feature(
        self,
        test_cases: str,
        app:        str,
        screen:     str,
    ) -> str:
        prompt = (
            f"App: {app}\n"
            f"Screen: {screen}\n\n"
            f"Generate a complete .feature file from these test cases:\n\n"
            f"{test_cases}"
        )
        return self._clean(self.call_claude(prompt, FEATURE_SYSTEM))

    def _generate_steps(
        self,
        test_cases:  str,
        app:         str,
        screen:      str,
        facade_name: str,
        feature_text: str,
    ) -> str:
        prompt = (
            f"App: {app}\n"
            f"Screen: {screen}\n"
            f"Facade class: {facade_name}\n"
            f"Facade import: from facade.{app}_facade import {facade_name}\n\n"
            f"Feature file to implement:\n{feature_text}\n\n"
            f"Original test cases for context:\n{test_cases}\n\n"
            f"Generate complete Python step definitions that implement "
            f"every step in the feature file above."
        )
        return self._clean(self.call_claude(prompt, STEPS_SYSTEM))

    def _generate_locators(
        self,
        test_cases: str,
        app:        str,
        screen:     str,
        dict_name:  str,
    ) -> str:
        prompt = (
            f"App: {app}\n"
            f"Screen: {screen}\n"
            f"Dict name: {dict_name}\n"
            f"File name: {app}_{screen}_locators.py\n\n"
            f"Generate a locator skeleton dict for all UI elements "
            f"referenced in these test cases. "
            f"Every value must be an empty string.\n\n"
            f"{test_cases}"
        )
        text = self._clean(self.call_claude(prompt, LOCATOR_SYSTEM))

        # ensure the file has proper header
        header = (
            f'"""\n'
            f'locators/{app}_{screen}_locators.py\n\n'
            f'Locator skeleton for {app} {screen} screen.\n'
            f'Fill each empty string value from DevTools inspection.\n\n'
            f'Selector priority:\n'
            f'  data-testid > aria-label > name attribute > CSS class\n\n'
            f'Never use auto-generated class names (e.g. sc-abc123).\n'
            f'"""\n\n'
        )
        if dict_name not in text:
            text = header + text
        elif '"""' not in text[:50]:
            text = header + text
        return text

    # ── plan mode ─────────────────────────────────────────────────

    def _plan_mode_review(self, files: GeneratedFiles) -> bool:
        """Show what will be created and wait for APPROVE or REJECT."""
        print("\n" + "=" * 60)
        print("PLAN MODE — Files to be created")
        print("=" * 60)
        print(f"\n1. FEATURE FILE: {files.feature_path}")
        print("-" * 40)
        # show first 30 lines of feature file
        preview_lines = files.feature_text.splitlines()[:30]
        print("\n".join(preview_lines))
        if len(files.feature_text.splitlines()) > 30:
            print("  ... (truncated)")

        print(f"\n2. STEPS FILE: {files.steps_path}")
        print("-" * 40)
        # show first 30 lines of steps
        steps_lines = files.steps_text.splitlines()[:30]
        print("\n".join(steps_lines))
        if len(files.steps_text.splitlines()) > 30:
            print("  ... (truncated)")

        print(f"\n3. LOCATOR SKELETON: {files.locator_path}")
        print("-" * 40)
        print(files.locator_text)

        print("\n" + "=" * 60)
        print("Type APPROVE to save all 3 files.")
        print("Type REJECT to abort without saving.")

        while True:
            decision = input("\nDecision: ").strip().upper()
            if decision == "APPROVE":
                print("Approved.")
                return True
            elif decision == "REJECT":
                return False
            print("Please type APPROVE or REJECT.")

    # ── helpers ───────────────────────────────────────────────────

    @staticmethod
    def _clean(text: str) -> str:
        """Strip markdown code fences the AI sometimes wraps output in."""
        text = text.strip()
        for fence in ("```gherkin", "```python", "```feature", "```"):
            text = text.replace(fence, "")
        return text.strip()

    @staticmethod
    def _derive_facade_name(app: str) -> str:
        """trademe → TradeMeFacade"""
        return "".join(w.capitalize() for w in app.split("_")) + "Facade"


# ── CLI ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Agent 2: Generate BDD feature file, step definitions, "
            "and locator skeleton from structured test cases"
        )
    )
    parser.add_argument(
        "--source", default="reports/test_cases.txt",
        help="Path to structured test cases (default: reports/test_cases.txt)"
    )
    parser.add_argument(
        "--app", default="app",
        help="App name slug (e.g. trademe)"
    )
    parser.add_argument(
        "--screen", default="screen",
        help="Screen name slug (e.g. property_search)"
    )
    parser.add_argument(
        "--facade", default="",
        help="Facade class name (default: derived from --app)"
    )
    parser.add_argument(
        "--no-plan", action="store_true",
        help="Skip plan mode and save immediately"
    )
    args = parser.parse_args()

    agent  = BDDGeneratorAgent()
    result = agent.run(
        source_path = args.source,
        app         = args.app,
        screen      = args.screen,
        facade_name = args.facade,
        plan_mode   = not args.no_plan,
    )

    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()

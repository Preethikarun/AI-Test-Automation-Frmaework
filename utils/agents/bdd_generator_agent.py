"""
utils/agents/bdd_generator_agent.py  —  Agent 2 (Mode 2 + Mode 3)

Reads structured test cases from Agent 1 output and generates:
  1. testCases/features/{app}_{screen}.feature   — Gherkin scenarios
  2. testCases/steps/{app}_steps.py              — step definitions (calls Facade only)
  3. locators/{app}_{screen}_locators.py         — nested dict skeleton (tester fills)

Plan mode runs first — shows all three files before writing anything.
Nothing is saved until you APPROVE.

Before generating, the agent reads the framework's own source files
(CLAUDE.md, utils/actions.py, utils/functions.py, existing facade files)
so it understands which utilities exist and follows the naming conventions.

Workflow:
  Agent 1 output (reports/test_cases.txt)
        ↓
  Agent 2 reads framework context + test cases → generates:
        ├── testCases/features/{app}_{screen}.feature
        ├── testCases/steps/{app}_steps.py
        └── locators/{app}_{screen}_locators.py   ← nested dict, empty strings

CLI:
  python -m utils.agents.bdd_generator_agent \\
      --source reports/test_cases.txt \\
      --app trademe \\
      --screen property_search \\
      --facade TradeMeFacade

  python -m utils.agents.bdd_generator_agent \\
      --source reports/test_cases.txt \\
      --app trademe --no-plan
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NamedTuple

from utils.agents.base_agent import BaseAgent


# ── system prompts ────────────────────────────────────────────────

FEATURE_SYSTEM = """
You are an expert BDD test automation engineer for a Python Playwright framework.

Generate a complete Gherkin .feature file from the structured test cases provided.

CRITICAL VALUE RULES — most important:
1. Copy ALL parameter values VERBATIM from the DATA block of each test case
   e.g. if DATA has  search_term: "Wellington homes"  → step must say: "Wellington homes"
2. NEVER invent, substitute, paraphrase, or round any value
3. Every value in the DATA block MUST appear somewhere in the Gherkin steps or Examples table
4. If DATA has FILL_ME, use a placeholder like "<search_term>" in an Examples column

SCENARIO RULES:
- Feature title describes the screen or functionality
- Use Background: for preconditions shared by ALL scenarios
- Every TEST CASE maps to exactly one Scenario (or one row in Scenario Outline)
- Use Scenario Outline + Examples table when multiple test cases share the same step
  structure but differ only in DATA values — put the values in the Examples table
- Tags come from the TAGS field: @smoke @regression @ui @api @e2e @filter @detail @search
- Given: passive voice — "the property search page is open"
- When:  active voice — "I search for "Wellington homes""
- Then:  state-based  — "search results appear showing properties matching "Wellington homes""
- Use double-quoted strings for all parameters in steps
- Output ONLY the .feature file content — no explanation, no markdown fences
""".strip()

STEPS_SYSTEM = """
You are an expert Python test automation engineer for a Playwright BDD framework.

Generate Python step definitions for a behave BDD framework.

MANDATORY RULES — read the framework context carefully before generating:

1. Steps ONLY call the Facade class — NEVER call PageObjects directly
2. NO Playwright API calls in step definitions (no page.locator, no page.goto)
3. Use context.tc (TestContext) to share state between steps
4. Helper function at the top of the file:
       def _facade(context): return {FacadeClass}(context.page, context.tc)
5. Call Facade assertion helpers for all assertions:
       facade.assert_has_results()
       facade.assert_listing_loaded()
   EXCEPTION: simple None / empty checks may be inline
6. Store intermediate results on context:
       context.results = facade.search_only(term)
       context.listing = facade.search_filter_and_view_detail(...)
7. Use ONLY the Actions and Functions classes for any UI interactions
   (but in steps you call Facade, not Actions or Functions directly)
8. Every step function name must be unique and snake_case
9. Imports at top: behave, facade import, TestContext

IMPORT PATTERN:
    from behave import given, when, then
    from facade.{app}_facade import {FacadeClass}
    from context.test_context import TestContext

Output format:
- Full Python file with all imports at top
- Group steps: GIVEN then WHEN then THEN
- One-line docstring per step explaining the BDD line it implements
- Output ONLY the Python file content — no explanation, no markdown fences
""".strip()

LOCATOR_SYSTEM = """
You are an expert Python test automation engineer for a Playwright Page Object Model.

Generate a locator skeleton file for the framework.

MANDATORY FORMAT — nested dictionary with UI sections as top-level keys:

{APP}_{SCREEN}_LOCATORS = {
    "section_name": {
        "element_key": "",   # //input[@aria-label='...'] or //input[@placeholder='...']
        "element_key": "",   # //button[normalize-space()='Text'] or //*[@data-testid='id']
    },
    "another_section": {
        "element_key": "",   # //*[@data-testid='id'] or //*[@role='list']
    },
}

RULES:
1. ALL CAPS dict name: {APP}_{SCREEN}_LOCATORS
2. Top-level keys = logical UI sections (e.g. "search", "filters", "results", "state")
3. Inner keys = individual element names in snake_case
4. ALL values are EMPTY STRINGS "" — the tester fills from DevTools
5. Each value line has an inline comment with XPath hint showing 1-2 options
6. XPath selector priority (put in file header comment):
       data-testid > aria-label > placeholder > name attribute > stable text > structural XPath
7. NEVER suggest CSS class selectors (no .class-name, no input.something, no div.xyz)
8. NEVER use auto-generated class names (sc-abc123, css-xyz, etc.)
9. Include ALL elements implied by the test cases
10. Output ONLY the Python file content — no explanation, no markdown fences

XPath patterns to use in comments (XPath only — no CSS):
- Text input:      //input[@aria-label='Label'] or //input[@placeholder='hint']
- Named input:     //input[@name='field_name']
- Button by text:  //button[normalize-space()='Text']
- Button by label: //button[@aria-label='Label']
- data-testid:     //*[@data-testid='element-id']
- Select:          //select[@aria-label='Label'] or //select[@name='name']
- Container:       //section[@data-testid='id'] or //*[@role='list']
- First of many:   (//*[@data-testid='card'])[1]
- Dynamic text:    //button[contains(normalize-space(),'result')]
- Role element:    //*[@role='progressbar'] or //*[@role='heading'][@aria-level='1']
""".strip()


DATA_FACTORY_SYSTEM = """
You are a Python developer writing test data for a BDD automation framework.

Generate a Python DataFactory class (or add methods to an existing one) from the
DATA blocks extracted from structured test cases.

RULES:
1. Class name: DataFactory
2. One @staticmethod per screen (e.g. property_search, login, checkout)
3. Method name: {screen}(...)  — snake_case matching the SCREEN field
4. Method returns a dict with keys matching the DATA block keys from the test cases
5. Use the EXACT values from the DATA block as Python default argument values
6. If a DATA value is FILL_ME, use None as the Python default
7. Callers can override any default by passing keyword arguments
8. Include a module-level docstring explaining the class
9. No external dependencies — pure Python standard library only
10. Output ONLY the Python file content — no explanation, no markdown fences

EXAMPLE — correct output for search_term: "Wellington homes", max_price: "$800,000":

class DataFactory:
    \"\"\"Generates deterministic test data. Values match intake test cases exactly.\"\"\"

    @staticmethod
    def property_search(
        search_term: str = "Wellington homes",
        max_price:   str = "$800,000",
        **overrides,
    ) -> dict:
        \"\"\"Test data for the property search screen.\"\"\"
        base = {
            "search_term": search_term,
            "max_price":   max_price,
        }
        return {**base, **overrides}
""".strip()


class GeneratedFiles(NamedTuple):
    feature_path:      str
    steps_path:        str
    locator_path:      str
    data_factory_path: str
    feature_text:      str
    steps_text:        str
    locator_text:      str
    data_factory_text: str


class BDDGeneratorAgent(BaseAgent):
    """
    Agent 2 — generates BDD feature file, step definitions, and locator
    skeleton from structured test cases produced by Agent 1.

    Reads the framework's own source files first so generated code uses
    the existing Actions, Functions, Facade methods and naming conventions.
    """

    def run(
        self,
        source_path:   str,
        app:           str = "app",
        screen:        str = "screen",
        facade_name:   str = "",
        project_root:  str = ".",
        plan_mode:     bool = True,
    ) -> GeneratedFiles | None:
        """
        Generate all three output files from structured test cases.

        Args:
            source_path:   path to reports/test_cases.txt (Agent 1 output)
            app:           app name slug  (e.g. "trademe")
            screen:        screen slug    (e.g. "property_search")
            facade_name:   Facade class name — auto-derived from app if blank
            project_root:  root of the framework project (for context reading)
            plan_mode:     show preview and wait for approval before saving

        Returns:
            GeneratedFiles namedtuple, or None if rejected
        """
        print(f"\nAgent 2 — BDD Generator")
        print(f"Source:  {source_path}")
        print(f"App: {app}  Screen: {screen}\n")

        if not facade_name:
            facade_name = self._derive_facade_name(app)

        # ── output paths (per CLAUDE.md) ──────────────────────────
        feature_path      = f"testCases/features/{app}_{screen}.feature"
        steps_path        = f"testCases/features/steps/{app}_steps.py"
        locator_path      = f"locators/{app}_{screen}_locators.py"
        data_factory_path = f"utils/data_factory.py"
        dict_name         = f"{app.upper()}_{screen.upper()}_LOCATORS"

        # ── read framework context ────────────────────────────────
        print("Reading framework context (CLAUDE.md, utils, facade)...")
        framework_ctx = self.read_framework_context(project_root)
        if framework_ctx:
            print(f"  Loaded {len(framework_ctx)} chars of framework context\n")
        else:
            print("  Warning: no framework context found — generating without it\n")

        # ── read test cases ───────────────────────────────────────
        test_cases = self.read_input(source_path)
        tc_count   = test_cases.count("TEST CASE:")
        print(f"Read {tc_count} test cases from source.\n")

        # ── generate all three files ──────────────────────────────
        print("Generating Gherkin feature file...")
        feature_text = self._generate_feature(
            test_cases, app, screen, framework_ctx
        )

        print("Generating step definitions...")
        steps_text = self._generate_steps(
            test_cases, app, screen, facade_name, feature_text, framework_ctx
        )

        print("Generating locator skeleton...")
        locator_text = self._generate_locators(
            test_cases, app, screen, dict_name, framework_ctx
        )

        print("Generating DataFactory test data...")
        data_factory_text = self._generate_data_factory(
            test_cases, app, screen, framework_ctx
        )

        files = GeneratedFiles(
            feature_path      = feature_path,
            steps_path        = steps_path,
            locator_path      = locator_path,
            data_factory_path = data_factory_path,
            feature_text      = feature_text,
            steps_text        = steps_text,
            locator_text      = locator_text,
            data_factory_text = data_factory_text,
        )

        # ── plan mode: show preview before saving ─────────────────
        if plan_mode:
            approved = self._plan_mode_review(files)
            if not approved:
                print("Rejected. Nothing saved.")
                return None

        # ── save all four files ───────────────────────────────────
        self.save_output(feature_text,      feature_path)
        self.save_output(steps_text,        steps_path)
        self.save_output(locator_text,      locator_path)
        self.save_output(data_factory_text, data_factory_path)

        print(f"\nAgent 2 complete — 4 files generated:")
        print(f"  {feature_path}")
        print(f"  {steps_path}")
        print(f"  {locator_path}")
        print(f"  {data_factory_path}")
        print(f"\nNext steps:")
        print(f"  1. Fill selector values in {locator_path}")
        print(f"     Run:  python scripts/capture_locators.py --all")
        print(f"  2. Review DataFactory values in {data_factory_path}")
        print(f"  3. Run:  behave testCases/features/{app}_{screen}.feature -v")
        return files

    # ── generators ────────────────────────────────────────────────

    def _generate_feature(
        self,
        test_cases:    str,
        app:           str,
        screen:        str,
        framework_ctx: str,
    ) -> str:
        prompt = (
            f"App: {app}\n"
            f"Screen: {screen}\n\n"
            f"Generate a complete .feature file from these test cases:\n\n"
            f"{test_cases}"
            f"{framework_ctx}"
        )
        return self._clean(self.call_claude(prompt, FEATURE_SYSTEM))

    def _generate_steps(
        self,
        test_cases:    str,
        app:           str,
        screen:        str,
        facade_name:   str,
        feature_text:  str,
        framework_ctx: str,
    ) -> str:
        system = STEPS_SYSTEM.replace("{FacadeClass}", facade_name).replace(
            "{app}", app
        )
        prompt = (
            f"App: {app}\n"
            f"Screen: {screen}\n"
            f"Facade class: {facade_name}\n"
            f"Facade import: from facade.{app}_facade import {facade_name}\n\n"
            f"Feature file to implement:\n"
            f"{feature_text}\n\n"
            f"Original test cases for context:\n"
            f"{test_cases}"
            f"{framework_ctx}"
        )
        return self._clean(self.call_claude(prompt, system))

    def _generate_locators(
        self,
        test_cases:    str,
        app:           str,
        screen:        str,
        dict_name:     str,
        framework_ctx: str,
    ) -> str:
        system = LOCATOR_SYSTEM.replace("{APP}", app.upper()).replace(
            "{SCREEN}", screen.upper()
        )
        prompt = (
            f"App: {app}\n"
            f"Screen: {screen}\n"
            f"Dict name: {dict_name}\n"
            f"File name: locators/{app}_{screen}_locators.py\n\n"
            f"Generate a nested locator skeleton dict for all UI elements "
            f"referenced in these test cases. All values must be empty strings.\n\n"
            f"{test_cases}"
            f"{framework_ctx}"
        )
        raw = self._clean(self.call_claude(prompt, system))

        # Ensure module docstring is present
        if not raw.startswith('"""'):
            header = (
                f'"""\n'
                f'locators/{app}_{screen}_locators.py\n\n'
                f'Locator skeleton for {app} — {screen} screen.\n'
                f'Fill each empty string value from DevTools inspection.\n\n'
                f'XPath selector priority:\n'
                f'  data-testid > aria-label > placeholder > name attribute > stable text > structural XPath\n'
                f'Never use CSS class selectors or auto-generated class names.\n'
                f'"""\n\n'
            )
            raw = header + raw
        return raw

    def _generate_data_factory(
        self,
        test_cases:    str,
        app:           str,
        screen:        str,
        framework_ctx: str,
    ) -> str:
        """
        Extract DATA blocks from test cases and generate a DataFactory class.
        Values are taken verbatim from the DATA section — no AI invention.
        """
        prompt = (
            f"App: {app}\n"
            f"Screen: {screen}\n\n"
            f"Extract all DATA blocks from these structured test cases and generate "
            f"a DataFactory class with a @staticmethod for the '{screen}' screen.\n"
            f"Use the EXACT values from the DATA blocks as Python default argument values.\n"
            f"If a DATA value is FILL_ME, use None as the Python default.\n\n"
            f"{test_cases}"
        )
        raw = self._clean(self.call_claude(prompt, DATA_FACTORY_SYSTEM))

        # Ensure module docstring is present
        if not raw.startswith('"""'):
            raw = (
                '"""\n'
                'utils/data_factory.py\n\n'
                'DataFactory — deterministic test data for all screens.\n'
                'Values are extracted verbatim from intake test case files.\n'
                'Override any default by passing keyword arguments.\n\n'
                'Usage:\n'
                '    from utils.data_factory import DataFactory\n'
                '    data = DataFactory.property_search()\n'
                '    data = DataFactory.property_search(search_term="Auckland")\n'
                '"""\n\n'
            ) + raw
        return raw

    # ── plan mode ─────────────────────────────────────────────────

    def _plan_mode_review(self, files: GeneratedFiles) -> bool:
        """Show all four generated files and wait for APPROVE or REJECT."""
        print("\n" + "=" * 60)
        print("PLAN MODE — Files to be written")
        print("=" * 60)

        for label, path, content in [
            ("FEATURE FILE",     files.feature_path,      files.feature_text),
            ("STEP DEFINITIONS", files.steps_path,         files.steps_text),
            ("LOCATOR SKELETON", files.locator_path,       files.locator_text),
            ("DATA FACTORY",     files.data_factory_path,  files.data_factory_text),
        ]:
            print(f"\n{'─'*60}")
            print(f"  {label}: {path}")
            print(f"{'─'*60}")
            lines = content.splitlines()
            for line in lines[:35]:
                print(line)
            if len(lines) > 35:
                print(f"  ... ({len(lines) - 35} more lines)")

        print("\n" + "=" * 60)
        print("Type APPROVE to write all 3 files.")
        print("Type REJECT  to abort without saving.")

        while True:
            decision = input("\nDecision: ").strip().upper()
            if decision == "APPROVE":
                print("Approved.")
                return True
            if decision == "REJECT":
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
        """
        Derive Facade class name from app slug.
        Uses underscore splitting only — if the app name has no underscores
        the result may have wrong casing (trademe → TrademeFacade not TradeMeFacade).
        Always pass --facade explicitly to avoid this ambiguity.
        e.g.  trade_me  → TradeMeFacade  ✓
              trademe   → TrademeFacade   ✗  (use --facade TradeMeFacade)
        """
        derived = "".join(w.capitalize() for w in app.split("_")) + "Facade"
        # Warn if the app name has no underscores — casing may be wrong
        if "_" not in app:
            print(
                f"\n  ⚠  Warning: --app '{app}' has no underscores. "
                f"Derived facade name is '{derived}'.\n"
                f"     If that's wrong (e.g. should be TradeMeFacade), "
                f"re-run with:  --facade TradeMeFacade\n"
            )
        return derived


# ── CLI ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Agent 2: Generate BDD feature, step definitions, "
            "and locator skeleton from structured test cases"
        )
    )
    parser.add_argument(
        "--source", default="reports/test_cases.txt",
        help="Path to structured test cases (default: reports/test_cases.txt)"
    )
    parser.add_argument("--app",    default="app",    help="App name slug (e.g. trademe)")
    parser.add_argument("--screen", default="screen", help="Screen slug (e.g. property_search)")
    parser.add_argument("--facade", default="",       help="Facade class name (derived if omitted)")
    parser.add_argument("--root",   default=".",      help="Project root for reading framework context")
    parser.add_argument("--no-plan", action="store_true", help="Skip plan mode, save immediately")
    args = parser.parse_args()

    agent  = BDDGeneratorAgent()
    result = agent.run(
        source_path  = args.source,
        app          = args.app,
        screen       = args.screen,
        facade_name  = args.facade,
        project_root = args.root,
        plan_mode    = not args.no_plan,
    )

    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()

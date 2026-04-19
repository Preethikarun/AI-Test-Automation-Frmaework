"""
utils/agents/pipeline.py  —  Full Agent 1 → Agent 2 pipeline

One command to go from a plain-text test case file to:
- testCases/features/{app}_{screen}.feature
- testCases/steps/{app}_steps.py
- locators/{app}_{screen}_locators.py

The pipeline:
1. Reads your plain-text test case (any format: .txt, .csv, .xlsx)
2. Agent 1 converts it to structured GIVEN/WHEN/THEN format
3. Agent 2 reads the framework source files (CLAUDE.md, utils/actions.py,
utils/functions.py, existing facades) so it knows exactly what utilities
exist and what naming conventions to follow
4. Agent 2 generates the feature file, step definitions, and locator skeleton
using those existing utilities — no invented helpers
5. Plan mode shows you everything before writing a single file
6. You type APPROVE → files are written

Usage:

# Minimal — provide a text file, app name, and screen name
python -m utils.agents.pipeline \\
    --input my_test_cases.txt \\
    --app trademe \\
    --screen property_search

# With explicit facade name
python -m utils.agents.pipeline \\
    --input intake/login_tests.txt \\
    --app myapp \\
    --screen login \\
    --facade MyAppFacade

# Skip plan mode (for CI or trusted inputs)
python -m utils.agents.pipeline \\
    --input my_test_cases.txt \\
    --app trademe \\
    --screen property_search \\
    --no-plan

# Keep Agent 1 output for inspection
python -m utils.agents.pipeline \\
    --input my_test_cases.txt \\
    --app trademe \\
    --screen property_search \\
    --keep-intermediate

What gets generated:
testCases/features/{app}_{screen}.feature  — Gherkin scenarios
testCases/steps/{app}_steps.py             — step definitions (Facade only)
locators/{app}_{screen}_locators.py        — nested dict skeleton (tester fills)

What the agent reads to guide generation:
CLAUDE.md                   — naming rules, architecture, patterns
utils/actions.py            — all Actions methods the PageObjects use
utils/functions.py          — all Functions methods (accept_cookies, assert_*, etc.)
utils/data_factory.py       — DataFactory methods
context/test_context.py     — TestContext fields
facade/*_facade.py          — existing Facade methods steps must call
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from utils.agents.test_reader_agent import TestReaderAgent
from utils.agents.bdd_generator_agent import BDDGeneratorAgent


def run_pipeline(
    input_path:         str,
    app:                str,
    screen:             str,
    facade_name:        str = "",
    project_root:       str = ".",
    plan_mode:          bool = True,
    keep_intermediate:  bool = False,
) -> bool:
    """
    Run the full Agent 1 → Agent 2 pipeline.

    Args:
        input_path:        path to your test case file (.txt, .csv, .xlsx)
        app:               app name slug (e.g. "trademe")
        screen:            screen name slug (e.g. "property_search")
        facade_name:       Facade class name — derived from app if not given
        project_root:      root of the framework project (default: current dir)
        plan_mode:         if True, show preview and wait for APPROVE before saving
        keep_intermediate: if True, save Agent 1 output to reports/test_cases.txt

    Returns:
        True if pipeline completed and files were saved, False if rejected or failed
    """
    print("\n" + "=" * 60)
    print("AI TEST GENERATION PIPELINE")
    print("=" * 60)
    print(f"Input:   {input_path}")
    print(f"App:     {app}")
    print(f"Screen:  {screen}")
    print(f"Root:    {project_root}")
    print("=" * 60)

    # ── Step 1: Agent 1 — read and structure test cases ──────────
    print("\n[STEP 1/2]  Agent 1 — Reading and structuring test cases...")
    agent1 = TestReaderAgent()

    # Determine intermediate file path
    intermediate_path = (
        f"reports/test_cases_{app}_{screen}.txt"
        if keep_intermediate
        else _temp_path()
    )

    structured = agent1.run(
        source_path = input_path,
        app         = app,
        screen      = screen,
        plan_mode   = plan_mode,  # show Agent 1 preview if plan_mode is on
    )

    if not structured:
        print("\nPipeline aborted at Agent 1 — no structured test cases produced.")
        return False

    # Save structured output so Agent 2 can read it as a file
    out = Path(intermediate_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(structured, encoding="utf-8")

    if keep_intermediate:
        print(f"\nAgent 1 output saved → {intermediate_path}")

    # ── Step 2: Agent 2 — generate BDD + steps + locators ────────
    print("\n[STEP 2/2]  Agent 2 — Generating BDD feature, steps, and locators...")
    agent2 = BDDGeneratorAgent()

    result = agent2.run(
        source_path  = intermediate_path,
        app          = app,
        screen       = screen,
        facade_name  = facade_name,
        project_root = project_root,
        plan_mode    = plan_mode,
    )

    # Clean up temp file if not keeping
    if not keep_intermediate:
        try:
            out.unlink()
        except Exception:
            pass

    if result is None:
        print("\nPipeline aborted at Agent 2 — nothing saved.")
        return False

    # ── Summary ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"\nFiles written:")
    print(f"  {result.feature_path}")
    print(f"  {result.steps_path}")
    print(f"  {result.locator_path}")
    print(f"\nWhat to do next:")
    print(f"  1. Open {result.locator_path}")
    print(f"     Inspect your app in DevTools and fill each empty string selector.")
    print(f"     Priority: data-testid > aria-label > placeholder > name > CSS")
    print(f"  2. Review {result.steps_path}")
    print(f"     Steps call the Facade — add any missing Facade methods if needed.")
    print(f"  3. Run smoke tests:")
    print(f"     pytest testCases/ -v --headed -m smoke")
    print("=" * 60 + "\n")
    return True


def _temp_path() -> str:
    """Return a temporary file path for Agent 1 intermediate output."""
    return str(Path(tempfile.gettempdir()) / "ai_pipeline_test_cases.txt")


# ── CLI ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "AI Test Generation Pipeline: plain text → BDD feature + steps + locators\n\n"
            "Reads your test cases, uses the framework's own source files as context,\n"
            "and generates Gherkin + step definitions that use your existing utilities."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Path to your test case file (.txt, .csv, .xlsx, .md)"
    )
    parser.add_argument(
        "--app", "-a", required=True,
        help="App name slug (e.g. trademe, myapp)"
    )
    parser.add_argument(
        "--screen", "-s", required=True,
        help="Screen name slug (e.g. property_search, login, checkout)"
    )
    parser.add_argument(
        "--facade", "-f", default="",
        help="Facade class name (e.g. TradeMeFacade — derived from --app if omitted)"
    )
    parser.add_argument(
        "--root", "-r", default=".",
        help="Project root directory for reading framework context (default: current dir)"
    )
    parser.add_argument(
        "--no-plan", action="store_true",
        help="Skip plan mode — save files immediately without preview"
    )
    parser.add_argument(
        "--keep-intermediate", action="store_true",
        help="Keep Agent 1 output at reports/test_cases_{app}_{screen}.txt"
    )

    args = parser.parse_args()

    success = run_pipeline(
        input_path        = args.input,
        app               = args.app,
        screen            = args.screen,
        facade_name       = args.facade,
        project_root      = args.root,
        plan_mode         = not args.no_plan,
        keep_intermediate = args.keep_intermediate,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

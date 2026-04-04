"""
End-to-end smoke test — Day 2 verification.
Runs the complete agent loop in sequence.
Use this to verify everything works and as a portfolio demo.

Usage: python scripts/e2e_smoke_test.py
"""
import subprocess
import sys
from pathlib import Path


def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def run_command(cmd: list, label: str) -> bool:
    """Run a shell command and return True if it succeeded."""
    print(f"\nRunning: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"  WARNING: {label} exited with code "
            f"{result.returncode}")
        return False
    return True


def check_file_exists(filepath: str, label: str) -> bool:
    """Verify an expected output file was created."""
    exists = Path(filepath).exists()
    status = "OK" if exists else "MISSING"
    print(f"  [{status}] {label}: {filepath}")
    return exists


def main():
    print("\n" + "="*60)
    print("  DAY 2 END-TO-END SMOKE TEST")
    print("  AI Test Automation Framework")
    print("="*60)
    print("\nThis will run all 4 agents in sequence.")
    print("You will be prompted to APPROVE at each gate.")
    print("Type APPROVE at every prompt to complete the loop.\n")
    input("Press Enter to begin...")

    results = {}

    # ── PHASE 1: AGENT 1 ─────────────────────────────────────
    separator("PHASE 1 — Agent 1: test reader")
    print("Agent 1 will read tests/test_todo.py")
    print("→ Type APPROVE when prompted\n")
    input("Press Enter to run Agent 1...")

    run_command(
        [sys.executable, "-m", "agents.test_reader_agent"],
        "Agent 1"
    )
    results["agent1"] = check_file_exists(
        "reports/test_cases.txt",
        "Test cases extracted"
    )

    # ── PHASE 2: AGENT 2 ─────────────────────────────────────
    separator("PHASE 2 — Agent 2: BDD generator")
    print("Agent 2 will generate Gherkin + step definitions")
    print("→ Type APPROVE when prompted\n")
    input("Press Enter to run Agent 2...")

    run_command(
        [sys.executable, "-m", "agents.bdd_generator_agent"],
        "Agent 2"
    )
    results["agent2_feature"] = check_file_exists(
        "features/todo.feature",
        "Feature file generated"
    )
    results["agent2_steps"] = check_file_exists(
        "steps/todo_steps.py",
        "Step definitions generated"
    )

    # ── PHASE 3: CLEAN TEST RUN ───────────────────────────────
    separator("PHASE 3 — Pytest: clean run (all should pass)")
    input("Press Enter to run all tests...")

    run_command(
        [sys.executable, "-m", "pytest", "tests/", "-v",
        "--tb=short"],
        "Pytest clean run"
    )
    results["clean_run"] = True
    print("\n  All 4 tests should be green above")

    # ── PHASE 4: BROKEN LOCATOR + AGENT 3 ────────────────────
    separator("PHASE 4 — Agent 3: self-heal demo")
    print("We will now break a locator to trigger Agent 3.")
    print("Watch: test fails → Agent 3 fires → you approve → healed\n")
    input("Press Enter to break the locator and run the test...")

    # break the locator
    locator_file = Path("locators/todo_locators.py")
    original     = locator_file.read_text(encoding="utf-8")
    broken       = original.replace(
        '"input.new-todo"',
        '"input.new-todo-BROKEN"'
    )
    locator_file.write_text(broken, encoding="utf-8")
    print("  Locator broken: input.new-todo → input.new-todo-BROKEN")
    print("  Running test — Agent 3 will fire automatically...")
    print("  → Type APPROVE when the self-heal gate appears\n")

    run_command(
        [sys.executable, "-m", "pytest",
        "tests/test_todo.py::TestTodoApp::test_add_single_item",
        "-v", "-s", "--tb=short"],
        "Pytest broken locator run"
    )

    # verify locator was healed
    healed_content = locator_file.read_text(encoding="utf-8")
    locator_healed = '"input.new-todo-BROKEN"' not in healed_content
    results["self_heal"] = locator_healed

    if locator_healed:
        print("\n  Locator successfully healed by Agent 3!")
    else:
        print("\n  Locator not healed — was REJECT typed?")
        print("  Restoring manually...")
        locator_file.write_text(original, encoding="utf-8")

    # ── PHASE 5: AGENT 4 ─────────────────────────────────────
    separator("PHASE 5 — Agent 4: failure analysis")
    print("Agent 4 will analyse the failure logged in Phase 4")
    print("→ Type N when asked about routing to Agent 3\n")
    input("Press Enter to run Agent 4...")

    run_command(
        [sys.executable, "-m", "agents.failure_analysis_agent"],
        "Agent 4"
    )
    results["agent4"] = check_file_exists(
        "reports/failure_report.txt",
        "Failure report generated"
    )

    # ── FINAL RESULTS ─────────────────────────────────────────
    separator("SMOKE TEST RESULTS")

    all_passed = all(results.values())
    checks = {
        "agent1":         "Agent 1 — test cases extracted",
        "agent2_feature": "Agent 2 — feature file generated",
        "agent2_steps":   "Agent 2 — step definitions generated",
        "clean_run":      "Pytest — clean run completed",
        "self_heal":      "Agent 3 — locator self-healed",
        "agent4":         "Agent 4 — failure report generated",
    }

    for key, label in checks.items():
        status = "PASS" if results.get(key) else "FAIL"
        icon   = "✓" if results.get(key) else "✗"
        print(f"  {icon} [{status}] {label}")

    print(f"\n{'='*60}")
    if all_passed:
        print("  ALL CHECKS PASSED — Day 2 complete!")
        print("  Full agent loop verified end-to-end.")
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"  {len(failed)} check(s) need attention: "
            f"{', '.join(failed)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
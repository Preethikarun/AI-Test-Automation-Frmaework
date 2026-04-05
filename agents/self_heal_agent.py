"""Agent 3 — Self-Healing Locator Repair (Mode 5)
Triggered by TimeoutError during test runs.
Receives broken locator + page HTML, suggests a fix,
shows a diff, patches locator file on approval.

No plan mode — this is a scoped surgical fix.
Usage: called automatically from conftest.py or manually:
python -m agents.self_heal_agent
"""
import re
from pathlib import Path
from agents.base_agent import BaseAgent

MOCK_MODE = True  # set False when API key is ready


class SelfHealAgent(BaseAgent):

    SYSTEM_PROMPT = """You are an expert Playwright test engineer
specialising in CSS selectors and locator strategies.
You analyse broken locators and suggest reliable replacements
based on the current page HTML.
Always prefer: data-testid > aria roles > CSS classes > XPath."""

    def suggest_fix(
        self,
        broken_locator: str,
        locator_key: str,
        page_html: str
    ) -> dict:
        """
        Analyse broken locator against page HTML.
        Returns dict with suggested fix and reasoning.
        """
        if MOCK_MODE:
            print("  [mock mode] suggesting locator fix")
            return {
                "broken": broken_locator,
                "suggested": broken_locator.replace("-BROKEN", ""),
                "reason": "Mock fix: removed -BROKEN suffix from"
                "selector",
                "confidence": "high"
            }

        prompt = f"""A Playwright test is failing with TimeoutError.
The locator cannot find an element on the page.

Broken locator key: {locator_key}
Broken locator value: {broken_locator}

Current page HTML (relevant section):
{page_html[:3000]}

Task:
1. Find what element broken locator was targeting
2. Identify best alternative selector in current HTML
3. Return answer as JSON with these exact keys:
   - broken: original broken selector
   - suggested: recommended replacement selector
   - reason: one sentence explaining why it broke
   - confidence: high / medium / low

Return ONLY valid JSON. No explanation outside JSON."""

        response = self.call_claude(prompt, self.SYSTEM_PROMPT)

        # parse JSON response
        import json
        try:
            # strip markdown code blocks if present
            clean = re.sub(r"```json|```", "", response).strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            return {
                "broken":    broken_locator,
                "suggested": broken_locator,
                "reason":    "Could not parse AI response",
                "confidence": "low"
            }

    def show_diff(
        self,
        fix: dict,
        locator_key: str,
        locator_file: str
    ):
        """Display a clear before/after diff for review."""
        print("\n" + "="*60)
        print("AGENT 3 — SELF-HEAL SUGGESTION")
        print("="*60)
        print(f"File:    {locator_file}")
        print(f"Key:     {locator_key}")
        print(f"Reason:  {fix['reason']}")
        print(f"Confidence: {fix['confidence']}")
        print("\nDIFF:")
        print(f"  - \"{locator_key}\": \"{fix['broken']}\",")
        print(f"  + \"{locator_key}\": \"{fix['suggested']}\",")
        print("="*60)

    def patch_locator_file(
        self,
        locator_file: str,
        locator_key: str,
        broken: str,
        suggested: str
    ) -> bool:
        """
        Patch the locator file — replace broken with suggested.
        Uses simple string replacement — safe and predictable.
        """
        path = Path(locator_file)
        if not path.exists():
            print(f"  Locator file not found: {locator_file}")
            return False

        content = path.read_text(encoding="utf-8")

        # Replace the broken locator value
        old_line = f'"{locator_key}": "{broken}"'
        new_line = f'"{locator_key}": "{suggested}"'

        if old_line not in content:
            print(f"  Could not find '{old_line}' in {locator_file}")
            print("  File not modified.")
            return False

        patched = content.replace(old_line, new_line)
        path.write_text(patched, encoding="utf-8")
        print(f"  Patched: {locator_file}")
        return True

    def run(
        self,
        broken_locator: str,
        locator_key: str,
        page_html: str,
        locator_file: str = "locators/todo_locators.py"
    ):
        """
        Full self-heal run.
        Plan: analyse -> suggest -> diff -> approve -> patch -> commit
        """
        print("\nAgent 3 — self-heal triggered")
        print(f"  Broken locator: {locator_key} = '{broken_locator}'")

        # Step 1: get AI suggestion
        print("  Analysing page HTML for fix...")
        fix = self.suggest_fix(
            broken_locator, locator_key, page_html
        )

        # Step 2: show diff
        self.show_diff(fix, locator_key, locator_file)

        # Step 3: approval gate
        self._approval_gate(fix, locator_key, locator_file)

    def _approval_gate(
        self,
        fix: dict,
        locator_key: str,
        locator_file: str
    ):
        """Scoped approval — patch this one locator or skip."""
        while True:
            print("\nSELF-HEAL APPROVAL")
            print("  APPROVE — apply patch and commit")
            print("  REJECT  — skip, log for failure analysis")
            decision = input("\n> ").strip().upper()

            if decision == "APPROVE":
                patched = self.patch_locator_file(
                    locator_file,
                    locator_key,
                    fix["broken"],
                    fix["suggested"]
                )
                if patched:
                    self._git_commit(
                        locator_file,
                        f"fix: Agent 3 self-heal — "
                        f"'{locator_key}' locator repaired"
                    )
                    print("\nLocator patched and committed!")
                return

            elif decision == "REJECT":
                print("Skipped — locator unchanged.")
                print("Failure will be logged for Agent 4 analysis.")
                return

            else:
                print("  Please type APPROVE or REJECT")

    def _git_commit(self, filepath: str, message: str):
        """Commit patched locator file."""
        import subprocess
        try:
            subprocess.run(
                ["git", "add", filepath],
                check=True, capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", message],
                check=True, capture_output=True
            )
            print(f"  Git commit: {message}")
        except subprocess.CalledProcessError as e:
            print(f"  Git commit skipped: {e}")


def main():
    """
    Manual test run — simulates a TimeoutError scenario.
    In real use this is called from conftest.py automatically.
    """
    agent = SelfHealAgent()

    # Simulate a broken locator scenario
    agent.run(
        broken_locator="input.new-todo-BROKEN",
        locator_key="new_input",
        page_html="<input class='new-todo'></input>",
        locator_file="locators/todo_locators.py"
    )


if __name__ == "__main__":
    main()

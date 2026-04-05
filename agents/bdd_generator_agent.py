"""
Agent 2 — BDD Generator (Mode 2+3)
Reads plain-English test cases from Agent 1 output and
generates Gherkin feature files + Python step definitions.
Approval gate covers both files — approve or reject together.

Usage: python -m agents.bdd_generator_agent
"""
from pathlib import Path
from agents.base_agent import BaseAgent

MOCK_MODE = False  # set False when API key is ready and True when its not Ready

MOCK_FEATURE = """Feature: Todo application
As a user
I want to manage my daily tasks
So that I can stay organised

@smoke @ui
Scenario: Add a single todo item
    Given the todo app is open
    When I add a todo item "Build AI test framework"
    Then the todo count shows 1
    And the item "Build AI test framework" is visible

@regression @ui
Scenario: Add multiple todo items
    Given the todo app is open
    When I add a todo item "Day 1 foundation"
    And I add a todo item "Day 2 AI agents"
    And I add a todo item "Day 3 CI/CD"
    Then the todo count shows 3

@regression @ui
Scenario: Complete a todo item
    Given the todo app is open
    And I add a todo item "Complete me"
    When I complete todo item 1
    Then the todo count shows 0

@regression @ui
Scenario: Delete a todo item
    Given the todo app is open
    And I add a todo item "Delete me"
    And I add a todo item "Keep me"
    When I delete todo item 1
    Then the item "Delete me" is not visible
    And the item "Keep me" is visible"""


MOCK_STEPS = '''from behave import given, when, then
from pages.todo_page import TodoPage


def get_todo(context):
    """Helper — get or create TodoPage instance."""
    if not hasattr(context, "todo"):
        context.todo = TodoPage(context.page)
    return context.todo


@given("the todo app is open")
def step_open_app(context):
    todo = get_todo(context)
    todo.navigate()


@when(\'I add a todo item "{text}"\')
def step_add_item(context, text):
    get_todo(context).add_item(text)


@when("I complete todo item {index:d}")
def step_complete_item(context, index):
    get_todo(context).complete_item(index - 1)


@when("I delete todo item {index:d}")
def step_delete_item(context, index):
    get_todo(context).delete_item(index - 1)


@then("the todo count shows {count:d}")
def step_check_count(context, count):
    actual = get_todo(context).get_item_count()
    assert actual == count, (
        f"Expected count {count} but got {actual}"
    )

@then(\'the item "{text}" is visible\')
def step_item_visible(context, text):
    assert get_todo(context).is_item_visible(text), (
        f"Item \'{text}\' not visible"
    )


@then(\'the item "{text}" is not visible\')
def step_item_not_visible(context, text):
    assert not get_todo(context).is_item_visible(text), (
        f"Item \'{text}\' should not be visible"
    )'''


class BDDGeneratorAgent(BaseAgent):

    SYSTEM_PROMPT = """You are an expert BDD test engineer.
You convert plain-English test cases into professional
Gherkin feature files and Python behave step definitions.
Follow BDD best practices — business-readable scenarios,
reusable steps, proper Given/When/Then structure."""

    def read_skill(self, skill_file: str) -> str:
        """Read a skill file to guide code generation."""
        path = Path(f"skills/{skill_file}")
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""  # skill optional — agent continues without it

    def read_test_cases(self,
                        filepath: str = "reports/test_cases.txt"
                        ) -> str:
        """Read Agent 1 output — plain-English test cases."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(
                f"Test cases not found: {filepath}\n"
                "Run Agent 1 first: python -m agents.test_reader_agent"
            )
        return path.read_text(encoding="utf-8")

    def generate_feature(self, test_cases: str) -> str:
        """Generate Gherkin .feature file from test cases."""
        if MOCK_MODE:
            print("  [mock mode] generating feature file")
            return MOCK_FEATURE

        skill = self.read_skill("BDD_SKILL.md")
        prompt = f"""Convert these plain-English test cases into a
professional Gherkin feature file.

Rules:
- Use Feature, Background (if needed), Scenario
- Tag each scenario with @smoke or @regression and @ui
- Use concrete examples in scenario names
- Keep steps reusable across scenarios
- Use parameters in quotes for dynamic values
- Follow this BDD skill guide:
{skill}

Test cases:
{test_cases}

Return ONLY the Gherkin feature file content.
No explanation, no markdown code blocks."""

        return self.call_claude(prompt, self.SYSTEM_PROMPT)

    def generate_steps(self, feature_content: str) -> str:
        """Generate Python behave step definitions."""
        if MOCK_MODE:
            print("  [mock mode] generating step definitions")
            return MOCK_STEPS

        prompt = f"""Write Python behave step definitions for this
Gherkin feature file.

Rules:
- Import from behave: given, when, then
- Import TodoPage from pages.todo_page
- Use context.todo to hold the page object
- Add a get_todo(context) helper function
- Handle integer with parameter indices like 1, 2
- Handle string with parameter values like \"todo text\"
- Add clear assertion messages on failure

Feature file:
{feature_content}

Return ONLY the Python code. No explanation."""

        return self.call_claude(prompt, self.SYSTEM_PROMPT)

    def show_preview(self, feature: str, steps: str):
        """Show both generated files for review."""
        print("\n" + "="*60)
        print("AGENT 2 — BDD GENERATOR OUTPUT")
        print("="*60)
        print("\n--- features/todo.feature ---")
        print(feature)
        print("\n--- steps/todo_steps.py ---")
        print(steps)
        print("="*60)

    def run(self, test_cases_file: str = "reports/test_cases.txt"):
        """
        Full agent run with approval gate.
        Plan: read → generate feature → generate steps
            → preview both → approve → save both → commit
        """
        print("\nAgent 2 starting — reading test cases...")

        # Step 1: read Agent 1 output
        test_cases = self.read_test_cases(test_cases_file)
        print(f"  Read test cases from {test_cases_file}")

        # Step 2: generate feature file
        print("  Generating Gherkin feature file...")
        feature = self.generate_feature(test_cases)

        # Step 3: generate step definitions
        print("  Generating step definitions...")
        steps = self.generate_steps(feature)

        # Step 4: preview both files
        self.show_preview(feature, steps)

        # Step 5: approval gate
        self._approval_gate(feature, steps)

    def _approval_gate(self, feature: str, steps: str):
        """
        Approve or reject BOTH files together.
        One decision covers feature file + step definitions.
        """
        while True:
            print("\nAPPROVAL GATE — reviewing 2 files:")
            print("  features/todo.feature")
            print("  steps/todo_steps.py")
            print("\n  Type APPROVE to save both and commit")
            print("  Type REJECT  to discard both")
            print("  Type IMPROVE to regenerate with feedback")
            decision = input("\n> ").strip().upper()

            if decision == "APPROVE":
                # Save both files
                self.save_output(feature, "features/todo.feature")
                self.save_output(steps, "steps/todo_steps.py")
                self._git_commit(
                    ["features/todo.feature", "steps/todo_steps.py"],
                    "feat: Agent 2 — BDD feature file and "
                    "step definitions generated"
                )
                print("\nApproved! Both files saved and committed.")
                return

            elif decision == "REJECT":
                print("Rejected — both files discarded.")
                return

            elif decision == "IMPROVE":
                feedback = input(
                    "What should be improved? > "
                ).strip()
                if MOCK_MODE:
                    msg = (
                        "[mock mode] IMPROVE is a no-op — "
                        "disable MOCK_MODE to use real feedback"
                    )
                    print(f"  {msg}")
                print(f"  Regenerating with: {feedback}")
                feature = self.generate_feature(
                    f"Feedback: {feedback}\n"
                    f"Previous feature:\n{feature}"
                )
                steps = self.generate_steps(feature)
                self.show_preview(feature, steps)

            else:
                print("  Please type APPROVE, REJECT or IMPROVE")

    def _git_commit(self, filepaths: list, message: str):
        """Commit multiple approved files to git."""
        import subprocess
        try:
            for fp in filepaths:
                subprocess.run(
                    ["git", "add", fp],
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
    agent = BDDGeneratorAgent()
    agent.run("reports/test_cases.txt")


if __name__ == "__main__":
    main()

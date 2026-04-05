"""
Agent 1 — Test Reader (Mode 1)
Reads existing Python test files and converts them
to structured plain-English test cases.
Includes approval gate — nothing saves without your sign-off.

Usage: python -m agents.test_reader_agent
"""
from pathlib import Path
from agents.base_agent import BaseAgent

MOCK_MODE = False  # set False when API key is ready

MOCK_OUTPUT = """TEST CASE: Add a single todo item
GIVEN: The Todo app is open and the list is empty
WHEN: User types "Build AI test framework" and presses Enter
THEN: One item appears in the list and counter shows 1
TAGS: smoke, ui
---
TEST CASE: Add multiple todo items
GIVEN: The Todo app is open and the list is empty
WHEN: User adds 3 items sequentially
THEN: All 3 items appear and counter shows 3
TAGS: regression, ui
---
TEST CASE: Complete a todo item
GIVEN: One uncompleted item exists in the list
WHEN: User clicks the checkbox next to the item
THEN: Item is marked complete and active counter shows 0
TAGS: regression, ui
---
TEST CASE: Delete a todo item
GIVEN: Two items exist in the list
WHEN: User hovers first item and clicks the destroy button
THEN: First item is removed, second item remains visible
TAGS: regression, ui"""


class TestReaderAgent(BaseAgent):

    SYSTEM_PROMPT = """You are an expert test analyst.
You read Python Playwright test code and extract
each test as a structured plain-English test case.
Be precise, concise and consistent in your format."""

    def read_test_file(self, filepath: str) -> str:
        """Read a Python test file and return its contents."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Test file not found: {filepath}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def extract_test_cases(self, test_code: str) -> str:
        """Send test code to AI and get structured test cases back."""
        if MOCK_MODE:
            print("  [mock mode] generating test cases from file content")
            # In mock mode — generate basic structure from
            # the actual file content so output matches the source
            lines = [l.strip() for l in test_code.splitlines()
                    if l.strip() and not l.strip().startswith("#")]
            mock_cases = []
            for i, line in enumerate(lines[:4], 1):
                mock_cases.append(
                    f"TEST CASE: {line[:60]}\n"
                    f"GIVEN: The application is in the correct state\n"
                    f"WHEN: {line[:80]}\n"
                    f"THEN: The expected result is achieved\n"
                    f"TAGS: regression, ui\n"
                    f"SOURCE: {self._current_source}\n"
                    f"---"
                )
            return "\n".join(mock_cases) if mock_cases else MOCK_OUTPUT

        prompt = f"""Read this file and extract each test case
in this exact format:

TEST CASE: [descriptive name]
GIVEN: [starting state / precondition]
WHEN: [action performed]
THEN: [expected result]
TAGS: [smoke | regression | ui | api]
SOURCE: [the filename]
---

File contents:
{test_code}"""

        return self.call_claude(prompt, self.SYSTEM_PROMPT)

    def show_preview(self, test_cases: str, source_file: str):
        """Print a formatted preview for the approval gate."""
        print("\n" + "="*60)
        print("AGENT 1 — TEST READER OUTPUT")
        print(f"Source: {source_file}")
        print("="*60)
        print(test_cases)
        print("="*60)

    def run(self, test_file: str = "tests/test_todo.py"):
        """
        Full agent run with approval gate.
        Plan: read → extract → preview → approve → save → commit
        """
        self._current_source = test_file
        print(f"\nAgent 1 starting — reading {test_file}")

        # Step 1: read the test file
        test_code = self.read_test_file(test_file)
        print(f"  Read {len(test_code)} characters from {test_file}")

        # Step 2: extract test cases via AI
        print("  Extracting test cases...")
        test_cases = self.extract_test_cases(test_code)

        # Step 3: show preview for approval
        self.show_preview(test_cases, test_file)

        # Step 4: approval gate
        output = self._approval_gate(test_cases, test_file)
        return output

    def _approval_gate(self, test_cases: str, source_file: str) -> str | None:
        """
        Human-in-the-loop approval gate.
        Nothing gets saved or committed without explicit approval.
        """
        while True:
            print("\nAPPROVAL GATE")
            print("  Type APPROVE to save and commit")
            print("  Type REJECT  to discard")
            print("  Type IMPROVE to regenerate with feedback")
            decision = input("\n> ").strip().upper()

            if decision == "APPROVE":
                output_path = "reports/test_cases.txt"
                self.save_output(test_cases, output_path)
                self._git_commit(
                    output_path,
                    "feat: Agent 1 — extracted "
                    f"test cases from {source_file}"
                )
                print("\nApproved and committed!")
                return test_cases

            elif decision == "REJECT":
                print("Rejected — output discarded. Nothing committed.")
                return None

            elif decision == "IMPROVE":
                feedback = input(
                    "What should be improved? > "
                ).strip()
                print(f"  Regenerating with feedback: {feedback}")
                # In live mode: re-call AI with feedback appended
                # In mock mode: return same output
                test_cases = self.extract_test_cases(
                    f"Previous output feedback: {feedback}\n"
                    f"Original test cases:\n{test_cases}"
                )
                self.show_preview(test_cases, source_file)

            else:
                print("  Please type APPROVE, REJECT or IMPROVE")

    def _git_commit(self, filepath: str, message: str):
        """Commit approved output to git."""
        import subprocess
        try:
            subprocess.run(
                ["git", "add", filepath], check=True, capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", message],
                check=True, capture_output=True
            )
            print(f"  Git commit: {message}")
        except subprocess.CalledProcessError as e:
            print(f"  Git commit skipped: {e}")


def main():
    import argparse

    # parse --source argument
    parser = argparse.ArgumentParser(
        description="Agent 1 — reads any test source file"
    )
    parser.add_argument(
        "--source",
        default="tests/test_todo.py",
        help="Path to the file to read (py, txt, xlsx, docx)"
    )
    args = parser.parse_args()

    agent = TestReaderAgent()
    agent.run(args.source)


if __name__ == "__main__":
    main()

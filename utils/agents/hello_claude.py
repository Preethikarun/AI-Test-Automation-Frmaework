"""Hello Claude — Day 1 verification agent.
Reads test_todo.py and extracts plain-English test cases.
Run: python agents/hello_claude.py
Inherits everything from BaseAgent — including call_claude()
and save_output().
"""
from utils.agents.base_agent import BaseAgent


class HelloClaudeAgent(BaseAgent):

    SYSTEM_PROMPT = """You are an expert test analyst.
You read Python Playwright test code and extract
each test as a structured plain-English test case.
Be precise and concise."""

    def extract_test_cases(self, test_file_path: str) -> str:
        """Read a test file and return structured test cases."""

        with open(test_file_path, "r", encoding="utf-8") as f:
            test_code = f.read()

        prompt = f"""Read this Playwright test file and extract
each test as a plain-English test case.

Use exactly this format for each test:

TEST CASE: [descriptive name]
GIVEN: [starting state / precondition]
WHEN: [action performed]
THEN: [expected result]
TAGS: [smoke | regression | ui]
---

Test file contents:
{test_code}"""

        print("Sending to Claude...")
        result = self.call_claude(prompt, self.SYSTEM_PROMPT)
        return result


def main():
    agent = HelloClaudeAgent()

    # Read your existing test file
    test_cases = agent.extract_test_cases("tests/test_todo.py")

    # Print to terminal
    print("\n" + "="*50)
    print("EXTRACTED TEST CASES")
    print("="*50)
    print(test_cases)

    # Save to reports/
    agent.save_output(
        test_cases,
        "reports/extracted_test_cases.txt"
    )
    print("\nDay 1 complete — Claude AI is connected and working!")


if __name__ == "__main__":
    main()

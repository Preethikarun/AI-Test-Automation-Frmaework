# USER_STORIES.md
# AI Test Automation Framework — User Stories

*Each of the 6 framework modes is written as a PM user story with
acceptance criteria and definition of done. This is how a product
manager thinks about features — not as technical tasks but as user
outcomes.*

---

## How to read these stories

**Format:**
> As a [persona], I want to [action], so that [outcome / benefit].

**Acceptance criteria:** The specific conditions that must be true
for the story to be considered done. Testable. Unambiguous.

**Definition of done:** The quality checklist every story must pass
before it is considered shippable. Applies to all stories equally.

---

## Global Definition of Done

Every story is done when ALL of the following are true:

- [ ] The feature works end-to-end from the project root
- [ ] MOCK_MODE=True works — full workflow without API credits
- [ ] Approval gate fires — APPROVE saves, REJECT discards
- [ ] Git commit is created automatically on APPROVE
- [ ] Commit message follows feat:/fix: convention
- [ ] The agent inherits from BaseAgent — no duplicated client code
- [ ] Docstring exists on every class and public method
- [ ] Type hints exist on every method signature
- [ ] A "Python lesson" comment explains any non-obvious pattern
- [ ] The run command is documented in CLAUDE.md section 11
- [ ] Unit tested manually with 3 different inputs before ship

---

## Story 1 — Test Reader (Mode 1)

**As a** test automation engineer with a backlog of manual test cases
written in Excel,

**I want to** drop an Excel file into the `intake/manual/` folder and
have an AI agent read it and produce structured GIVEN/WHEN/THEN test
cases,

**so that** I can skip the mechanical transcription step and spend my
time reviewing and approving the output instead of writing it.

### Acceptance criteria

- [ ] Agent accepts `.py`, `.xlsx`, `.docx`, and `.txt` files
- [ ] Agent detects file type automatically from the extension
- [ ] Output always follows the standard format regardless of input:
      TEST CASE / GIVEN / WHEN / THEN / TAGS / PRIORITY / SOURCE
- [ ] Source field shows which file the test case came from
- [ ] Output is shown in terminal for review before saving
- [ ] Approval gate fires with APPROVE / REJECT / IMPROVE options
- [ ] APPROVE saves output to `reports/test_cases.txt`
- [ ] APPROVE creates a git commit with the output file
- [ ] REJECT discards the output — nothing is saved or committed
- [ ] IMPROVE asks for feedback and regenerates with that feedback
- [ ] Agent runs in under 30 seconds in mock mode
- [ ] Agent runs in under 2 minutes in live AI mode

### Notes for PM
The key insight here is that the input format should not matter to
the user. Whether they have a Pytest script, an Excel sheet, or a
plain text document — the experience is identical: drop it in
`intake/`, run the agent, approve the output. The agent absorbs the
format complexity.

---

## Story 2+3 — BDD Generator (Modes 2 and 3)

**As a** test automation engineer who needs to write Gherkin feature
files for a new feature,

**I want to** have an AI agent read the plain-English test cases from
Story 1 and generate a complete `.feature` file and matching Python
step definitions,

**so that** I have working BDD automation I can review and approve
rather than starting from a blank file.

### Acceptance criteria

- [ ] Agent reads `reports/test_cases.txt` from Agent 1 output
- [ ] Agent generates a `.feature` file with proper Gherkin syntax:
      Feature / Background / Scenario / Given / When / Then / And
- [ ] Agent generates matching step definitions in Python with
      behave decorators, helper function, and assertion messages
- [ ] Feature file tags match the TAGS field from test cases:
      @smoke or @regression, plus @ui or @api
- [ ] Agent reads `skills/BDD_SKILL.md` before generating
      to ensure conventions are followed
- [ ] Both files are shown in terminal for review together
- [ ] ONE approval gate covers both files — approve or reject both
- [ ] APPROVE saves `features/todo.feature` AND `steps/todo_steps.py`
- [ ] APPROVE creates ONE git commit covering both files
- [ ] Generated step definitions use the `get_{page}(context)` helper
      pattern from BDD_SKILL.md
- [ ] Integer parameters use `{count:d}`, strings use `"{text}"`
- [ ] IMPROVE regenerates both files with feedback applied

### Notes for PM
The single approval gate for two files is a deliberate product
decision. Feature files and step definitions are always a pair —
approving one without the other leaves the framework in a broken
state. One decision, two files, one commit.

---

## Story 4 — New Test Case (Mode 4)

**As a** test automation engineer adding a single new test to an
existing test class,

**I want to** describe the new test in plain English and have the AI
add a correctly formatted pytest method to the existing class,

**so that** I don't have to remember the exact test structure,
marker conventions, and assertion patterns every time I add a test.

### Acceptance criteria

- [ ] Mode 4 does NOT run plan mode — no overhead for simple additions
- [ ] Agent identifies the correct existing test class to add to
- [ ] Agent generates a method with correct PascalCase class,
      snake_case method name, and docstring
- [ ] Generated method has exactly TWO markers: category + type
- [ ] Generated method follows Arrange / Act / Assert structure
- [ ] Approval gate fires before the method is added to the file
- [ ] APPROVE patches the existing test file — does not rewrite it
- [ ] APPROVE creates a git commit: `test: Agent 4 — added [test name]`
- [ ] The new test runs successfully with `pytest` after approval

### Notes for PM
Mode 4 deliberately skips plan mode. The overhead of planning
is only justified for complex multi-file generation (Modes 1, 2, 3).
Adding one test method to an existing class is a scoped, low-risk
operation. Removing friction here increases adoption.

---

## Story 5 — Self-Healing Locator (Mode 5)

**As a** test automation engineer whose tests are failing because a
UI change broke a CSS selector,

**I want** the framework to automatically detect the broken locator,
suggest a replacement using the current page HTML, show me a clear
diff, and patch the locator file when I approve,

**so that** I spend seconds approving a fix rather than hours
debugging a broken selector hunt across multiple files.

### Acceptance criteria

- [ ] Agent fires automatically when a `TimeoutError` occurs in pytest
- [ ] Agent extracts the broken selector from the error message
- [ ] Agent captures the current page HTML at the moment of failure
- [ ] Agent sends broken selector + page HTML to Claude/Gemini
- [ ] Agent shows a clear before/after diff in the terminal:
        - "old_key": "old-selector",
        + "old_key": "new-selector",
- [ ] Agent shows confidence level: high / medium / low
- [ ] Agent shows one-line reason: "Original selector no longer found"
- [ ] Approval gate fires with APPROVE / REJECT (no IMPROVE — scoped)
- [ ] APPROVE patches the locator file using regex — handles any spacing
- [ ] APPROVE creates a git commit: `fix: Agent 3 self-heal — 'key' repaired`
- [ ] REJECT logs the failure to `reports/failures.json` for Agent 4
- [ ] Patched test passes on next pytest run without any other changes
- [ ] Agent can also be run manually: `python -m agents.self_heal_agent`

### Notes for PM
Mode 5 has NO plan mode by design. Self-healing is a surgical,
scoped operation with a single well-defined output: one locator
replaced. Plan mode adds overhead without adding safety — the diff
IS the plan. The approval gate IS the safety net.

---

## Story 6 — Failure Analysis (Mode 6)

**As a** test automation engineer or QA lead looking at a failed
CI run,

**I want** an AI agent to read the structured failure log, classify
each failure by type, explain the root cause in plain English, and
tell me what to do to fix it,

**so that** I spend minutes reading an actionable report rather than
hours reading stacktraces and guessing at causes.

### Acceptance criteria

- [ ] Agent reads `reports/failures.json` automatically after test run
- [ ] Agent classifies each failure into one of four categories:
      locator / logic / flaky / environment
- [ ] Agent generates a plain-English root cause for each failure
- [ ] Agent provides specific, actionable fix steps (not vague advice)
- [ ] Agent assigns priority: high / medium / low to each failure
- [ ] Agent generates a SUMMARY section with failure counts by category
- [ ] Agent identifies patterns: "3 locator failures in the same page
      object suggests a recent UI change to that page"
- [ ] Agent saves report to `reports/failure_report.txt`
- [ ] Agent offers to route locator failures directly to Agent 3
- [ ] No approval gate — this is read-only analysis, nothing is committed
- [ ] Report is readable by a non-technical delivery manager
- [ ] Report generates in under 60 seconds in live AI mode

### Acceptance criteria specific to the continuous loop
- [ ] `conftest.py` writes a failure record to `failures.json` on
      every test failure — automatically, no manual step
- [ ] Each failure record includes: timestamp, test name, error type,
      error message, category, broken locator (if applicable),
      screenshot path, healed status
- [ ] Agent 4 can be run immediately after any test run:
      `python -m agents.failure_analysis_agent`

### Notes for PM
Mode 6 is the only mode with no approval gate. This is intentional.
Failure analysis is read-only — it cannot modify files or commit code.
There is no risk in running it automatically. In v2, this agent will
run automatically as a post-test step in the CI pipeline, posting
the report summary to a Slack channel or GitHub PR comment.

---

## Cross-cutting story — The approval gate

**As a** QA lead responsible for the integrity of our test codebase,

**I want** every AI-generated file to require my explicit approval
before it is saved or committed,

**so that** AI accelerates our work without creating unreviewed
changes in our shared codebase.

### Acceptance criteria

- [ ] Every Mode 1, 2, 3, 4, 5 agent shows output before saving
- [ ] Terminal prompt is clear: APPROVE / REJECT / IMPROVE
- [ ] APPROVE is case-insensitive: approve, APPROVE, Approve all work
- [ ] REJECT discards all output — git status shows no changes
- [ ] IMPROVE asks for specific feedback and regenerates
- [ ] Git log after APPROVE shows exactly one commit per approval
- [ ] Git log after REJECT shows zero new commits
- [ ] No file is ever modified without going through this gate
- [ ] The gate works identically in mock mode and live AI mode

### Notes for PM
The approval gate is not a feature — it is the framework's core
value proposition. "AI-powered test automation with human control"
is the product. The gate is what makes that claim true. If the gate
is removed for convenience, the product becomes "AI generates untrusted
code that commits itself" — which is a different and worse product.

---

*Stories written pre-build and validated against the shipped v1.0.0
framework. All acceptance criteria have been manually verified.*

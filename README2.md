<img width="1440" height="1822" alt="image" src="https://github.com/user-attachments/assets/3adb4746-1dca-4d21-938f-3cc332409175" />

🧱 # What does the framework contains (simple)
# 🔧 Basics of what each part does
## Python environment
python -m venv venv -> creates isolated env
source venv/Scripts/Activate.ps1 -> activates
pip install -r requirements.txt  -> installs libs
## Playwright
pip install playwright
playwright install -> downloads browser binaries
used to run browser automation tests (Chrome/Firefox/WebKit)
## pytest
pytest.ini -> sets test discovery:
- where tests live
- file patterns
- extra flags
conftest.py -> defines fixtures / setup code (e.g., browser session fixture, shared objects)
run tests: pytest, pytest tests/test_xxx.py
## Anthropic/Claude agent
base_agent.py:
- loads API key from env
- constructs prompt messages
- calls anthropic.Client(...).messages.create(...)
hello_claude.py:
- example routine:
  - read source file (test_todo.py)
  - call -> agent.extract_test_cases(...)
  - parse AI response, save results
run from root as package: python -m agents.hello_claude

# 💬 What “framework behavior” is
1. Test templates + page objects define app flows.
2. Agent layer can generate or transform tests via LLM (classical agentic architecture).
3. Pytest executes tests in controlled environment.
4. Playwright executes browser interactions.
5. Reporting + allure maybe from -> allure-pytest.

# 🔑 Need-to-know essentials
1. ModuleNotFoundError fix → use package invocation:
python -m agents.hello_claude
2. Billing mismatch from Anthropic:
  - you got to fund the account / mock API for offline development.
3. playwright 1.59.x for node vs Python: Python has 1.58 right now, OK.

# 🧪 How to run full sequence
1. Activate venv
2. python -m pip install -r requirements.txt
3. python -m playwright install
4. python -m agents.hello_claude (API credit needed)
5. pytest (runs your current tests)

# 🌟 Next step to achieve goals
- Add nice README section: setup, run, agent-mode, test-mode
- Add conftest.py fixtures for playwright browser and API mocks.
- Add fallback to no-API mode for CI: stub BaseAgent.call_claude() if no credit.

# Agents
Agent 1 — test reader
Agent 2 — BDD generator
Approval gateway
Wire 1+2+gateway together
Agent 3 — self-healer
Agent 4 — failure analysis
Failure logger (pytest plugin)
End-to-end smoke test

Every agent follows the same pattern. Input file → Claude prompt → output file → approval gate → git commit. 
Mock mode means nothing blocks you. Every agent has a MOCK_MODE = True flag at the top. It returns realistic hardcoded output so the full workflow runs — approval gate, file writing, git commit — all of it works today regardless of API credits. 
The approval gateway is the most important piece. It's what makes this framework safe and portfolio-worthy. Nothing touches your codebase without your explicit sign-off.

*****************************************************************************
# AI Test Automation Framework — Claude briefing

## Project overview
Python + Playwright AI test automation framework with
self-healing locators, BDD generation, and continuous
failure analysis. Built by a Test Automation Architect
transitioning into AI PM.

## Tech stack
- Python 3.11 · pytest · Playwright · behave
- Anthropic Claude SDK (primary) · Gemini (fallback)
- Docker · GitHub Actions · Azure AKS
- Allure reporting

## Folder structure
```
agents/      # AI agents — base_agent + 4 specialist agents
locators/    # CSS selectors — one file per page
pages/       # Page Object Model classes — one class per page
features/    # Gherkin .feature files (BDD)
steps/       # Python behave step definitions
tests/       # pytest test classes
fixtures/    # test data + data factories
har/         # HAR recordings for API mocking
reports/     # Allure HTML + failures.json + screenshots
skills/      # reusable skill instruction files
docs/pm/     # PM artefacts — vision, decisions, metrics
tools/       # migration tools — Postman, ReadyAPI importers
```

## Key conventions
- All locators live in locators/ — never hardcode in pages
- Page objects use locators via TODO_LOCATORS["key"] pattern
- All agents inherit from agents/base_agent.py
- MOCK_MODE = True in every agent — flip to False for live AI
- Approval gate required for Modes 1, 2, 3 — not 4, 5
- Every approved output gets a git commit with feat: or fix: prefix
- Tests tagged with @pytest.mark.smoke or @pytest.mark.regression

## Agent modes
| Mode | Agent | Plan first? | Approval? |
|------|-------|-------------|-----------|
| 1 | test_reader_agent | yes | yes |
| 2+3 | bdd_generator_agent | yes | yes |
| 4 | direct test addition | no | yes |
| 5 | self_heal_agent | no | yes |
| 6 | failure_analysis_agent | no | no |

## Running the framework
```bash
# activate venv first
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# run all tests
pytest tests/ -v

# run smoke tests only
pytest tests/ -v -m smoke

# run a specific agent
python -m agents.test_reader_agent

# run full e2e loop
python scripts/e2e_smoke_test.py

# build and run in Docker
docker build -t ai-test-framework .
docker run ai-test-framework
```

## Skills location
Before writing any POM, test class or BDD feature,
read the relevant skill file in skills/:
- POM → skills/PAGE_OBJECT_SKILL.md
- Test class → skills/TEST_CLASS_SKILL.md
- BDD → skills/BDD_SKILL.md

## What NOT to do
- Never hardcode selectors in page files
- Never commit .env or API keys
- Never skip the approval gate for Modes 1-3
- Never use print() for errors — use proper assertions
- Never create a Page Object without a matching locators file
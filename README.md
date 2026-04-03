ai-test-framework/ 
    ├── agents/ # AI agents — Modes 1-5 + failure analysis 
    ├── locators/ # Mode 1 — all CSS selectors 
    ├── pages/ # Mode 2 — Page Object Model classes 
    ├── features/ # Mode 3 — Gherkin .feature files 
    ├── steps/ # Mode 3 — BDD step definitions 
    ├── tests/ # Mode 4 — pytest test classes 
    ├── fixtures/ # test data + data factories 
    ├── har/ # HAR recordings for API mocking 
    ├── reports/ # Allure HTML + failures.json 
    ├── tools/ # Postman + ReadyAPI importers (v2) 
    ├── docs/pm/ # PRODUCT_VISION · DECISION_LOG · METRICS 
    ├── docs/architecture/ # ADRs + agent orchestration diagrams 
    ├── .github/workflows/ # GitHub Actions CI/CD YAML (Day 3) 
    ├── .env # API keys — never commit 
    ├── .gitignore 
    ├── conftest.py # pytest hooks + screenshot on failure 
    ├── pytest.ini # markers: smoke regression flaky 
****************************************************************************

# AI Test Automation Framework

> Built by a Test Automation Architect transitioning into AI PM.
> Reduces manual test creation from days to minutes using Claude AI agents,
> Playwright BDD, self-healing locators, and a human-in-the-loop approval workflow.
> Deployed on Azure AKS via GitHub Actions CI/CD.

## Architecture


## Quick start
```bash
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
pytest tests/ -v
```

## Modes
| Mode | Purpose | Plan first? |
|------|---------|-------------|
| 1 | Locator repository | Yes |
| 2 | Page object creation | Yes |
| 3 | Test class creation | Yes |
| 4 | New test case | No |
| 5 | Self-healing | No |
| 6 | Reporting + dashboard | No |

## PM Artefacts
See `docs/pm/` for PRODUCT_VISION, DECISION_LOG and METRICS.

## conftest.py 
 yield page is what makes this a fixture — pytest calls everything before yield as setup, and everything after as teardown. **browser_context_args unpacks a dict and merges it — the ** operator spreads key-value pairs.
************************************************************************

## To create every folder in one go 

@("agents","locators","pages","features",
"tests","steps","fixtures") | ForEach-Object {
    New-Item -ItemType File -Force -Path "$_/__init__.py"
}
Write-Host "Init files created!"
*************************************************************************

pip freeze > requirements.txt 

# saves every installed package and version to requirements.txt — so anyone cloning your repo can run pip install -r requirements.txt and get the exact same environment
***************************************************************************

## Add __init__.py to each folder
# Python needs an empty __init__.py in each folder to treat it as a module — so your imports work correctly when agents reference page objects and locators

@("agents","locators","pages","features",
"tests","steps","fixtures") | ForEach-Object {
    New-Item -ItemType File -Force -Path "$_/__init__.py"
}
Write-Host "Init files created!"
****************************************************************************
 ## Running Tests 
 # Run all 4 tests with verbose output
pytest tests/ -v

# Run headed (see the browser open) — great for learning
pytest tests/ -v --headed

# Run just one test by name
pytest tests/test_todo.py::TestTodoApp::test_add_single_item -v
****************************************************************************
## What is HAR and why it matters
# Record once — replay forever
HAR (HTTP Archive) is a recording of every network request your app makes. Once recorded, Playwright replays it — your tests run even with no internet, no live server, no flaky API responses. This is how enterprise frameworks achieve CI reliability.
Without HAR - Tests fail if API is down, Slow — waits for real network, Flaky — API returns different data and Can't run offline in CI
With HAR - Tests pass regardless of API state, Fast — instant response from file, Deterministic — same data every run and Runs fully offline in Docker/AKS

Create scripts/record_har.py

## To capture the HAR file, execute the below command once 
python scripts/record_har.py

## This will open Chromium browser window, navigates to the demo app, adds two todo items, ticks one complete — then closes automatically. The HAR file is saved to har/todo_app.har.
****************************************************************************


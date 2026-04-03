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
************************************************************************

To create every folder in one go => @("agents","locators","pages","features",
"tests","steps","fixtures") | ForEach-Object {
    New-Item -ItemType File -Force -Path "$_/__init__.py"
}
Write-Host "Init files created!"
*************************************************************************

pip freeze > requirements.txt => saves every installed package and version to requirements.txt — so anyone cloning your repo can run pip install -r requirements.txt and get the exact same environment
***************************************************************************

Add __init__.py to each folder
Python needs an empty __init__.py in each folder to treat it as a module — so your imports work correctly when agents reference page objects and locators

@("agents","locators","pages","features",
"tests","steps","fixtures") | ForEach-Object {
    New-Item -ItemType File -Force -Path "$_/__init__.py"
}
Write-Host "Init files created!"
****************************************************************************




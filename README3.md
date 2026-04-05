# AI Test Automation Framework

> Built by a Test Automation Architect transitioning into AI PM.
> Reduces manual test creation from days to minutes using Claude AI agents,
> Playwright BDD, self-healing locators, and a human-in-the-loop approval workflow.
> Deployed on Azure AKS via GitHub Actions CI/CD.

![CI](https://github.com/Preethikarun/AI-Test-Automation-Frmaework/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Playwright](https://img.shields.io/badge/playwright-1.58.0-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![Allure](https://img.shields.io/badge/allure-reporting-orange)
![Claude AI](https://img.shields.io/badge/claude-AI--powered-purple)

---

## What this framework does

This is not just a test automation framework — it is an **AI-powered continuous
improvement system**. Every part of the test lifecycle is handled by an AI agent:

| Step | What happens | Agent |
|------|-------------|-------|
| Read existing tests | Converts `.py` scripts to plain-English test cases | Agent 1 |
| Generate BDD | Creates Gherkin `.feature` files + step definitions | Agent 2 |
| Self-heal | Detects broken locators and patches them automatically | Agent 3 |
| Analyse failures | Reads failure logs, classifies root cause, suggests fixes | Agent 4 |

Nothing commits to Git without **your explicit approval**. Every agent shows
you a diff and waits for `APPROVE` before touching the codebase.

---

## Architecture

```
Requirement / Manual test case / Existing script
       ↓
   Intake layer — Agent 1 reads any source format
       ↓
   Plain-English structured test cases
       ↓
   Agent 2 generates BDD Gherkin + step definitions
       ↓  [you APPROVE]
   Playwright runs automation
       ↓
   GitHub Actions CI/CD pipeline
       ↓
   Claude AI analyses failures
       ↓
   Framework improves continuously  ↻
```

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| UI automation | Playwright + pytest |
| BDD | behave + Gherkin |
| AI agents | Anthropic Claude / Google Gemini |
| API mocking | HAR replay |
| Reporting | Allure HTML |
| Container | Docker |
| CI/CD | GitHub Actions |
| Cloud | Azure AKS |
| Security | OWASP ZAP |

---

## Project structure

```
ai-test-framework/
├── agents/                    # AI agents — the brain of the framework
│   ├── base_agent.py          # Parent class — Anthropic/Gemini switching
│   ├── test_reader_agent.py   # Mode 1 — reads any intake source
│   ├── bdd_generator_agent.py # Modes 2+3 — generates BDD
│   ├── self_heal_agent.py     # Mode 5 — fixes broken locators
│   └── failure_analysis_agent.py # Mode 6 — root cause analysis
├── intake/                    # All input sources land here
│   ├── scripts/               # Existing Playwright .py test files
│   ├── manual/                # Excel/Word manual test cases
│   ├── requirements/          # Requirements docs + user stories
│   ├── postman/               # Postman JSON exports
│   └── readyapi/              # ReadyAPI XML exports
├── locators/                  # CSS selectors — one file per page
├── pages/                     # Page Object Model classes
├── features/                  # Gherkin .feature files
├── steps/                     # behave step definitions
├── tests/                     # pytest test classes
├── fixtures/                  # Test data + data factories
├── har/                       # HAR recordings for API mocking
├── reports/                   # Allure HTML + failures.json
├── skills/                    # Instruction files for agents
├── docs/pm/                   # PM artefacts — vision, decisions, metrics
└── .github/workflows/         # GitHub Actions CI/CD
```

---

## Quick start — local

### Prerequisites
- Python 3.11+
- Git
- Docker Desktop (for containerised runs)
- Java 8+ (for Allure CLI)
- Allure CLI (see Allure section below)

### 1. Clone and set up environment

```bash
git clone https://github.com/YOUR_USERNAME/ai-test-automation-framework.git
cd ai-test-automation-framework

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure API keys

Create a `.env` file in the project root:

```bash
# .env — never commit this file
GEMINI_API_KEY=AIza-your-gemini-key-here

# Optional — add when Anthropic credits available
# ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get a free Gemini key at: https://aistudio.google.com

### 3. Record HAR file (run once)

```bash
python scripts/record_har.py
```

This opens a browser, records network traffic, and saves `har/todo_app.har`.
Tests replay from this file — no live network dependency.

### 4. Run the tests

```bash
# Run all tests
pytest tests/ -v

# Run smoke tests only
pytest tests/ -v -m smoke

# Run regression suite
pytest tests/ -v -m regression

# Run with headed browser (watch it work)
pytest tests/ -v --headed
```

---

## Running the AI agents

### Mode 1 — test reader (reads existing scripts)

```bash
python -m agents.test_reader_agent
```

Reads `tests/test_todo.py` → extracts plain-English test cases →
shows you the output → waits for `APPROVE` → saves to `reports/test_cases.txt`.

### Mode 1 — with intake sources

```bash
# Read from existing Python test file
python -m agents.test_reader_agent --source intake/scripts/test_todo.py

# Read from Excel manual test cases
python -m agents.test_reader_agent --source intake/manual/test_cases.xlsx

# Read from requirements document
python -m agents.test_reader_agent --source intake/requirements/requirements.txt
```

### Mode 2+3 — BDD generator

```bash
python -m agents.bdd_generator_agent
```

Reads `reports/test_cases.txt` → generates `features/todo.feature` +
`steps/todo_steps.py` → shows both files → waits for `APPROVE`.

### Mode 5 — self-healer

```bash
python -m agents.self_heal_agent
```

Triggered automatically when a `TimeoutError` fires during a test run.
Shows broken vs suggested locator as a diff → waits for `APPROVE` →
patches `locators/todo_locators.py` and commits.

### Mode 6 — failure analysis

```bash
python -m agents.failure_analysis_agent
```

Reads `reports/failures.json` → classifies each failure →
outputs fix plan to `reports/failure_report.txt`.

### Full end-to-end loop

```bash
python scripts/e2e_smoke_test.py
```

Runs all 4 agents in sequence with real approval gates. Proves the
complete AI loop works end to end. Use this as a portfolio demo.

---

## Docker

### Prerequisites
- Docker Desktop installed and running
- Check: `docker --version`

### Build the image

```bash
docker build -t ai-test-framework .
```

First build takes 3–5 minutes (downloads Playwright + Chromium).
Subsequent builds use cache and take ~30 seconds.

### Run all tests in Docker

```bash
# Pass environment variables from .env file
docker run --env-file .env ai-test-framework

# Mount HAR file and reports folder for output
docker run \
  --env-file .env \
  -v ${PWD}/har:/app/har \
  -v ${PWD}/reports:/app/reports \
  ai-test-framework
```

### Run specific test tags in Docker

```bash
# Smoke tests only
docker run --env-file .env ai-test-framework \
  pytest tests/ -v -m smoke

# Regression suite
docker run --env-file .env ai-test-framework \
  pytest tests/ -v -m regression

# Single test
docker run --env-file .env ai-test-framework \
  pytest tests/test_todo.py::TestTodoApp::test_add_single_item -v
```

### Run with Allure results output

```bash
# Run tests and export Allure results to your local machine
docker run \
  --env-file .env \
  -v ${PWD}/har:/app/har \
  -v ${PWD}/reports:/app/reports \
  ai-test-framework \
  pytest tests/ -v --alluredir=reports/allure-results

# Then generate the HTML report locally (see Allure section below)
allure generate reports/allure-results -o reports/allure-html --clean
allure open reports/allure-html
```

### Docker Compose (local development)

```bash
# Run full test suite
docker-compose run tests

# Run smoke tests only
docker-compose run smoke
```

---

## Allure reporting

Allure gives you an interactive HTML dashboard instead of a plain
terminal output. It shows test history, failure screenshots, step
breakdown, and trend charts.

### Prerequisites — install Allure CLI

Allure CLI needs **Java 8+** installed first.

**Install Java (if not already installed):**
Download from https://adoptium.net → install → restart terminal.

**Install Allure CLI on Windows (via Scoop):**

```bash
# Install Scoop (Windows package manager) — run in PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex

# Install Allure
scoop install allure

# Verify
allure --version
```

**Install Allure CLI on Mac:**

```bash
brew install allure
allure --version
```

**Install Allure CLI manually (any OS):**
1. Download `allure-X.X.X.zip` from https://github.com/allure-framework/allure2/releases
2. Extract to `C:\allure` (Windows) or `/usr/local/allure` (Mac/Linux)
3. Add `C:\allure\bin` to your system PATH
4. Restart terminal → `allure --version`

---

### Option A — Live server report (recommended for local viewing)

Starts a local web server and opens the report in your browser.
Report stays live and interactive until you press `Ctrl+C`.

```bash
# Step 1 — run tests and generate raw results
pytest tests/ -v --alluredir=reports/allure-results

# Step 2 — start live Allure server and open in browser
allure serve reports/allure-results
```

The browser opens automatically at `http://localhost:PORT`.
Use this when reviewing results locally — it's faster and fully interactive.

---

### Option B — Static HTML report (for sharing and GitHub Pages)

Generates a complete self-contained HTML folder you can host anywhere,
share as a zip, or publish to GitHub Pages.

```bash
# Step 1 — run tests and generate raw results
pytest tests/ -v --alluredir=reports/allure-results

# Step 2 — generate static HTML report
allure generate reports/allure-results -o reports/allure-html --clean

# Step 3 — open the static report in your browser
allure open reports/allure-html
```

The `--clean` flag wipes the output folder before regenerating —
always use it to avoid stale results mixing with new ones.

The generated `reports/allure-html/` folder is completely self-contained.
Open `reports/allure-html/index.html` directly in any browser,
or serve it from any web server.

---

### Option C — Docker run with Allure results

```bash
# Run tests in Docker, write results to your local machine
docker run \
  --env-file .env \
  -v ${PWD}/har:/app/har \
  -v ${PWD}/reports:/app/reports \
  ai-test-framework \
  pytest tests/ -v --alluredir=reports/allure-results

# Generate report from Docker results (runs locally, not in Docker)
allure generate reports/allure-results -o reports/allure-html --clean

# View the report
allure open reports/allure-html
```

---

### Allure report features

| Feature | Where to find it |
|---------|-----------------|
| Overall pass/fail summary | Dashboard → Overview |
| Test breakdown by tag | Dashboard → Behaviors |
| Failure screenshots | Click any failed test → Attachments |
| Test execution time | Dashboard → Timeline |
| Retry history | Click any test → Retries tab |
| Trend over time | Dashboard → Trend (after 2+ runs) |

---

## CI/CD — GitHub Actions

Every push to `main` or pull request triggers the pipeline automatically.

```
git push → GitHub Actions → Docker build → pytest → Allure report → GitHub Pages
```

Pipeline status is shown in the badge at the top of this README.

---

## PM artefacts

This framework was designed with a product mindset. See `docs/pm/` for:

| Document | What it contains |
|----------|-----------------|
| `PRODUCT_VISION.md` | Why this framework exists, who it serves, the roadmap |
| `DECISION_LOG.md` | Why each tool was chosen over alternatives |
| `METRICS.md` | Success criteria and KPIs — defined before building |
| `USER_STORIES.md` | Each mode written as a PM user story |
| `ROADMAP.md` | v2 API layer, v3 MCP integration, v4 multi-app scale |

---

## Approval gate — how it works

Every AI-generated file goes through a human review before committing:

```
Agent generates output
       ↓
   Shows you a preview / diff
       ↓
   APPROVE → saves file + git commits
   REJECT  → discards, nothing changes
   IMPROVE → regenerates with your feedback
```

This is the core architectural decision: AI accelerates, humans control.

---

## Roadmap

### v2 — API testing layer (planned)
Replace Postman and ReadyAPI with Python-native alternatives:
- REST adapter (httpx)
- SOAP adapter (zeep)  
- GraphQL adapter (gql)
- Contract testing (jsonschema + pydantic)
- Locust load testing

### v3 — MCP integration (planned)
Give agents direct access to your toolchain:
- GitHub MCP — agents read issues and PRs
- Azure MCP — agents read pipeline logs
- Confluence MCP — agents pull requirements live
- Jira MCP — agents read acceptance criteria

### v4 — Team scale (planned)
- Multi-app support
- Slack approval workflow
- Executive test health dashboard

---

## Contributing

Read `CLAUDE.md` before making any changes — it contains the project
conventions, Definition of Done, and how Claude agents should behave
in this codebase.

1. Create a feature branch: `git checkout -b feat/your-feature`
2. Follow conventions in `CLAUDE.md` and `skills/`
3. All new code goes through the approval gate
4. Commit messages: `feat:` / `fix:` / `docs:` / `test:` / `chore:`
5. Push and open a PR

---

*Built over 4 days as a portfolio project demonstrating AI Test Automation
Architecture and AI Product Management thinking.*

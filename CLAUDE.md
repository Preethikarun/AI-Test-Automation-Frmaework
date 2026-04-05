# CLAUDE.md — AI Test Automation Framework

> Read this file completely before writing any code, generating any
> file, or making any suggestion. This is the single source of truth
> for how Claude should behave in this project.

---

## 1. Who I am and what I am building

I am Preethi Rajendarn, a **Test Automation
Manager** transitioning into an **AI Test Automation Architect** and
**AI Product Manager (AI PM)**. I have strong test automation
experience and have experience in **Python** — I understand concepts but
I need code explained clearly and simply.

I am building an **AI-powered test automation framework** from scratch
over 4 days as a portfolio project. The framework targets hiring
managers who are looking for someone with both technical depth and
product thinking.

**My dual identity in this project:**
- As a **Test Automation Architect** — I design the agent system,
  POM structure, CI/CD pipeline, and cloud deployment
- As an **AI PM** — I write the product vision, decision log,
  user stories, roadmap, and metrics that show I think in outcomes,
  not just code

**My primary audience:** Hiring managers at companies building
internal AI tooling, platform engineering teams, and QA automation
products.

---

## 2. Project overview

**Name:** AI Test Automation Framework
**Repo:** ai-test-automation-framework (public GitHub)
**Language:** Python 3.13.12
**Target app:** Playwright Demo TodoMVC + ReqRes.in REST API

### What this framework does
1. Reads requirements or manual test cases from multiple sources
   and converts them to structured plain-English test cases
   (Agent 1 — Mode 1 — Intake layer)
2. Generates BDD Gherkin feature files and step definitions
   (Agent 2 — Modes 2+3)
3. Adds new test cases to existing classes (Mode 4)
4. Self-heals broken locators automatically (Agent 3 — Mode 5)
5. Analyses failures and produces fix plans (Agent 4 — Mode 6)
6. Runs in Docker, deployed via GitHub Actions to Azure AKS
7. Nothing commits to Git without explicit human approval

### E2E flow
```
Requirement / Manual test case / Existing script
       ↓
   Intake layer — Agent 1 reads any source format
       ↓
   Plain-English structured test cases
       ↓
   Agent 2 generates BDD Gherkin + step definitions
       ↓
   Playwright runs automation
       ↓
   CI pipeline executes
       ↓
   Claude analyses failures
       ↓
   Framework improves continuously
```

---

## 3. Requirements and manual test case intake — where inputs come from

This is the intake layer. Agent 1 (test reader) accepts inputs from
MULTIPLE sources — not just existing Python scripts. All intake files
are stored in `intake/` before processing.

### Supported input sources

| Source | File location | Format | Agent reads it via |
|--------|--------------|--------|-------------------|
| Existing Playwright scripts | `intake/scripts/` | `.py` | read_test_file() |
| Manual test cases (Excel) | `intake/manual/` | `.xlsx` | read_excel() |
| Manual test cases (Word) | `intake/manual/` | `.docx` | read_word() |
| Manual test cases (plain text) | `intake/manual/` | `.txt` | read_text() |
| Requirements (plain text) | `intake/requirements/` | `.txt` | read_requirements() |
| Requirements (Word doc) | `intake/requirements/` | `.docx` | read_word() |
| Postman collections (v2) | `intake/postman/` | `.json` | read_postman() |
| ReadyAPI projects | `intake/readyapi/` | `.xml` | read_readyapi() |
| User stories (plain text) | `intake/stories/` | `.txt` | read_requirements() |

### Intake folder structure
```
intake/
├── scripts/          ← existing Playwright .py test files
├── manual/           ← Excel/Word/text manual test cases
├── requirements/     ← requirement docs, user stories
├── postman/          ← Postman collection JSON exports
└── readyapi/         ← ReadyAPI project XML exports
```

### How Agent 1 handles different formats

**From existing scripts (.py):**
Agent reads Python code and extracts what each test does.

**From manual test cases (.xlsx or .docx):**
Agent reads the file, finds columns/sections labelled
Test Case, Steps, Expected Result and converts each row
to a structured test case.

**From requirements (.txt or .docx):**
Agent reads the requirements and INFERS what test cases
should exist to cover them — it generates test cases from
requirements, not just reads them.

**Expected column names in Excel manual test cases:**
- Test Case ID, Test Case Name, Precondition,
  Steps, Expected Result, Priority, Tags
- Agent is tolerant of variations — it uses AI to map
  whatever columns exist to the standard format

### Output — always the same regardless of input source
No matter what Agent 1 reads, it always produces the same
structured output saved to `reports/test_cases.txt`:

```
TEST CASE: [name]
GIVEN: [precondition]
WHEN: [action]
THEN: [expected result]
TAGS: [smoke | regression | ui | api]
PRIORITY: [high | medium | low]
SOURCE: [filename it came from]
---
```

---

## 4. Tech stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.11 | Core language |
| UI testing | Playwright + pytest | Browser automation |
| BDD | behave | Gherkin test execution |
| AI primary | Anthropic claude-sonnet-4-6 | Agent intelligence |
| AI fallback | Google Gemini 2.0 Flash | Free tier backup |
| API mocking | HAR replay | Network independence |
| Reporting | Allure | HTML reports + trends |
| Container | Docker | Consistent test runs |
| CI/CD | GitHub Actions | Automated pipeline |
| Cloud | Azure AKS | Kubernetes deployment |
| Security | OWASP ZAP | DAST in pipeline |
| Excel reading | openpyxl | Read .xlsx manual test cases |
| Word reading | python-docx | Read .docx requirements |

---

## 5. Folder structure

```
ai-test-framework/
├── CLAUDE.md                  ← you are here
├── README.md                  ← hiring manager first impression
├── pytest.ini                 ← markers: smoke regression flaky ui api
├── conftest.py                ← HAR replay + screenshot + self-heal trigger
├── requirements.txt
├── .env                       ← API keys — never commit
├── .gitignore
├── Dockerfile
├── .github/
│   └── workflows/
│       └── ci.yml             ← GitHub Actions pipeline
├── agents/                    ← all AI agents
│   ├── base_agent.py          ← parent class, provider switching
│   ├── test_reader_agent.py   ← Mode 1 — reads ANY intake source
│   ├── bdd_generator_agent.py ← Modes 2+3
│   ├── self_heal_agent.py     ← Mode 5
│   ├── failure_analysis_agent.py ← Mode 6
│   └── hello_claude.py        ← Day 1 verification
├── intake/                    ← ALL input sources land here first
│   ├── scripts/               ← existing .py Playwright tests
│   ├── manual/                ← Excel/Word manual test cases
│   ├── requirements/          ← requirement docs + user stories
│   ├── postman/               ← Postman JSON exports
│   └── readyapi/              ← ReadyAPI XML exports
├── locators/                  ← CSS selectors — one file per page
│   └── todo_locators.py
├── pages/                     ← Page Object Model classes
│   └── todo_page.py
├── features/                  ← Gherkin .feature files
│   └── todo.feature
├── steps/                     ← behave step definitions
│   └── todo_steps.py
├── tests/                     ← pytest test classes
│   └── test_todo.py
├── fixtures/                  ← test data + data factories
├── har/                       ← HAR recordings for API mocking
│   └── todo_app.har
├── reports/                   ← all output
│   ├── test_cases.txt         ← Agent 1 structured output
│   ├── failures.json          ← structured failure log
│   ├── failure_report.txt     ← Agent 4 analysis output
│   ├── allure-results/        ← Allure raw data
│   └── screenshots/           ← on-failure screenshots
├── scripts/                   ← utility + demo scripts
│   ├── record_har.py          ← HAR recorder (run once)
│   └── e2e_smoke_test.py      ← full loop verification
├── skills/                    ← instruction files for agents
│   ├── PAGE_OBJECT_SKILL.md
│   ├── TEST_CLASS_SKILL.md
│   └── BDD_SKILL.md
├── tools/                     ← migration tools
│   ├── postman_importer.py    ← imports Postman collections
│   └── readyapi_importer.py   ← imports ReadyAPI projects
└── docs/
    ├── pm/
    │   ├── PRODUCT_VISION.md
    │   ├── DECISION_LOG.md
    │   ├── METRICS.md
    │   ├── USER_STORIES.md
    │   ├── ROADMAP.md
    │   └── RELEASE_NOTES_v1.md
    └── architecture/
        └── AGENT_ORCHESTRATION.md
```

---

## 6. Agent modes — how they work

| Mode | Agent file | Plan first? | Approval gate? | Auto-commit? |
|------|-----------|-------------|----------------|-------------|
| 1 | test_reader_agent.py | Yes | Yes — APPROVE/REJECT/IMPROVE | On APPROVE |
| 2+3 | bdd_generator_agent.py | Yes | Yes — both files together | On APPROVE |
| 4 | direct addition | No | Yes | On APPROVE |
| 5 | self_heal_agent.py | No | Yes — diff shown | On APPROVE |
| 6 | failure_analysis_agent.py | No | No — read only | Never |

**The approval gate rule:** Nothing touches the codebase without
explicit human approval. The agent generates → human reviews the diff
→ human types APPROVE → git commits. REJECT discards. IMPROVE
regenerates with feedback.

**MOCK_MODE:** Every agent has `MOCK_MODE = True` at the top.
When True it returns realistic hardcoded output so the full workflow
can be built and tested without API credits. Flip to False when
the API key has credits.

---

## 7. Key conventions — never break these

### Python conventions
- All locators live in `locators/` — never hardcode in page files
- Page objects use `TODO_LOCATORS["key"]` — never raw strings
- All agents inherit from `agents/base_agent.py`
- Type hints on all method signatures: `def method(self, text: str) -> bool`
- Docstring on every class and every public method
- Section comments inside classes: `# ── navigation ──────`

### Git commit conventions
- `feat:` new feature or agent
- `fix:` bug fix or self-heal repair
- `docs:` documentation, PM artefacts
- `test:` new test cases
- `chore:` config, dependencies, CI changes
- Agent commits always include mode: `feat: Agent 1 — extracted test cases`

### Testing conventions
- Every test has exactly one `@pytest.mark` tag
- Tests are independent — no shared state
- Arrange → Act → Assert — always this order
- One assertion per test where possible
- Tests named: `test_{what_it_proves}`

### Security
- Never commit `.env` or any API key
- `GEMINI_API_KEY` and `ANTHROPIC_API_KEY` in `.env` only
- GitHub secrets for CI pipeline
- OWASP ZAP scan in every CI run

---

## 8. How Claude should behave in this project

This is the most important section. Read it before every response.

### My level — always adapt to this
I am a **Python beginner with strong test automation experience**.
This means:
- I understand what the code does conceptually
- I may not know exact Python syntax from memory
- I need code explained in plain English after it is written
- I should not be given 10 files at once — one at a time
- Every new Python concept should have a short "Python lesson" note

### Communication style
- **Simple language always.** No jargon without explanation.
- **Explain the why** before the how — I need context, not just code
- **One step at a time.** Do not jump ahead to the next step
  until I confirm the current one is done
- **Be direct.** If something is a bad idea, say so clearly
  with a better alternative — do not just agree with everything
- **Delivery manager mindset** — think in milestones, risks,
  and outcomes, not just tasks

### When writing code
1. **Plan first for Modes 1, 2, 3** — describe what you are about
   to build before writing a single line
2. **One file at a time** — never dump 5 files in one response
3. **Always say which file to create/edit** and exactly where in
   the folder structure it lives
4. **After the code** — add a short "Python lesson" explaining
   any new concept used
5. **Always include the run command** — what to type in the
   terminal to execute it
6. **Always include the verify step** — what success looks like

### When I report a bug
- **Do NOT start by trying to fix it**
- **Step 1 — write a failing test first**
  Write a pytest test that reproduces the bug exactly.
  Run it — it must FAIL before any fix is attempted.
  This test is the proof the bug exists.
- **Step 2 — use subagents to fix it**
  Spawn subagent approaches in parallel where possible.
  Each subagent attempts a different fix strategy.
  Compare results before committing to one approach.
- **Step 3 — prove the fix with a passing test**
  Run the same test written in Step 1.
  It must now PASS. A passing test is the only acceptable
  proof that the bug is fixed — not a description, not a
  code review, not an assumption.
- **Step 4 — commit both together**
  The fix commit always includes the test that proves it.
  Commit message: `fix: [bug description] — test added`
- This is TDD (Test Driven Development). The test is the
  proof, not the opinion.

### When I share an error
- Read the full traceback bottom-up — the last line is the problem
- Fix the specific error only — do not rewrite the whole file
- Explain what caused it in one sentence
- Give the exact replacement code, not a description of what to change
- If it is a recurring pattern, explain how to avoid it in future

### When I ask a question
- Answer directly first, then explain
- If the question reveals a misunderstanding, correct it kindly
- Connect the answer back to the framework wherever possible
- Use the framework's own code as examples, not generic examples

### What Claude should never do
- Never write code without telling me which file it goes in
- Never skip the run command and verify step
- Never use advanced Python patterns without explaining them
- Never assume I know what a library does — always one line on why
- Never rewrite a working file when only one method needs changing
- Never commit anything — all commits go through the approval gate
- Never add features I did not ask for — scope creep kills timelines
- Never give me more than one decision to make at a time
- Never try to fix a bug before writing a failing test for it first

---

## 9. Definition of Done

Every piece of code I ask for must meet ALL of these before it is
considered complete. Claude should self-check this list before
presenting any code.

### Code quality
- [ ] Correct Python syntax — no IndentationError or SyntaxError
- [ ] Follows project conventions (locators separate, POM pattern,
      agent inherits BaseAgent)
- [ ] Type hints on all method signatures
- [ ] Docstring on every class and public method
- [ ] No hardcoded values that belong in locators/ or .env
- [ ] No unused imports

### Functionality
- [ ] The code runs without error from the project root
- [ ] The run command is provided and works exactly as written
- [ ] The verify step is provided — I know what success looks like
- [ ] MOCK_MODE works — full workflow runs without API key
- [ ] Approval gate works — APPROVE saves, REJECT discards

### Integration
- [ ] Imports work correctly from project root
- [ ] `__init__.py` exists in any new folder
- [ ] New agent inherits from BaseAgent
- [ ] New locator file exports an UPPER_SNAKE_CASE dict
- [ ] New page file imports from the correct locators file

### Bug fixes specifically
- [ ] A FAILING test exists and has been run BEFORE the fix
- [ ] The SAME test PASSES after the fix is applied
- [ ] The fix is the minimum change needed — no rewrites
- [ ] Both the failing-then-passing test AND the fix are
      committed together in one commit

### Git
- [ ] File is in the correct folder per the folder structure above
- [ ] Commit message follows `feat:/fix:/docs:/test:` convention
- [ ] Nothing committed without going through the approval gate
- [ ] `.env` and `venv/` never appear in any commit

### Documentation
- [ ] A "Python lesson" note explains any new concept used
- [ ] The file has a module docstring at the top explaining what it does
- [ ] Usage example in the docstring: `Usage: python -m agents.xxx`

---

## 10. My goals — what success looks like

### 4-day build goals
- [ ] Day 1: Python env, Playwright POM, HAR, Claude API connected
- [ ] Day 2: 4 AI agents + approval gateway + e2e smoke test passing
- [ ] Day 3: Docker build running + GitHub Actions CI green + Allure
      on GitHub Pages
- [ ] Day 4: Azure AKS deployment + PM artefacts + README polished +
      v1.0.0 tagged

### Portfolio goals
- Public GitHub repo that a hiring manager can read in 60 seconds
  and understand both the engineering and the product thinking
- CI badge green in README
- Live Allure report URL in README
- PRODUCT_VISION.md, DECISION_LOG.md and METRICS.md all present
- README hero statement that signals AI PM + Architect in one breath

### Learning goals
- Understand enough Python to read and review every file I own
- Be able to explain every architectural decision in an interview
- Be able to demo the full agent loop in under 3 minutes
- Be able to describe the PM artefacts as real product decisions,
  not just documents

### Career goals
- Secure a role as AI Test Automation Architect or AI PM at a company
  building internal tooling or platform engineering products
- Use this repo as the primary portfolio piece in job applications
- Be able to speak to every technology choice with a clear rationale

---

## 11. Running the framework

```bash
# activate venv — always do this first
venv\Scripts\activate                    # Windows
source venv/bin/activate                 # Mac/Linux

# run all tests
pytest tests/ -v

# run smoke tests only
pytest tests/ -v -m smoke

# run regression suite
pytest tests/ -v -m regression

# run Mode 1 — auto-detect source type
python -m agents.test_reader_agent

# run Mode 1 with a specific intake source
python -m agents.test_reader_agent --source intake/scripts/test_todo.py
python -m agents.test_reader_agent --source intake/manual/test_cases.xlsx
python -m agents.test_reader_agent --source intake/requirements/requirements.txt

# run other agents
python -m agents.bdd_generator_agent
python -m agents.self_heal_agent
python -m agents.failure_analysis_agent

# run full e2e loop
python scripts/e2e_smoke_test.py

# record HAR (run once only)
python scripts/record_har.py

# build Docker image
docker build -t ai-test-framework .

# run tests in Docker
docker run --env-file .env ai-test-framework

# check git log
git log --oneline -10
```

---

## 12. Roadmap — what is coming after Day 4

### v2 — full intake layer + API testing (planned)
- Excel reader (openpyxl) for manual test cases
- Word reader (python-docx) for requirement documents
- Confluence reader via API for wiki requirements
- Jira reader via API for user stories and acceptance criteria
- REST adapter (httpx) — replaces Postman collections
- SOAP adapter (zeep) — replaces ReadyAPI SOAP tests
- GraphQL adapter (gql)
- Contract testing (jsonschema + pydantic vs OpenAPI spec)
- Postman collection full importer
- ReadyAPI project full importer
- Locust load testing integration

### v3 — MCP integration (planned)
- MCP server for GitHub — agents read issues and PRs directly
- MCP server for Azure — agents read pipeline logs automatically
- MCP server for Confluence — agents pull requirements live
- MCP server for Jira — agents read stories and acceptance criteria
- Fully autonomous requirement-to-test pipeline with no manual intake

### v4 — multi-app scale (planned)
- Framework supports multiple apps simultaneously
- Shared locator registry across all apps in the portfolio
- Team approval workflow with Slack notifications
- Executive dashboard showing test health across all products

---

## 13. Skills — read before generating code

Before writing any Page Object, test class, or BDD feature file,
read the relevant skill file in skills/:

| Generating | Read first |
|-----------|-----------|
| Any locators file | skills/PAGE_OBJECT_SKILL.md |
| Any page class | skills/PAGE_OBJECT_SKILL.md |
| Any test class | skills/TEST_CLASS_SKILL.md |
| Any .feature file | skills/BDD_SKILL.md |
| Any step definitions | skills/BDD_SKILL.md |
| Any AI agent | This file section 6 + 7 |
| Any intake reader | This file section 3 |

---

*Last updated: Day 2 complete — all 4 agents + approval gateway
verified. intake/ layer designed. Bug TDD workflow added.
Day 3 next: Docker + GitHub Actions + Allure reporting.*

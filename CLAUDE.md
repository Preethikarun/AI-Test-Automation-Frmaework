# CLAUDE.md — AI Test Automation Framework

> Cursor reads this file at the start of every session.
> Read it fully before writing a single line of code.

---

## Who I am

I am an AI Test Automation Architect building a production-grade Python Playwright BDD framework.
This framework sits on top of `automation-pylib` (a shared internal library) and adds AI agents,
context-driven API testing, self-healing locators, multi-browser support, behaviour capture,
and a continuous improvement feedback loop.

---

## Python-Pytest terminology (use these — not Cucumber/Ruby terms)

| Concept | Python-Pytest name | Do NOT use |
|---------|-------------------|------------|
| Shared test state | `TestContext` | World, Context |
| Test state folder | `context/` | world/ |
| State class | `TestContext` | World |
| Test state file | `test_context.py` | context.py |
| Service abstraction | `ServiceLayer` | Domain |
| HTTP client wrapper | `APIClient` | RestClient, GatewayAPI |
| HTTP response object | `APIResponse` | RestClient Result |
| Fixture scope | `conftest.py` fixtures | "mixin all services" |
| Setup per test | `@pytest.fixture` | before_scenario |
| Step implementation | `step definitions` | step defs |
| Test data generation | `DataFactory` | DataStore |
| Shared utilities | `utils/` | helpers/ |
| Test runner config | `pytest.ini` / `conftest.py` | behave.ini only |

---

## Project overview

**Framework name:** `ai-test-framework`
**Language:** Python 3.11+
**Test runner:** pytest + behave (BDD)
**Browser automation:** Playwright
**AI:** Anthropic Claude API (`claude-sonnet-4-6`)
**Behaviour capture:** Playwright Trace + MCP + Windsurf
**Reporting:** Allure (combined UI + API + E2E suites)
**CI/CD:** GitHub Actions → Docker → Azure AKS
**Shared library:** `automation-pylib` (imported, never modified)

---

## The two-layer architecture

```
automation-pylib  (shared library — pip install or git submodule)
    └── utils/common/        helper functions, config, dates, strings
    └── utils/db/            MySQL, Oracle, SQLite connectors
    └── utils/api/           api_context, json_parser, xml_parser
    └── utils/tools/         bdd_common_data, bdd_steps_functions

ai-test-framework  (this project — layer ON TOP of automation-pylib)
    └── locators/            selector dicts — tester fills values
    └── pages/               PageObjects — one class per screen
    └── facade/              multi-screen + multi-API flows
    └── api/                 REST/SOAP/mock clients + auth + validator
    └── context/             TestContext, RetryManager, Logger
    └── utils/               actions.py, functions.py, agents/
    └── capture/             behaviour capture: trace → MCP → Windsurf
    └── tests/               api/ and e2e/ Spec tests
    └── testCases/           features/, steps/, api/rest/, api/soap/
    └── data/                JSON/CSV test data + DataFactory
    └── fixtures/            conftest.py, setup, teardown
    └── config/              browsers.py, environments.py
    └── reports/             Allure, screenshots, failures.json, traces
    └── k8s/                 Azure AKS manifests
    └── .github/workflows/   CI/CD pipeline
```

---

## Complete folder structure

```
ai-test-framework/
│
├── locators/                     ← selector dicts, tester fills ""
├── pages/                        ← PageObjects, one per screen
├── facade/                       ← multi-screen + multi-API flows
│
├── api/
│   ├── rest_client.py            ← REST via httpx
│   ├── soap_client.py            ← SOAP via zeep
│   ├── mock_client.py            ← returns mock from file
│   ├── auth_handler.py           ← none/apikey/bearer/basic/oauth2/cert
│   ├── validator.py              ← status/time/fields/values/text
│   └── runner.py                 ← reads definition → routes → validates
│
├── context/
│   ├── test_context.py           ← TestContext: shared state per test
│   ├── retry_manager.py          ← tracks retry counts per test
│   └── logger.py                 ← structured JSON failure logger
│
├── capture/                      ← behaviour capture pipeline
│   ├── trace_recorder.py         ← Playwright Trace config + recording
│   ├── mcp_analyser.py           ← MCP: intent + causality + semantics
│   ├── windsurf_exporter.py      ← formats trace output for Windsurf
│   └── ci_failure_capture.py     ← CI trace artifacts + failures.json
│
├── utils/
│   ├── actions.py                ← UI helpers + data readers
│   ├── functions.py              ← assertions + common app flows
│   ├── data_factory.py           ← DataFactory: generates test data
│   └── agents/
│       ├── base_agent.py         ← BaseAgent (Anthropic + Gemini fallback)
│       ├── test_reader_agent.py  ← Agent 1: reads scripts → test cases
│       ├── bdd_generator_agent.py ← Agent 2: test cases → Gherkin
│       ├── self_heal_agent.py    ← Agent 3: MCP self-healing
│       ├── failure_analysis_agent.py ← Agent 4: classifies failures
│       └── approval_gateway.py  ← orchestrates all agents
│
├── tests/
│   ├── api/
│   │   └── test_api_runner.py    ← Spec: REST + SOAP definitions
│   └── e2e/
│       └── test_e2e_*.py         ← Spec: API + UI combined
│
├── testCases/
│   ├── features/                 ← BDD Gherkin scenarios
│   ├── steps/                    ← step definitions → Facade
│   └── api/
│       ├── rest/                 ← REST definitions + mocks (JSON)
│       └── soap/                 ← SOAP definitions + mocks (XML)
│
├── data/                         ← test data JSON/CSV
├── fixtures/                     ← conftest.py
├── config/
│   ├── browsers.py               ← Chromium/Firefox/WebKit config
│   └── environments.py           ← env URLs, credentials lookup
│
├── reports/
│   ├── allure-results/           ← Allure report output
│   ├── screenshots/              ← on-failure screenshots
│   ├── traces/                   ← Playwright .zip trace files
│   └── failures.json             ← structured failure log
│
├── k8s/                          ← AKS manifests
├── scripts/                      ← record_har.py, utilities
├── har/                          ← recorded HAR files
├── skills/                       ← PAGE_OBJECT_SKILL.md etc.
│
├── .env                          ← API keys — never commit
├── conftest.py                   ← root conftest + trace hooks
├── pytest.ini                    ← markers: smoke/regression/flaky/api/ui/e2e
├── CLAUDE.md                     ← this file
└── README.md
```

---

## Naming conventions — use these exactly

| Layer | File pattern | Example |
|-------|-------------|---------|
| Locators | `{app}_{screen}_locators.py` | `trademe_search_locators.py` |
| Pages | `{app}_{screen}_page.py` | `trademe_search_page.py` |
| Facade | `{app}_facade.py` | `trademe_facade.py` |
| REST definition | `{feature}.json` | `property_search.json` |
| REST mock | `{feature}_mock.json` | `property_search_mock.json` |
| SOAP definition | `{feature}.xml` | `property_search.xml` |
| SOAP mock | `{feature}_mock.xml` | `property_search_mock.xml` |
| BDD feature | `{app}_{domain}.feature` | `trademe_property.feature` |
| BDD steps | `{app}_steps.py` | `trademe_steps.py` |
| API Spec | `test_api_runner.py` | fixed name |
| E2E Spec | `test_e2e_{domain}.py` | `test_e2e_property.py` |

---

## Design patterns

### Locators

```python
# locators/trademe_search_locators.py

TRADEME_SEARCH_LOCATORS = {
    "search_box":    "",   # inspect: main search input field
    "search_button": "",   # inspect: search submit button
    "page_loaded":   "",   # inspect: stable element confirming load
}
```

**Rules:**
- ALL CAPS dict name · empty string values — tester fills from DevTools
- Selector priority: `data-testid` > `aria-label` > `name` > CSS class
- Never auto-generated class names (`sc-abc123`)
- Never import Playwright here — pure data

---

### PageObject

```python
# pages/trademe_search_page.py
import allure
from playwright.sync_api import Page
from locators.trademe_search_locators import TRADEME_SEARCH_LOCATORS
from utils.actions import Actions
from utils.functions import Functions

class TradeMeSearchPage:
    URL = "https://www.trademe.co.nz/a/property/residential/sale"

    def __init__(self, page: Page):
        self.page      = page
        self.actions   = Actions(page)
        self.functions = Functions(page)
        self.loc       = TRADEME_SEARCH_LOCATORS

    @allure.step("Navigate to Trade Me property search")
    def navigate(self):
        self.page.goto(self.URL)
        self.actions.wait_for_page_load()
        self.functions.accept_cookies()

    @allure.step("Search for '{term}'")
    def search_for(self, term: str):
        self.actions.wait_for_visible(self.loc["search_box"])
        self.actions.fill(self.loc["search_box"], term)
        self.actions.click(self.loc["search_button"])
        self.actions.wait_for_page_load()
```

**Rules:**
- One class per screen
- Never call `page.locator()` directly — always `Actions` or `Functions`
- `@allure.step` on every public method
- Type hints on all arguments and return types
- No assertions in PageObjects

---

### Facade

```python
# facade/trademe_facade.py
import allure
from playwright.sync_api import Page
from pages.trademe_search_page import TradeMeSearchPage
from pages.trademe_results_page import TradeMeResultsPage

class TradeMeFacade:
    def __init__(self, page: Page):
        self.page = page

    @allure.step("Trade Me: search and filter by price")
    def search_and_filter(self, term: str, min_price: str, max_price: str) -> TradeMeResultsPage:
        search = TradeMeSearchPage(self.page)
        search.navigate()
        search.search_for(term)
        results = TradeMeResultsPage(self.page)
        results.apply_price_filter(min_price, max_price)
        return results
```

**Rules:**
- One method per business flow
- Both BDD step definitions AND E2E Specs call the same Facade
- `@allure.step` on every method
- Return the final PageObject for assertions

---

### TestContext (shared test state)

```python
# context/test_context.py

class TestContext:
    """
    Shared test state per test run.
    Fixtures set state. ServiceLayer reads state. APIClient posts back.
    Replaces the Cucumber 'World' pattern with Python-Pytest idiom.
    """
    def __init__(self):
        self.resource    = None    # what is being tested
        self.user        = None    # who is testing
        self.api_response: APIResponse = None   # last APIClient response
        self.data:  dict = {}      # shared test data
        self.retry       = RetryManager()
        self.log         = Logger()

    def set(self, resource: str, user: str):
        self.resource = resource
        self.user     = user

    def post_back(self, response: "APIResponse"):
        """Update context from APIClient response — closes the loop."""
        self.api_response = response
        if isinstance(response.body, dict):
            self.data.update(response.body)
```

**conftest.py fixture:**
```python
@pytest.fixture
def test_context() -> TestContext:
    """Inject TestContext into every test via fixture."""
    return TestContext()
```

**In step definitions (behave):**
```python
def before_scenario(context, scenario):
    context.tc = TestContext()

@given("the user is authenticated as admin")
def step_auth(context):
    context.tc.set(resource="property", user="admin")
    TradeMeFacade(context.page).login(context.tc.user)
```

---

### ServiceLayer (replaces Domain)

```python
# services/property_service.py

class PropertyService:
    """
    Orchestrates requests for the property domain.
    Called by step definitions with TestContext.
    """
    def __init__(self, tc: TestContext):
        self.tc     = tc
        self.client = APIClient(base_url=config.BASE_URL)

    def search(self, term: str) -> APIResponse:
        response = self.client.get(
            endpoint="/v1/Search/Property/Residential.json",
            params={"search_string": term},
            auth=self.tc.user
        )
        self.tc.post_back(response)   # post-back closes the loop
        return response
```

---

### APIClient + APIResponse (replaces RestClient / GatewayAPI)

```python
# api/api_client.py

class APIClient:
    """
    Wraps httpx. Handles auth, request construction, response parsing.
    All API calls go through this — never raw httpx in tests.
    """
    def get(self, endpoint: str, params: dict = None, auth=None) -> "APIResponse":
        ...

@dataclass
class APIResponse:
    status:        int
    body:          dict
    response_time: float
    text:          str
    mocked:        bool = False
```

---

### DataFactory

```python
# utils/data_factory.py

class DataFactory:
    """
    Generates test data. Never hardcode test data in tests.
    Uses automation-pylib data_structures as base.
    """
    @staticmethod
    def property_search(term: str = "Wellington homes", **overrides) -> dict:
        base = {"search_string": term, "rows": 10}
        return {**base, **overrides}

    @staticmethod
    def user(role: str = "buyer") -> dict:
        return {"username": f"test_{role}@example.com", "role": role}
```

---

## Behaviour capture pipeline

### Three-layer model

```
Playwright Trace  →  WHAT happened
       ↓
MCP Intent Engine →  WHY it happened
       ↓
Windsurf          →  HOW to automate it
```

### Layer 1 — Playwright Trace (WHAT)

Captures raw browser events: network requests, DOM snapshots, screenshots, video, user actions, console logs, timing.

```python
# context/test_context.py — trace enabled in conftest.py fixture

# conftest.py
@pytest.fixture
def browser_context(browser):
    context = browser.new_context()
    context.tracing.start(
        screenshots=True,
        snapshots=True,
        sources=True
    )
    yield context
    context.tracing.stop(
        path=f"reports/traces/{pytest.current_test_name}.zip"
    )
    context.close()
```

Trace files are saved to `reports/traces/` on every test run and uploaded as CI artifacts.

---

### Layer 2 — MCP Intent Engine (WHY)

Reads the Playwright trace and infers:

- **Intent detection** — what the user was trying to do (login, checkout, view dashboard, filter results)
- **Causality chain** — click → API call → DOM update → state change
- **Semantic role understanding** — what each UI element means (submit button, error message, product card)
- **Auth pattern detection** — which API calls set up session tokens, cookies, headers

```python
# capture/mcp_analyser.py

class MCPAnalyser:
    """
    Sends Playwright trace to MCP for intent + causality analysis.
    Output feeds into Windsurf for test generation.
    """
    def analyse(self, trace_path: str) -> MCPAnalysis:
        """
        Returns:
          intent:     str       "property_search_and_filter"
          causality:  list[str] ["click search → GET /api/search → results DOM update"]
          auth_apis:  list[str] ["/oauth/token", "/api/session"]
          role_map:   dict      {"search_box": "textbox[name='search']"}
          flaky_risk: str       "high" | "medium" | "low"
        """
        ...
```

---

### Layer 3 — Windsurf (HOW)

Takes MCP analysis + your framework conventions (`CLAUDE.md` + `skills/`) and generates:

- **PageObject** with role-based locators (not brittle CSS selectors)
- **pytest test** using your POM + fixture patterns
- **APIClient setup** — session + auth shortcut from inferred auth APIs
- **API + UI optimisation** — single trace used for both API and UI test generation

```python
# capture/windsurf_exporter.py

class WindsurfExporter:
    """
    Formats MCP analysis output for Windsurf consumption.
    Windsurf reads:
      - MCP analysis JSON
      - CLAUDE.md (framework conventions)
      - skills/PAGE_OBJECT_SKILL.md
      - Playwright trace (optional deep reference)
    """
    def export(self, analysis: MCPAnalysis, output_dir: str):
        payload = {
            "intent":          analysis.intent,
            "causality":       analysis.causality,
            "role_locators":   analysis.role_map,
            "auth_setup":      analysis.auth_apis,
            "framework_style": "pytest_pom",
            "conventions_ref": "CLAUDE.md"
        }
        self._write_json(payload, f"{output_dir}/windsurf_input.json")
```

---

### Semi-automated capture workflow

Use this for: new features, complex flows, flaky test areas.

```
Step 1 — Record
  playwright codegen --save-trace reports/traces/feature_x.zip

Step 2 — Analyse with MCP
  python -m capture.mcp_analyser --trace reports/traces/feature_x.zip

Step 3 — Export for Windsurf
  python -m capture.windsurf_exporter --analysis output/analysis.json

Step 4 — Windsurf generates tests
  Windsurf reads windsurf_input.json + CLAUDE.md + skills/
  → generates pages/{screen}_page.py
  → generates tests/{feature}_test.py
  → uses role locators not brittle CSS

Step 5 — Approval gate
  Review generated files → APPROVE → git commit
```

---

### CI failure capture

On every CI test failure:
1. `conftest.py` saves `reports/traces/{test_name}.zip`
2. `ci_failure_capture.py` appends to `reports/failures.json`
3. Trace + `failures.json` uploaded as CI artifacts
4. Agent 4 reads both and classifies failure
5. If `locator` → Agent 3 heals using MCP live DOM snapshot
6. If `logic` → fix plan generated, routed to approval gate

```python
# capture/ci_failure_capture.py

class CIFailureCapture:
    """
    Captures full context on CI failure.
    Output feeds into Agent 4 (failure_analysis_agent).
    """
    def capture(self, item, call, report):
        record = {
            "timestamp":   datetime.now().isoformat(),
            "test":        item.nodeid,
            "error":       str(call.excinfo.value)[:500],
            "category":    self._classify(call.excinfo),
            "trace_path":  f"reports/traces/{item.name}.zip",
            "screenshot":  f"reports/screenshots/{item.name}.png",
            "mcp_input":   None    # filled by mcp_analyser on flaky failures
        }
        self._append_to_failures_json(record)

    def _classify(self, excinfo) -> str:
        err = type(excinfo.value).__name__
        if "Timeout" in err:       return "locator"
        if "Assertion" in err:     return "logic"
        if "Connection" in err:    return "environment"
        return "unknown"
```

---

### Role-based locators (Windsurf output)

Instead of brittle CSS, Windsurf generates role-based locators that survive UI changes:

```python
# Brittle — breaks when class names change
SEARCH_LOCATORS = {
    "search_box": "input.sc-abc123-search",   # WRONG
}

# Role-based — survives redesigns (Windsurf output)
SEARCH_LOCATORS = {
    "search_box":    "input[aria-label='Search properties']",
    "search_button": "button[type='submit']",
    "results_count": "[role='status']",
}
```

Windsurf can also infer `page.get_by_role()` and `page.get_by_label()` patterns from the MCP semantic analysis, which are even more resilient.

---

## Agent modes

| Mode | File | Plan mode | Trigger |
|------|------|-----------|---------|
| 1 | `test_reader_agent.py` | YES | reads existing `.py` scripts |
| 2 | `bdd_generator_agent.py` | YES | generates Gherkin from test cases |
| 3 | `bdd_generator_agent.py` | YES | generates step definitions |
| 4 | (direct edit) | NO | adds one method to existing class |
| 5 | `self_heal_agent.py` | NO | scoped locator fix via MCP |
| 6 | (allure + capture config) | NO | reporting + trace setup |

**Plan mode = output a plan before writing any code:**
1. Files to create or modify
2. Classes and methods to add
3. Imports needed
4. Assumptions about missing selectors or data

Wait for explicit approval before writing.

---

## Self-healing (Agent 3 + MCP)

When `TimeoutError` fires in CI or locally:

1. `conftest.py` catches it and saves trace
2. Extracts broken locator from error message
3. `SelfHealAgent` connects to MCP with live DOM snapshot (not HTML string)
4. MCP infers correct role-based locator
5. Shows diff → APPROVE → patches locator file → git commit

**Never auto-commit. Always show diff first.**

---

## Multi-browser

```bash
pytest tests/ --browser chromium   # default
pytest tests/ --browser firefox
pytest tests/ --browser webkit

# CI matrix runs all three in parallel
# Allure tags each result with browser name
```

---

## Feedback loop

```
Test fails in CI
    → trace saved to reports/traces/
    → failures.json updated
    → CI uploads both as artifacts
    → Agent 4 reads failures.json + trace
    → locator fail → Agent 3 heals (MCP role locator)
    → logic fail   → fix plan → approval gate → commit
    → flaky        → quarantine + MCPAnalyser captures intent
    → Re-run → Allure trend chart updates
    → ↻ each run improves CI stability
```

---

## Allure structure

```
Allure Dashboard
├── UI Tests     ← @allure.suite("UI Tests") — BDD-driven
├── API Tests    ← @allure.suite("API Tests") — Spec-driven
└── E2E Tests    ← @allure.suite("E2E Tests") — API + UI combined
```

All suites in one report. Trace viewer links embedded in failed test reports.

---

## How Cursor should behave

### Before generating any file — read skill first
- Locators or PageObjects → `skills/PAGE_OBJECT_SKILL.md`
- Test Spec classes → `skills/TEST_CLASS_SKILL.md`
- Feature files or steps → `skills/BDD_SKILL.md`

### Naming rules (enforce strictly)
- `TestContext` not `World` or `Context`
- `APIClient` not `RestClient` or `GatewayAPI`
- `APIResponse` not `RestClient Result`
- `ServiceLayer` not `Domain`
- `DataFactory` not `DataStore`
- `step definitions` not `step defs`

### PageObject files
- Plan mode first for new classes
- Import: locators dict + `Actions` + `Functions`
- `@allure.step` on every public method
- Never raw Playwright calls

### Test Spec files
- Plan mode for new classes, no plan mode for adding one method
- Arrange / Act / Assert with inline comments
- `@allure.title` + `@pytest.mark.*` on every test

### BDD steps
- Steps call `Facade` only — never `PageObject` directly
- No Playwright in steps

### API definitions
- JSON (REST) or XML (SOAP)
- Always generate matching mock file alongside

### Capture pipeline files
- `trace_recorder.py` — only configure, never call Playwright directly in tests
- `mcp_analyser.py` — input is `.zip` trace path, output is `MCPAnalysis` dataclass
- `windsurf_exporter.py` — output is `windsurf_input.json`, references `CLAUDE.md`

### Bug fixes
1. Write failing test first — prove it fails
2. Fix
3. Prove it passes
4. Commit both together

---

## Running commands

```bash
# BDD UI tests
pytest testCases/ -v --headed

# API tests (mock mode)
MOCK_MODE=true pytest tests/api/ -v

# API tests (live)
MOCK_MODE=false pytest tests/api/ -v

# E2E tests
pytest tests/e2e/ -v --headed

# Specific browser
pytest tests/ --browser firefox -v

# With retries
pytest tests/ --reruns 2 -v

# Record trace for capture pipeline
playwright codegen --save-trace reports/traces/feature_x.zip https://app.example.com

# Run MCP analysis
python -m capture.mcp_analyser --trace reports/traces/feature_x.zip

# Export for Windsurf
python -m capture.windsurf_exporter --analysis output/analysis.json

# Allure report
allure serve reports/allure-results

# Docker
docker build -t ai-test-framework .
docker run --env-file .env ai-test-framework pytest tests/ -v

# Agents
python -m utils.agents.test_reader_agent --source tests/test_todo.py
python -m utils.agents.bdd_generator_agent
```

---

## Definition of Done

- [ ] Locators: empty selectors, ALL CAPS dict, role-based preferred
- [ ] PageObject: uses `Actions` + `Functions`, `@allure.step` on all methods
- [ ] Facade: created if flow spans multiple screens
- [ ] BDD feature + steps OR Spec test (not both for same scenario)
- [ ] API definition + mock file
- [ ] pytest markers: `smoke` / `regression` / `api` / `ui` / `e2e`
- [ ] Trace recording enabled in `conftest.py`
- [ ] Passes locally: `pytest tests/ -v`
- [ ] Mock mode: `MOCK_MODE=true pytest tests/api/ -v`
- [ ] No hardcoded credentials
- [ ] Git committed with descriptive message

---

## Key decisions (do not re-debate)

| Decision | Choice |
|----------|--------|
| Shared state class | `TestContext` (Python-Pytest) |
| UI entry point | BDD feature files |
| API entry point | Spec (pytest) |
| Both call | Same `Facade` |
| API mocking | `_mock.json` / `_mock.xml` + `MOCK_MODE` flag |
| Locators | Dict with empty strings, role-based preferred |
| API run selection | Explicit — no auto-discovery |
| Allure | Combined report, separate suite titles |
| `automation-pylib` | Import only — never modify |
| Self-heal locators | Agent 3 via MCP (role-based output) |
| Behaviour capture | Trace → MCP → Windsurf pipeline |
| Auth in capture | MCP infers auth APIs for session shortcuts |
| CI failure artifacts | trace `.zip` + `failures.json` uploaded per run |

---

## Goals

1. Zero manual test creation — agents + Windsurf generate everything
2. Zero brittle locators — role-based locators from MCP/Windsurf
3. Zero flaky tests — `RetryManager` + `MCPAnalyser` + quarantine
4. Zero broken locators surviving CI — Agent 3 heals with MCP
5. Every run improves CI stability — feedback loop
6. One Allure dashboard: UI + API + E2E + trace viewer links
7. Works offline — HAR replay + `MOCK_MODE`

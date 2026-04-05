# DECISION_LOG.md
# AI Test Automation Framework — Architecture Decision Log

*Every significant tool and design choice is recorded here with the
reasoning behind it. This document answers the question hiring managers
and architects always ask: "Why did you choose X over Y?"*

---

## ADR-001 — Python over JavaScript / TypeScript

**Decision:** Python 3.11

**Alternatives considered:** JavaScript with Playwright, TypeScript
with Playwright

**Reasoning:**
Python is the dominant language for AI/ML tooling. The Anthropic SDK,
Google Gemini SDK, and every major AI library have first-class Python
support. Building the test framework in Python means the AI agents,
the test code, and the data processing all share one language — no
context switching, no cross-language integration complexity.

JavaScript Playwright is excellent for web-first teams but creates a
split between the AI layer (Python) and the test layer (JS). Python
gives us one coherent codebase.

**Trade-off accepted:** Python is slower than Node.js for I/O-heavy
workloads. For a test framework running sequential browser tests, this
is irrelevant — test execution time is dominated by browser rendering,
not the Python runtime.

---

## ADR-002 — Playwright over Selenium

**Decision:** Playwright 1.58

**Alternatives considered:** Selenium WebDriver, Cypress, WebdriverIO

**Reasoning:**
Playwright was chosen for four specific technical advantages that
directly enable the framework's AI capabilities:

1. **Native HAR recording and replay.** Playwright records network
   traffic to a HAR file and replays it natively. This is what
   decouples our tests from live APIs — a critical reliability feature
   for CI runs.

2. **Auto-waiting.** Playwright waits for elements to be actionable
   before interacting with them. This eliminates the majority of
   timing-related flaky tests without explicit waits.

3. **Browser context isolation.** Each test gets a clean browser
   context. No state leaks between tests. This makes tests
   independently runnable — a requirement for the approval gate pattern.

4. **Async-native architecture.** Playwright's design makes parallel
   test execution straightforward, which matters for AKS pod
   parallelisation in v2.

Selenium was rejected because it requires explicit waits, has no
native HAR support, and has slower page interaction speeds. Cypress
was rejected because it runs in-browser (limiting network control)
and has no native Python SDK.

---

## ADR-003 — Anthropic Claude over OpenAI GPT

**Decision:** Anthropic claude-sonnet-4-6 (with Gemini 2.0 Flash fallback)

**Alternatives considered:** OpenAI GPT-4o, Google Gemini Pro,
local LLM (Ollama + Llama 3)

**Reasoning:**
Claude was chosen as the primary AI provider for three reasons:

1. **Code reasoning quality.** Claude consistently produces more
   accurate Python and Gherkin when given context about an existing
   codebase. In testing, Claude was better at inferring the project's
   conventions from CLAUDE.md and skills/ files than GPT-4o.

2. **Structured output reliability.** The agents require Claude to
   return output in a specific format (GIVEN/WHEN/THEN, JSON diffs).
   Claude follows structural instructions more consistently than
   GPT-4o in our testing.

3. **Safety-conscious design.** Anthropic's safety-first approach
   aligns with our human-in-the-loop approval gate design philosophy.
   Claude is less likely to generate and commit code without prompting.

**Gemini fallback:** Google Gemini 2.0 Flash is the free-tier fallback
for development and portfolio demonstration when Anthropic credits are
not available. The BaseAgent class handles provider switching
transparently — agents never need to know which model is running.

**Local LLM rejected:** Ollama + Llama 3 was considered for
cost-zero operation. Rejected because code generation quality for
complex Playwright patterns was significantly lower, and latency
(30–60s per call on local hardware) makes the approval gate workflow
feel broken.

---

## ADR-004 — behave over pytest-bdd

**Decision:** behave for BDD execution

**Alternatives considered:** pytest-bdd, Robot Framework

**Reasoning:**
behave was chosen because it treats Gherkin as a first-class citizen.
Feature files are the source of truth — not test functions decorated
with strings. This matters for the AI PM positioning of the framework:
`.feature` files are readable by business stakeholders, product
managers, and delivery managers without any Python knowledge.

pytest-bdd embeds Gherkin inside pytest decorators. The feature files
still exist but the step definitions are tightly coupled to pytest
structure. For a framework where AI generates the feature files and
humans review them, behave's clean separation of concern is the
right choice.

Robot Framework was rejected because its keyword-driven syntax is a
different paradigm that adds learning overhead without additional
capability for our use case.

---

## ADR-005 — Azure over AWS over GCP

**Decision:** Azure AKS for Kubernetes deployment

**Alternatives considered:** AWS EKS, Google GKE

**Reasoning:**
Azure was chosen for pragmatic reasons:
- Azure has the most enterprise adoption in ANZ and UK markets where
  this framework is most likely to be deployed
- Azure DevOps integrates natively with GitHub Actions via the
  azure/login action — zero additional tooling needed
- Azure Container Registry pairs naturally with AKS — same auth,
  same network, simpler IAM
- The target hiring audience (large enterprise, financial services,
  government) predominantly runs Azure

AWS EKS is technically equivalent but adds complexity — ECR auth
is more involved than ACR, and the GitHub Actions integration
requires additional credential management.

GCP GKE is excellent but has lower enterprise adoption in our
target markets.

---

## ADR-006 — HAR mocking over service virtualisation

**Decision:** Playwright HAR replay for API mocking

**Alternatives considered:** WireMock, MockServer, ReadyAPI service
virtualisation

**Reasoning:**
HAR replay is simpler, cheaper (free), and sufficient for our v1 use
case. Record once against the real app, replay forever in CI — no
mock server to maintain, no mapping files to write.

WireMock and MockServer are powerful but require running a separate
service in CI. This adds infrastructure complexity, cost, and a new
failure mode. For a portfolio project and for teams running simple
web app automation, HAR is the right trade-off.

ReadyAPI service virtualisation is excellent but requires an
enterprise licence. Rejecting paid tooling where free alternatives
are sufficient is a deliberate cost decision — documented here so
teams can choose to upgrade if they need ReadyAPI's advanced
matching capabilities.

**v2 note:** When we add API testing (REST/SOAP/GraphQL), we will
re-evaluate. httpx-based API tests with a proper mock layer
(respx for REST, zeep for SOAP) will be more appropriate than
HAR files for API test scenarios.

---

## ADR-007 — Allure over pytest-html over custom dashboard

**Decision:** Allure reporting

**Alternatives considered:** pytest-html, custom Dash/Streamlit
dashboard, Azure Monitor workbooks

**Reasoning:**
Allure was chosen because it provides the best hiring manager
demonstration value at zero additional cost. The interactive HTML
report with screenshot attachments, step breakdown, retry history,
and trend charts conveys test framework maturity immediately.

pytest-html is simpler but produces a flat report with no trend
history, no screenshot embedding, and no tag-based filtering. It
would have required custom work to match Allure's out-of-the-box
capability.

A custom Dash/Streamlit dashboard was considered for maximum control.
Rejected because it adds a web application to maintain alongside the
test framework — scope creep that delays delivery without proportional
value in v1.

Azure Monitor workbooks are excellent for operational dashboards but
require Azure-specific knowledge to read and are not portable.
Allure HTML is universally understood by QA professionals.

---

## ADR-008 — Human-in-the-loop approval gate as a core pattern

**Decision:** Every agent requires explicit APPROVE before committing

**Alternatives considered:** Fully autonomous commits, PR-based review,
async approval via Slack

**Reasoning:**
This was the most important architectural decision in the framework.
AI-generated code that commits itself without human review is not
safe for production use. The framework is designed to be used on real
projects with real codebases — one bad AI-generated commit in a shared
repo damages trust in the entire system.

The approval gate design has three benefits beyond safety:
1. It forces the human to read the AI output — building understanding
2. It creates an auditable log of every AI decision in git history
3. It makes the framework demonstrably trustworthy to stakeholders
   who are sceptical of AI in their pipelines

Fully autonomous commits were considered for efficiency. Rejected
because the time saved (seconds) does not justify the risk of
an unreviewed bad commit in a team codebase.

PR-based review was considered — agent opens a PR, human reviews.
This is the v3 direction (via MCP + GitHub integration) but requires
more infrastructure than is warranted in v1.

Async Slack approval was considered — agent posts to Slack, human
reacts with an emoji. Interesting UX but adds Slack dependency to
the framework. Roadmap for v4.

---

*Last updated: v1.0.0 shipped. All decisions above were made during
the 4-day build. Revisit on any major framework version change.*

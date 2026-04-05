# PRODUCT_VISION.md
# AI Test Automation Framework — Product Vision

*Version 1.0 · Author: AI Test Automation Architect / AI PM*
*Last updated: Day 4 — framework shipped*

---

## The problem we are solving

Manual test automation is broken in three specific ways that cost
delivery teams time, money and confidence:

**Problem 1 — Creation is slow.**
A test engineer writing automation from scratch for a new feature
spends 3–5 days per feature. They read the requirement, write
locators, build page objects, write test cases, write BDD scenarios,
and wire up step definitions — all manually. This is mostly
mechanical work that should not require senior engineering time.

**Problem 2 — Maintenance is unpredictable.**
Every time a UI changes — a CSS class renamed, a button moved, a
form restructured — existing tests break. A test engineer manually
hunts for every broken locator across every test file. In a large
suite this takes hours. In a fast-moving product this happens weekly.
Teams stop trusting their test suite because it breaks too often.

**Problem 3 — Failures are opaque.**
When tests fail in CI, engineers read a raw stacktrace and start
debugging manually. There is no system that says "this is a locator
failure, this is a logic failure, this is a flaky timing issue" —
and certainly nothing that suggests a fix. Every failure is a manual
investigation starting from zero.

**The result:** teams either under-invest in test automation (slow,
brittle suites that nobody trusts) or over-invest in test engineering
headcount (expensive, hard to scale). Neither is sustainable.

---

## The opportunity

Large language models can now read code, understand intent, generate
structured output, and reason about failures — reliably enough to
automate the mechanical parts of test creation and maintenance.

The opportunity is to build a framework where:
- AI generates tests from any input (requirements, manual cases, scripts)
- AI repairs broken tests automatically
- AI diagnoses failures and suggests fixes
- Humans stay in control — reviewing and approving every AI decision

This is not "AI replaces testers." It is "AI removes the mechanical
work so testers focus on what requires human judgement."

---

## Our solution

The **AI Test Automation Framework** is a Python-based, agent-driven
system that handles the full test lifecycle from requirement to report.

Four AI agents, each with a specific job:

| Agent | Job | Human touchpoint |
|-------|-----|-----------------|
| Test Reader (Mode 1) | Reads any source, extracts structured test cases | Approves the output |
| BDD Generator (Modes 2+3) | Generates Gherkin features + step definitions | Approves both files |
| Self-Healer (Mode 5) | Detects broken locators and patches them | Approves the diff |
| Failure Analyst (Mode 6) | Classifies failures, outputs a fix plan | Reviews the report |

**The core design principle:** AI accelerates, humans control.
Nothing commits to the codebase without explicit human approval.
Every agent shows a diff or preview before touching any file.

---

## Who this serves — user personas

### Primary user: Test Automation Engineer
**Context:** Responsible for building and maintaining the test suite.
Spends 60–70% of time on mechanical work — writing boilerplate,
fixing locators, debugging failures.

**What they gain:** Test creation time drops from days to minutes.
Locator failures are diagnosed and patched automatically.
Failure reports tell them exactly what broke and why.

**Success signal:** "I spent today writing test logic, not boilerplate."

---

### Secondary user: Delivery Manager / QA Lead
**Context:** Responsible for release quality. Currently has no
visibility into test health between release cycles. Discovers
failures in standup, not in a dashboard.

**What they gain:** Live Allure dashboard showing test pass rate,
failure trends, and coverage gaps after every pipeline run.
AI-generated failure reports in plain English — no technical
decoding required.

**Success signal:** "I knew about the test failures before standup."

---

### Tertiary user: New team member / junior engineer
**Context:** Joining a project with an existing test suite.
Currently spends days understanding the structure before
contributing a single test.

**What they gain:** CLAUDE.md and skills/ files explain the entire
framework in plain language. BDD features are readable without
knowing Python.

**Success signal:** "I shipped my first test on day 2, not day 10."

---

## What success looks like — outcomes not outputs

| Outcome | Target | How measured |
|---------|--------|-------------|
| Test creation time | Under 10 minutes per feature | Timer from requirement to approved BDD file |
| Locator self-heal rate | Greater than 80% of TimeoutErrors auto-patched | failures.json healed: true rate |
| Flaky test detection | Within 2 CI runs | pytest-rerunfailures failure patterns |
| Failure classification accuracy | Greater than 90% correct | Manual review of failure_report.txt |
| Coverage suggestions accepted | Greater than 60% acted on | Agent 4 recommendations vs tests added |
| CI pipeline green rate | Greater than 95% on main | GitHub Actions pass rate over 30 days |

---

## What we explicitly chose NOT to build in v1

Good product decisions include what you leave out.

- No GUI or web interface — engineers work in terminals and IDEs
- No full API testing layer — scoped to UI in v1, API in v2
- No automated commits without human approval — safety first
- No multi-app support — one app proven, then scale
- No Slack notifications — reporting via Allure and GitHub Pages
- No database-backed test management — Git is the source of truth

These are in the roadmap with clear rationale for when they become
the right investment.

---

## Roadmap — three phases after v1

### v2 — API layer and full intake (planned)
REST, SOAP, GraphQL testing. Intake from Excel, Word, Confluence,
Jira, Postman, ReadyAPI. Full migration path from existing tools.

### v3 — MCP integration (planned)
Agents gain direct access to the organisation's toolchain via
Model Context Protocol. Claude reads Jira tickets, generates tests,
runs them, reports back — with human approval at each stage.

### v4 — Team scale (planned)
Multi-app support, Slack approval workflows, executive test health
dashboard across all products in the portfolio.

---

*This document is a living artefact. Update it when assumptions
change, when users give feedback, or when roadmap priorities shift.*

# METRICS.md
# AI Test Automation Framework — Success Metrics and KPIs

*Metrics were defined BEFORE building began. This is a core PM
discipline — know what success looks like before you ship.*

---

## Guiding principle

We measure outcomes, not outputs.

A framework that generates 500 test cases automatically but none of
them pass is not successful. A framework that reduces test creation
time by 70% and increases suite reliability is.

Every metric below has a target, a baseline, and a measurement method.
If we cannot measure it, we do not include it.

---

## Tier 1 — Core delivery metrics

These directly measure whether the framework delivers its
primary value proposition.

### M1 — Test creation time

**What it measures:** How long from receiving a requirement or manual
test case to having an approved, committed BDD test running in CI.

**Baseline (before framework):**
3–5 days per feature for an experienced test engineer writing
manually. This includes reading requirements, writing locators,
building page objects, writing test cases, writing BDD, and wiring
step definitions.

**Target (with framework):**
Under 10 minutes for a feature whose page object already exists.
Under 60 minutes including page object creation for a new page.

**How measured:**
Timer from dropping a file into `intake/` to approved commit in
git log. Logged manually during the first 10 framework uses.
Automated timing added in v2.

**Current status (v1 demo):**
End-to-end demo run (existing test → Agent 1 → Agent 2 → APPROVE →
commit) completes in under 3 minutes in mock mode.
Live AI mode target: under 10 minutes.

---

### M2 — Locator self-heal success rate

**What it measures:** The percentage of TimeoutError test failures
where Agent 3 (self-healer) correctly identifies and patches the
broken locator without human intervention beyond the APPROVE step.

**Baseline (before framework):**
0% — all locator failures required manual debugging. Average time
to diagnose and fix a broken locator: 45–90 minutes per occurrence
in a large test suite.

**Target (with framework):**
Greater than 80% of TimeoutErrors resolved by Agent 3 with one
APPROVE action. Less than 20% requiring manual intervention.

**How measured:**
`reports/failures.json` — category field set to "locator",
healed field set to true/false. Rate calculated as
healed:true / total category:locator over a 30-day period.

**Current status (v1):**
Mock mode: 100% (mock always returns a fix).
Live AI mode: Being validated — selector strategy in SKILL.md
prioritises data-testid which is most stable.

---

### M3 — CI pipeline green rate

**What it measures:** Percentage of pushes to the main branch where
the full pipeline (lint → test → report → security) passes without
human intervention.

**Baseline (before framework):**
Not applicable — no CI pipeline existed before Day 3.

**Target:**
Greater than 95% green rate on main branch over any 30-day period.
Failures must be caused by genuine application bugs, not framework
fragility.

**How measured:**
GitHub Actions run history. Failed runs categorised as:
framework failure (our fault) vs. application failure (expected).
Only framework failures count against the metric.

**Current status (v1):**
Pipeline established. Baseline measurement begins from first week
of production use.

---

### M4 — Failure classification accuracy

**What it measures:** How often Agent 4 (failure analysis) correctly
classifies a test failure into the right category:
locator / logic / flaky / environment.

**Baseline (before framework):**
0% — no automated classification existed. Engineers classified
manually (implicitly, by reading stacktraces).

**Target:**
Greater than 90% correct classification on a labelled test set
of 50 real failures across all four categories.

**How measured:**
Manual audit: run Agent 4 on 50 known failures, compare its
classification to the correct label. Accuracy = correct / total.
Audit to be run after first 30 days of production use.

**Current status (v1):**
Rule-based classification implemented (TimeoutError → locator,
AssertionError → logic, etc.). AI classification in live mode
expected to exceed rule-based accuracy.

---

## Tier 2 — User satisfaction metrics

These measure whether the framework is actually being used and
valued, not just technically working.

### M5 — Agent output acceptance rate

**What it measures:** The percentage of agent outputs that receive
APPROVE vs. REJECT or IMPROVE at the approval gate.

**Target:** Greater than 70% APPROVE on first generation.
Below 70% suggests the AI prompts or skill files need improvement.

**How measured:**
Approval gate logs — add logging to base_agent.py tracking
decision per agent per run. Dashboard view in v2.

**Why this matters (PM insight):** A low acceptance rate means
engineers are spending as much time reviewing and rejecting AI output
as they would writing it themselves. That is not a productivity gain.
If acceptance rate falls below 70%, review the system prompt and
skill files before adding more agents.

---

### M6 — Framework adoption — runs per week

**What it measures:** How many times the agents are invoked per week
by real users (not during development).

**Target:** At least 5 agent runs per week by week 4 of production use.

**How measured:**
`reports/` folder timestamped output files. Count of new
`test_cases.txt` files per week.

**Leading indicator:** If adoption is low, the framework is not
solving a real pain point — or the user experience is too difficult.
Both are product problems, not engineering problems.

---

## Tier 3 — Portfolio and positioning metrics

These measure whether the framework achieves its secondary goal:
positioning the author as an AI PM and Test Automation Architect.

### M7 — GitHub repo engagement

**Target:**
- At least 10 GitHub stars within 30 days of LinkedIn post
- At least 3 meaningful forks (indicating others want to use it)
- README viewed by hiring managers — measured via LinkedIn post
  impressions and direct messages received

---

### M8 — Interview conversion rate

**Target:**
- Framework mentioned in at least 80% of job application responses
- At least 50% of technical interviews include questions directly
  about the framework's architecture
- At least 1 job offer citing the framework as a differentiator
  within 90 days of completion

---

## Metrics we decided NOT to track

These are tempting to measure but lead to wrong optimisations:

**Lines of code generated:** More code is not better code. An agent
that generates 500 lines of verbose boilerplate is worse than one
that generates 50 lines of clean, maintainable tests.

**Number of tests in the suite:** Coverage without quality is noise.
A suite of 1000 flaky tests provides less value than 50 reliable ones.

**Agent response time:** Speed matters only if it affects the
human's experience. A 30-second AI response that saves 3 days of
manual work is an excellent trade-off. Optimising for seconds is
premature.

**Cost per agent call:** In v1, API costs are negligible (under $2
for the entire 4-day build). Cost becomes a metric when usage scales
to hundreds of calls per day — that is a v3 problem.

---

## Review cadence

| Metric tier | Review frequency | Owner |
|------------|-----------------|-------|
| Tier 1 — delivery | Weekly during first month | Test Automation Architect |
| Tier 2 — satisfaction | Bi-weekly | AI PM |
| Tier 3 — portfolio | Monthly | Author |

Metrics that consistently miss target for 4 weeks trigger a
retrospective — not just a technical fix. Missing a metric is a
signal that either the target was wrong, the measurement is wrong,
or the product needs to change. All three are valid outcomes.

---

*Metrics defined pre-build: April 2025. First review: 30 days
post v1.0.0 release.*

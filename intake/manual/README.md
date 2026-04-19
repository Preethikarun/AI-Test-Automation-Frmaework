# intake/manual/ — Manual Test Cases

Place Excel (.xlsx) or plain-text (.txt) manual test cases here.
The pipeline converts them to BDD feature files, steps, locators, and DataFactory.

## Required format

Every test case must include explicit values — do NOT write vague descriptions.

**Plain text format:**
```
Test: <descriptive name>
Screen: <snake_case screen name>
Tags: smoke, ui, search  (from: smoke regression ui api e2e filter detail search)
Priority: High / Medium / Low
Given: <starting state — passive, not an action>
When: <user action — active voice>
Then: <expected result — what user sees>
Data:
  key: "exact value"    ← copy values VERBATIM from requirements
  key: "exact value"    ← if unknown write: FILL_ME
```

**Excel format (.xlsx):** Use columns: Name, Given, When, Then, Tags, Priority, Data

## Run the pipeline

```bash
python -m utils.agents.pipeline \
    --input intake/manual/your_test_cases.txt \
    --app <app_name> \
    --screen <screen_name> \
    --facade <FacadeClassName>
```

See `intake/TEMPLATE.txt` for a full example.

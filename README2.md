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

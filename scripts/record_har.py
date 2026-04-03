"""
Run this script ONCE to record network traffic from the demo app.
It opens a real browser — watch it run, then it saves the HAR file.
Usage: python scripts/record_har.py
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

HAR_PATH = "har/todo_app.har"

# Creates the har/ folder if it doesn't exist
def record():
    Path("har").mkdir(exist_ok=True) 

#This is a context manager. It automatically cleans up the browser when the block ends.  
    with sync_playwright() as p: 
        browser = p.chromium.launch(headless=False)

    # record=True tells Playwright to capture all requests
        context = browser.new_context(
            record_har_path=HAR_PATH,
            record_har_url_filter="**/*"
        )
        page = context.new_page()

        print("Recording started — performing user journey...")
        page.goto("https://demo.playwright.dev/todomvc")
        page.wait_for_load_state("networkidle")

    # Perform actions to capture all API calls
        page.fill("input.new-todo", "HAR captured item one")
        page.keyboard.press("Enter")
        page.fill("input.new-todo", "HAR captured item two")
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)

    # Complete an item
        page.locator(".todo-list li .toggle").first.click()
        page.wait_for_timeout(500)

    # Close context — this SAVES the HAR file
        context.close()
        browser.close()

    print(f"HAR saved → {HAR_PATH}")
    print("File size:", Path(HAR_PATH).stat().st_size, "bytes")

#It means this only runs when you execute the file directly, not when it's imported.
if __name__ == "__main__": 
    record()

"""
scripts/capture_locators.py

Interactive Playwright-based locator capture tool.

Instead of manually inspecting in DevTools, this script:
1. Loads your existing locator file (with empty strings)
2. Opens a real browser to the target URL
3. For each empty key, highlights a prompt and waits for you to click
4. Captures the best available XPath for the clicked element
    Priority: data-testid > aria-label > placeholder > name > text > structural
5. Writes the XPath straight back into the locator dict

Selector priority (XPath only — no CSS classes):
  //*[@data-testid='...']
  //input[@aria-label='...']
  //input[@placeholder='...']
  //input[@name='...']
  //button[normalize-space()='...']
Structural fallback only if none of the above exist

Usage:

python scripts/capture_locators.py \\
    --locator locators/trademe_property_search_locators.py \\
    --url https://www.trademe.co.nz/a/property/residential/sale

# Capture only empty keys (default — skips already-filled ones)
python scripts/capture_locators.py \\
    --locator locators/trademe_results_locators.py \\
    --url https://www.trademe.co.nz/a/property/residential/sale \\
    --empty-only

# Re-capture everything including filled keys
python scripts/capture_locators.py \\
    --locator locators/trademe_property_search_locators.py \\
    --url https://www.trademe.co.nz/a/property/residential/sale \\
    --all

# Use a specific browser
python scripts/capture_locators.py \\
    --locator locators/trademe_property_search_locators.py \\
    --url https://www.trademe.co.nz \\
    --browser firefox

Controls during capture:
Click element  →  captures XPath for current key
Press S        →  skip this key (leave empty)
Press Q        →  quit and save what was captured so far
Press R        →  redo — recapture the previous key
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any


# ── XPath extraction (injected into the browser via JS) ────────────
_XPATH_SCRIPT = """
(element) => {
    // Priority 1: data-testid on the element or a close ancestor
    function findTestId(el) {
        let node = el;
        for (let i = 0; i < 3; i++) {
            if (!node) break;
            const id = node.getAttribute('data-testid');
            if (id) return `//*[@data-testid='${id}']`;
            node = node.parentElement;
        }
        return null;
    }

    // Priority 2: aria-label on the element itself
    function findAriaLabel(el) {
        const label = el.getAttribute('aria-label');
        if (!label) return null;
        const tag = el.tagName.toLowerCase();
        return `//${tag}[@aria-label='${label}']`;
    }

    // Priority 3: placeholder (inputs only)
    function findPlaceholder(el) {
        const ph = el.getAttribute('placeholder');
        if (!ph) return null;
        const tag = el.tagName.toLowerCase();
        return `//${tag}[@placeholder='${ph}']`;
    }

    // Priority 4: name attribute
    function findName(el) {
        const name = el.getAttribute('name');
        if (!name) return null;
        const tag = el.tagName.toLowerCase();
        return `//${tag}[@name='${name}']`;
    }

    // Priority 5: stable visible text content (buttons / links / labels)
    function findText(el) {
        const tag = el.tagName.toLowerCase();
        if (!['button', 'a', 'label', 'h1','h2','h3','span'].includes(tag)) return null;
        const text = (el.textContent || '').replace(/\\s+/g, ' ').trim();
        if (text && text.length < 60 && !text.match(/^[0-9,.$]+$/)) {
            return `//${tag}[normalize-space()='${text}']`;
        }
        return null;
    }

    // Priority 6: id attribute
    function findId(el) {
        const id = el.id;
        if (!id || id.match(/^(sc-|css-)/)) return null;
        return `//*[@id='${id}']`;
    }

    // Priority 7: structural XPath (fallback)
    function buildStructural(el) {
        const parts = [];
        let node = el;
        while (node && node.nodeType === 1 && node.tagName !== 'HTML') {
            const tag = node.tagName.toLowerCase();
            const parent = node.parentElement;
            if (!parent) { parts.unshift(tag); break; }
            const siblings = Array.from(parent.children).filter(c => c.tagName === node.tagName);
            if (siblings.length > 1) {
                const idx = siblings.indexOf(node) + 1;
                parts.unshift(`${tag}[${idx}]`);
            } else {
                parts.unshift(tag);
            }
            node = parent;
        }
        return '//' + parts.join('/');
    }

    const result = (
        findTestId(element)    ||
        findAriaLabel(element) ||
        findPlaceholder(element) ||
        findName(element)      ||
        findText(element)      ||
        findId(element)        ||
        buildStructural(element)
    );

    return result;
}
"""

# ── overlay injection (shows the current key being captured) ────────
_OVERLAY_SCRIPT = """
(message) => {
    const existing = document.getElementById('__locator_capture_overlay__');
    if (existing) existing.remove();

    const div = document.createElement('div');
    div.id = '__locator_capture_overlay__';
    div.innerHTML = message;
    div.style.cssText = [
        'position: fixed',
        'top: 0',
        'left: 0',
        'right: 0',
        'z-index: 999999',
        'background: #1a1a2e',
        'color: #eee',
        'font: bold 14px monospace',
        'padding: 12px 20px',
        'box-shadow: 0 3px 10px rgba(0,0,0,0.5)',
        'pointer-events: none',
    ].join(';');
    document.body.prepend(div);
}
"""

_REMOVE_OVERLAY_SCRIPT = """
() => {
    const el = document.getElementById('__locator_capture_overlay__');
    if (el) el.remove();
}
"""


# ── locator file loader ──────────────────────────────────────────────

def load_locator_dict(filepath: Path) -> tuple[str, dict]:
    """
    Import the locator file and return (dict_name, dict_value).
    Works by importing the module dynamically.
    """
    spec   = importlib.util.spec_from_file_location("_locators", str(filepath))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Find the ALLCAPS dict
    for name in dir(module):
        if name.isupper() and name.endswith("_LOCATORS"):
            return name, getattr(module, name)

    # Fallback: look for any dict ending in _LOCATORS
    for name in dir(module):
        if name.endswith("_LOCATORS"):
            return name, getattr(module, name)

    raise ValueError(
        f"No *_LOCATORS dict found in {filepath}. "
        "Expected a dict variable ending with _LOCATORS."
    )


def collect_empty_keys(locator_dict: dict, empty_only: bool) -> list[tuple[str, str]]:
    """
    Return list of (section, key) tuples for keys that need capturing.
    If empty_only=True, only return keys with empty string values.
    """
    targets = []
    for section, keys in locator_dict.items():
        if not isinstance(keys, dict):
            continue
        for key, value in keys.items():
            if empty_only and value:
                continue   # skip already-filled keys
            targets.append((section, key))
    return targets


# ── file updater ─────────────────────────────────────────────────────

def update_locator_file(
    filepath:    Path,
    dict_name:   str,
    captured:    dict[tuple[str, str], str],
) -> None:
    """
    Write captured XPath values back into the locator file.
    Replaces empty strings for the captured keys while preserving
    all comments, formatting, and keys that were not captured.
    """
    source = filepath.read_text(encoding="utf-8")

    for (section, key), xpath in captured.items():
        # Match the key with any existing string value (empty or already filled)
        pattern = rf'("{key}"\s*:\s*)"(?:[^"\\]|\\.)*"\s*(#.*)?$'
        escaped = xpath.replace("\\", "\\\\").replace('"', '\\"')
        replacement = rf'\1"{escaped}"  \2'
        new_source, count = re.subn(pattern, replacement, source, flags=re.MULTILINE)
        if count == 0:
            print(f"  ⚠  Could not update {section}.{key} in file (key not found)")
        else:
            source = new_source

    filepath.write_text(source, encoding="utf-8")
    print(f"\nLocator file updated → {filepath}")


# ── main capture session ──────────────────────────────────────────────

def run_capture(
    locator_path: str,
    url:          str,
    browser_name: str = "chromium",
    empty_only:   bool = True,
) -> None:
    """
    Open a Playwright browser session and interactively capture locators.
    """
    from playwright.sync_api import sync_playwright

    filepath    = Path(locator_path)
    dict_name, locator_dict = load_locator_dict(filepath)
    targets     = collect_empty_keys(locator_dict, empty_only)

    if not targets:
        print("All locators are already filled. Use --all to re-capture.")
        return

    total    = len(targets)
    captured = {}
    history  = []   # for redo

    print(f"\nLocator capture session")
    print(f"  File:    {filepath}")
    print(f"  URL:     {url}")
    print(f"  Browser: {browser_name}")
    print(f"  Keys to capture: {total}")
    print(f"\nControls:")
    print(f"  Click element  → capture XPath")
    print(f"  S key          → skip this key")
    print(f"  Q key          → quit and save now")
    print(f"  R key          → redo previous key\n")

    with sync_playwright() as p:
        browser_engine = getattr(p, browser_name)
        browser        = browser_engine.launch(headless=False, slow_mo=100)
        context        = browser.new_context(viewport={"width": 1400, "height": 900})
        page           = context.new_page()

        print(f"Opening {url} ...")
        page.goto(url)
        page.wait_for_load_state("networkidle")

        idx = 0
        while idx < len(targets):
            section, key = targets[idx]
            progress     = f"{idx + 1}/{total}"

            # Show overlay banner
            page.evaluate(
                _OVERLAY_SCRIPT,
                f"🎯 [{progress}]  Capture:  {section} → {key}"
                f"  |  Click the element  |  [S] skip  [R] redo  [Q] quit"
            )

            print(f"\n[{progress}]  Click the element for:  {section} → {key}")

            # Wait for a click or keyboard shortcut
            action = _wait_for_action(page)

            if action == "quit":
                print("Quitting — saving captured locators so far.")
                break

            elif action == "skip":
                print(f"  Skipped {section}.{key}")
                history.append(("skip", section, key))
                idx += 1

            elif action == "redo":
                if history:
                    last = history.pop()
                    if last[0] == "capture":
                        _, prev_section, prev_key, _ = last
                        # Remove the last captured entry
                        captured.pop((prev_section, prev_key), None)
                        prev_idx = next(
                            (i for i, t in enumerate(targets)
                             if t == (prev_section, prev_key)), None
                        )
                        if prev_idx is not None:
                            idx = prev_idx
                            print(f"  Redo — recapturing {prev_section}.{prev_key}")
                            continue
                print("  Nothing to redo.")

            elif action and action.startswith("xpath:"):
                xpath = action[len("xpath:"):]
                captured[(section, key)] = xpath
                history.append(("capture", section, key, xpath))
                print(f"  ✓  {section}.{key}  =  {xpath}")
                idx += 1

        # Remove overlay and close
        try:
            page.evaluate(_REMOVE_OVERLAY_SCRIPT)
        except Exception:
            pass

        browser.close()

    # Write captured values back to file
    if captured:
        update_locator_file(filepath, dict_name, captured)
        print(f"\nCaptured {len(captured)} of {total} locators.")
    else:
        print("\nNo locators captured — file unchanged.")


def _wait_for_action(page) -> str | None:
    """
    Wait for either a mouse click or a keyboard key press (S/R/Q).

    Strategy:
    - Injects a single capture listener that stores the clicked element
        on window.__clickedEl AND the computed XPath on window.__clickedXPath
    - Polls every 100 ms for either a click result or a keyboard flag
    - Keyboard listener sets window.__keyFlag to 'S', 'R', or 'Q'

    Returns:
    "xpath:<value>"  — element clicked, xpath extracted
    "skip"           — S pressed
    "redo"           — R pressed
    "quit"           — Q pressed
    None             — unexpected state
    """
    # Install both listeners in one JS evaluation.
    # The click listener runs the full XPath extraction inline so we never
    # need to re-reference the element across separate evaluate() calls.
    page.evaluate(
        _XPATH_SCRIPT.rstrip() + """
;
window.__clickedXPath = null;
window.__keyFlag      = null;

// ── click capture ─────────────────────────────────────────────
(function installClick() {
    document.removeEventListener('click', window.__clickHandler, true);
    window.__clickHandler = function(e) {
        // Don't block navigation — just record
        const el    = e.target;
        const xpath = arguments.callee._getXPath(el);
        window.__clickedXPath = xpath;
    };
    window.__clickHandler._getXPath = """ + _XPATH_SCRIPT.strip() + """;
    document.addEventListener('click', window.__clickHandler, true);
})();

// ── keyboard capture ──────────────────────────────────────────
(function installKey() {
    document.removeEventListener('keydown', window.__keyHandler, true);
    window.__keyHandler = function(e) {
        const k = e.key.toUpperCase();
        if (['S','R','Q'].includes(k)) {
            window.__keyFlag = k;
        }
    };
    document.addEventListener('keydown', window.__keyHandler, true);
})();
"""
    )

    # Poll until we get a result
    while True:
        page.wait_for_timeout(120)

        state = page.evaluate("""
            () => ({
                xpath: window.__clickedXPath,
                key:   window.__keyFlag,
            })
        """)

        if state.get("key"):
            page.evaluate("window.__keyFlag = null; window.__clickedXPath = null;")
            k = state["key"]
            if k == "S": return "skip"
            if k == "R": return "redo"
            if k == "Q": return "quit"

        if state.get("xpath"):
            xpath = state["xpath"]
            page.evaluate("window.__clickedXPath = null;")
            return f"xpath:{xpath}"


# ── alternative: codegen → locator file mode ─────────────────────────

def run_codegen_and_map(url: str, locator_path: str) -> None:
    """
    Launch Playwright codegen, save the output Python file, then
    use regex to extract page.get_by_* and page.locator() calls
    and map them into the locator dict as XPath equivalents.

    This is a simpler alternative to the interactive picker.
    The tester records the full flow and we extract selectors afterward.
    """
    import subprocess
    import tempfile

    out_file = Path(tempfile.gettempdir()) / "codegen_output.py"

    print(f"\nLaunching Playwright codegen for: {url}")
    print(f"Record your interactions, then close the browser.")
    print(f"Output will be saved to: {out_file}\n")

    subprocess.run(
        ["playwright", "codegen",
        "--target", "python",
        "--output", str(out_file),
        url],
        check=True,
    )

    if not out_file.exists():
        print("No output file produced — nothing to map.")
        return

    print(f"\nCodegen output saved to {out_file}")
    print("Parsing selectors from generated code...\n")

    source = out_file.read_text(encoding="utf-8")
    _print_codegen_selectors(source)
    print(
        f"\nTo map these selectors into {locator_path}:\n"
        f"  Run:  python scripts/capture_locators.py "
        f"--locator {locator_path} --url {url}\n"
        f"and click each element interactively."
    )


def _print_codegen_selectors(source: str) -> None:
    """Print all selectors extracted from a codegen output file."""
    patterns = [
        r'get_by_role\("([^"]+)"[^)]*name="([^"]+)"',
        r'get_by_label\("([^"]+)"\)',
        r'get_by_placeholder\("([^"]+)"\)',
        r'get_by_text\("([^"]+)"\)',
        r'locator\("([^"]+)"\)',
    ]
    found = []
    for pat in patterns:
        for match in re.finditer(pat, source):
            found.append(match.group(0))

    if found:
        print("Selectors found in codegen output:")
        for s in found:
            print(f"  {s}")
    else:
        print("No selectors found in codegen output.")


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Interactive Playwright locator capture tool.\n"
            "Opens a browser, prompts you to click each element,\n"
            "and writes the best XPath straight into the locator file."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--locator", "-l", required=True,
        help="Path to the locator file (e.g. locators/trademe_property_search_locators.py)"
    )
    parser.add_argument(
        "--url", "-u", required=True,
        help="URL of the page to open for capturing"
    )
    parser.add_argument(
        "--browser", "-b", default="chromium",
        choices=["chromium", "firefox", "webkit"],
        help="Browser to use (default: chromium)"
    )
    parser.add_argument(
        "--all", "-a", action="store_true",
        help="Recapture ALL keys including already-filled ones (default: empty only)"
    )
    parser.add_argument(
        "--codegen", action="store_true",
        help="Use codegen mode instead of interactive picker"
    )

    args = parser.parse_args()

    if args.codegen:
        run_codegen_and_map(url=args.url, locator_path=args.locator)
    else:
        run_capture(
            locator_path = args.locator,
            url          = args.url,
            browser_name = args.browser,
            empty_only   = not args.all,
        )


if __name__ == "__main__":
    main()

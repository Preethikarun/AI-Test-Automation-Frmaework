#!/usr/bin/env python3
"""
Inspect Trade Me page structure and print actual selectors.
Run this to discover the correct locators for Trade Me elements.
"""

from playwright.sync_api import sync_playwright
import json

def inspect_trademe():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to Trade Me property search
        print("🌐 Opening Trade Me property search page...")
        page.goto("https://www.trademe.co.nz/a/property/residential/sale")
        page.wait_for_load_state("networkidle")
        
        print("\n" + "="*80)
        print("SEARCHING FOR KEY ELEMENTS")
        print("="*80)
        
        # Check for search input - try multiple selectors
        search_inputs = [
            ("//input[@placeholder='Search properties']", "placeholder='Search properties'"),
            ("//input[contains(@placeholder, 'search')]", "contains placeholder 'search'"),
            ("//input[@aria-label*='search']", "aria-label contains 'search'"),
            ("//input[@type='search']", "type='search'"),
            ("//tm-global-search//input", "tm-global-search input"),
        ]
        
        print("\n📍 SEARCH INPUT CANDIDATES:")
        for selector, desc in search_inputs:
            try:
                elem = page.locator(selector).first
                if elem.is_visible():
                    print(f"  ✓ FOUND: {desc}")
                    print(f"    Selector: {selector}")
                    print(f"    Actual HTML: {elem.evaluate('el => el.outerHTML')[:150]}")
                    break
            except:
                pass
        
        # Search for Wellington
        print("\n🔍 Searching for 'Wellington'...")
        try:
            search_input = page.locator("//input[@placeholder='Search properties']").first
            search_input.fill("Wellington")
            page.keyboard.press("Enter")
            page.wait_for_load_state("networkidle")
            print("  ✓ Search completed")
        except Exception as e:
            print(f"  ✗ Search failed: {e}")
            browser.close()
            return
        
        # Check for result containers
        print("\n📍 RESULTS CONTAINER CANDIDATES:")
        result_containers = [
            ("//div[@data-testid='search-results']", "data-testid='search-results'"),
            ("//section[@aria-label='Search results']", "aria-label='Search results'"),
            ("//ul[contains(@class, 'results')]", "ul contains class 'results'"),
            ("//div[contains(@class, 'results')]", "div contains class 'results'"),
            ("//*[@role='list']", "role='list'"),
        ]
        
        for selector, desc in result_containers:
            try:
                elem = page.locator(selector).first
                if elem.is_visible():
                    print(f"  ✓ FOUND: {desc}")
                    print(f"    Selector: {selector}")
                    count = page.locator(selector).count()
                    print(f"    Visible: count={count}")
                    break
            except:
                pass
        
        # Check for property cards
        print("\n📍 PROPERTY CARD CANDIDATES:")
        card_selectors = [
            ("//article[@aria-label]", "article[@aria-label]"),
            ("//div[@data-testid='listing-card']", "data-testid='listing-card'"),
            ("//div[contains(@class, 'card')]", "div contains class 'card'"),
            ("//li[contains(@class, 'result')]", "li contains class 'result'"),
        ]
        
        for selector, desc in card_selectors:
            try:
                cards = page.locator(selector)
                count = cards.count()
                if count > 0:
                    print(f"  ✓ FOUND: {desc}")
                    print(f"    Selector: {selector}")
                    print(f"    Card count: {count}")
                    
                    # Get first card details
                    first_card = cards.first
                    print(f"\n    First card HTML (first 200 chars):")
                    html = first_card.evaluate("el => el.outerHTML")
                    print(f"    {html[:200]}...")
                    break
            except Exception as e:
                print(f"    ✗ Error: {e}")
        
        # Check for filter buttons
        print("\n📍 FILTER BUTTON CANDIDATES:")
        filter_buttons = [
            ("//button[@aria-label='Price']", "aria-label='Price'"),
            ("//button[contains(., 'Price')]", "contains text 'Price'"),
            ("//button[@aria-label*='price']", "aria-label contains 'price'"),
        ]
        
        for selector, desc in filter_buttons:
            try:
                btn = page.locator(selector).first
                if btn.is_visible():
                    print(f"  ✓ FOUND: {desc}")
                    print(f"    Selector: {selector}")
                    break
            except:
                pass
        
        print("\n" + "="*80)
        print("✅ INSPECTION COMPLETE - Browser stays open for manual inspection")
        print("="*80)
        print("\nYou can now manually inspect the page in DevTools.")
        print("When done, close the browser window to continue.\n")
        
        # Keep browser open for manual inspection
        try:
            page.wait_for_url("about:blank")  # This won't happen, keeps browser open
        except KeyboardInterrupt:
            pass
        
        browser.close()

if __name__ == "__main__":
    inspect_trademe()

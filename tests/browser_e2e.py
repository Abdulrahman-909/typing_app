"""Run separately against the development server; CI installs Playwright browsers."""

import os
from playwright.sync_api import sync_playwright

url = os.environ.get("E2E_URL", "http://127.0.0.1:8000")
with sync_playwright() as p:
    browser = p.chromium.launch()
    for language, text in [("en", "calm focus"), ("fa", "کتاب خوب"), ("ps", "زما کتاب")]:
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(url)
        page.locator("#typing").wait_for(state="visible")
        page.locator("#language").select_option(language)
        page.locator("summary").click()
        page.locator("#custom-text").fill(text)
        page.locator("#custom-start").click()
        page.wait_for_function(
            "document.getElementById('passage').textContent.trim() === " + repr(text)
        )
        page.locator("#typing").press_sequentially(text, delay=80)
        page.locator("#results").wait_for(state="visible")
        assert "100%" in page.locator("#result-metrics").inner_text()
        assert page.locator("#passage").get_attribute("dir") == (
            "ltr" if language == "en" else "rtl"
        )
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.close()
    browser.close()
print("Browser E2E: three languages, completion, accuracy and narrow viewport passed.")

"""Open the public explorer in Chromium and check that project records load."""

import argparse
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic, sleep

from playwright.sync_api import Browser, Error, expect, sync_playwright

APP_URL = "https://mia-capital-intelligence.streamlit.app/"


def visit_app(browser: Browser, url: str, timeout_ms: int) -> bool:
    """Return whether this visit used Community Cloud's wake-up control."""
    deadline = monotonic() + timeout_ms / 1000

    def remaining() -> float:
        return max(1, (deadline - monotonic()) * 1000)

    context = browser.new_context()
    try:
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=remaining())
        search = page.get_by_role("textbox", name="Search projects", exact=True)
        wake = page.get_by_role("button", name=re.compile("get this app back up", re.I))
        app_frame = page.locator('iframe[src*="/~/+/"]')
        search.or_(wake).or_(app_frame).first.wait_for(state="visible", timeout=remaining())
        woke = wake.is_visible()
        if woke:
            wake.click(timeout=remaining())
        search.or_(app_frame).first.wait_for(state="visible", timeout=remaining())
        app = page.frame_locator('iframe[src*="/~/+/"]') if app_frame.is_visible() else page
        search = app.get_by_role("textbox", name="Search projects", exact=True)
        expect(search).to_be_visible(timeout=remaining())
        records = app.get_by_role("button", name=re.compile(r"^Browse [1-9][0-9]* source records?$"))
        expect(records).to_be_visible(timeout=remaining())
        expect(records).to_be_enabled(timeout=remaining())
        return woke
    finally:
        context.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=APP_URL)
    parser.add_argument("--executable-path", help="Use an installed browser for local checks")
    args = parser.parse_args()
    started = monotonic()
    lines = []
    success = False
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.executable_path)
        try:
            for attempt in range(1, 4):
                print(f"Opening app, attempt {attempt} of 3...", flush=True)
                try:
                    woke = visit_app(browser, args.url, timeout_ms=90_000)
                    state = "Wake-up was required." if woke else "App opened directly."
                    lines.append(f"Attempt {attempt} passed. {state} Project records loaded.")
                    print(lines[-1], flush=True)
                    success = True
                    break
                except (Error, AssertionError) as error:
                    lines.append(f"Attempt {attempt} failed: {error}")
                    print(lines[-1], flush=True)
                    if attempt < 3:
                        sleep(10)
        finally:
            browser.close()
    lines.append(f"Checked at {datetime.now(UTC).isoformat()} in {monotonic() - started:.1f} seconds.")
    report = "\n\n".join(lines) + "\n"
    print(report)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(summary).open("a", encoding="utf-8") as file:
            file.write("## App availability\n\n" + report)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

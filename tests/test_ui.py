import subprocess
import sys
import time

import pytest
import requests
from playwright.sync_api import Page


@pytest.fixture(scope="session")
def server():
    """Start the FastAPI app in a subprocess for browser tests."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.app:app", "--host", "127.0.0.1", "--port", "8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    for _ in range(30):
        try:
            requests.get("http://127.0.0.1:8001/activities", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        pytest.fail("Server did not start for UI tests")

    yield "http://127.0.0.1:8001"

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()


def test_register_user(page: Page, server):
    base = server

    page.goto(f"{base}/static/index.html")

    # Register a new participant via the UI
    email = "ui-test@mergington.edu"
    page.fill("#email", email)
    page.select_option("#activity", "Chess Club")
    page.click("button[type=submit]")

    # Wait for success message and new participant to appear
    page.wait_for_selector("#message.success", timeout=5000)
    participant = page.locator(f"li:has-text('{email}')")
    participant.wait_for(timeout=5000)
    assert participant.count() >= 1


def test_unregister_user(page: Page, server):
    base = server
    # Pre-create a participant using the API so the UI can remove it
    email = "ui-unreg@mergington.edu"
    r = requests.post(f"{base}/activities/Chess%20Club/signup?email={email}")
    assert r.status_code == 200

    page.goto(f"{base}/static/index.html")

    # Find the pre-created participant and remove via UI
    participant = page.locator(f"li:has-text('{email}')")
    participant.wait_for(timeout=5000)
    assert participant.count() >= 1

    # Click remove and accept confirmation
    page.once("dialog", lambda dialog: dialog.accept())
    participant.locator(".remove-btn").click()

    # Ensure participant is removed from the UI
    participant.wait_for(state="detached", timeout=5000)

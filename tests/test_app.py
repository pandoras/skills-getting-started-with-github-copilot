import copy
from fastapi.testclient import TestClient
import pytest

from src import app as mod

client = TestClient(mod.app)

# Capture baseline at import time so tests can reset state
baseline = copy.deepcopy(mod.activities)

@pytest.fixture(autouse=True)
def reset_activities():
    mod.activities = copy.deepcopy(baseline)
    yield
    mod.activities = copy.deepcopy(baseline)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert "Chess Club" in data


def test_signup_success():
    email = "testuser@mergington.edu"
    resp = client.post(f"/activities/Chess%20Club/signup?email={email}")
    assert resp.status_code == 200
    assert f"Signed up {email} for Chess Club" in resp.json().get("message", "")

    data = client.get("/activities").json()
    assert email in data["Chess Club"]["participants"]


def test_signup_duplicate_returns_400():
    email = "duplicate@mergington.edu"
    r1 = client.post(f"/activities/Chess%20Club/signup?email={email}")
    assert r1.status_code == 200
    r2 = client.post(f"/activities/Chess%20Club/signup?email={email}")
    assert r2.status_code == 400


def test_signup_nonexistent_activity_404():
    resp = client.post("/activities/NotAnActivity/signup?email=a@b.com")
    assert resp.status_code == 404


def test_remove_participant_success():
    # michael@mergington.edu exists in the baseline for Chess Club
    assert "michael@mergington.edu" in mod.activities["Chess Club"]["participants"]
    resp = client.delete("/activities/Chess%20Club/participants?email=michael@mergington.edu")
    assert resp.status_code == 200
    assert "Removed michael@mergington.edu from Chess Club" in resp.json().get("message", "")

    data = client.get("/activities").json()
    assert "michael@mergington.edu" not in data["Chess Club"]["participants"]


def test_remove_nonexistent_participant_returns_404():
    resp = client.delete("/activities/Chess%20Club/participants?email=notexists@mergington.edu")
    assert resp.status_code == 404

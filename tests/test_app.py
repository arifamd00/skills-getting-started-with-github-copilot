import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities before and after each test so tests are isolated."""
    original = copy.deepcopy(app_module.activities)
    try:
        yield
    finally:
        app_module.activities.clear()
        app_module.activities.update(original)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # Basic shape checks
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_and_duplicate():
    activity = "Chess Club"
    email = "test_student@mergington.edu"

    # Signup
    url = f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(email)}"
    resp = client.post(url)
    assert resp.status_code == 200
    assert f"Signed up {email}" in resp.json()["message"]

    # Confirm in participants
    resp2 = client.get("/activities")
    participants = resp2.json()[activity]["participants"]
    assert email in participants

    # Duplicate signup should be rejected
    resp3 = client.post(url)
    assert resp3.status_code == 400
    assert resp3.json()["detail"]


def test_unregister_participant_and_not_found():
    activity = "Programming Class"
    existing = app_module.activities[activity]["participants"][0]

    # Ensure participant exists
    resp = client.get("/activities")
    assert existing in resp.json()[activity]["participants"]

    # Remove the participant
    url = f"/activities/{urllib.parse.quote(activity)}/participants?email={urllib.parse.quote(existing)}"
    del_resp = client.delete(url)
    assert del_resp.status_code == 200
    assert f"Removed {existing}" in del_resp.json()["message"]

    # Confirm removed
    after = client.get("/activities").json()[activity]["participants"]
    assert existing not in after

    # Attempt to remove same participant again -> 404
    del_resp2 = client.delete(url)
    assert del_resp2.status_code == 404
    assert del_resp2.json()["detail"]

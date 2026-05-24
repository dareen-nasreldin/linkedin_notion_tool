"""
Integration tests for /api/save.

Mocks httpx.request (used by notion_api.py) so no real Notion credentials needed.
Verifies that the correct job data reaches the Notion API payload.
"""
import pytest
from unittest.mock import patch, MagicMock, call
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_JOB = {
    "title": "Software Engineer",
    "company": "Shopify",
    "url": "https://example.com/jobs/123",
    "location": "Toronto, ON",
    "job_type": "fulltime",
    "date_posted": "2026-05-20",
    "is_remote": True,
    "flagged_reason": "",
}

FAKE_TOKEN = "ntn_fake_token_for_testing"
FAKE_DB_ID = "fake-database-id-abc"


def _schema_resp():
    """Notion GET database response with all required columns already present."""
    return MagicMock(is_error=False, json=lambda: {
        "properties": {
            "Name": {}, "Company": {}, "Status": {}, "Link": {},
            "Location": {}, "Job Type": {}, "Date Posted": {}, "Remote": {}, "Flagged": {},
        }
    })


def _no_dup_resp():
    """Notion query response: no duplicate found."""
    return MagicMock(is_error=False, json=lambda: {"results": []})


def _dup_resp():
    """Notion query response: duplicate already exists."""
    return MagicMock(is_error=False, json=lambda: {"results": [{"id": "existing-page-id"}]})


def _create_resp(page_id="new-page-id-xyz"):
    """Notion create page success response."""
    return MagicMock(is_error=False, json=lambda: {"object": "page", "id": page_id})


# ── Core save behaviour ───────────────────────────────────────────────────────

@patch("routes.notion_api.httpx.request")
def test_job_saved_to_notion(mock_req):
    """Happy path: job is saved, title/company/url reach Notion correctly."""
    mock_req.side_effect = [_schema_resp(), _no_dup_resp(), _create_resp()]

    resp = client.post("/api/save", json={
        "jobs": [SAMPLE_JOB],
        "notion_token": FAKE_TOKEN,
        "database_id": FAKE_DB_ID,
    })

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["saved"]) == 1
    assert data["saved"][0]["title"] == "Software Engineer"
    assert data["saved"][0]["company"] == "Shopify"
    assert data["saved"][0]["url"] == "https://example.com/jobs/123"
    assert len(data["skipped"]) == 0
    assert len(data["errors"]) == 0


@patch("routes.notion_api.httpx.request")
def test_notion_payload_has_correct_fields(mock_req):
    """The exact payload sent to Notion must map job fields correctly."""
    mock_req.side_effect = [_schema_resp(), _no_dup_resp(), _create_resp()]

    client.post("/api/save", json={
        "jobs": [SAMPLE_JOB],
        "notion_token": FAKE_TOKEN,
        "database_id": FAKE_DB_ID,
    })

    # Third call is the create_page POST
    create_call = mock_req.call_args_list[2]
    body = create_call.kwargs.get("json") or create_call.args[3]
    props = body["properties"]

    assert props["Name"]["title"][0]["text"]["content"] == "Software Engineer"
    assert props["Company"]["select"]["name"] == "Shopify"
    assert props["Link"]["url"] == "https://example.com/jobs/123"
    assert props["Status"]["select"]["name"] == "To Apply"
    assert props["Job Type"]["select"]["name"] == "Full-time"
    assert props["Location"]["rich_text"][0]["text"]["content"] == "Toronto, ON"
    assert props["Remote"]["checkbox"] is True
    assert props["Date Posted"]["date"]["start"] == "2026-05-20"


@patch("routes.notion_api.httpx.request")
def test_duplicate_is_skipped_not_saved(mock_req):
    """Job already in Notion should land in skipped[], not saved[]."""
    mock_req.side_effect = [_schema_resp(), _dup_resp()]

    resp = client.post("/api/save", json={
        "jobs": [SAMPLE_JOB],
        "notion_token": FAKE_TOKEN,
        "database_id": FAKE_DB_ID,
    })

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["saved"]) == 0
    assert len(data["skipped"]) == 1
    assert data["skipped"][0]["url"] == SAMPLE_JOB["url"]
    # create_page must NOT have been called
    assert mock_req.call_count == 2


@patch("routes.notion_api.httpx.request")
def test_comma_job_type_fixed_before_notion(mock_req):
    """Comma-separated job_type must be normalized — Notion rejects commas in select."""
    bad_job = {**SAMPLE_JOB, "job_type": "Parttime, fulltime, internship"}
    mock_req.side_effect = [_schema_resp(), _no_dup_resp(), _create_resp()]

    resp = client.post("/api/save", json={
        "jobs": [bad_job],
        "notion_token": FAKE_TOKEN,
        "database_id": FAKE_DB_ID,
    })

    assert resp.status_code == 200
    assert len(resp.json()["errors"]) == 0

    create_call = mock_req.call_args_list[2]
    body = create_call.kwargs.get("json") or create_call.args[3]
    job_type_val = body["properties"]["Job Type"]["select"]["name"]
    assert "," not in job_type_val
    assert job_type_val == "Part-time"


@patch("routes.notion_api.httpx.request")
def test_unknown_job_type_omitted(mock_req):
    """Unrecognized job_type should be silently dropped, not cause a 400."""
    weird_job = {**SAMPLE_JOB, "job_type": "gig-work-something-weird"}
    mock_req.side_effect = [_schema_resp(), _no_dup_resp(), _create_resp()]

    resp = client.post("/api/save", json={
        "jobs": [weird_job],
        "notion_token": FAKE_TOKEN,
        "database_id": FAKE_DB_ID,
    })

    assert resp.status_code == 200
    create_call = mock_req.call_args_list[2]
    body = create_call.kwargs.get("json") or create_call.args[3]
    assert "Job Type" not in body["properties"]


@patch("routes.notion_api.httpx.request")
def test_multiple_jobs_saved_independently(mock_req):
    """Each job in the list is checked for duplicates and saved separately."""
    job2 = {**SAMPLE_JOB, "url": "https://example.com/jobs/456", "company": "Stripe"}
    mock_req.side_effect = [
        _schema_resp(),
        _no_dup_resp(), _create_resp("page-1"),   # job 1
        _no_dup_resp(), _create_resp("page-2"),   # job 2
    ]

    resp = client.post("/api/save", json={
        "jobs": [SAMPLE_JOB, job2],
        "notion_token": FAKE_TOKEN,
        "database_id": FAKE_DB_ID,
    })

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["saved"]) == 2
    companies = {j["company"] for j in data["saved"]}
    assert companies == {"Shopify", "Stripe"}


@patch("routes.notion_api.httpx.request")
def test_mixed_save_skip_error(mock_req):
    """One saved, one skipped, one erroring Notion call → all reflected in response."""
    job_saved   = {**SAMPLE_JOB, "url": "https://example.com/1", "company": "Google"}
    job_skip    = {**SAMPLE_JOB, "url": "https://example.com/2", "company": "Meta"}
    job_error   = {**SAMPLE_JOB, "url": "https://example.com/3", "company": "Amazon"}

    error_mock = MagicMock(is_error=True, status_code=400)
    error_mock.json.return_value = {"message": "Bad request from Notion"}
    error_mock.text = "Bad request"

    mock_req.side_effect = [
        _schema_resp(),
        _no_dup_resp(), _create_resp(),        # job_saved: no dup → saved
        _dup_resp(),                            # job_skip: dup found → skipped
        _no_dup_resp(), error_mock,             # job_error: no dup → create fails
    ]

    resp = client.post("/api/save", json={
        "jobs": [job_saved, job_skip, job_error],
        "notion_token": FAKE_TOKEN,
        "database_id": FAKE_DB_ID,
    })

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["saved"])   == 1
    assert len(data["skipped"]) == 1
    assert len(data["errors"])  == 1
    assert data["saved"][0]["company"]   == "Google"
    assert data["skipped"][0]["company"] == "Meta"
    assert data["errors"][0]["job"]["company"] == "Amazon"


# ── Notion auth forwarded correctly ──────────────────────────────────────────

@patch("routes.notion_api.httpx.request")
def test_notion_token_in_auth_header(mock_req):
    """The caller's Notion token must be forwarded in Authorization header."""
    mock_req.side_effect = [_schema_resp(), _no_dup_resp(), _create_resp()]

    client.post("/api/save", json={
        "jobs": [SAMPLE_JOB],
        "notion_token": FAKE_TOKEN,
        "database_id": FAKE_DB_ID,
    })

    for c in mock_req.call_args_list:
        headers = c.kwargs.get("headers") or c.args[2]
        assert headers["Authorization"] == f"Bearer {FAKE_TOKEN}"

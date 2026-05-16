"""Direct Notion API calls using stable 2022-06-28 version.

The notion-client library 2.x targets Notion API 2025-09-03 which moved
database schema management to a 'data_sources' concept and dropped 'properties'
from databases.create() and databases.update(). We call the API directly to
keep using the well-documented 2022-06-28 behaviour.
"""
import httpx

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

REQUIRED_PROPERTIES = {
    "Company": {"select": {"options": []}},
    "Link": {"url": {}},
    "Status": {
        "select": {
            "options": [
                {"name": "To Apply",     "color": "blue"},
                {"name": "Applied",      "color": "yellow"},
                {"name": "Interviewing", "color": "green"},
                {"name": "Rejected",     "color": "red"},
                {"name": "Offer",        "color": "purple"},
            ]
        }
    },
}


def _req(method: str, path: str, token: str, body: dict | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    resp = httpx.request(method, f"{BASE_URL}/{path}", headers=headers, json=body, timeout=30)
    if resp.is_error:
        msg = resp.json().get("message", resp.text)
        raise Exception(f"Notion API {resp.status_code}: {msg}")
    return resp.json()


def validate_token(token: str) -> dict:
    return _req("GET", "users/me", token)


def search_pages(token: str) -> list[dict]:
    result = _req("POST", "search", token, body={"filter": {"property": "object", "value": "page"}})
    return result.get("results", [])


def search_databases(token: str) -> list[dict]:
    result = _req("POST", "search", token, body={"filter": {"property": "object", "value": "database"}})
    return result.get("results", [])


def create_database(token: str, parent_page_id: str) -> dict:
    return _req("POST", "databases", token, body={
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "Job Tracker"}}],
        "properties": {
            "Name": {"title": {}},
            **REQUIRED_PROPERTIES,
        },
    })


def get_database(token: str, database_id: str) -> dict:
    return _req("GET", f"databases/{database_id.strip()}", token)


def update_database_properties(token: str, database_id: str, properties: dict) -> dict:
    return _req("PATCH", f"databases/{database_id.strip()}", token, body={"properties": properties})


def ensure_schema(token: str, database_id: str) -> list[str]:
    """Add missing required columns to the database. Returns list of added property names."""
    db = get_database(token, database_id)
    existing = db.get("properties", {})
    missing = {k: v for k, v in REQUIRED_PROPERTIES.items() if k not in existing}
    if missing:
        update_database_properties(token, database_id, missing)
    return list(missing.keys())


def create_page(token: str, database_id: str, job: dict) -> dict:
    return _req("POST", "pages", token, body={
        "parent": {"database_id": database_id.strip()},
        "properties": {
            "Name":    {"title":  [{"text": {"content": job["title"]}}]},
            "Company": {"select": {"name": job["company"].strip()}},
            "Link":    {"url":    job["url"]},
            "Status":  {"select": {"name": "To Apply"}},
        },
    })


def query_database(token: str, database_id: str, page_size: int = 5) -> list[dict]:
    result = _req("POST", f"databases/{database_id.strip()}/query", token, body={"page_size": page_size})
    return result.get("results", [])


def archive_page(token: str, page_id: str) -> dict:
    return _req("PATCH", f"pages/{page_id}", token, body={"archived": True})

"""Direct Notion API calls using stable 2022-06-28 version.

The notion-client library 3.x targets Notion API 2025-09-03 which moved
database schema management to a 'data_sources' concept and dropped 'properties'
from databases.create() and databases.update(). We call the API directly to
keep using the well-documented 2022-06-28 behaviour.
"""
import httpx

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

REQUIRED_PROPERTIES = {
    "Company": {"select": {"options": []}},
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
    "Link":        {"url": {}},
    "Location":    {"rich_text": {}},
    "Job Type": {
        "select": {
            "options": [
                {"name": "Full-time",  "color": "blue"},
                {"name": "Part-time",  "color": "yellow"},
                {"name": "Internship", "color": "green"},
                {"name": "Contract",   "color": "orange"},
                {"name": "Temporary",  "color": "gray"},
            ]
        }
    },
    "Date Posted": {"date": {}},
    "Remote":      {"checkbox": {}},
    "Flagged":     {"rich_text": {}},
}

COLUMN_ORDER = [
    "Name", "Status", "Company", "Location",
    "Job Type", "Remote", "Date Posted", "Link", "Flagged",
]


def _req(
    method: str,
    path: str,
    token: str,
    body: dict | None = None,
    params: dict | None = None,
) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    resp = httpx.request(
        method, f"{BASE_URL}/{path}",
        headers=headers, json=body, params=params, timeout=30,
    )
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


def _score_database(db: dict) -> int:
    """Score how likely a database is a job tracker (higher = better match)."""
    props = db.get("properties", {})
    types = {v.get("type") for v in props.values()}
    score = 0
    if "url" in types:      score += 2
    if "select" in types:   score += 1
    if "checkbox" in types: score += 1
    return score


def find_or_create_database(token: str) -> dict:
    """Find the best matching existing database, or create one. Returns info dict."""
    databases = search_databases(token)

    if databases:
        best = sorted(databases, key=_score_database, reverse=True)[0]
        title_parts = best.get("title", [])
        title = "".join(p.get("plain_text", "") for p in title_parts) or "Untitled"
        return {
            "id": best["id"],
            "url": best.get("url", f"https://notion.so/{best['id'].replace('-', '')}"),
            "title": title,
            "created": False,
        }

    # No databases — create one in the first accessible page
    pages = search_pages(token)
    if not pages:
        raise Exception(
            "No pages or databases are shared with this integration. "
            "In Notion: open any page → ••• → Connections → enable your integration."
        )

    parent_page_id = pages[0]["id"]
    title_prop = pages[0].get("properties", {}).get("title", {}).get("title", [])
    parent_title = title_prop[0].get("plain_text", "Untitled") if title_prop else "Untitled"

    db = create_database(token, parent_page_id)
    return {
        "id": db["id"],
        "url": db.get("url", f"https://notion.so/{db['id'].replace('-', '')}"),
        "title": "Job Tracker",
        "parent_page": parent_title,
        "created": True,
    }


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


def reorder_columns(token: str, database_id: str) -> bool:
    """Set column order in the default table view to COLUMN_ORDER. Returns True if successful."""
    db = get_database(token, database_id)
    props = db.get("properties", {})
    name_to_id = {name: prop["id"] for name, prop in props.items()}

    ordered = []
    for name in COLUMN_ORDER:
        if name in name_to_id:
            ordered.append({"property": name_to_id[name], "visible": True})
    for name, prop in props.items():
        if name not in COLUMN_ORDER:
            ordered.append({"property": prop["id"], "visible": True})

    views_resp = _req("GET", "views", token, params={"database_id": database_id.strip()})
    views = views_resp.get("results", [])
    if not views:
        return False

    view_id = views[0]["id"]
    _req("PATCH", f"views/{view_id}", token, body={"format": {"table_properties": ordered}})
    return True


def ensure_schema(token: str, database_id: str) -> list[str]:
    """Add missing required columns. Returns list of added property names."""
    db = get_database(token, database_id)
    existing = db.get("properties", {})
    missing = {k: v for k, v in REQUIRED_PROPERTIES.items() if k not in existing}
    if missing:
        update_database_properties(token, database_id, missing)
    return list(missing.keys())


def check_duplicate(token: str, database_id: str, url: str) -> bool:
    """Returns True if a page with this URL already exists in the database."""
    result = _req("POST", f"databases/{database_id.strip()}/query", token, body={
        "filter": {"property": "Link", "url": {"equals": url}},
        "page_size": 1,
    })
    return len(result.get("results", [])) > 0


_JOB_TYPE_MAP = {
    "fulltime": "Full-time", "full-time": "Full-time", "full time": "Full-time",
    "parttime": "Part-time", "part-time": "Part-time", "part time": "Part-time",
    "internship": "Internship", "intern": "Internship",
    "contract": "Contract", "contractor": "Contract",
    "temporary": "Temporary", "temp": "Temporary",
}


def _normalize_job_type(raw: str) -> str | None:
    first = raw.split(",")[0].strip().lower()
    return _JOB_TYPE_MAP.get(first)


def create_page(token: str, database_id: str, job: dict) -> dict:
    props = {
        "Name":    {"title":  [{"text": {"content": job["title"]}}]},
        "Company": {"select": {"name": job["company"].strip()}},
        "Link":    {"url":    job["url"]},
        "Status":  {"select": {"name": "To Apply"}},
    }
    if job.get("location"):
        props["Location"] = {"rich_text": [{"text": {"content": str(job["location"])}}]}
    if job.get("job_type"):
        normalized = _normalize_job_type(str(job["job_type"]))
        if normalized:
            props["Job Type"] = {"select": {"name": normalized}}
    if job.get("date_posted"):
        props["Date Posted"] = {"date": {"start": str(job["date_posted"])[:10]}}
    if job.get("is_remote") is not None:
        props["Remote"] = {"checkbox": bool(job["is_remote"])}
    if job.get("flagged_reason"):
        props["Flagged"] = {"rich_text": [{"text": {"content": str(job["flagged_reason"])}}]}
    return _req("POST", "pages", token, body={
        "parent": {"database_id": database_id.strip()},
        "properties": props,
    })


def query_database(token: str, database_id: str, page_size: int = 5) -> list[dict]:
    result = _req("POST", f"databases/{database_id.strip()}/query", token, body={"page_size": page_size})
    return result.get("results", [])


def archive_page(token: str, page_id: str) -> dict:
    return _req("PATCH", f"pages/{page_id}", token, body={"archived": True})

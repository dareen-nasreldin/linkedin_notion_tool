"""
One-time setup. Only NOTION_TOKEN is required in your .env.

What this does:
  1. Finds all databases your integration can access
  2. Picks the job tracker (or lets you choose / creates a new one)
  3. Adds any missing columns without touching existing ones
  4. Saves DATABASE_ID to .env automatically

Usage: python setup_notion_schema.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key
from notion_client import Client

sys.stdout.reconfigure(encoding="utf-8")

ENV_PATH = Path(__file__).parent / ".env"

# All columns the job tracker needs (Name/title is always present in every DB)
REQUIRED_PROPERTIES = {
    "Company": {"select": {}},
    "Status": {
        "select": {
            "options": [
                {"name": "To Apply",   "color": "blue"},
                {"name": "Applied",    "color": "yellow"},
                {"name": "Interview",  "color": "orange"},
                {"name": "Offer",      "color": "green"},
                {"name": "Rejected",   "color": "red"},
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


def _db_title(db: dict) -> str:
    parts = db.get("title", [])
    return "".join(p.get("plain_text", "") for p in parts) or "(Untitled)"


def _create_database(notion: Client, parent_page_id: str) -> str:
    """Create the job tracker database inside the given parent page."""
    db = notion.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "Job Tracker"}}],
        properties={
            "Name": {"title": {}},
            **REQUIRED_PROPERTIES,
        },
    )
    return db["id"]


def _find_or_create_database(notion: Client) -> str:
    """Return the database ID to use, searching first then creating if needed."""
    print("🔍 Searching your Notion workspace...")

    all_results = []
    cursor = None
    while True:
        kwargs = {"page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = notion.search(**kwargs)
        all_results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    databases = [r for r in all_results if r.get("object") == "database"]
    pages     = [r for r in all_results if r.get("object") == "page"]

    if databases:
        def _score(db):
            props = db.get("properties", {})
            types = {v.get("type") for v in props.values()}
            score = 0
            if "url" in types:      score += 2
            if "select" in types:   score += 1
            if "checkbox" in types: score += 1
            return score

        best = sorted(databases, key=_score, reverse=True)[0]
        print(f"   Found existing database: \"{_db_title(best)}\" — using it.")
        return best["id"]

    # No database — create one inside the first accessible page
    if pages:
        parent_page = pages[0]
        parent_title = "".join(
            p.get("plain_text", "")
            for p in parent_page.get("properties", {})
                                .get("title", {})
                                .get("title", [])
        ) or "(untitled)"
        print(f"   No database found. Creating one inside page: \"{parent_title}\"...")
        db_id = _create_database(notion, parent_page["id"])
        print("   ✅ Created \"Job Tracker\" database.")
        return db_id

    # Nothing accessible at all
    print("\n❌ No pages or databases are shared with this integration.")
    print("   In Notion: open any page → ••• menu → Connections → enable your integration.")
    print("   Then re-run this script.")
    raise SystemExit(1)


def setup_schema():
    load_dotenv(ENV_PATH)

    token = os.getenv("NOTION_TOKEN", "").strip()
    if not token:
        print("❌ NOTION_TOKEN not found in .env")
        print("   Add it to your .env file:  NOTION_TOKEN=secret_xxxx")
        return

    notion = Client(auth=token, notion_version="2022-06-28")

    # Verify token works before doing anything else
    try:
        notion.users.me()
    except Exception:
        print("❌ NOTION_TOKEN is invalid or expired. Check your integration token.")
        return

    # Get or find database ID
    db_id = os.getenv("DATABASE_ID", "").strip()
    if db_id:
        print(f"   Using DATABASE_ID from .env: {db_id[:8]}...")
    else:
        db_id = _find_or_create_database(notion)
        set_key(str(ENV_PATH), "DATABASE_ID", db_id)
        print(f"   💾 Saved DATABASE_ID to .env")

    # Check and patch schema
    db = notion.databases.retrieve(db_id)
    existing = set(db.get("properties", {}).keys())

    to_add = {
        name: schema
        for name, schema in REQUIRED_PROPERTIES.items()
        if name not in existing
    }

    if not to_add:
        print("✅ Schema is up to date — all required columns present.")
    else:
        # notion-client 3.x drops 'properties' from databases.update — call raw endpoint instead
        notion.request(
            path=f"databases/{db_id}",
            method="PATCH",
            body={"properties": to_add},
        )
        print(f"✅ Added {len(to_add)} missing column(s): {list(to_add.keys())}")
        print("   Your custom columns were left untouched.")


if __name__ == "__main__":
    setup_schema()

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
import re
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


def _extract_page_id(url_or_id: str) -> str:
    """Pull a 32-char hex ID out of a Notion URL or plain ID string."""
    cleaned = url_or_id.strip().replace("-", "")
    match = re.search(r"[0-9a-f]{32}", cleaned, re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not find a Notion ID in: {url_or_id}")
    raw = match.group(0).lower()
    return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"


def _create_database(notion: Client, parent_page_id: str) -> str:
    """Create a fresh job tracker database under the given page."""
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
    """Return the database ID to use, searching first then optionally creating."""
    print("🔍 Searching your Notion workspace for databases...")

    all_dbs = []
    cursor = None
    while True:
        kwargs = {"filter": {"property": "object", "value": "database"}, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = notion.search(**kwargs)
        all_dbs.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    if not all_dbs:
        print("   No databases found in your workspace.")
    else:
        # Score each database: prefer ones that already look like a job tracker
        def _score(db):
            props = db.get("properties", {})
            types = {v.get("type") for v in props.values()}
            score = 0
            if "url" in types:      score += 2
            if "select" in types:   score += 1
            if "checkbox" in types: score += 1
            return score

        scored = sorted(all_dbs, key=_score, reverse=True)

        if len(scored) == 1:
            db = scored[0]
            print(f"   Found 1 database: \"{_db_title(db)}\"")
            confirm = input("   Use this database? (y/n): ").strip().lower()
            if confirm == "y":
                return db["id"]
        else:
            print(f"   Found {len(scored)} databases:")
            for i, db in enumerate(scored):
                props = db.get("properties", {})
                col_names = ", ".join(list(props.keys())[:5])
                print(f"     {i + 1}. \"{_db_title(db)}\"  [{col_names}...]")
            choice = input("   Select number to use (or press Enter to create a new one): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(scored):
                return scored[int(choice) - 1]["id"]

    # Create a new database
    print("\n📄 Let's create a new Job Tracker database.")
    print("   Open any Notion page where you want the database to live.")
    print("   Copy its URL (e.g. https://notion.so/My-Page-abc123...) and paste it here.")
    page_input = input("   Notion page URL or ID: ").strip()
    page_id = _extract_page_id(page_input)
    db_id = _create_database(notion, page_id)
    print(f"   ✅ Created \"Job Tracker\" database.")
    return db_id


def setup_schema():
    load_dotenv(ENV_PATH)

    token = os.getenv("NOTION_TOKEN", "").strip()
    if not token:
        print("❌ NOTION_TOKEN not found in .env")
        print("   Add it to your .env file:  NOTION_TOKEN=secret_xxxx")
        return

    notion = Client(auth=token)

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
    existing = set(db["properties"].keys())

    to_add = {
        name: schema
        for name, schema in REQUIRED_PROPERTIES.items()
        if name not in existing
    }

    if not to_add:
        print("✅ Schema is up to date — all required columns present.")
    else:
        notion.databases.update(db_id, properties=to_add)
        print(f"✅ Added {len(to_add)} missing column(s): {list(to_add.keys())}")
        print("   Your custom columns were left untouched.")


if __name__ == "__main__":
    setup_schema()

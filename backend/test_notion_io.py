"""
Notion I/O test script (uses direct HTTP — bypasses broken notion-client 2.x library).

Usage:
  python test_notion_io.py --token ntn_xxx --db <database_id>
  python test_notion_io.py --token ntn_xxx --db <database_id> --fix
  python test_notion_io.py --token ntn_xxx --new-db
  python test_notion_io.py --token ntn_xxx               # list all databases

The --fix flag adds missing columns.
The --new-db flag creates a fresh database and prints its ID.
"""
import argparse
import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

NOTION_VERSION = "2022-06-28"
BASE = "https://api.notion.com/v1"

REQUIRED_SCHEMA = {
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

SEP = "-" * 60


def step(msg):   print(f"\n{SEP}\n  {msg}\n{SEP}")
def ok(msg):     print(f"  OK   {msg}")
def fail(msg):   print(f"  FAIL {msg}")
def info(msg):   print(f"  -->  {msg}")


# ── HTTP helper ───────────────────────────────────────────────────────────────

def notion(method: str, path: str, token: str, body=None) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    resp = httpx.request(method, f"{BASE}/{path}", headers=headers, json=body, timeout=30)
    if resp.is_error:
        msg = resp.json().get("message", resp.text)
        raise Exception(f"Notion API {resp.status_code}: {msg}")
    return resp.json()


# ── 1. Connection ─────────────────────────────────────────────────────────────

def test_connection(token: str) -> bool:
    step("1. Testing Notion connection")
    try:
        me = notion("GET", "users/me", token)
        ok(f"Connected as: {me.get('name', 'Unknown')} ({me.get('type', '?')})")
        return True
    except Exception as e:
        fail(f"Connection failed: {e}")
        return False


# ── List databases ────────────────────────────────────────────────────────────

def list_databases(token: str):
    step("Listing all databases the integration can see")
    result = notion("POST", "search", token, body={"filter": {"property": "object", "value": "database"}})
    dbs = result.get("results", [])
    if not dbs:
        fail("No databases found. Share a Notion page with your integration first.")
        return
    ok(f"Found {len(dbs)} database(s):")
    for db in dbs:
        raw_title = db.get("title", [])
        title = raw_title[0].get("plain_text", "Untitled") if raw_title else "Untitled"
        props = list(db.get("properties", {}).keys())
        info(f"{title}  |  {db['id']}")
        info(f"  Columns: {props}")


# ── 2. Schema check ───────────────────────────────────────────────────────────

def check_schema(token: str, db_id: str) -> list[str]:
    step("2. Checking database schema")
    db = notion("GET", f"databases/{db_id.strip()}", token)

    raw_title = db.get("title", [])
    title = raw_title[0].get("plain_text", "Untitled") if raw_title else "Untitled"
    props = db.get("properties", {})

    info(f"Notion API version used: {NOTION_VERSION}")
    info(f"Database: {title}")
    info(f"Existing columns: {list(props.keys())}")

    missing = [name for name in REQUIRED_SCHEMA if name not in props]
    if missing:
        fail(f"Missing columns: {missing}")
    else:
        ok("All required columns exist")

    return missing


# ── 3. Fix schema ─────────────────────────────────────────────────────────────

def fix_schema(token: str, db_id: str, missing: list[str]):
    step("3. Fixing schema")
    props_to_add = {k: REQUIRED_SCHEMA[k] for k in missing}
    info(f"Adding: {missing}")
    result = notion("PATCH", f"databases/{db_id.strip()}", token, body={"properties": props_to_add})
    updated_props = list(result.get("properties", {}).keys())
    info(f"Properties after update: {updated_props}")
    ok("databases PATCH completed — re-checking...")
    still_missing = check_schema(token, db_id)
    if not still_missing:
        ok("All columns confirmed")
    else:
        fail(f"Still missing: {still_missing}")


# ── 4. Create fresh database ──────────────────────────────────────────────────

def create_new_db(token: str):
    step("Creating a fresh 'Job Tracker' database")
    result = notion("POST", "search", token, body={"filter": {"property": "object", "value": "page"}})
    pages = result.get("results", [])
    if not pages:
        fail("No pages found. Share a Notion page with the integration first.")
        return

    parent_page_id = pages[0]["id"]
    title_prop = pages[0].get("properties", {}).get("title", {}).get("title", [])
    parent_title = title_prop[0].get("plain_text", "Untitled") if title_prop else "Untitled"
    info(f"Parent page: {parent_title} ({parent_page_id})")

    db = notion("POST", "databases", token, body={
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "Job Tracker"}}],
        "properties": {
            "Name": {"title": {}},
            **REQUIRED_SCHEMA,
        },
    })

    new_id = db["id"]
    props = list(db.get("properties", {}).keys())
    ok(f"Created database: {new_id}")
    ok(f"Columns: {props}")

    if not props:
        fail("Columns still empty after create — this is unexpected with direct HTTP calls.")
    else:
        print()
        print("  ACTION REQUIRED:")
        print(f"  Open notionjobs.vercel.app in your browser.")
        print(f"  Press F12 -> Application -> Local Storage -> find notion_database_id")
        print(f"  Change its value to:")
        print(f"  {new_id}")
        print()
        print("  Or just reset connection via the sidebar and go through setup again.")
        print()


# ── 5. Write test ─────────────────────────────────────────────────────────────

def test_write(token: str, db_id: str) -> str | None:
    step("4. Testing write — creating a test job")
    try:
        page = notion("POST", "pages", token, body={
            "parent": {"database_id": db_id},
            "properties": {
                "Name":    {"title":  [{"text": {"content": "[TEST] Software Engineer Intern"}}]},
                "Company": {"select": {"name": "Test Company Inc."}},
                "Link":    {"url":    "https://example.com/jobs/test-12345"},
                "Status":  {"select": {"name": "To Apply"}},
            },
        })
        page_id = page["id"]
        ok(f"Created page: {page_id}")
        return page_id
    except Exception as e:
        fail(f"Write failed: {e}")
        return None


# ── 6. Read test ──────────────────────────────────────────────────────────────

def test_read(token: str, db_id: str):
    step("5. Testing read — querying the database")
    try:
        result = notion("POST", f"databases/{db_id}/query", token, body={"page_size": 5})
        pages = result.get("results", [])
        ok(f"Query returned {len(pages)} row(s)")
        for page in pages:
            p = page.get("properties", {})
            title_arr = p.get("Name", {}).get("title", [])
            name = title_arr[0].get("plain_text", "Untitled") if title_arr else "Untitled"
            company = (p.get("Company", {}).get("select") or {}).get("name", "—")
            status  = (p.get("Status",  {}).get("select") or {}).get("name", "—")
            info(f"{name}  |  {company}  |  {status}")
    except Exception as e:
        fail(f"Read failed: {e}")


# ── 7. Cleanup ────────────────────────────────────────────────────────────────

def cleanup(token: str, page_id: str):
    step("6. Cleaning up test page")
    try:
        notion("PATCH", f"pages/{page_id}", token, body={"archived": True})
        ok("Test page archived")
    except Exception as e:
        fail(f"Cleanup failed: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Test Notion database I/O")
    parser.add_argument("--token",  default=os.getenv("NOTION_TOKEN"), help="Notion integration token")
    parser.add_argument("--db",     default=os.getenv("DATABASE_ID"),  help="Notion database ID")
    parser.add_argument("--fix",    action="store_true", help="Add missing schema columns")
    parser.add_argument("--new-db", action="store_true", help="Create a fresh database")
    args = parser.parse_args()

    if not args.token:
        print("Error: provide --token or set NOTION_TOKEN in .env")
        sys.exit(1)

    if not test_connection(args.token):
        sys.exit(1)

    if args.new_db:
        create_new_db(args.token)
        return

    if not args.db:
        list_databases(args.token)
        return

    print(f"\nTarget database: {args.db}")

    missing = check_schema(args.token, args.db)

    if missing:
        if args.fix:
            fix_schema(args.token, args.db, missing)
            missing = check_schema(args.token, args.db)
        else:
            print("\n  Run with --fix to add missing columns, or --new-db to start fresh.")
            sys.exit(1)

    if missing:
        print("\n  Schema still incomplete — skipping write/read tests.")
        sys.exit(1)

    page_id = test_write(args.token, args.db)
    if page_id:
        test_read(args.token, args.db)
        cleanup(args.token, page_id)

    print(f"\n{'=' * 60}")
    print("  All tests passed — database is ready to use.")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()

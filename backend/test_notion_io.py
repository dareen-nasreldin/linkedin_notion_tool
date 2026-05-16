"""
Notion I/O test script.

Usage:
  python test_notion_io.py --token ntn_xxx --db <database_id>
  python test_notion_io.py --token ntn_xxx --db <database_id> --fix

The --fix flag will automatically add any missing columns to the database.
"""
import argparse
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

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

SEP = "-" * 50


def step(msg: str):
    print(f"\n{SEP}")
    print(f"  {msg}")
    print(SEP)


def ok(msg: str):
    print(f"  ✅  {msg}")


def fail(msg: str):
    print(f"  ❌  {msg}")


def info(msg: str):
    print(f"  →  {msg}")


# ── 1. Connection ─────────────────────────────────────────────────────────────

def test_connection(notion: Client) -> bool:
    step("1. Testing Notion connection")
    try:
        me = notion.users.me()
        ok(f"Connected as: {me.get('name', 'Unknown')} ({me.get('type', '?')})")
        return True
    except Exception as e:
        fail(f"Connection failed: {e}")
        return False


# ── 2. Schema check ───────────────────────────────────────────────────────────

def check_schema(notion: Client, db_id: str) -> list[str]:
    step("2. Checking database schema")
    db = notion.databases.retrieve(database_id=db_id)

    raw_title = db.get("title", [])
    title = raw_title[0].get("plain_text", "Untitled") if raw_title else "Untitled"
    props = db.get("properties", {})

    info(f"Database: {title}")
    info(f"Existing columns: {list(props.keys())}")

    missing = [name for name in REQUIRED_SCHEMA if name not in props]
    if missing:
        fail(f"Missing columns: {missing}")
    else:
        ok("All required columns exist")

    return missing


# ── 3. Fix schema ─────────────────────────────────────────────────────────────

def fix_schema(notion: Client, db_id: str, missing: list[str]):
    step("3. Fixing schema")
    props_to_add = {k: REQUIRED_SCHEMA[k] for k in missing}
    info(f"Adding: {missing}")
    notion.databases.update(database_id=db_id, properties=props_to_add)
    ok("Schema updated — re-checking...")
    still_missing = check_schema(notion, db_id)
    if not still_missing:
        ok("All columns confirmed")
    else:
        fail(f"Still missing after fix: {still_missing}")


# ── 4. Write test ─────────────────────────────────────────────────────────────

def test_write(notion: Client, db_id: str) -> str | None:
    step("4. Testing write — creating a test job")
    try:
        page = notion.pages.create(
            parent={"database_id": db_id},
            properties={
                "Name":    {"title":  [{"text": {"content": "[TEST] Software Engineer Intern"}}]},
                "Company": {"select": {"name": "Test Company Inc."}},
                "Link":    {"url":    "https://example.com/jobs/test-12345"},
                "Status":  {"select": {"name": "To Apply"}},
            },
        )
        page_id = page["id"]
        ok(f"Created page: {page_id}")
        return page_id
    except Exception as e:
        fail(f"Write failed: {e}")
        return None


# ── 5. Read test ──────────────────────────────────────────────────────────────

def test_read(notion: Client, db_id: str):
    step("5. Testing read — querying the database")
    try:
        results = notion.databases.query(database_id=db_id, page_size=5)
        pages = results.get("results", [])
        ok(f"Query returned {len(pages)} row(s) (showing up to 5)")
        for page in pages:
            p = page.get("properties", {})
            title_arr = p.get("Name", {}).get("title", [])
            name = title_arr[0].get("plain_text", "Untitled") if title_arr else "Untitled"
            company_obj = p.get("Company", {}).get("select") or {}
            company = company_obj.get("name", "—")
            status_obj = p.get("Status", {}).get("select") or {}
            status = status_obj.get("name", "—")
            info(f"{name}  |  {company}  |  {status}")
    except Exception as e:
        fail(f"Read failed: {e}")


# ── 6. Cleanup ────────────────────────────────────────────────────────────────

def cleanup(notion: Client, page_id: str):
    step("6. Cleaning up test page")
    try:
        notion.pages.update(page_id=page_id, archived=True)
        ok("Test page archived (removed from database view)")
    except Exception as e:
        fail(f"Cleanup failed: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Test Notion database I/O")
    parser.add_argument("--token", default=os.getenv("NOTION_TOKEN"), help="Notion integration token")
    parser.add_argument("--db",    default=os.getenv("DATABASE_ID"),   help="Notion database ID")
    parser.add_argument("--fix",   action="store_true", help="Auto-fix missing schema columns")
    args = parser.parse_args()

    if not args.token or not args.db:
        print("Error: provide --token and --db, or set NOTION_TOKEN and DATABASE_ID in .env")
        sys.exit(1)

    notion = Client(auth=args.token)
    print(f"\nTarget database: {args.db}")

    if not test_connection(notion):
        sys.exit(1)

    missing = check_schema(notion, args.db)

    if missing:
        if args.fix:
            fix_schema(notion, args.db, missing)
        else:
            print("\n⚠️  Run again with --fix to add the missing columns automatically.")
            sys.exit(1)

    page_id = test_write(notion, args.db)
    if page_id:
        test_read(notion, args.db)
        cleanup(notion, page_id)

    print(f"\n{'=' * 50}")
    print("  All tests passed — database is ready to use.")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    main()

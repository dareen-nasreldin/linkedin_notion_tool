"""
Run once to add any missing properties to your Notion database.
Safe to re-run — never removes existing columns (preserves custom ones).

Usage: python setup_notion_schema.py
"""
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()
notion = Client(auth=os.getenv("NOTION_TOKEN"))
DATABASE_ID = os.getenv("DATABASE_ID", "").strip()

REQUIRED_PROPERTIES = {
    "Location": {"rich_text": {}},
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


def setup_schema():
    db = notion.databases.retrieve(DATABASE_ID)
    existing = set(db["properties"].keys())

    to_add = {
        name: schema
        for name, schema in REQUIRED_PROPERTIES.items()
        if name not in existing
    }

    if not to_add:
        print("✅ Schema already up to date — no changes needed.")
        return

    notion.databases.update(DATABASE_ID, properties=to_add)
    print(f"✅ Added {len(to_add)} missing properties: {list(to_add.keys())}")
    print("   Existing custom columns were left untouched.")


if __name__ == "__main__":
    setup_schema()

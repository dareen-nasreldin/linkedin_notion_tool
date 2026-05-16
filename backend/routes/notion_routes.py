from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from notion_client import Client

router = APIRouter()

REQUIRED_PROPERTIES = {
    "Company": {"select": {"options": []}},
    "Link": {"url": {}},
    "Status": {
        "select": {
            "options": [
                {"name": "To Apply", "color": "blue"},
                {"name": "Applied", "color": "yellow"},
                {"name": "Interviewing", "color": "green"},
                {"name": "Rejected", "color": "red"},
                {"name": "Offer", "color": "purple"},
            ]
        }
    },
}


def ensure_schema(notion: Client, database_id: str) -> list[str]:
    """Add any missing required columns to the database. Returns list of added property names."""
    db = notion.databases.retrieve(database_id=database_id.strip())
    existing = db.get("properties", {})
    missing = {k: v for k, v in REQUIRED_PROPERTIES.items() if k not in existing}
    if missing:
        notion.databases.update(database_id=database_id.strip(), properties=missing)
    return list(missing.keys())


class SetupRequest(BaseModel):
    notion_token: str


class RepairRequest(BaseModel):
    notion_token: str
    database_id: str


class AddJobRequest(BaseModel):
    notion_token: str
    database_id: str
    title: str
    company: str
    url: str


@router.post("/notion/setup")
def setup_notion(req: SetupRequest):
    try:
        notion = Client(auth=req.notion_token)
        notion.users.me()  # validate token

        results = notion.search(filter={"property": "object", "value": "page"})
        pages = results.get("results", [])

        if not pages:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No Notion pages found. Please create a page in Notion "
                    "and share it with your integration first."
                ),
            )

        parent_page_id = pages[0]["id"]
        title_prop = pages[0].get("properties", {}).get("title", {}).get("title", [])
        parent_title = title_prop[0].get("plain_text", "Untitled") if title_prop else "Untitled"

        db = notion.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": "Job Tracker"}}],
            properties={
                "Name": {"title": {}},
                **REQUIRED_PROPERTIES,
            },
        )

        database_id = db["id"]
        database_url = db.get("url", f"https://notion.so/{database_id.replace('-', '')}")

        # Ensure schema is correct even if create returned partial state
        ensure_schema(notion, database_id)

        return {
            "success": True,
            "database_id": database_id,
            "database_url": database_url,
            "parent_page": parent_title,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Notion setup failed: {str(e)}")


@router.post("/notion/repair")
def repair_notion(req: RepairRequest):
    """Check and repair missing columns in an existing database."""
    try:
        notion = Client(auth=req.notion_token)
        notion.users.me()
        added = ensure_schema(notion, req.database_id)
        return {
            "success": True,
            "added": added,
            "message": f"Added {len(added)} missing column(s): {added}" if added else "All columns already present.",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Repair failed: {str(e)}")


@router.post("/notion/add")
def add_job(req: AddJobRequest):
    try:
        notion = Client(auth=req.notion_token)
        ensure_schema(notion, req.database_id)
        notion.pages.create(
            parent={"database_id": req.database_id.strip()},
            properties={
                "Name": {"title": [{"text": {"content": req.title}}]},
                "Company": {"select": {"name": req.company.strip()}},
                "Link": {"url": req.url},
                "Status": {"select": {"name": "To Apply"}},
            },
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

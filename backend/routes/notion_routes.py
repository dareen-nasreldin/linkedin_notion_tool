from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .notion_api import (
    validate_token, search_pages, create_database,
    ensure_schema, REQUIRED_PROPERTIES,
)

router = APIRouter()


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
        me = validate_token(req.notion_token)
        if me.get("object") != "user":
            raise HTTPException(status_code=400, detail="Invalid Notion token.")

        pages = search_pages(req.notion_token)
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

        db = create_database(req.notion_token, parent_page_id)
        database_id = db["id"]
        database_url = db.get("url", f"https://notion.so/{database_id.replace('-', '')}")

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
    try:
        validate_token(req.notion_token)
        added = ensure_schema(req.notion_token, req.database_id)
        return {
            "success": True,
            "added": added,
            "message": (
                f"Added {len(added)} missing column(s): {added}"
                if added else "All columns already present."
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Repair failed: {str(e)}")


@router.post("/notion/add")
def add_job(req: AddJobRequest):
    try:
        from .notion_api import create_page
        ensure_schema(req.notion_token, req.database_id)
        create_page(req.notion_token, req.database_id, {
            "title": req.title,
            "company": req.company,
            "url": req.url,
        })
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

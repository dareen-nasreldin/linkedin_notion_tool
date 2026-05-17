from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .notion_api import (
    validate_token, find_or_create_database,
    ensure_schema, reorder_columns, REQUIRED_PROPERTIES,
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

        info = find_or_create_database(req.notion_token)
        database_id = info["id"]

        added = ensure_schema(req.notion_token, database_id)

        reordered = False
        try:
            reordered = reorder_columns(req.notion_token, database_id)
        except Exception:
            pass

        return {
            "success": True,
            "database_id": database_id,
            "database_url": info["url"],
            "database_title": info["title"],
            "parent_page": info.get("parent_page"),
            "created": info["created"],
            "columns_added": added,
            "columns_reordered": reordered,
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

        reordered = False
        try:
            reordered = reorder_columns(req.notion_token, req.database_id)
        except Exception:
            pass

        return {
            "success": True,
            "added": added,
            "reordered": reordered,
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

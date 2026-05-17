from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from jobspy import scrape_jobs
import requests
from bs4 import BeautifulSoup
from .ai_filter import filter_jobs
from .notion_api import ensure_schema, create_page, check_duplicate

router = APIRouter()

SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


class SearchRequest(BaseModel):
    keyword: str
    location: str
    country: str = "canada"
    results_wanted: int = 10
    notion_token: str
    database_id: str


class AddUrlRequest(BaseModel):
    url: str
    notion_token: str
    database_id: str


class AddManualRequest(BaseModel):
    title: str
    company: str
    url: str
    notion_token: str
    database_id: str


@router.post("/search")
def search_jobs(req: SearchRequest):
    try:
        jobs_df = scrape_jobs(
            site_name=["indeed"],
            search_term=req.keyword,
            location=req.location,
            results_wanted=req.results_wanted,
            hours_old=72,
            country_selection=req.country,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job search failed: {str(e)}")

    if jobs_df is None or jobs_df.empty:
        return {"saved": [], "filtered": [], "errors": []}

    raw_jobs = []
    for _, row in jobs_df.iterrows():
        title = str(row.get("title", "")).strip()
        company = str(row.get("company", "")).strip()
        url = str(row.get("job_url", "")).strip()
        if not (title and company and url and title != "nan" and company != "nan"):
            continue

        loc = row.get("location")
        if isinstance(loc, dict):
            parts = [loc.get("city"), loc.get("state")]
            location_str = ", ".join(p for p in parts if p) or None
        elif isinstance(loc, str) and loc.strip():
            location_str = loc.strip()
        else:
            location_str = None

        raw_jobs.append({
            "title": title,
            "company": company,
            "url": url,
            "location": location_str,
            "job_type": row.get("job_type"),
            "date_posted": row.get("date_posted"),
            "is_remote": row.get("is_remote"),
        })

    classified = filter_jobs(raw_jobs, req.keyword)

    try:
        ensure_schema(req.notion_token, req.database_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Notion schema repair failed: {str(e)}")

    saved, filtered, errors, skipped = [], [], [], []
    for item in classified:
        job = item["job"]
        if item["decision"] == "keep":
            try:
                if check_duplicate(req.notion_token, req.database_id, job["url"]):
                    skipped.append(job)
                else:
                    create_page(req.notion_token, req.database_id, job)
                    saved.append(job)
            except Exception as e:
                errors.append({"job": job, "error": str(e)})
        else:
            filtered.append({"job": job, "reason": item["reason"]})

    return {"saved": saved, "filtered": filtered, "skipped": skipped, "errors": errors}


@router.post("/add-url")
def add_single_url(req: AddUrlRequest):
    try:
        response = requests.get(req.url, headers=SCRAPE_HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        title = None
        company = None

        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

        for selector in [
            {"class_": "topcard__org-name-link"},
            {"class_": "top-card-layout__first-subline"},
            {"class_": "jobs-unified-top-card__company-name"},
        ]:
            tag = soup.find(attrs=selector)
            if tag:
                company = tag.get_text(strip=True)
                break

        if title and company:
            return {"scraped": True, "title": title, "company": company, "url": req.url}

        return {
            "scraped": False,
            "message": "Could not extract job details automatically. Please fill them in below.",
        }
    except Exception as e:
        return {"scraped": False, "message": f"Could not reach that URL: {str(e)}"}


@router.post("/add-manual")
def add_manual(req: AddManualRequest):
    try:
        ensure_schema(req.notion_token, req.database_id)
        job = {"title": req.title, "company": req.company, "url": req.url}
        create_page(req.notion_token, req.database_id, job)
        return {"success": True, "job": job}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from notion_client import Client
from jobspy import scrape_jobs
import requests
from bs4 import BeautifulSoup
from .ai_filter import filter_jobs

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


def _save_to_notion(notion_token: str, database_id: str, job: dict, ai_note: str = ""):
    notion = Client(auth=notion_token)
    notion.pages.create(
        parent={"database_id": database_id.strip()},
        properties={
            "Name": {"title": [{"text": {"content": job["title"]}}]},
            "Company": {"select": {"name": job["company"].strip()}},
            "Link": {"url": job["url"]},
            "Status": {"select": {"name": "To Apply"}},
            "AI Note": {
                "rich_text": [{"text": {"content": ai_note}}] if ai_note else []
            },
        },
    )


@router.post("/search")
def search_jobs(req: SearchRequest):
    try:
        jobs_df = scrape_jobs(
            site_name=["linkedin", "indeed"],
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
        if title and company and url and title != "nan" and company != "nan":
            raw_jobs.append({"title": title, "company": company, "url": url})

    classified = filter_jobs(raw_jobs, req.keyword)

    saved, filtered, errors = [], [], []
    for item in classified:
        job = item["job"]
        if item["decision"] == "keep":
            try:
                _save_to_notion(req.notion_token, req.database_id, job)
                saved.append(job)
            except Exception as e:
                errors.append({"job": job, "error": str(e)})
        else:
            filtered.append({"job": job, "reason": item["reason"]})

    return {"saved": saved, "filtered": filtered, "errors": errors}


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
        job = {"title": req.title, "company": req.company, "url": req.url}
        _save_to_notion(req.notion_token, req.database_id, job)
        return {"success": True, "job": job}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from notion_client import Client
from jobspy import scrape_jobs
from filters import flag_jobs

# Load your Notion credentials
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
RESULTS_WANTED = int(os.getenv("RESULTS_WANTED", 20))
HOURS_OLD = int(os.getenv("HOURS_OLD", 72))
COUNTRY = os.getenv("COUNTRY", "canada")

# Initialize Notion
notion = Client(auth=NOTION_TOKEN)

def check_duplicate(url: str) -> bool:
    """Returns True if a job with this URL already exists in Notion."""
    response = notion.databases.query(
        database_id=DATABASE_ID.strip(),
        filter={"property": "Link", "url": {"equals": url}}
    )
    return len(response["results"]) > 0

async def add_to_notion(data):
    """Resilient logic to add jobs directly to Notion."""
    if check_duplicate(data['url']):
        print(f"⏭️  SKIP (duplicate): {data['title']}")
        return
    try:
        props = {
            "Name":    {"title":  [{"text": {"content": data['title']}}]},
            "Company": {"select": {"name": data['company'].strip()}},
            "Link":    {"url": data['url']},
            "Status":  {"select": {"name": "To Apply"}},
        }
        if data.get("location"):
            props["Location"] = {"rich_text": [{"text": {"content": data["location"]}}]}
        if data.get("job_type"):
            props["Job Type"] = {"select": {"name": str(data["job_type"]).capitalize()}}
        if data.get("date_posted"):
            props["Date Posted"] = {"date": {"start": str(data["date_posted"])[:10]}}
        if data.get("is_remote") is not None:
            props["Remote"] = {"checkbox": bool(data["is_remote"])}
        if data.get("flagged_reason"):
            props["Flagged"] = {"rich_text": [{"text": {"content": data["flagged_reason"]}}]}
        notion.pages.create(
            parent={"database_id": DATABASE_ID.strip()},
            properties=props,
        )
        flag_note = f" ⚠️ [{data['flagged_reason']}]" if data.get("flagged_reason") else ""
        print(f"✅ SUCCESS: {data['title']} at {data['company']} added!{flag_note}")
    except Exception as e:
        print(f"❌ Notion Error: {e}")

async def scrape_single_url(url):
    """Your Phase 1 Playwright scraper for specific links."""
    print("Scraping single job page...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded")
            # Refined selectors for LinkedIn job pages
            title = await page.locator('h1').first.inner_text()
            company = await page.locator('.topcard__org-name-link').first.inner_text()
            return {"title": title.strip(), "company": company.strip(), "url": url}
        finally:
            await browser.close()

async def run_bulk_search():
    """Phase 3: Bulk Search using JobSpy."""
    keyword = input("Enter search (e.g., Software Engineer Intern): ")
    location = input("Enter location (e.g., Toronto): ")
    job_type = input("Filter job type (internship/full-time/blank=any): ").strip() or None

    print(f"🔍 Searching for top {RESULTS_WANTED} '{keyword}' roles...")
    jobs = scrape_jobs(
        site_name=["linkedin", "indeed"],
        search_term=keyword,
        location=location,
        results_wanted=RESULTS_WANTED,
        hours_old=HOURS_OLD,
        country_selection=COUNTRY,
        job_type=job_type,
    )

    jobs = flag_jobs(jobs, keyword)
    flagged = (jobs["flagged_reason"] != "").sum()
    print(f"📋 {len(jobs)} jobs found ({flagged} flagged).")

    for _, row in jobs.iterrows():
        loc = row.get("location")
        if isinstance(loc, dict):
            parts = [loc.get("city"), loc.get("state")]
            location_str = ", ".join(p for p in parts if p) or None
        elif isinstance(loc, str) and loc.strip():
            location_str = loc.strip()
        else:
            location_str = None

        await add_to_notion({
            "title":          row["title"],
            "company":        row["company"],
            "url":            row["job_url"],
            "location":       location_str,
            "job_type":       row.get("job_type"),
            "date_posted":    row.get("date_posted"),
            "is_remote":      row.get("is_remote"),
            "flagged_reason": row.get("flagged_reason", ""),
        })

async def main():
    print("\n--- LinkedIn/Notion Automator ---")
    print("1. Add Single Job URL (Playwright)")
    print("2. Bulk Search (JobSpy)")
    choice = input("Select 1 or 2: ")

    if choice == "1":
        url = input("Paste LinkedIn URL: ")
        data = await scrape_single_url(url)
        if data: await add_to_notion(data)
    elif choice == "2":
        await run_bulk_search()

if __name__ == "__main__":
    asyncio.run(main())
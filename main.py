import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from notion_client import Client
from jobspy import scrape_jobs

# Load your Notion credentials
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

# Initialize Notion
notion = Client(auth=NOTION_TOKEN)

async def add_to_notion(data):
    """Resilient logic to add jobs directly to Notion."""
    try:
        notion.pages.create(
            parent={"database_id": DATABASE_ID.strip()},
            properties={
                "Name": {"title": [{"text": {"content": data['title']}}]},
                "Company": {"select": {"name": data['company'].strip()}},
                "Link": {"url": data['url']},
                "Status": {"select": {"name": "To Apply"}}
            }
        )
        print(f"✅ SUCCESS: {data['title']} at {data['company']} added!")
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
    
    print(f"🔍 Searching for top 5 '{keyword}' roles...")
    jobs = scrape_jobs(
        site_name=["linkedin", "indeed"],
        search_term=keyword,
        location=location,
        results_wanted=5,
        hours_old=72,
        country_selection="canada"
    )

    for _, row in jobs.iterrows():
        await add_to_notion({
            "title": row['title'],
            "company": row['company'],
            "url": row['job_url']
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
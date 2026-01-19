import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from notion_client import Client

# Load secrets
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

# Initialize Notion client
notion = Client(auth=NOTION_TOKEN)

async def scrape_linkedin(url):
    async with async_playwright() as p:
        # Using a standard browser context to look more human
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # Increase timeout to 60s for slow loads
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3) # Wait for JS to render the job details

            # Try multiple selectors because LinkedIn changes them constantly
            title = await page.locator('h1, .top-card-layout__title').first.inner_text()
            company = await page.locator('.topcard__org-name-link, .top-card-layout__first-subline a').first.inner_text()
            location = await page.locator('.topcard__flavor--bullet, .top-card-layout__first-subline span:nth-child(2)').first.inner_text()
            
            job_data = {
                "title": title.strip(),
                "company": company.strip(),
                "location": location.strip().split('·')[0].strip(), # Clean up "City · 2,000 applicants"
                "url": url
            }
            return job_data
        finally:
            await browser.close()

async def add_to_notion(data):
    clean_db_id = DATABASE_ID.strip()
    
    print(f"Checking for duplicates in Notion...")
    
    try:
        # Standard query call - this is the most reliable if the SDK is working
        response = notion.databases.query(
            database_id=clean_db_id,
            filter={
                "property": "Link",
                "url": {"equals": data['url']}
            }
        )
    except Exception as e:
        # If the query fails, we skip it and try to just create the page
        print(f"⚠️ Duplicate check skipped (Error: {e})")
        response = {"results": []}

    if response.get("results"):
        print(f"⚠️ Job already exists in Notion: {data['title']}")
        return

    print(f"Adding {data['title']} to Notion...")
    try:
        # Standard page creation
        notion.pages.create(
            parent={"database_id": clean_db_id},
            properties={
                "Name": {"title": [{"text": {"content": data['title']}}]},
                "Company": {"select": {"name": data['company'].strip()}},
                "Link": {"url": data['url']},
                "Status": {"select": {"name": "To Apply"}}
            }
        )
        print(f"✅ SUCCESS: {data['title']} added to your Job Tracker!")
    except Exception as e:
        print(f"❌ Notion Creation Error: {e}")
        print("Note: Ensure your 'Status' column in Notion has a 'To Apply' option.")
async def main():
    job_url = input("Enter LinkedIn Job URL: ")
    print("Scraping... (please wait)")
    try:
        data = await scrape_linkedin(job_url)
        if data:
            await add_to_notion(data)
    except Exception as e:
        print(f"❌ Scraper Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
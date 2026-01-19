import asyncio
from playwright.async_api import async_playwright

async def test_scrape(url):
    async with async_playwright() as p:
        print(f"Opening browser...")
        browser = await p.chromium.launch(headless=False) # Headed mode to see what happens
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print(f"Navigating to: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5) # Long wait to ensure page fully renders

            # Check if we are being blocked
            if "Security Verification" in await page.content():
                print("❌ BLOCKED: LinkedIn is showing a CAPTCHA/Auth wall.")
                return

            title = await page.locator('h1, .top-card-layout__title').first.inner_text()
            print(f"Found Title: {title}")
            
            company = await page.locator('.topcard__org-name-link, .top-card-layout__first-subline a').first.inner_text()
            print(f"Found Company: {company}")

        except Exception as e:
            print(f"❌ Scraper Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    url = input("Enter LinkedIn URL: ")
    asyncio.run(test_scrape(url))
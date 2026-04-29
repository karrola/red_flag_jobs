import asyncio
from playwright.async_api import async_playwright

URL_GOWORK = "https://www.gowork.pl/opinie_czytaj,949234"
SELECTOR = "span.MuiTypography-body1.whitespace-pre-wrap"


async def _scrape(url: str) -> list[str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="pl-PL",
        )

        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            for _ in range(5):
                await page.mouse.wheel(0, 600)
                await asyncio.sleep(0.8)

            await asyncio.sleep(2)

            await page.wait_for_selector(SELECTOR, timeout=20000)
            reviews = await page.locator(SELECTOR).all_inner_texts()

        finally:
            await browser.close()

    return reviews


def get_reviews(url: str = URL_GOWORK) -> list[str]:
    return asyncio.run(_scrape(url))
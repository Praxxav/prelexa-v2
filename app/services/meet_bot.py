# app/services/meet_bot.py
from playwright.async_api import async_playwright

async def join_google_meet(meet_url: str):
    p = await async_playwright().start()
    browser = await p.chromium.launch(
        headless=False,
        args=[
            "--use-fake-ui-for-media-stream",
            "--autoplay-policy=no-user-gesture-required"
        ]
    )

    page = await browser.new_page()
    await page.goto(meet_url)
    await page.wait_for_timeout(3000)

    await page.click(
        "button:has-text('Ask to join'), button:has-text('Join now')"
    )

    return browser

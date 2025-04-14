from playwright.async_api import async_playwright


class Renderer:
    def __init__(self):
        pass

    async def init(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch()

    async def close(self):
        await self._browser.close()
        await self._playwright.stop()

    async def render(self, url: str) -> str:
        page = await self._browser.new_page()
        await page.goto(url)
        await page.pause()
        return await page.content()

"""TikTok Creative Center — trending hashtags in Games, public, via Playwright.
The hashtag table renders client-side (rank / #tag / posts / views over the selected period,
default 7 days); the industry filter is a byted-select input whose value reads "All".
Top hashtags get an example clip id scraped from their detail page (hero = TikTok embed)."""
import asyncio, re
from ..util import parse_count

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
BASE = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en"

def _parse_rows(text):
    rows, tag, nums = [], None, []
    for line in [l.strip() for l in text.splitlines() if l.strip()]:
        if line.startswith("#") and len(line) > 1 and " " not in line:
            tag, nums = line[1:], []
        elif tag and re.fullmatch(r"[\d.,]+[KMB]?", line):
            nums.append(parse_count(line))
        elif tag and line == "See analytics":
            if len(nums) >= 2: rows.append({"tag": tag, "posts": nums[0], "views": nums[1]})
            tag, nums = None, []
    return rows

async def _harvest(detail_top=8, more_clicks=1):
    from playwright.async_api import async_playwright
    out = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        try:
            pg = await (await b.new_context(user_agent=UA)).new_page()
            await pg.goto(BASE, timeout=45000)
            await pg.wait_for_timeout(3500)
            # industry filter → Games
            clicked = await pg.evaluate("""() => {
              const el=[...document.querySelectorAll('input.byted-input')].find(i=>i.value==='All');
              if(!el) return false;
              el.dispatchEvent(new MouseEvent('mousedown',{bubbles:true})); el.click(); return true; }""")
            if clicked:
                await pg.wait_for_timeout(1200)
                opt = pg.locator(".byted-select-option", has_text="Games").first
                if await opt.count():
                    await opt.click()
                    await pg.wait_for_timeout(2500)
            for _ in range(more_clicks):
                vm = pg.locator("button", has_text="View more").first
                if await vm.count():
                    try: await vm.click(); await pg.wait_for_timeout(2000)
                    except Exception: break
            rows = _parse_rows(await pg.evaluate("document.body.innerText"))
            # per-hashtag detail pages are login-gated → no clip ids anonymously; the caller
            # attaches a hero (Games hashtags are game names → YouTube clip of the game).
            for r in rows[:detail_top]:
                r["url"] = BASE
                out.append(r)
        finally:
            await b.close()
    return out

def hashtags(detail_top=8):
    return asyncio.run(_harvest(detail_top))

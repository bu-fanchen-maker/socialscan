"""X search via Playwright with a logged-in storage_state (one manual login, then reuse).
Selectors and the like/repost/view parsing were validated in Chrome on 21–22 Sep 2026.
Floors: dev posts 2–5k likes; mainstream 10–20k; anything ≥100k is AAA/sports/memes."""
import os, re, json, asyncio
from ..util import parse_count

GRAB_JS = """
() => { const num=s=>{if(!s)return 0;s=s.replace(/,/g,'');const m=s.match(/([\\d.]+)\\s*([KMB]?)/i);if(!m)return 0;return Math.round(parseFloat(m[1])*({K:1e3,M:1e6,B:1e9}[m[2].toUpperCase()]||1))};
  const out=[];for(const a of document.querySelectorAll('article[data-testid="tweet"]')){const link=[...a.querySelectorAll('a[href*="/status/"]')].map(x=>x.getAttribute('href')).find(h=>/^\\/[^/]+\\/status\\/\\d+$/.test(h));if(!link)continue;
   const txt=(a.querySelector('[data-testid="tweetText"]')?.innerText||'').replace(/\\s+/g,' ').slice(0,200);const lab=a.querySelector('[role="group"]')?.getAttribute('aria-label')||'';
   out.push({link,txt,likes:num((lab.match(/([\\d.,]+[KMB]?) likes?/i)||[])[1]),reposts:num((lab.match(/([\\d.,]+[KMB]?) reposts?/i)||[])[1]),views:num((lab.match(/([\\d.,]+[KMB]?) views?/i)||[])[1]),video:!!a.querySelector('video,[data-testid="videoPlayer"]'),date:(a.querySelector('time')?.getAttribute('datetime')||'').slice(0,10)})}
  return out }"""

async def search(queries, since, storage_state=None, scrolls=12):
    from playwright.async_api import async_playwright
    seen = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context(storage_state=storage_state or os.getenv("X_STORAGE_STATE"))
        page = await ctx.new_page()
        for q in queries:
            full = f"{q['q']} min_faves:{q['min_faves']} since:{since}"
            for tab in ("top", "live"):
                await page.goto(f"https://x.com/search?q={full}&src=typed_query&f={tab}", wait_until="domcontentloaded")
                await page.wait_for_timeout(3500)
                for _ in range(scrolls):
                    for t in await page.evaluate(GRAB_JS):
                        if t["link"] not in seen: t["query"] = q["q"]; seen[t["link"]] = t
                    await page.mouse.wheel(0, 2800); await page.wait_for_timeout(1300)
        await b.close()
    return sorted(seen.values(), key=lambda t: -t["likes"])

def tweet_id(link): return link.rsplit("/", 1)[-1]
def handle(link): return link.split("/")[1]

"""Reddit public JSON. www.reddit.com 403s plain requests (WAF) since ~Sep 2026; a Playwright
context with a real-Chrome UA that warms up on the homepage first gets the JSON fine.
Hero: v.redd.it fallback mp4 plays in a <video> tag with no referrer constraints."""
import json, time
from ..util import get, parse_count

CHROME_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

def _fetch_json(url):
    r = get(url, headers={"User-Agent": "social-scan/0.1 by voodoo-publishing"})
    if r is not None and r.status_code == 200:
        try: return r.json()
        except Exception: pass
    return _fetch_json_playwright(url)

def _fetch_json_playwright(url):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        try:
            pg = b.new_context(user_agent=CHROME_UA).new_page()
            pg.goto("https://www.reddit.com/", timeout=30000)
            pg.wait_for_timeout(1500)
            pg.goto(url, timeout=30000)
            return json.loads(pg.evaluate("document.body.innerText"))
        except Exception as e:
            print("[reddit] playwright fetch failed:", e); return None
        finally:
            b.close()

def top_week(subreddits, min_score=2000, limit=100):
    subs = "+".join(subreddits)
    j = _fetch_json(f"https://www.reddit.com/r/{subs}/top.json?t=week&limit={limit}")
    try: posts = [c["data"] for c in j["data"]["children"]]
    except Exception: return []
    out = []
    for p in posts:
        if p.get("score", 0) < min_score: continue
        video = None
        rv = (p.get("media") or {}).get("reddit_video") or (p.get("secure_media") or {}).get("reddit_video")
        if rv and rv.get("fallback_url"): video = rv["fallback_url"].split("?")[0]
        yt = None
        if "youtu" in (p.get("url") or ""): yt = p["url"]
        out.append({"id": p["id"], "title": p["title"], "sub": p["subreddit"], "score": p["score"], "comments": p.get("num_comments", 0),
                    "url": "https://www.reddit.com" + p["permalink"], "created": time.strftime("%Y-%m-%d", time.gmtime(p["created_utc"])),
                    "video": video, "yt": yt, "thumb": p.get("thumbnail") if str(p.get("thumbnail", "")).startswith("http") else None,
                    "flair": p.get("link_flair_text")})
    return out

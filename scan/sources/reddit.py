"""Reddit public JSON. Blocked from the Claude.ai sandbox, trivial from anywhere else.
Hero: v.redd.it fallback mp4 plays in a <video> tag with no referrer constraints."""
import time
from ..util import get, parse_count

def top_week(subreddits, min_score=2000, limit=100):
    subs = "+".join(subreddits)
    r = get(f"https://www.reddit.com/r/{subs}/top.json", params={"t": "week", "limit": limit}, headers={"User-Agent": "social-scan/0.1 by voodoo-publishing"})
    try: posts = [c["data"] for c in r.json()["data"]["children"]]
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

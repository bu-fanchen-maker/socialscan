"""Bilibili search API. order=click ignores date params → use order=pubdate and filter locally (30d)."""
import os, time
from ..util import get, k

def clips_30d(keyword, pages=2):
    since = time.time() - 30 * 86400
    res = []
    for p in range(1, pages + 1):
        r = get("https://api.bilibili.com/x/web-interface/search/type", params={"search_type": "video", "order": "pubdate", "page": p, "page_size": 50, "keyword": keyword},
                headers={"Cookie": os.getenv("BILIBILI_COOKIE", ""), "Referer": "https://www.bilibili.com/"})
        try: items = r.json()["data"]["result"]
        except Exception: break
        res += [v for v in items if v.get("pubdate", 0) >= since]
        time.sleep(0.3)
    res.sort(key=lambda v: -(v.get("play") or 0))
    top = res[0] if res else None
    return {"n": len(res), "sum": sum(v.get("play") or 0 for v in res),
            "top": {"bvid": top["bvid"], "plays": top.get("play"), "title": top.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""), "pic": top.get("pic")} if top else None}

def evidence(b):
    return [{"t": f"{'100+' if b['n'] >= 100 else b['n']} Bilibili clips · {k(b['sum'])} plays · 30d", "v": "bili"}] if b and b["sum"] else []

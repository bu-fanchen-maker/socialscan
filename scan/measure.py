"""Attach measured evidence to candidates. Nothing here estimates."""
from .sources import steam, youtube, bilibili
from .util import k

def measure_steam(c, appid):
    v = steam.velocity(appid); ccu = steam.players_now(appid)
    c["velocity"] = {**v, "ccu": ccu}; c["rating"] = v.get("pct")
    c["evidence"] += steam.evidence(v, ccu)
    if v.get("desc"): c["punch"].append(f"{v['desc']} {v['pct']}% · {k(v['total'])} reviews")

def measure_youtube(c, name):
    y = youtube.week_clips(f"{name} game", must_match=name)
    if y and y["sum"] >= 1000:
        c["yt"] = {"n": y["n"], "sum": y["sum"], "top": y["top"]["id"], "topViews": y["top"]["views"]}
        c["evidence"].append({"t": f"{y['n']} YouTube clips · {k(y['sum'])} views · 7d", "v": "yt"})
        t = y["top"]; c["top"] = {"platform": "youtube", "label": f"{t['channel']} — {k(t['views'])} views · {t['when']}", "url": f"https://www.youtube.com/watch?v={t['id']}"}
        if c["media"].get("kind") in (None, "none", "img"): c["media"] = {"kind": "yt", "id": t["id"]}

def measure_bilibili(c, keyword):
    b = bilibili.clips_30d(keyword)
    if b and b["sum"] >= 1000:
        c["bili"] = {"n": b["n"], "sum": b["sum"], "top": b["top"]["bvid"], "topViews": b["top"]["plays"]}
        c["evidence"] += bilibili.evidence(b)
        if c["region"] == "CN" or not c.get("yt"):
            c["top"] = {"platform": "bilibili", "label": f"{b['top']['title'][:48]} · {k(b['top']['plays'])} plays", "url": f"https://www.bilibili.com/video/{b['top']['bvid']}/"}
            if c["media"].get("kind") in (None, "none", "img"): c["media"] = {"kind": "bili", "id": b["top"]["bvid"]}

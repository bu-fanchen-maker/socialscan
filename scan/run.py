"""Daily orchestrator. python -m scan.run [--no-x] [--no-llm]"""
import sys, yaml, json, re, time
from dotenv import load_dotenv; load_dotenv()
from .util import today, days_ago, load_json, save_json, slug, k
from .model import Card
from .sources import steam, reddit, roblox, gamediscover, stubs
from . import measure, score, build

def main(argv):
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    th = cfg["thresholds"]; memory = load_json("data/_memory.json", {"seen": {}})
    cards = []

    # 1. Steam candidates → store page → measurements
    for row in steam.discover(cfg["steam"]["lists"], cfg["steam"]["released_within_days"]):
        sp = steam.store_page(row["id"]) or {}
        c = Card(id=f"steam_{row['id']}", title=row["name"], alias=sp.get("developer", ""), genre=sp.get("tags", [])[:3],
                 punch=[re.split(r"(?<=[.!?])\s", sp.get("short", ""))[0][:72].rstrip(" .")] if sp.get("short") else [],
                 released=str(steam._date(row["released"]) or ""), surfaced=today(), platforms=["steam"],
                 media={"kind": "mp4", "src": sp["media"][0]} if sp.get("media") else {"kind": "img", "src": sp.get("header", "")},
                 top={"platform": "steam", "label": f"Steam page · {row['review_desc'] or 'no reviews yet'}", "url": f"https://store.steampowered.com/app/{row['id']}/"}).dict()
        measure.measure_steam(c, row["id"]); measure.measure_youtube(c, row["name"])
        if row["total_reviews"] >= cfg["steam"]["major_review_total"] or (sp.get("price_cents") or 0) >= cfg["steam"]["major_price_usd"] * 100 \
           or any(b.lower() in (sp.get("developer", "").lower()) for b in cfg["tiers"]["big_publishers"]): c["tier"] = "Major"
        if re.search(cfg["tiers"]["sequel_regex"], row["name"], re.I): c["kind"] = "franchise / sequel / remake"
        cards.append(c); time.sleep(0.3)

    # 2. Reddit
    for p in reddit.top_week(cfg["reddit"]["subreddits"], cfg["reddit"]["min_score"]):
        c = Card(id=f"rd_{p['id']}", title=p["title"][:90], alias=f"r/{p['sub']}", platforms=["reddit"], surfaced=p["created"],
                 media={"kind": "reddit", "src": p["video"]} if p["video"] else ({"kind": "yt", "id": p["yt"].split("v=")[-1][:11]} if p["yt"] else {"kind": "img", "src": p["thumb"] or ""}),
                 evidence=[{"t": f"{k(p['score'])} upvotes · r/{p['sub']} · 7d", "v": "rd"}, {"t": f"{k(p['comments'])} comments", "v": "rd"}],
                 top={"platform": "reddit", "label": f"r/{p['sub']} — {k(p['score'])} upvotes", "url": p["url"]}).dict()
        c["reddit"] = {"score": p["score"], "sum": p["score"] * 50}; cards.append(c)

    # 3. Roblox (Rotrends)
    for g in roblox.rotrends(cfg["roblox"]["rotrends_url"]):
        c = Card(id=f"rb_{slug(g['name'])}", title=g["name"], alias=g["section"], platforms=["roblox"], surfaced=today(),
                 evidence=[{"t": f"{k(g['ccu'])} CCU · Roblox · today", "v": "rb"}], top={"platform": "roblox", "label": "Rotrends — trending today", "url": cfg["roblox"]["rotrends_url"]}).dict()
        c["roblox"] = {"ccu": g["ccu"], "move": g.get("move", 0)}; cards.append(c)

    # 4. X (Playwright) — optional
    if "--no-x" not in argv:
        try:
            import asyncio; from .sources import x_search
            for t in asyncio.run(x_search.search(cfg["x"]["queries"], days_ago(cfg["date_window_days"]))):
                c = Card(id=f"x_{x_search.tweet_id(t['link'])}", title=t["txt"][:90], alias=f"@{x_search.handle(t['link'])}", platforms=["x"], surfaced=t["date"],
                         media={"kind": "x", "id": x_search.tweet_id(t["link"])},
                         evidence=[{"t": f"{k(t['likes'])} likes · X · 7d", "v": "x"}, {"t": f"{k(t['views'])} views · X", "v": "x"}],
                         top={"platform": "x", "label": f"@{x_search.handle(t['link'])} — {k(t['likes'])} likes · {k(t['views'])} views", "url": "https://x.com" + t["link"]}).dict()
                c["x"] = {"likes": t["likes"], "views": t["views"], "sum": t["views"]}; cards.append(c)
        except Exception as e: print("[x] skipped:", e)

    # 5. Stubs (skip themselves without creds)
    for fn in (stubs.dataeye, stubs.tiktok_creative_center, stubs.sensortower):
        try: cards += fn()
        except NotImplementedError as e: print(f"[{fn.__name__}] TODO: {e}")

    # 6. Threshold, then Claude pass only on survivors
    survivors = [c for c in cards if score.meets_bar(c, th)]
    if "--no-llm" not in argv and survivors:
        try:
            from .classify import classify
            for c, r in zip(survivors, classify([{"id": c["id"], "title": c["title"], "alias": c["alias"], "genre": c["genre"], "punch": c["punch"], "platform": c["platforms"]} for c in survivors])):
                if not r or r.get("noise"): c["dropped"] = True; continue
                for key in ("tier", "kind", "region", "cat"):
                    if r.get(key): c[key] = r[key]
                if r.get("game"): c["title"] = r["game"]; c["alias"] = r.get("alias") or c["alias"]
                if r.get("genre"): c["genre"] = r["genre"]
                if r.get("punch"): c["punch"] = (r["punch"] + c["punch"])[:6]
        except Exception as e: print("[classify] skipped:", e)
    survivors = [c for c in survivors if not c.get("dropped")]

    # 7. Dedup vs memory (same game seen earlier resurfaces only on a spike) + scoring
    for c in survivors:
        prev = memory["seen"].get(c["id"])
        if prev and c.get("velocity", {}).get("w7") and prev.get("w7") and c["velocity"]["w7"] < 2 * prev["w7"]: c["dropped"] = True
        memory["seen"][c["id"]] = {"w7": c.get("velocity", {}).get("w7"), "day": today()}
    survivors = [c for c in survivors if not c.get("dropped")]
    freq = score.baseline(cards)
    for c in survivors:
        c["score"] = score.traction(c); c["novelty"] = score.novelty(c, freq); c["surprise"] = score.surprise(c); c["mech"] = score.mechanics(c); c["eng"] = int(c["score"] * 1000)
    save_json("data/_memory.json", memory)

    meta = {"date": f"measured {today()}", "sources": "Steam, YouTube, Reddit, Roblox" + (", X" if "--no-x" not in argv else ""), "read": ""}
    out = build.build(survivors, meta)
    print(f"{len(cards)} candidates → {len(survivors)} cards → {out}")

if __name__ == "__main__": main(sys.argv[1:])

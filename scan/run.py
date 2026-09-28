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

    # 1. Steam candidates → store page → measurements. The store also sells hardware (Steam Frame/Deck);
    #    hardware is never a card (Bu Fan, 28 Sep).
    HARDWARE = re.compile(r"\bsteam\s+(frame|deck|machine|controller)\b|\bvalve\s+index\b", re.I)
    for row in steam.discover(cfg["steam"]["lists"], cfg["steam"]["released_within_days"]):
        if HARDWARE.search(row["name"]): continue
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

    # 2. Reddit — relevance heuristics (Bu Fan, 28 Sep): a card must show a playable game/mechanic/visual.
    #    Celebration/milestone posts, discussion threads and industry news have big numbers and zero ideation
    #    value. Cheap filters here; the Claude pass is the real judge once enabled.
    NOISE_TITLE = re.compile(r"\bthank(s| you)\b|\bmilestone\b|\bwishlist(s|ed)?\b.*\b(hit|reached|passed)\b|\b(hit|reached|passed)\b.*\bwishlist", re.I)
    NOISE_FLAIR = {"discussion", "news", "article", "meme"}
    for p in reddit.top_week(cfg["reddit"]["subreddits"], cfg["reddit"]["min_score"]):
        if NOISE_TITLE.search(p["title"]) or (p.get("flair") or "").lower() in NOISE_FLAIR: continue
        if not p["video"] and not p["yt"]: continue   # gameplay shows itself; text/screenshot-only top posts are usually meta
        c = Card(id=f"rd_{p['id']}", title=p["title"][:90], alias=f"r/{p['sub']}", platforms=["reddit"], surfaced=p["created"],
                 media={"kind": "reddit", "src": p["video"]} if p["video"] else ({"kind": "yt", "id": p["yt"].split("v=")[-1][:11]} if p["yt"] else {"kind": "img", "src": p["thumb"] or ""}),
                 evidence=[{"t": f"{k(p['score'])} upvotes · r/{p['sub']} · 7d", "v": "rd"}, {"t": f"{k(p['comments'])} comments", "v": "rd"}],
                 top={"platform": "reddit", "label": f"r/{p['sub']} — {k(p['score'])} upvotes", "url": p["url"]}).dict()
        c["reddit"] = {"score": p["score"], "sum": p["score"] * 50}; cards.append(c)

    # 3. Roblox (Rotrends → real game page + official thumbnail). Pace the API: bursts get rate-limited.
    for g in roblox.rotrends(cfg["roblox"]["rotrends_url"]):
        time.sleep(1.0)
        rg = roblox.resolve(g["name"]) or roblox.resolve(g["name"]) or {}
        c = Card(id=f"rb_{slug(g['name'])}", title=g["name"], alias=g.get("studio") or g["section"], platforms=["roblox"], surfaced=today(),
                 media={"kind": "img", "src": rg["thumb"]} if rg.get("thumb") else {"kind": "none"},
                 evidence=[{"t": f"{k(g['ccu'])} CCU · Roblox · today", "v": "rb"}] + ([{"t": f"▲ {k(g['move'])} rank move · 24h", "v": "up"}] if g.get("move") else []),
                 top={"platform": "roblox", "label": f"Roblox — {rg.get('name') or g['name']}", "url": rg["url"]} if rg.get("url")
                     else {"platform": "roblox", "label": "Rotrends — trending today", "url": cfg["roblox"]["rotrends_url"]}).dict()
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

    # 4b. TikTok Creative Center — trending Games hashtags (public). Hashtags are game names;
    #     hero = top YouTube clip of the game (CC detail pages are login-gated, no clip ids).
    try:
        from .sources import tiktok_cc
        # confirmation rule: a hashtag ships only when it names a game measured elsewhere this run —
        # generic hashtags (#deal) and creator tags are exactly the noise Bu Fan flagged.
        names = {re.sub(r"[^0-9a-z]+", "", c["title"].lower()) for c in cards}
        for t in tiktok_cc.hashtags():
            nt = re.sub(r"[^0-9a-z]+", "", t["tag"].lower())
            if not any(nt == n or (len(nt) >= 6 and nt in n) for n in names):
                print(f"[tiktok] #{t['tag']} skipped: no matching measured game"); continue
            c = Card(id=f"tt_{slug(t['tag'])}", title=f"#{t['tag']}", alias="TikTok Games hashtag", platforms=["tiktok"],
                     surfaced=today(), cat="other",
                     evidence=[{"t": f"{k(t['posts'])} TikTok posts · 7d", "v": "mob"}, {"t": f"{k(t['views'])} TikTok views · 7d", "v": "mob"}],
                     top={"platform": "tiktok", "label": f"TikTok Creative Center — #{t['tag']} (Games)", "url": t["url"]}).dict()
            measure.measure_youtube(c, t["tag"])
            c["tiktok"] = {"posts": t["posts"], "views": t["views"], "sum": t["views"]}
            cards.append(c)
    except Exception as e: print("[tiktok] skipped:", e)

    # 5. Stubs (skip themselves without creds)
    for fn in (stubs.dataeye, stubs.sensortower):
        try: cards += fn()
        except NotImplementedError as e: print(f"[{fn.__name__}] TODO: {e}")

    # 6. Visual law: the hero must show what it is — an mp4/embed or an informative image. No visual, no card.
    def has_visual(c):
        m = c.get("media") or {}
        return m.get("kind") not in (None, "", "none") and (m.get("kind") != "img" or bool(m.get("src")))
    no_vis = [c for c in cards if not has_visual(c)]
    if no_vis: print(f"[visual-law] dropped {len(no_vis)}: " + " | ".join(c["title"][:30] for c in no_vis[:8]))

    # 7. Threshold, then Claude pass only on survivors
    survivors = [c for c in cards if has_visual(c) and score.meets_bar(c, th)]
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
    method = {"thresholds": th, "released_within_days": cfg["steam"]["released_within_days"],
              "subreddits": cfg["reddit"]["subreddits"], "reddit_min": cfg["reddit"]["min_score"],
              "x_enabled": "--no-x" not in argv}
    out = build.build(survivors, meta, method=method)
    print(f"{len(cards)} candidates → {len(survivors)} cards → {out}")

if __name__ == "__main__": main(sys.argv[1:])

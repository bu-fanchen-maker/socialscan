"""Traction / novelty / surprise / mechanics. Baseline = tag frequency over the last 30 days of Steam candidates."""
import math, collections, re

def traction(c):
    v = c.get("velocity", {}); s = 0.0
    if v.get("w7"): s += math.log10(v["w7"] + 1)
    if v.get("prev7") and v["w7"] / v["prev7"] >= 1.1: s += 0.5
    if v.get("ccu"): s += 0.8 * math.log10(v["ccu"] + 1)
    for key, w in (("yt", 1.0), ("bili", 0.8), ("reddit", 0.9), ("x", 0.9)):
        d = c.get(key)
        if d and d.get("sum"): s += w * math.log10(d["sum"] + 1)
    return round(s, 2)

def baseline(cards):
    f = collections.Counter()
    for c in cards:
        for t in c.get("genre", []): f[t.lower()] += 1
    return f

FAM = {"card": ["deck", "card", "dice"], "td": ["tower", "defense"], "auto": ["auto battler", "idle", "incremental", "clicker"],
       "action": ["shooter", "action", "fps", "hack", "bullet"], "build": ["city", "base", "automation", "colony", "building"],
       "sim": ["simulation", "management", "farming"], "coop": ["co-op", "party", "multiplayer", "pvp"], "rogue": ["roguel"],
       "horror": ["horror"], "physics": ["physics", "sandbox"], "extract": ["extraction"]}

def novelty(c, freq):
    tags = [t.lower() for t in c.get("genre", []) if t.lower() not in ("aaa", "indie")]
    if not tags: return 0.0
    N = sum(freq.values()) + 1
    s = sum(-math.log10((freq.get(t, 0) + 1) / N) for t in tags) / len(tags)
    words = tags + [p.lower() for p in c.get("punch", [])]
    fam = {f for f, ks in FAM.items() if any(k in w for k in ks for w in words)}
    return round(s + 0.4 * max(0, len(fam) - 1), 2)

def surprise(c):
    social = sum((c.get(k) or {}).get("sum", 0) for k in ("yt", "bili", "reddit", "x"))
    total = c.get("velocity", {}).get("total", 0) or 0
    footprint = 0.6 * math.log10(total + 10) + (1.5 if c.get("tier") == "Major" else 0) + (0.5 if c.get("kind") != "new IP" else 0)
    return round((math.log10(social + 1) if social else 0) - footprint, 2)

def mechanics(c):
    return round(c["novelty"] * 1.2 + c["surprise"] * 0.8 + (0.8 if c.get("kind") == "new IP" else 0) + (0.6 if c.get("tier") == "Indie" else 0), 2)

def meets_bar(c, th):
    v = c.get("velocity", {})
    return any([(v.get("w7") or 0) >= th["steam_reviews_7d"], (v.get("ccu") or 0) >= th["steam_players_now"],
                ((c.get("yt") or {}).get("sum", 0)) >= th["youtube_views_7d"], ((c.get("bili") or {}).get("sum", 0)) >= th["bilibili_plays_30d"],
                ((c.get("x") or {}).get("likes", 0)) >= th["x_likes_7d"], ((c.get("reddit") or {}).get("score", 0)) >= th["reddit_upvotes_7d"],
                ((c.get("roblox") or {}).get("ccu", 0)) >= th["roblox_ccu"], ((c.get("roblox") or {}).get("move", 0)) >= th["roblox_rank_move_24h"]])

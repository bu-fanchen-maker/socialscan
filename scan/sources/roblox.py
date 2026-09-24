"""Roblox trending via Rotrends (CCU + rank movement), resolved to real game pages + official
thumbnails via Roblox's public APIs (omni-search → universeId → thumbnails.roblox.com)."""
import re, time
from html import unescape
from ..util import get, parse_count

SECTIONS = {"New and Rising", "Top Moving Games", "Top 100 Movers"}
END = {"Explore List", "New and Stable"}   # New and Stable = single-digit CCU noise, skip

def rotrends(url="https://www.rotrends.com/"):
    r = get(url)
    if not r: return []
    # Rotrends now renders each game as a 6-line block: name / "@" / studio / CCU / "#" / rank move.
    text = re.sub(r"<[^>]+>", "\n", r.text)
    lines = [unescape(l.strip()) for l in text.splitlines() if l.strip()]
    out, section, i = [], None, 0
    while i < len(lines):
        l = lines[i]
        if l in SECTIONS: section, i = l, i + 1; continue
        if l in END: section, i = None, i + 1; continue
        if section and i + 5 < len(lines) and lines[i + 1] == "@" \
           and re.fullmatch(r"[\d,]+", lines[i + 3]) and lines[i + 4] == "#" and re.fullmatch(r"[+-]?[\d,]+", lines[i + 5]):
            out.append({"name": l, "studio": lines[i + 2], "ccu": parse_count(lines[i + 3]),
                        "move": abs(parse_count(lines[i + 5])), "section": section})
            i += 6; continue
        i += 1
    return out

def _norm(s):
    return re.sub(r"[^0-9a-z]+", "", s.lower())

def resolve(name):
    """Rotrends display name → real Roblox game page + official 768x432 thumbnail. None if not found.
    Candidates carry emoji/update decorations ('[ICE 🧊] How to Really Fish'), so match on normalized
    containment, never on raw equality or bare playerCount — 'How to Fish' must not beat 'How to Really Fish'."""
    q = re.sub(r"^[^0-9A-Za-z+]+", "", name).strip() or name   # strip leading emoji / [🚁] decorations
    r = None
    for attempt in range(3):                                    # omni-search rate-limits bursts
        r = get("https://apis.roblox.com/search-api/omni-search",
                params={"searchQuery": q, "pageType": "Games", "sessionId": "socialscan"})
        if r is not None: break
        time.sleep(2 + 2 * attempt)
    try: groups = r.json().get("searchResults", [])
    except Exception: return None
    nq, best = _norm(q), None
    for g in groups:
        for it in g.get("contents", []):
            if not it.get("universeId") or not it.get("rootPlaceId"): continue
            nn = _norm(it.get("name", ""))
            if not nq or not nn or (nq not in nn and nn not in nq): continue
            key = (nn == nq, it.get("playerCount") or 0)
            if best is None or key > best[0]: best = (key, it)
    if not best: return None
    time.sleep(0.4)
    it = best[1]; uid, pid = it["universeId"], it["rootPlaceId"]
    thumb = None
    r2 = get(f"https://thumbnails.roblox.com/v1/games/multiget/thumbnails?universeIds={uid}&countPerUniverse=1&size=768x432&format=Png")
    try:
        th = r2.json()["data"][0]["thumbnails"]
        if th and th[0].get("state") == "Completed": thumb = th[0]["imageUrl"]
    except Exception: pass
    if not thumb:
        r3 = get(f"https://thumbnails.roblox.com/v1/games/icons?universeIds={uid}&size=512x512&format=Png")
        try:
            d = r3.json()["data"][0]
            if d.get("state") == "Completed": thumb = d["imageUrl"]
        except Exception: pass
    return {"universe_id": uid, "place_id": pid, "url": f"https://www.roblox.com/games/{pid}",
            "thumb": thumb, "name": it.get("name", ""), "ccu": it.get("playerCount")}

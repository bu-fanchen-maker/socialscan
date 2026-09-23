"""Steam: discovery lists → appdetails-lite via store page (tags, extras .mp4 loops) → reviews velocity → players now.
Everything here was validated live on 21 Sep 2026."""
import re, json, time, datetime
from html import unescape
from ..util import get, days_ago, k

STORE = "https://store.steampowered.com"

def _rows(html):
    out = []
    # href and data-ds-appid are separated by a newline + tabs since ~Sep 2026; tooltip HTML is entity-escaped.
    for m in re.finditer(r'<a href="[^"]+"\s+data-ds-appid="(\d+)".*?>(.*?)</a>', html, re.S):
        appid, body = m.group(1), m.group(2)
        title = re.search(r'class="title">([^<]+)<', body)
        rel = re.search(r'class="search_released[^"]*">([^<]*)<', body)
        rev = re.search(r'data-tooltip-html="([^"]*)"', body)
        tooltip = unescape(rev.group(1)) if rev else ""
        pct = re.search(r"(\d+)% of the ([\d,]+)", tooltip)
        out.append({"id": appid, "name": title.group(1).strip() if title else "", "released": (rel.group(1).strip() if rel else ""),
                    "review_desc": tooltip.split("<br>")[0], "pct": int(pct.group(1)) if pct else None,
                    "total_reviews": int(pct.group(2).replace(",", "")) if pct else 0})
    return out

def discover(lists, released_within_days=45):
    seen, out = set(), []
    cutoff = datetime.date.today() - datetime.timedelta(days=released_within_days)
    for qs in lists:
        r = get(f"{STORE}/search/results/?{qs}&os=win&infinite=1&count=100&start=0&json=1")
        if not r: continue
        try: html = r.json().get("results_html", "")
        except Exception: continue
        for row in _rows(html):
            if row["id"] in seen or not row["name"]: continue
            d = _date(row["released"])
            if not d or d < cutoff: continue
            seen.add(row["id"]); row["src"] = qs; out.append(row)
        time.sleep(0.4)
    return out

def _date(s):
    for fmt in ("%d %b, %Y", "%b %d, %Y"):
        try: return datetime.datetime.strptime(s.strip(), fmt).date()
        except Exception: pass
    return None

def store_page(appid):
    """tags, short description, extras .mp4/.webm loops, developer, price. Trailers are HLS now → not embeddable."""
    r = get(f"{STORE}/app/{appid}/?l=english", cookies={"birthtime": "568022401", "mature_content": "1"})
    if not r or "agecheck" in r.url or len(r.text) < 20000: return None
    h = r.text
    media = list(dict.fromkeys(re.findall(r"https?://[a-z0-9.-]*steamstatic\.com/store_item_assets/steam/apps/\d+/extras/[a-f0-9]+\.(?:mp4|webm)", h)))
    tags = []
    m = re.search(r"InitAppTagModal\(\s*\d+,\s*(\[.*?\])\s*,", h, re.S)
    if m:
        try: tags = [t["name"] for t in json.loads(m.group(1))][:10]
        except Exception: pass
    sd = re.search(r'<div class="game_description_snippet">\s*(.*?)\s*</div>', h, re.S)
    dev = re.search(r'id="developers_list">\s*<a[^>]*>([^<]+)<', h)
    price = re.search(r'data-price-final="(\d+)"', h)
    return {"tags": tags, "short": re.sub(r"\s+", " ", sd.group(1)).strip()[:200] if sd else "", "media": media[:3],
            "developer": dev.group(1).strip() if dev else "", "price_cents": int(price.group(1)) if price else None,
            "header": f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg"}

def reviews_window(appid, days):
    now = int(time.time())
    r = get(f"{STORE}/appreviews/{appid}?json=1&num_per_page=0&filter=all&purchase_type=all&language=all&start_date={now-days*86400}&end_date={now}&date_range_type=include")
    try: return r.json()["query_summary"]
    except Exception: return {}

def velocity(appid):
    a, w, p, m = reviews_window(appid, 365), reviews_window(appid, 7), reviews_window(appid, 14), reviews_window(appid, 30)
    w7, p14 = w.get("total_reviews", 0), p.get("total_reviews", 0)
    return {"total": a.get("total_reviews", 0), "w7": w7, "prev7": max(0, p14 - w7), "m30": m.get("total_reviews", 0),
            "desc": a.get("review_score_desc", ""), "pct": round(100 * a.get("total_positive", 0) / max(1, a.get("total_reviews", 1)))}

def players_now(appid):
    r = get(f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}")
    try: return r.json()["response"]["player_count"]
    except Exception: return None

def evidence(v, ccu):
    ev = []
    if v.get("w7"): 
        ev.append({"t": f"{k(v['w7'])} reviews · 7d", "v": "steam"})
        if v.get("prev7", 0) == 0 and v.get("total"): ev.append({"t": "launched this week", "v": "new"})
        elif v.get("prev7"):
            r = v["w7"] / v["prev7"]; ev.append({"t": ("▲" if r >= 1.1 else "▼" if r <= 0.9 else "→") + f" {r:.1f}× wk/wk", "v": "up" if r >= 1.1 else "down" if r <= 0.9 else "flat"})
    if ccu: ev.append({"t": f"{k(ccu)} playing now", "v": "steam"})
    return ev

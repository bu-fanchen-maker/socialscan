"""YouTube via the search results page (no key needed). sp=CAMSBAgDEAE%3D = sort by view count, uploaded this week."""
import re, json
from ..util import get, parse_count

STOP = {"the", "and", "for", "with", "from", "that", "this", "your", "game", "games",
        "a", "an", "of", "in", "on", "to", "is", "its", "it's"}

def title_match(title, name):
    """Does a video title actually refer to this game? Word-boundary matching on significant words only —
    stopwords are never evidence. ("FEED THE AI" once matched a Feed & Grow Fish video on "feed"+"the".)"""
    t = title.lower()
    flat_t = re.sub(r"[^a-z0-9]+", "", t)
    flat_n = re.sub(r"[^a-z0-9]+", "", name.lower())
    if len(flat_n) >= 4 and flat_n in flat_t: return True          # full name, spacing/punct-insensitive
    words = [w for w in re.findall(r"[a-z0-9]+", name.lower()) if w not in STOP]
    if not words: return False
    if len(words) <= 2:
        # short generic names ("FEED THE AI") must appear as an ordered phrase, not scattered words —
        # "AI Modding is taking over my feed" has both words and is not the game
        pat = r"(?:\W+\w+){0,2}?\W+".join(rf"\b{re.escape(w)}\b" for w in words)
        return bool(re.search(pat, t))
    hits = sum(1 for w in words if re.search(rf"\b{re.escape(w)}\b", t))
    return hits >= 2                                 # longer names are distinctive: any two significant words

def week_clips(query, must_match=None):
    r = get("https://www.youtube.com/results", params={"search_query": query, "sp": "CAMSBAgDEAE%3D"}, cookies={"CONSENT": "YES+"})
    if not r: return None
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", r.text, re.S)
    if not m: return None
    vids = []
    def walk(o):
        if isinstance(o, dict):
            if "videoRenderer" in o:
                v = o["videoRenderer"]
                vids.append({"id": v.get("videoId"), "title": "".join(x.get("text", "") for x in v.get("title", {}).get("runs", [])),
                             "views": parse_count(v.get("viewCountText", {}).get("simpleText")), "when": v.get("publishedTimeText", {}).get("simpleText", ""),
                             "channel": "".join(x.get("text", "") for x in v.get("ownerText", {}).get("runs", []))})
            for x in o.values(): walk(x)
        elif isinstance(o, list):
            for x in o: walk(x)
    walk(json.loads(m.group(1)))
    if must_match:
        vids = [v for v in vids if title_match(v["title"], must_match)]
    vids.sort(key=lambda v: -v["views"])
    return {"n": len(vids), "sum": sum(v["views"] for v in vids), "top": vids[0] if vids else None, "clips": vids[:10]}

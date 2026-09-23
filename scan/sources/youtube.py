"""YouTube via the search results page (no key needed). sp=CAMSBAgDEAE%3D = sort by view count, uploaded this week."""
import re, json
from ..util import get, parse_count

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
        words = [w for w in must_match.lower().split() if len(w) > 2]
        vids = [v for v in vids if must_match.lower() in v["title"].lower() or sum(w in v["title"].lower() for w in words) >= min(2, len(words))]
    vids.sort(key=lambda v: -v["views"])
    return {"n": len(vids), "sum": sum(v["views"] for v in vids), "top": vids[0] if vids else None, "clips": vids[:10]}

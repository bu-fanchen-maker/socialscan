"""GameDiscoverCo RSS → analysis cards + deconstruction links (units, wishlists, CCU quotes)."""
import re
from ..util import get

def latest(rss="https://newsletter.gamediscover.co/feed", n=6):
    r = get(rss)
    if not r: return []
    items = re.findall(r"<item>(.*?)</item>", r.text, re.S)[:n]
    out = []
    for it in items:
        t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", it, re.S); l = re.search(r"<link>(.*?)</link>", it)
        out.append({"title": t.group(1).strip() if t else "", "url": l.group(1).strip() if l else ""})
    return out

"""Roblox trending via Rotrends (CCU + rank movement). TODO: resolve universeId → thumbnails.roblox.com for hero images."""
import re
from ..util import get, parse_count

def rotrends(url="https://www.rotrends.com/"):
    r = get(url)
    if not r: return []
    # Rotrends renders sections: "New and Rising", "Top Moving Games"; each card: name, CCU, rank delta.
    text = re.sub(r"<[^>]+>", "\n", r.text)
    out, section = [], None
    for line in [l.strip() for l in text.splitlines() if l.strip()]:
        if line in ("New and Rising", "Top Moving Games", "Top 100 Movers"): section = line; continue
        m = re.match(r"^(.*?)\s+(\d[\d,]*)\s*CCU", line)
        if m and section: out.append({"name": m.group(1), "ccu": parse_count(m.group(2)), "section": section})
    return out

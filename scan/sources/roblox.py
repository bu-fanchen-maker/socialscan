"""Roblox trending via Rotrends (CCU + rank movement). TODO: resolve universeId → thumbnails.roblox.com for hero images."""
import re
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

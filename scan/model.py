"""Card schema — identical to what web/template.html renders."""
from dataclasses import dataclass, field, asdict
from typing import Optional

@dataclass
class Card:
    id: str
    title: str
    alias: str = ""
    genre: list = field(default_factory=list)      # outlined tags (GameRefinery / Steam user tags)
    punch: list = field(default_factory=list)      # amber tags: hook sentence + 3–5 facts
    released: str = ""                              # ISO date or ""
    surfaced: str = ""                              # ISO date this card first met the bar
    platforms: list = field(default_factory=list)  # steam|youtube|bilibili|x|reddit|roblox|web|itch|mobile|douyin|wechat
    region: str = "Global"                          # Global|CN|JP
    media: dict = field(default_factory=lambda: {"kind": "none"})   # {kind: mp4|yt|ytlist|bili|x|reddit|img|none, src|id}
    evidence: list = field(default_factory=list)   # [{t:"4.5k reviews · 7d", v:"steam|yt|bili|x|rd|rb|up|down|flat|new"}]
    top: dict = field(default_factory=dict)        # {platform,label,url} — the actual highest-engagement post
    more: list = field(default_factory=list)       # [[label,url],...]
    decon: list = field(default_factory=list)      # deconstruction articles
    tier: str = "Indie"                             # Major|Indie|Prototype
    kind: str = "new IP"                            # new IP | franchise / sequel / remake
    velocity: dict = field(default_factory=dict)   # raw measured numbers (never estimated)
    yt: Optional[dict] = None
    bili: Optional[dict] = None
    x: Optional[dict] = None
    reddit: Optional[dict] = None
    score: float = 0.0        # traction
    novelty: float = 0.0
    surprise: float = 0.0
    mech: float = 0.0
    eng: int = 0
    curated: bool = False
    aaa: bool = False
    rating: Optional[int] = None
    dropped: bool = False

    def dict(self): return asdict(self)

# Social Scan — hot mechanics feed

Daily harvester + static feed page. Pulls new/trending games from Steam, YouTube, Bilibili, Reddit,
Roblox (Rotrends), X, GameDiscoverCo and (when credentials exist) DataEye, TikTok Creative Center and
Sensor Tower; measures traction; drops anything without a measured signal; scores novelty + surprise;
writes `data/YYYY-MM-DD.json`; renders `site/index.html`.

**Rule the whole pipeline obeys:** a number is either measured by a source module or the field is empty.
No estimates, no placeholders. This was learned the hard way (see CLAUDE.md).

## Quick start
```
pip install -r requirements.txt
cp .env.example .env         # fill what you have; sources with missing creds skip themselves
python -m scan.run           # harvest → score → build site/
python -m http.server -d site 8787   # open http://localhost:8787
```
Deploy `site/` anywhere static (Netlify Drop, S3, Scout sub-page). `site/data/` grows one file per day;
the page loads today first and walks back as you scroll.

## Layout
```
scan/run.py            orchestrator (daily)
scan/sources/*.py      one module per source, each returns Candidate dicts (see scan/model.py)
scan/measure.py        attaches evidence: Steam 7d reviews / CCU, YouTube 7d clips+views, Bilibili 30d plays…
scan/classify.py       Claude pass: entity resolution, post type, tier, punch tags, "the twist"
scan/score.py          traction, novelty, surprise, mechanics score; threshold
scan/build.py          writes data/ + site/
config.yaml            queries, subreddits, thresholds, tag baseline
web/template.html      the feed page (validated with Bu Fan, Sep 2026)
```

## Sources — status at hand-off (22 Sep 2026)
| Source | Method | Status |
|---|---|---|
| Steam | store search JSON, `appreviews` date-filtered, `GetNumberOfCurrentPlayers`, store-page extras `.mp4` loops + user tags | proven |
| YouTube | search results page, `ytInitialData`, sort by views + this week | proven (Data API optional) |
| Bilibili | `x/web-interface/search/type` `order=pubdate`, filter 30d client-side, needs a cookie | proven |
| X | search UI via Playwright (logged-in profile); `min_faves` floors per query | proven via Chrome, needs Playwright port |
| Roblox | Rotrends New & Rising / Top Moving; Roblox thumbnails API for images | proven (parse), thumbnails TODO |
| Reddit | `/r/<subs>/top.json?t=week` public JSON; `v.redd.it` fallback mp4 as hero | not runnable from Claude.ai; trivial here |
| GameDiscoverCo | RSS + issue pages → analysis cards + deconstruction links | proven (manual) |
| CrazyGames / itch | listings, no engagement → confirmation / Prototype tier only | proven |
| DataEye, TikTok CC | Playwright with saved login state | TODO |
| Sensor Tower | MCP or API: breakout downloads, ad spend | TODO |

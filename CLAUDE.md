# Notes for Claude Code working in this repo

Owner: Bu Fan (Publishing Manager, Voodoo). Purpose: surface hot new game mechanics for midcore ideation.

## Non-negotiables (from the validation sessions)
1. **Measured or empty.** Never write an estimated view/like/download count into a card. Two bad cards
   (a fake ~15.6M views, a GTA 6 "delay" from a stale snippet) cost real trust. If a source didn't return
   it, the field is `null` and the UI shows "—".
2. **Traction bar before card.** A candidate becomes a card only if at least one threshold in
   `config.yaml: thresholds` is met. Pretty gameplay with no signal is not a card.
3. **Video first.** Every card needs an inline-playable hero: Steam extras `.mp4` > YouTube embed >
   Bilibili player > X embed > Reddit `v.redd.it` mp4. Link-out is the last resort and must say so.
4. **Dedup at three levels:** same post cross-posted (URL / thumbnail hash), same game different posts
   (entity resolution — "Castle on Wheels" is Wanderburg), same game different weeks (resurfaces only
   on a velocity spike).
5. **Tier and kind on every card.** Major vs Indie vs Prototype; new IP vs franchise/sequel/remake/DLC.
   Default view is Indie + new IP. Major and sequels stay one toggle away, never deleted.
6. **Mechanics sort is the default**: novelty (rare tag combos vs the rolling 30-day Steam baseline)
   + surprise (engagement relative to marketing footprint). Trending is popularity; it is not the goal.
7. Punch tags over paragraphs. 3–6 short tags, one of them the hook sentence from the store text.
8. **The visual must show what it is** (Bu Fan, 24 Sep 2026: every card he called garbage had no visual).
   Preferred: playable loop/clip; an informative image (store art, official Roblox thumbnail) qualifies.
   No visual after fallbacks → the card is dropped in run.py, never shipped with a placeholder.
9. **Specific links only.** "Top post" opens the exact game page or post — never a chart homepage
   (rotrends.com, crazygames.com/hot). Roblox names resolve via omni-search → place page + thumbnail.
10. **English titles (CN ok), plain words.** Punch tags in English; pure-JP/other posts are noise unless
    the game resolves to an English title. No scene jargon. Trend-cluster cards need ≥3 measured member
    games and a hero from the top member — otherwise ship the members as individual game cards.

## What we learned about each source
- Steam `appdetails` no longer returns movie URLs; trailers are HLS. Use the `extras/*.mp4` loops in the
  store page HTML — present for ~75% of titles. `appreviews` supports `start_date/end_date` with
  `date_range_type=include` (7d / 14d / 30d windows work; `day_range` alone does not).
- YouTube `sp=CAMSBAgDEAE%3D` = sort by view count + uploaded this week. Filter results by title match
  to the game name or you count Blooket videos as How to Fish.
- Bilibili `order=click` ignores date params; use `order=pubdate`, two pages, filter by `pubdate` locally.
  Search-by-clicks without a date filter is ~80% noise.
- X: floors matter. Dev posts peak at 2–20k likes; ≥100k is AAA/sports/memes. Productive queries are
  hashtag sets (#indiedev #screenshotsaturday …), "mobile game / 手游 / スマホゲーム", and milestone
  words (wishlists, copies sold). Complex boolean queries with many negations return nothing.
  Roughly half of results above 2k likes are noise → classifier is mandatory.
- Roblox re-implements Steam hits within weeks (How to Really Fish, Clean Leaves Adventure). Treat as a
  confirmation signal and as the incubator for mobile-portable loops ("+1 per action" escape).
- GameDiscoverCo is the best deconstruction source; attach as `decon` links and mint Analysis cards.

## Working style
Bu Fan confirms approach before big builds, then refines on output. Show a small result early. He reads
Slack-style prose; delegate items to named colleagues when relevant. Keep Voodoo terms in English inside
Chinese messages.

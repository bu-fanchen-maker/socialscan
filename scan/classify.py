"""Claude pass. Cheap: only runs on candidates that met a threshold. Returns structured JSON.
Tasks: (1) resolve the game entity behind a post/clip (taglines, nicknames, CN/JP names → canonical title),
(2) post type: gameplay clip | trailer | dev post | meme | news | ad creative,
(3) tier Major/Indie, kind new IP / franchise, (4) 3–6 punch tags incl. the twist in ≤10 words,
(5) map genre to the GameRefinery taxonomy where possible, propose a new tag only if nothing fits."""
import os, json
SYSTEM = open(os.path.join(os.path.dirname(__file__), "prompts", "classify.md"), encoding="utf-8").read()

def classify(items, model="claude-sonnet-4-6"):
    import anthropic
    client = anthropic.Anthropic()
    out = []
    for batch in [items[i:i+15] for i in range(0, len(items), 15)]:
        msg = client.messages.create(model=model, max_tokens=4000, system=SYSTEM,
            messages=[{"role": "user", "content": "Classify each item. Return ONLY a JSON array in the same order.\n" + json.dumps(batch, ensure_ascii=False)}])
        txt = "".join(b.text for b in msg.content if b.type == "text").strip().strip("`")
        if txt.startswith("json"): txt = txt[4:]
        try: out += json.loads(txt)
        except Exception: out += [{} for _ in batch]
    return out

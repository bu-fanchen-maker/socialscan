"""Write data/<date>.json + data/index.json, render site/index.html from web/template.html."""
import json, os, shutil, glob
from .util import save_json, load_json, today

def build(cards, meta, root="."):
    day = today()
    save_json(f"{root}/data/{day}.json", cards)
    days = sorted({os.path.basename(p)[:-5] for p in glob.glob(f"{root}/data/*.json")
                   if not p.endswith("index.json") and not os.path.basename(p).startswith("_")}, reverse=True)
    save_json(f"{root}/data/index.json", {"days": days, "meta": meta})
    t = open(f"{root}/web/template.html", encoding="utf-8").read()
    html = t.replace("/*CARDS*/[]", json.dumps(cards, ensure_ascii=False).replace("</", "<\\/")).replace("/*META*/{}", json.dumps(meta, ensure_ascii=False))
    os.makedirs(f"{root}/site/data", exist_ok=True)
    open(f"{root}/site/index.html", "w", encoding="utf-8").write(html)
    for p in glob.glob(f"{root}/data/*.json"):
        if not os.path.basename(p).startswith("_"): shutil.copy(p, f"{root}/site/data/")
    return f"{root}/site/index.html"

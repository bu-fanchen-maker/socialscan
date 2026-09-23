import requests, time, math, re, datetime, os, json
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36 social-scan/0.1"
S = requests.Session(); S.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,ja;q=0.7"})

def get(url, **kw):
    for i in range(3):
        try:
            r = S.get(url, timeout=kw.pop("timeout", 25), **kw); 
            if r.status_code == 429: time.sleep(2 + i * 3); continue
            return r
        except requests.RequestException:
            time.sleep(1 + i)
    return None

def today(): return datetime.date.today().isoformat()
def days_ago(n): return (datetime.date.today() - datetime.timedelta(days=n)).isoformat()
def k(n):
    n = int(n or 0)
    return f"{n/1e6:.1f}M" if n >= 1e6 else (f"{n/1e3:.1f}k" if n >= 1e3 else str(n))
def parse_count(s):
    if not s: return 0
    s = str(s).replace(",", "")
    m = re.search(r"([\d.]+)\s*([KMB万亿]?)", s, re.I)
    if not m: return 0
    mult = {"K": 1e3, "M": 1e6, "B": 1e9, "万": 1e4, "亿": 1e8}.get(m.group(2).upper() if m.group(2) else "", 1)
    return int(float(m.group(1)) * mult)
def slug(s): return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]
def load_json(p, default):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return default
def save_json(p, obj):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

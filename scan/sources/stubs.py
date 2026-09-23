"""Sources not yet wired. Each returns [] and logs why, so run.py never fails on a missing credential."""
import os
def dataeye():   # Douyin / WeChat mini-game charts. Playwright with DATAEYE_STORAGE_STATE. Bu Fan has a login.
    if not os.getenv("DATAEYE_STORAGE_STATE"): print("[dataeye] skipped: no storage state"); return []
    raise NotImplementedError("port the Chrome flow: 小游戏榜 → 抖音/微信 ranking table → name, rank Δ, creative count")
def tiktok_creative_center():   # public; trending hashtags in Games + top ads. Playwright.
    print("[tiktok] TODO: https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en (Games)"); return []
def sensortower():   # breakout downloads/revenue 30d in midcore genres; ad intel (creative count, spend ramp)
    if not os.getenv("SENSORTOWER_TOKEN"): print("[sensortower] skipped: no token"); return []
    raise NotImplementedError

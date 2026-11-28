#!/usr/bin/env python3
"""Builds the Trend Radar AI site from the channel's public YouTube feed.
Keeps every video it has ever seen in videos.json, then writes the home page,
topic pages, sitemap.xml and robots.txt."""
import html, json, os, re, sys, urllib.request
from datetime import date

CHANNEL_ID = "UC9d29f-6iINvwI5yzrlgnnQ"
CH = "https://www.youtube.com/@TrendRadarAI"
BASE = "https://bishoynabilanis.github.io/trendradar/"
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
ROOT = os.path.dirname(os.path.abspath(__file__))

# slug, nav label, page title, description, keywords (lowercase, matched on word starts)
TOPICS = [
 ("ai", "AI", "AI News and Trends in Short Videos",
  "The latest AI news explained fast: new models, labs, chips and research. Short videos from Trend Radar AI.",
  ["ai", "openai", "anthropic", "claude", "gpt", "gemini", "llm", "model", "nvidia", "deepmind", "qwen", "deepseek", "grok", "agent", "chatbot", "robot", "artificial intelligence", "machine learning", "protein"]),
 ("tech", "Tech", "Tech News Explained in Short Videos",
  "Big tech stories in plain words: software, chips, space and science. Short videos from Trend Radar AI.",
  ["tech", "apple", "microsoft", "google", "meta", "amazon", "chip", "tsmc", "samsung", "intel", "software", "app", "windows", "mac", "desktop", "outage", "cloud", "cyber", "hack", "space", "astronaut", "tiangong", "satellite", "computer", "algorithm", "quantum", "science"]),
 ("business", "Business and Markets", "Business and Market Trends in Short Videos",
  "Markets, earnings and company moves that matter, explained fast. Short videos from Trend Radar AI.",
  ["market", "stock", "nasdaq", "dow", "s&p", "kospi", "selloff", "plunge", "rally", "earnings", "ipo", "invest", "econom", "inflation", "fed", "bank", "business", "ceo", "revenue", "valuation", "bubble", "boom", "bitcoin", "crypto", "oil"]),
 ("world", "World News", "World News Trends in Short Videos",
  "The world stories people are talking about, in short and clear videos from Trend Radar AI.",
  ["china", "india", "pakistan", "russia", "ukraine", "europe", "eu ", "us ", "u.s.", "trump", "election", "war", "government", "world", "global", "president", "minister", "united states", "japan", "korea", "africa", "foreign"]),
 ("middle-east", "Middle East", "Middle East News Trends in Short Videos",
  "Middle East headlines explained quickly: Egypt, Gulf, Iran, Israel and the region. Short videos from Trend Radar AI.",
  ["middle east", "egypt", "iran", "israel", "gaza", "saudi", "uae", "dubai", "gulf", "qatar", "iraq", "syria", "lebanon", "turkey", "yemen", "jordan", "tehran"]),
 ("weekly-roundup", "Weekly Roundup", "Weekly AI and Tech Roundup",
  "One video with the stories that mattered this week in AI, tech and the world. Weekly roundup from Trend Radar AI.",
  ["this week", "weekly", "roundup", "stories that mattered", "week in"]),
]

def fetch_feed():
    req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0"})
    x = urllib.request.urlopen(req, timeout=30).read().decode("utf8")
    out = []
    for e in re.findall(r"<entry>.*?</entry>", x, re.S):
        vid = re.search(r"<yt:videoId>(.*?)<", e).group(1)
        title = html.unescape(re.search(r"<title>(.*?)</title>", e).group(1))
        pub_full = re.search(r"<published>(.*?)<", e).group(1)
        pub = pub_full[:10]
        url = re.search(r'<link rel="alternate" href="([^"]+)"', e)
        url = url.group(1) if url else f"https://www.youtube.com/watch?v={vid}"
        desc = re.search(r"<media:description>(.*?)</media:description>", e, re.S)
        desc = html.unescape(desc.group(1)).strip().split("\n")[0][:200] if desc else ""
        out.append({"id": vid, "title": title, "date": pub, "ts": pub_full, "url": url, "desc": desc})
    return out

def load_store():
    p = os.path.join(ROOT, "videos.json")
    return json.load(open(p, encoding="utf8")) if os.path.exists(p) else []

def clean(t): return t.replace(" #Shorts", "").replace("#Shorts", "").strip()
def kind(v): return "Short" if "/shorts/" in v["url"] else "Video"

def topics_of(v):
    t = " " + clean(v["title"]).lower() + " "
    res = []
    for slug, _, _, _, kws in TOPICS:
        for k in kws:
            if re.search(r"(?<![a-z0-9])" + re.escape(k.strip()) + (r"" if k.endswith(" ") else r""), t):
                res.append(slug); break
    if "5 ai stories" in t or "this week" in t: res = [s for s in res if s != "world"] + (["weekly-roundup"] if "weekly-roundup" not in res else [])
    if not res: res = ["world"]
    return res

CSS = open(os.path.join(ROOT, "style.css"), encoding="utf8").read()

def short(t, n):
    t = clean(t)
    if len(t) <= n: return t
    cut = t[:n].rsplit(" ", 1)[0]
    return cut.rstrip(" ,:;-|") + "..."

def trend_title(label, vs):
    pre = {"AI": "AI news today", "Tech": "Tech news today", "Business and Markets": "Market and business news today",
           "World News": "World news today", "Middle East": "Middle East news today", "Weekly Roundup": "Weekly AI and tech roundup"}.get(label, label)
    base = f"{pre}: {short(vs[0]['title'], 48)}" if vs else pre
    return base + " | Trend Radar AI"

def trend_desc(base, vs):
    heads = "; ".join(short(v["title"], 70) for v in vs[:2])
    d = f"{base} Latest: {heads}." if heads else base
    return d if len(d) <= 300 else d[:297].rsplit(" ", 1)[0] + "..."

def trending_block(vs):
    items = "".join(f'<li><a href="{html.escape(v["url"])}"><span>{html.escape(clean(v["title"]))}</span><em>Watch on YouTube</em></a></li>' for v in vs[:5])
    return f'<section><h2>Trending now</h2><p class="sub">The newest stories we covered, newest first.</p><ol class="tr">{items}</ol></section>'

def card(v):
    t = html.escape(clean(v["title"]))
    return (f'<a class="v" href="{html.escape(v["url"])}"><div class="t" style="background-image:url(https://img.youtube.com/vi/{v["id"]}/hqdefault.jpg)"></div>'
            f'<h3>{t}</h3><p>{kind(v)} &middot; {v["date"]} &middot; <b>Watch on YouTube</b></p></a>')

def jsonld(vs, extra):
    g = list(extra)
    for v in vs:
        g.append({"@type": "VideoObject", "name": clean(v["title"]),
                  "description": v["desc"] or clean(v["title"]),
                  "thumbnailUrl": f"https://img.youtube.com/vi/{v['id']}/hqdefault.jpg",
                  "contentUrl": v["url"], "embedUrl": f"https://www.youtube.com/embed/{v['id']}",
                  "uploadDate": v.get("ts") or (v["date"] + "T00:00:00+00:00")})
    return json.dumps({"@context": "https://schema.org", "@graph": g}, ensure_ascii=False).replace("</", "<\\/")

def nav(active, slugs):
    items = [("", "Home")] + [(s, l) for s, l, *_ in TOPICS if s in slugs]
    return "".join(f'<a href="{BASE}{s + "/" if s else ""}"{" class=on" if s == active else ""}>{l}</a>' for s, l in items)

def h1_plain(h): return re.sub(r'<[^>]+>', '', h)

def fit_title(t, n=60):
    suf = " | Trend Radar AI"
    if len(t) <= n: return t
    body = t[:-len(suf)] if t.endswith(suf) else t
    room = n - len(suf)
    cut = body[:room].rsplit(" ", 1)[0].rstrip(" ,:;-|.") if len(body) > room else body
    return cut + suf

def fit_desc(d, n=158):
    if len(d) <= n: return d
    return d[:n - 1].rsplit(" ", 1)[0].rstrip(" ,:;-|") + "."

def page(url, title, desc, h1, lead, vs, slugs, active, hero=False, extra_ld=None, extra_html=""):
    title, desc = fit_title(title), fit_desc(desc)
    crumbs = [{"@type": "ListItem", "position": 1, "name": "Trend Radar AI", "item": BASE}]
    if url != BASE: crumbs.append({"@type": "ListItem", "position": 2, "name": h1_plain(h1), "item": url})
    ld = jsonld(vs, (extra_ld or []) + [{"@type": "BreadcrumbList", "itemListElement": crumbs}])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<link rel="alternate" type="application/atom+xml" title="Trend Radar AI: latest stories" href="{BASE}feed.xml">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="{url}"><meta property="og:site_name" content="Trend Radar AI"><meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{html.escape(title)}"><meta name="twitter:description" content="{html.escape(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"><meta name="theme-color" content="#050b1a">
<meta property="og:image" content="https://img.youtube.com/vi/{vs[0]["id"] if vs else ""}/hqdefault.jpg">
<script type="application/ld+json">{ld}</script>
<style>{CSS}</style></head><body>
<header{' class="hero"' if hero else ''}><div class="radar"></div><div class="w">
<div class="badge">AI first. World trends.</div>
<h1>{h1}</h1>
<p class="lead">{html.escape(lead)}</p>
<a class="btn yt" href="{CH}?sub_confirmation=1">Subscribe on YouTube</a><a class="btn gh" href="{vs[0]["url"] if vs else CH}">Watch the latest on YouTube</a>
</div></header>
<nav>{nav(active, slugs)}</nav>
<div class="w">
{trending_block(vs)}
<section><h2>{"Latest videos" if hero else "Videos"}</h2><p class="sub">Tap a card to watch on YouTube.</p>
<div class="g">
{"".join(card(v) for v in vs)}
</div></section>
{extra_html}
<section><div class="cta"><h2>Never miss a trend</h2><p>New videos every day.</p><a class="btn yt" href="{CH}?sub_confirmation=1">Subscribe free</a></div></section>
</div>
<a class="bar" href="{CH}?sub_confirmation=1">Subscribe to Trend Radar AI</a>
<footer>Trend Radar AI &middot; <a href="{CH}">YouTube channel</a> &middot; X: <a href="https://x.com/TrendRadarAIHQ" rel="noopener">https://x.com/TrendRadarAIHQ</a></footer>
</body></html>'''

def main():
    store = {v["id"]: v for v in load_store()}
    try:
        for v in fetch_feed():
            store[v["id"]] = {**store.get(v["id"], {}), **v}
    except Exception as e:
        print("feed failed, using stored videos:", e, file=sys.stderr)
        if not store: sys.exit(1)
    vids = sorted(store.values(), key=lambda v: (v["date"], v["id"]), reverse=True)
    json.dump(vids, open(os.path.join(ROOT, "videos.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

    by = {s: [] for s, *_ in TOPICS}
    for v in vids:
        for s in topics_of(v): by[s].append(v)
    live = [s for s, *_ in TOPICS if by[s]]

    org = [{"@type": "Organization", "name": "Trend Radar AI", "url": BASE, "sameAs": [CH]}]
    # topic hub cards for home
    hub = '<section id="topics"><h2>Browse by topic</h2><p class="sub">Pick what you care about.</p><div class="steps">' + "".join(
        f'<a class="s" href="{BASE}{s}/"><b>{l}</b><span>{len(by[s])} video{"s" if len(by[s]) != 1 else ""}</span></a>'
        for s, l, *_ in TOPICS if s in live) + "</div></section>"
    home = page(BASE, "Trend Radar AI | AI, tech and world trends explained in short videos",
                trend_desc("Trend Radar AI tracks what the world is talking about, AI first. Trends in AI, tech, business and world news as clear videos and Shorts.", vids),
                'Trend Radar <span>AI</span>',
                "We track what the world is talking about and turn the biggest trends in AI, tech, business and world news into clear videos and Shorts.",
                vids[:12], live, "", hero=True, extra_ld=org, extra_html=hub)
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf8").write(home)

    urls = [(BASE, vids[0]["date"] if vids else str(date.today()))]
    for slug, label, title, desc, _ in TOPICS:
        d = os.path.join(ROOT, slug)
        if not by[slug]:
            if os.path.isdir(d):
                for f in os.listdir(d): os.remove(os.path.join(d, f))
                os.rmdir(d)
            continue
        os.makedirs(d, exist_ok=True)
        u = f"{BASE}{slug}/"
        p = page(u, trend_title(label, by[slug]), trend_desc(desc, by[slug]), f"{label} <span>on Trend Radar</span>", desc, by[slug], live, slug,
                 extra_ld=org + [{"@type": "CollectionPage", "name": title, "url": u}])
        open(os.path.join(d, "index.html"), "w", encoding="utf8").write(p)
        urls.append((u, by[slug][0]["date"]))
    adir = os.path.join(ROOT, "articles")
    if os.path.isdir(adir):
        for a in sorted(os.listdir(adir)):
            ap = os.path.join(adir, a, "index.html")
            if os.path.isfile(ap):
                urls.append((f"{BASE}articles/{a}/", date.fromtimestamp(os.path.getmtime(ap)).isoformat()))
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(
        f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls) + "</urlset>\n"
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(sm)
    ents = "".join(
        f"<entry><title>{html.escape(clean(v['title']))}</title><link rel=\"alternate\" href=\"{html.escape(v['url'])}\"/><id>yt:video:{v['id']}</id><updated>{v['date']}T00:00:00Z</updated><summary>{html.escape(v.get('desc',''))}</summary></entry>"
        for v in vids[:30])
    atom = ('<?xml version="1.0" encoding="UTF-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom"><title>Trend Radar AI: latest stories</title>'
        f'<subtitle>AI first, world trends. Short videos from Trend Radar AI.</subtitle><link rel="self" href="{BASE}feed.xml"/><link rel="alternate" href="{BASE}"/>'
        f'<id>{BASE}</id><updated>{vids[0]["date"]}T00:00:00Z</updated><author><name>Trend Radar AI</name></author>' + ents + "</feed>\n")
    open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf8").write(atom)
    open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")
    print("videos:", len(vids), {s: len(by[s]) for s in by})

main()

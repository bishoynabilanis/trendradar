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

# ---- per-video article pages: built only from each video's cleared script and sources ----
X_URL = "https://x.com/TrendRadarAIHQ"
AI_NOTE = "The script, voice and slides of the video are AI-generated. No real footage or people are shown."
ARTICLES = [
 {"slug": "pkg26-us-disables-ship-iran-blockade", "yt": "HTWeyfD2sAk", "topic": ("middle-east", "Middle East"),
  "title": "CENTCOM: US disables ship over Iran blockade",
  "script": ["CENTCOM said Friday, November 27, a US military aircraft disabled a commercial ship Thursday, November 26, that it says tried to run the naval blockade of Iran.",
   "Precision munitions struck the stern of the Palau-flagged Pacific Archer in the Gulf of Oman, after it left Bandar Abbas. The propulsion was ultimately disabled; the civilian crew was unharmed.",
   "Times Now says the Pacific Archer is at least the fifteenth vessel disabled since blockade operations started in April.",
   "Mohammad Mokhber, an adviser to Iran's supreme leader, said, per state media, that Hormuz will not reopen and the blockade will not stay. No details.",
   "The strike details are from the CENTCOM statement; no independent confirmation, no response from the ship's owner or crew."],
  "sources": [("CENTCOM statement (Nov 27), via DVIDS", "https://www.dvidshub.net/news/580348/us-forces-disable-commercial-vessel-during-blockade-enforcement-against-iran"),
   ("Times Now", "https://www.timesnownews.com/world/middle-east/us-strikes-iran-bound-ship-gulf-of-oman-centcom-mine-strikes-strait-of-hormuz-article-156577281"),
   ("Reuters, via Arab News", "https://www.arabnews.com/middle-east/us-disables-ship-trying-to-leave-iran-as-tehran-vows-to-confront-blockade-3014303")]},
 {"slug": "pkg27-msf-gaza-clinic-strike", "yt": "8JLCMlQCEIE", "topic": ("middle-east", "Middle East"),
  "title": "MSF says Israeli strike killed two staff; army disputes",
  "script": ["Doctors Without Borders says an Israeli strike hit one of its Gaza clinics on Friday, November 27, killing two of its staff, both watchmen.",
   "MSF says the clinic was clearly marked and its location was known to the Israeli military, calling it a direct hit. MSF says the total of its staff killed in Gaza is now seventeen.",
   "The Israeli military says the two men were militants working as MSF watchmen, and says one was an artillery squad commander in Hamas's military wing.",
   "Middle East Eye reports the clinic is close to al-Shifa Hospital and that the death toll from Israeli attacks across Gaza on Friday, November 27, reached eight.",
   "MSF had not responded to the army's claim in the coverage we checked."],
  "sources": [("MSF statement", "https://prezly.msf.org.uk/msf-gaza-israeli-strike-kills-two-msf-colleagues"),
   ("Times of Israel (for the army's statement)", "https://www.timesofisrael.com/idf-says-gaza-strike-killed-two-terrorists-working-for-doctors-without-borders/"),
   ("Middle East Eye (for location and the November 27 toll)", "https://www.middleeasteye.net/live-blog/live-blog-update/doctors-without-borders-says-two-staff-killed-israeli-direct-hit-gaza")]},
 {"slug": "pkg28-ai-labs-encryption-rumors", "yt": "6UmoacLO7gs", "topic": ("ai", "AI"),
  "title": "AI labs may hold encryption 'bombshell'",
  "script": ["The Guardian reports that top computer scientists warn leading AI labs may be sitting on breakthroughs that could shake the encryption protecting banks and governments.",
   "Scott Aaronson wrote he is virtually certain, from multiple reliable sources, that AI labs are sitting on one or more cryptography bombshells, the Guardian reports.",
   "The rumors follow AI models solving decades-old math problems. No lab has announced any encryption finding, and OpenAI and Anthropic did not comment.",
   "Bank of England governor Andrew Bailey said AI companies should be cautious about releasing new models.",
   "Experts quoted by the Guardian say a breakthrough could force rapid encryption upgrades, or prove current systems safer than thought."],
  "sources": [("The Guardian (Nov 28)", "https://www.theguardian.com/technology/2026/nov/28/ai-artificial-intelligence-encryption-global-chaos"),
   ("Nature (Nov 26)", "https://www.nature.com/articles/d41586-026-03875-6"),
   ("The Independent (Nov 27)", "https://www.independent.co.uk/tech/encryption-ai-safety-security-privacy-artificial-intelligence-b3092983.html")]},
 {"slug": "pkg29-uswnt-qualifies-2027-world-cup", "yt": "u9h6geVrxtI", "topic": ("world", "World News"),
  "title": "USWNT qualifies for 2027 World Cup after 8-0 win",
  "script": ["The US women's national team has qualified for the 2027 Women's World Cup, beating El Salvador 8-0 in the Concacaf W Championship quarterfinals on Friday, November 27, AP reports.",
   "Ashley Sanchez scored a hat trick, all three goals in the first half, AP says. Concacaf says the US scored seven first-half goals, the first time it has done that since January 2012.",
   "Jamaica also clinched a World Cup berth earlier on Friday, November 27, with a 3-0 win over Costa Rica, AP reports.",
   "US Soccer says the US plays Jamaica in the semifinals on Tuesday, December 1. The tournament runs June 24 to July 25, 2027, in Brazil."],
  "sources": [("AP (Nov 28)", "https://apnews.com/article/uswnt-el-salvador-womens-world-cup-concacaf-a06a0e4c716c4e302bac79007f53ed56"),
   ("Concacaf (Nov 28)", "https://www.concacaf.com/competitions/w-championship/news/uswnt-qualifies-to-women-s-world-cup-2027"),
   ("US Soccer (Nov 28)", "https://www.ussoccer.com/stories/2026/11/uswnt/instant-recap-usa-qualifies-fifa-womens-world-cup-2027-brazil")]},
 {"slug": "pkg30-el-nino-floods-peru-ecuador", "yt": "s3skktnKpu0", "topic": ("world", "World News"),
  "title": "El Nino floods hit Peru and Ecuador",
  "script": ["Floods linked to an exceptionally strong El Nino are hitting cities in Peru and Ecuador, Al Jazeera reports, citing AFP.",
   "In Piura, northern Peru, waist-high water filled streets after about 12 hours of rain on Thursday, November 26, Al Jazeera reports. Peru's civil defense chief said about 2,000 families could be affected, according to preliminary estimates, Anadolu reports.",
   "In Ecuador, the risk management agency reported 34 deaths and 47,000 people affected on Friday, November 27, per AFP.",
   "EFE, citing the same agency on Thursday, November 26, reported 30 deaths and more than 121,000 affected since late August. The counts differ.",
   "Peru's weather service warned rain could continue for four more days, Anadolu reports."],
  "sources": [("Al Jazeera, citing AFP (Nov 28)", "https://www.aljazeera.com/news/2026/11/28/el-nino-linked-deluges-flood-cities-in-peru-ecuador"),
   ("Anadolu Agency, citing RPP (Nov 27)", "https://www.aa.com.tr/en/americas/heavy-rains-flood-homes-in-perus-piura-affecting-hundreds-of-families/4140922"),
   ("EFE via El Comercio, in Spanish (Nov 26)", "https://elcomercio.pe/mundo/latinoamerica/fenomeno-el-nino-lluvias-ligadas-al-fenomeno-climatico-ya-han-causado-30-muertos-y-mas-de-121000-afectados-en-ecuador-sngr-ultimas-noticia/")]},
 {"slug": "pkg31-hera-crater-asteroid-dimorphos", "yt": "b54tkp1prI0", "topic": ("tech", "Tech"),
  "title": "Hera finds stadium-sized crater on asteroid Dimorphos",
  "script": ["The European Space Agency says its Hera spacecraft found a stadium-sized crater on the asteroid Dimorphos, left by NASA's DART impact in 2022.",
   "ESA says the crater flattened the face DART hit and extends across the asteroid's entire width, and that Dimorphos is now tumbling chaotically.",
   "ESA also reports hundreds of previously unknown boulders, a few metres in size, orbiting the asteroid pair. Science magazine says whether they are impact debris is not yet confirmed.",
   "Science reports the boulders worry mission managers, who want to send two shoebox-sized CubeSats closer. Space.com says one carries radar to probe the interior.",
   "ESA presented the findings on Wednesday, November 25."],
  "sources": [("ESA", "https://www.esa.int/articles/about-us/directorates/operations/space-safety/hera/hera-reveals-stadium-sized-asteroid-crater-left-after-spacecraft-impact"),
   ("Science", "https://www.science.org/content/article/when-humans-walloped-asteroid-we-left-stadium-size-crater"),
   ("Space.com", "https://www.space.com/astronomy/asteroids/hera-spacecraft-gets-1st-up-close-look-at-stadium-sized-hole-punched-in-asteroid-by-nasa-dart-mission")]},
 {"slug": "pkg32-argentina-central-bank-printing-money", "yt": "Oo30DnzM2CQ", "topic": ("business", "Business and Markets"),
  "title": "Argentina bans central bank from printing money for government",
  "script": ["The Associated Press reports Argentina's Congress voted Thursday, November 26, to bar the central bank from printing money to pay the government's bills.",
   "The AP says the Chamber of Deputies approved it 141 to zero, with 99 abstentions, and the bank's \"primary and fundamental mission\" is now to preserve the peso's value.",
   "Per DPA, the bank can no longer give advances to the Finance Ministry or directly buy newly issued government bonds.",
   "The Telegraph reports October inflation was thirty-three per cent, down from more than 211 per cent in 2023, while poverty has surged.",
   "DPA says Argentina may have slipped into a technical recession, with full third-quarter figures due in mid-December."],
  "sources": [("AP", "https://apnews.com/article/javier-milei-central-bank-economy-argentina-peso-primaries-paso-e4598186ef6cbcf05ecc598788c52cec"),
   ("DPA via Yahoo Finance", "https://finance.yahoo.com/economy/policy/articles/argentina-approves-mileis-reform-restricting-074834530.html"),
   ("The Telegraph", "https://www.telegraph.co.uk/world-news/2026/11/27/milei-bans-central-bank-from-printing-money-recession/")]},
 {"slug": "pkg33-openai-countersues-apple-trade-secrets", "yt": "rQOuUd2wh-c", "topic": ("ai", "AI"),
  "title": "OpenAI countersues Apple over trade secrets",
  "script": ["Reuters reports OpenAI sued Apple on Friday, November 27, accusing it of stealing OpenAI's trade secrets, after Apple sued OpenAI over alleged employee poaching.",
   "In its California filing, OpenAI says Apple rehired a former employee who had accessed information on a new device and OpenAI's hardware roadmap, Reuters reports.",
   "Reuters says OpenAI also accuses Apple of discouraging hardware suppliers from working on future OpenAI devices.",
   "Apple told CBS News the counterclaims are \"a transparent attempt to distract from the substance of Apple's lawsuit.\"",
   "OpenAI has denied Apple's allegations, Reuters says. Apple's original case is set for trial on July 19, 2027, according to 9to5Mac."],
  "sources": [("Reuters", "https://www.reuters.com/5f374b32b07b/technology/openai-countersues-apple-stealing-trade-secrets-ft-reports-2026-11-27/"),
   ("CBS News", "https://www.cbsnews.com/news/openai-countersues-apple-trade-secrets-lawsuit/"),
   ("9to5Mac", "https://9to5mac.com/2026/11/27/openai-countersues-apple-alleging-trade-secret-theft-and-supplier-threats/")]},
]
ART_DATE = "2026-11-28"
ART_CSS = ("body{font-family:system-ui,sans-serif;max-width:720px;margin:0 auto;padding:16px;line-height:1.65;background:#050b1a;color:#e8eefc;font-size:17px}"
           "a{color:#6cb6ff}h1{line-height:1.25}h2{margin-top:1.6em}.v{position:relative;padding-top:56.25%;margin:1em 0}"
           ".v iframe{position:absolute;inset:0;width:100%;height:100%;border:0;border-radius:12px}"
           ".note{border:1px solid #2a3a63;border-radius:10px;padding:10px 14px;color:#b9c7ea;font-size:15px}"
           ".more a{display:block;padding:10px 0}footer{margin:2em 0 1em;color:#b9c7ea;font-size:15px}")

def art_desc(a):
    s = a["script"][0]
    return fit_desc(s)

def build_article(a):
    u = f"{BASE}articles/{a['slug']}/"
    yt = f"https://www.youtube.com/shorts/{a['yt']}"
    t = a["title"]
    title = fit_title(t + " | Trend Radar AI")
    desc = art_desc(a)
    tp_slug, tp_label = a["topic"]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "NewsArticle", "headline": t, "description": desc, "mainEntityOfPage": u,
         "datePublished": ART_DATE, "dateModified": ART_DATE, "inLanguage": "en",
         "author": {"@type": "Organization", "name": "Trend Radar AI", "url": BASE},
         "publisher": {"@type": "Organization", "name": "Trend Radar AI", "url": BASE},
         "image": f"https://img.youtube.com/vi/{a['yt']}/hqdefault.jpg",
         "citation": [s[1] for s in a["sources"]]},
        {"@type": "VideoObject", "name": t, "description": desc, "thumbnailUrl": f"https://img.youtube.com/vi/{a['yt']}/hqdefault.jpg",
         "contentUrl": yt, "embedUrl": f"https://www.youtube.com/embed/{a['yt']}", "uploadDate": ART_DATE},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Trend Radar AI", "item": BASE},
            {"@type": "ListItem", "position": 2, "name": tp_label, "item": f"{BASE}{tp_slug}/"},
            {"@type": "ListItem", "position": 3, "name": t, "item": u}]}]}
    ldj = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
    E = html.escape
    paras = "".join(f"<p>{E(s)}</p>" for s in a["script"])
    srcs = "".join(f'<li><a href="{E(h)}" rel="noopener">{E(n)}</a></li>' for n, h in a["sources"])
    others = "".join(f'<a href="{BASE}articles/{b["slug"]}/">{E(b["title"])}</a>' for b in ARTICLES if b is not a)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{u}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:type" content="article"><meta property="og:url" content="{u}"><meta property="og:site_name" content="Trend Radar AI"><meta property="og:image" content="https://img.youtube.com/vi/{a['yt']}/hqdefault.jpg">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{E(title)}"><meta name="twitter:description" content="{E(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<script type="application/ld+json">{ldj}</script>
<style>{ART_CSS}</style></head><body>
<p><a href="{BASE}">Trend Radar AI</a> / <a href="{BASE}{tp_slug}/">{E(tp_label)}</a></p>
<article><h1>{E(t)}</h1>
<p><time datetime="{ART_DATE}">November 28, 2026</time></p>
<p class="note">{AI_NOTE}</p>
{paras}
<div class="v"><iframe src="https://www.youtube-nocookie.com/embed/{a['yt']}" title="{E(t)}" loading="lazy" allowfullscreen></iframe></div>
<p>Watch on YouTube: <a href="{yt}">{E(t)}</a></p>
<h2>Sources</h2>
<ul>{srcs}</ul>
<p class="note">{AI_NOTE} This page repeats what the video says and links the sources it used.</p>
<p>More trends daily: <a href="{CH}">Trend Radar AI on YouTube</a> and on X: <a href="{X_URL}" rel="noopener">{X_URL}</a></p>
<p>Which trend should we cover next? Tell us in the comments on YouTube.</p>
<h2>More from Trend Radar AI</h2>
<div class="more">{others}</div>
</article>
<footer>Trend Radar AI &middot; <a href="{CH}">YouTube channel</a> &middot; X: <a href="{X_URL}" rel="noopener">{X_URL}</a></footer>
</body></html>'''

def build_articles():
    for a in ARTICLES:
        d = os.path.join(ROOT, "articles", a["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf8").write(build_article(a))

def article_list_html():
    items = "".join(f'<a class="s" href="{BASE}articles/{a["slug"]}/"><b>{html.escape(a["title"])}</b><span>Article &middot; sources</span></a>' for a in ARTICLES)
    return f'<section id="articles"><h2>Articles</h2><p class="sub">Each video with its sources.</p><div class="steps">{items}</div></section>'


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

    build_articles()
    org = [{"@type": "Organization", "name": "Trend Radar AI", "url": BASE, "sameAs": [CH]}]
    # topic hub cards for home
    hub = '<section id="topics"><h2>Browse by topic</h2><p class="sub">Pick what you care about.</p><div class="steps">' + "".join(
        f'<a class="s" href="{BASE}{s}/"><b>{l}</b><span>{len(by[s])} video{"s" if len(by[s]) != 1 else ""}</span></a>'
        for s, l, *_ in TOPICS if s in live) + "</div></section>" + article_list_html()
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

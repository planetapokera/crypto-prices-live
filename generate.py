#!/usr/bin/env python3
"""Multilingual static site: 9 languages × 6 pairs × 10 keywords ≈ 540 pages.

Layout:
  site/index.html                                  # RU (default language)
  site/<lang>/index.html                           # per-language homepage
  site/<lang>/<pair>/index.html                    # pair index (= first keyword page)
  site/<lang>/<pair>/<keyword-slug>/index.html     # keyword page
  site/sitemap.xml, robots.txt, <indexnow-key>.txt
"""
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from i18n import LANGS, LANG_META, UI, KEYWORDS, CONTEXT

ROOT = Path(__file__).parent
SITE = ROOT / "site"
SITE.mkdir(exist_ok=True)

DOMAIN = "https://planetapokera.github.io/crypto-prices-live"
DEFAULT_LANG = "ru"


# ---------- pair definitions ----------

@dataclass
class Pair:
    slug: str
    base: str
    quote: str
    label: str
    channel: str
    source: str
    price_fn: str


PAIRS = [
    Pair("btc-usdt", "BTC", "USDT", "BTC/USDT", "@btcusdtpriced", "Binance spot", "btc_usdt"),
    Pair("btc-usd",  "BTC", "USD",  "BTC/USD",  "@btcusdprice",   "Coinbase",     "btc_usd"),
    Pair("btc-rub",  "BTC", "RUB",  "BTC/RUB",  "@btcrubprice",
         "Binance BTCUSDT × MOEX USD/RUB", "btc_rub"),
    Pair("ton-usdt", "TON", "USDT", "TON/USDT", "@tonusdprice",   "Binance spot", "ton_usdt"),
    Pair("wld-usdt", "WLD", "USDT", "WLD/USDT", "@wldusdprice",   "Binance spot", "wld_usdt"),
    Pair("usd-rub",  "USD", "RUB",  "USD/RUB",  "@usdrubprice",   "MOEX USD000UTSTOM", "usd_rub"),
]


# ---------- prices ----------

def fetch_prices() -> dict[str, float]:
    out: dict[str, float] = {}
    def _get_json(url: str, timeout: int = 10) -> dict:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

    try:
        out["btc_usdt"] = float(_get_json(
            "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")["price"])
    except Exception:
        pass
    try:
        out["ton_usdt"] = float(_get_json(
            "https://api.binance.com/api/v3/ticker/price?symbol=TONUSDT")["price"])
    except Exception:
        pass
    try:
        out["wld_usdt"] = float(_get_json(
            "https://api.binance.com/api/v3/ticker/price?symbol=WLDUSDT")["price"])
    except Exception:
        pass
    try:
        out["btc_usd"] = float(_get_json(
            "https://api.coinbase.com/v2/prices/BTC-USD/spot")["data"]["amount"])
    except Exception:
        pass
    try:
        j = _get_json(
            "https://iss.moex.com/iss/engines/currency/markets/selt/securities/"
            "USD000UTSTOM.json?iss.only=marketdata&marketdata.columns=BOARDID,LAST")
        for board, last in j["marketdata"]["data"]:
            if board == "CETS" and last is not None:
                out["usd_rub"] = float(last)
                break
    except Exception:
        pass
    if "btc_usdt" in out and "usd_rub" in out:
        out["btc_rub"] = out["btc_usdt"] * out["usd_rub"]

    cached = ROOT / "prices.json"
    if cached.exists():
        for k, v in json.loads(cached.read_text()).items():
            out.setdefault(k, v)
    return out


def fmt_price(p: float) -> str:
    if p >= 1000:
        return f"{p:,.2f}".replace(",", " ")
    if p >= 10:
        return f"{p:,.3f}"
    if p >= 1:
        return f"{p:,.4f}"
    return f"{p:,.6f}"


# ---------- styling ----------

BASE_CSS = """
:root{--bg:#0b1220;--fg:#e8eef9;--muted:#8fa3c2;--accent:#3ecf8e;--card:#141c32}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
.wrap{max-width:820px;margin:0 auto;padding:32px 20px 80px}
header{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;flex-wrap:wrap;gap:12px}
header a{color:var(--muted);text-decoration:none;font-size:14px}
header a:hover{color:var(--fg)}
.lang-nav{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 24px}
.lang-nav a{font-size:12px;padding:3px 8px;border:1px solid #243356;border-radius:6px}
.lang-nav a.active{background:var(--accent);color:#06241a;border-color:var(--accent)}
h1{font-size:26px;line-height:1.25;margin:0 0 12px}
h2{font-size:20px;margin:28px 0 12px}
h3{font-size:16px;margin:18px 0 6px}
.price-card{background:linear-gradient(135deg,#1a2647,#121b33);padding:24px;border-radius:14px;margin:20px 0;border:1px solid #243356}
.price{font-size:40px;font-weight:700;color:var(--accent);margin:8px 0}
.price small{color:var(--muted);font-size:14px;font-weight:400;margin-left:8px}
.meta{color:var(--muted);font-size:13px;margin-top:4px}
.cta{display:inline-block;background:var(--accent);color:#06241a;padding:14px 22px;border-radius:10px;font-weight:700;text-decoration:none;margin:14px 0}
.cta:hover{filter:brightness(1.08)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:20px 0}
.grid a{display:block;background:var(--card);color:var(--fg);padding:14px;border-radius:10px;text-decoration:none;border:1px solid #243356}
.grid a:hover{border-color:var(--accent)}
.grid strong{display:block;color:var(--accent)}
.grid span{color:var(--muted);font-size:13px}
p{color:#c9d4e9}
ul{color:#c9d4e9}
footer{margin-top:50px;padding-top:24px;border-top:1px solid #243356;color:var(--muted);font-size:13px}
footer a{color:var(--muted)}
.calc{background:var(--card);border:1px solid #243356;border-radius:12px;padding:18px;margin:20px 0}
.calc .row{display:flex;gap:8px;align-items:stretch;margin:8px 0;flex-wrap:wrap}
.calc input{flex:1;min-width:140px;background:#0b1220;border:1px solid #243356;color:var(--fg);padding:10px 12px;border-radius:8px;font-size:16px;font-family:inherit}
.calc input:focus{outline:none;border-color:var(--accent)}
.calc .ccy{min-width:70px;padding:10px 12px;background:#0b1220;border:1px solid #243356;border-radius:8px;color:var(--muted);font-weight:600;display:flex;align-items:center;justify-content:center}
.calc button{background:transparent;border:1px solid #243356;color:var(--muted);border-radius:8px;padding:6px 12px;cursor:pointer;font-size:13px}
.calc button:hover{border-color:var(--accent);color:var(--fg)}
.calc .rate{color:var(--muted);font-size:13px;margin-top:10px}
[dir="rtl"] .grid strong,[dir="rtl"] .price small{direction:rtl}
"""

VERIFY_META = (
    '<meta name="yandex-verification" content="1edba899112310f3"/>\n'
    '<meta name="google-site-verification" content="OI8q2vN1dp3ChHueOuCCzlqUxtmBmFcApUMo30wDKno"/>'
)


# ---------- templates ----------

def lang_nav_html(lang_slug: str, current_path: str) -> str:
    """current_path: canonical path inside site minus leading '/', no trailing slash.
    For each supported language emit a link to same page under that language.
    """
    out = []
    for lg in LANGS:
        # Compute counterpart URL in other lang.
        # current_path looks like "<lang>/<pair>/<kw>/" or "<lang>/" or "<lang>/<pair>/"
        # Replace the <lang> prefix with lg.
        parts = [p for p in current_path.split("/") if p]
        if not parts:
            href = f"/crypto-prices-live/{lg}/"
        else:
            parts[0] = lg
            href = "/crypto-prices-live/" + "/".join(parts) + "/"
        cls = "active" if lg == lang_slug else ""
        out.append(f'<a href="{href}" class="{cls}" hreflang="{LANG_META[lg]["html_lang"]}">{LANG_META[lg]["name"]}</a>')
    return '<div class="lang-nav">' + "".join(out) + "</div>"


ALL_CHANNELS = [
    ("@btcusdtpriced", "BTC/USDT", "btc-usdt"),
    ("@btcusdprice",   "BTC/USD",  "btc-usd"),
    ("@btcrubprice",   "BTC/RUB",  "btc-rub"),
    ("@tonusdprice",   "TON/USDT", "ton-usdt"),
    ("@wldusdprice",   "WLD/USDT", "wld-usdt"),
    ("@usdrubprice",   "USD/RUB",  "usd-rub"),
]


def cross_grid(lang_slug: str, current_pair_slug: str, prices: dict[str, float]) -> str:
    items = []
    for ch, lbl, slug in ALL_CHANNELS:
        if slug == current_pair_slug:
            continue
        fn = slug.replace("-", "_")
        price = prices.get(fn)
        price_str = fmt_price(price) if price is not None else "—"
        items.append(
            f'<a href="/crypto-prices-live/{lang_slug}/{slug}/"><strong>{lbl}</strong>'
            f'<span>{price_str} · {ch}</span></a>'
        )
    return '<div class="grid">' + "".join(items) + "</div>"


def hreflang_links(kind: str, pair_slug: str | None, kw_slug: str | None) -> str:
    """Emit <link rel="alternate" hreflang="..." href="...">.

    kind: 'home' | 'pair' | 'kw'
    """
    out = []
    for lg in LANGS:
        if kind == "home":
            href = f"{DOMAIN}/{lg}/"
        elif kind == "pair":
            href = f"{DOMAIN}/{lg}/{pair_slug}/"
        else:
            # kw slugs are language-specific; cross-link to language homepage if
            # we can't map the slug, otherwise use the same slug position (which
            # will 404 if the other lang uses a different slug). Safer: go to
            # pair index for other languages.
            href = f"{DOMAIN}/{lg}/{pair_slug}/"
        out.append(f'<link rel="alternate" hreflang="{LANG_META[lg]["html_lang"]}" href="{href}"/>')
    # x-default
    out.append(f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}/{pair_slug}/"/>' if pair_slug and kind != "home" else f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}/"/>')
    return "\n".join(out)


def page_html(lang: str, pair: Pair, kw_slug: str, kw: str,
              price: float | None, prices: dict[str, float]) -> str:
    ui = UI[lang]
    meta = LANG_META[lang]
    dir_attr = meta["dir"]
    html_lang = meta["html_lang"]
    price_str = fmt_price(price) if price is not None else "—"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    tg_url = f"https://t.me/{pair.channel.lstrip('@')}"
    canonical = f"{DOMAIN}/{lang}/{pair.slug}/{kw_slug}/"

    json_ld_rate = {
        "@context": "https://schema.org",
        "@type": "ExchangeRateSpecification",
        "currency": pair.base,
        "currentExchangeRate": {
            "@type": "UnitPriceSpecification",
            "price": price if price is not None else 0,
            "priceCurrency": pair.quote,
        },
        "name": f"{pair.label} live exchange rate",
        "url": canonical,
    }
    json_ld_faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": ui["q_freq"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": ui["a_freq"].format(channel=pair.channel),
                },
            },
            {
                "@type": "Question",
                "name": ui["q_source"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": ui["a_source"].format(source=pair.source),
                },
            },
            {
                "@type": "Question",
                "name": ui["q_free"],
                "acceptedAnswer": {"@type": "Answer", "text": ui["a_free"]},
            },
            {
                "@type": "Question",
                "name": ui["q_notif"],
                "acceptedAnswer": {"@type": "Answer", "text": ui["a_notif"]},
            },
        ],
    }

    title = f"{kw} — {pair.label} | {pair.channel}"
    description = ui["live_line"].format(label=pair.label, source=pair.source, channel=pair.channel)
    ctx_h2, ctx_p1, ctx_p2 = CONTEXT[lang][pair.slug]
    cross = cross_grid(lang, pair.slug, prices)
    lang_nav = lang_nav_html(lang, f"{lang}/{pair.slug}/{kw_slug}/")
    hreflang = hreflang_links("kw", pair.slug, kw_slug)

    return f"""<!doctype html>
<html lang="{html_lang}" dir="{dir_attr}">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
<meta name="description" content="{description}"/>
<meta name="keywords" content="{kw}, {pair.label}, {pair.base} {pair.quote}, live price, telegram, {pair.channel}"/>
<link rel="canonical" href="{canonical}"/>
{hreflang}
<meta property="og:title" content="{title}"/>
<meta property="og:description" content="{description}"/>
<meta property="og:url" content="{canonical}"/>
<meta property="og:type" content="website"/>
<meta name="twitter:card" content="summary"/>
<meta name="theme-color" content="#0b1220"/>
{VERIFY_META}
<script type="application/ld+json">{json.dumps(json_ld_rate, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(json_ld_faq, ensure_ascii=False)}</script>
<style>{BASE_CSS}</style>
</head>
<body>
<div class="wrap">
  <header>
    <a href="/crypto-prices-live/{lang}/">← {ui['home']}</a>
    <a href="{tg_url}">{ui['subscribe']} →</a>
  </header>
  {lang_nav}

  <h1>{kw}</h1>
  <p>{description}</p>

  <div class="price-card">
    <div class="meta">{pair.label} · {ui['source_prefix']}: {pair.source}</div>
    <div class="price">{price_str} <small>{pair.quote}</small></div>
    <div class="meta">{ui['snapshot_at']} {ts} · {ui['refreshed']}</div>
    <a class="cta" href="{tg_url}">{ui['view_each_minute']} → {pair.channel}</a>
  </div>

  <h2>{ui['calc_title'].format(label=pair.label)}</h2>
  <div class="calc" data-rate="{price if price is not None else 0}" data-base="{pair.base}" data-quote="{pair.quote}">
    <div class="row">
      <input type="number" inputmode="decimal" step="any" class="calc-from" value="1" aria-label="{ui['calc_amount']}"/>
      <div class="ccy">{pair.base}</div>
    </div>
    <div class="row">
      <input type="number" inputmode="decimal" step="any" class="calc-to" aria-label="{ui['calc_result']}"/>
      <div class="ccy">{pair.quote}</div>
      <button type="button" class="calc-swap">⇅ {ui['calc_swap']}</button>
    </div>
    <div class="rate">{ui['calc_rate_line'].format(base=pair.base, price=price_str, quote=pair.quote)}</div>
  </div>
  <script>
  (function(){{
    document.querySelectorAll('.calc').forEach(function(root){{
      if(root._init) return; root._init = true;
      var rate = parseFloat(root.dataset.rate) || 0;
      var base = root.dataset.base, quote = root.dataset.quote;
      var fromEl = root.querySelector('.calc-from');
      var toEl   = root.querySelector('.calc-to');
      var ccyFrom = root.querySelectorAll('.ccy')[0];
      var ccyTo   = root.querySelectorAll('.ccy')[1];
      var swapBtn = root.querySelector('.calc-swap');
      var inverted = false;
      function fmt(n){{
        if(!isFinite(n)) return '';
        if(Math.abs(n)>=1000) return n.toLocaleString('en-US',{{maximumFractionDigits:2}}).replace(/,/g,' ');
        if(Math.abs(n)>=1)    return n.toLocaleString('en-US',{{maximumFractionDigits:4}});
        return n.toLocaleString('en-US',{{maximumFractionDigits:8}});
      }}
      function recalc(src){{
        var r = inverted ? (rate>0?1/rate:0) : rate;
        if(src==='to'){{ var v=parseFloat(toEl.value); fromEl.value = fmt(v/(r||1)); }}
        else           {{ var v=parseFloat(fromEl.value); toEl.value = fmt(v*r); }}
      }}
      fromEl.addEventListener('input', function(){{recalc('from');}});
      toEl.addEventListener('input',   function(){{recalc('to');}});
      swapBtn.addEventListener('click', function(){{
        inverted = !inverted;
        ccyFrom.textContent = inverted ? quote : base;
        ccyTo.textContent   = inverted ? base  : quote;
        recalc('from');
      }});
      recalc('from');
    }});
  }})();
  </script>

  <h2>{ctx_h2}</h2>
  <p>{ctx_p1}</p>
  <p>{ctx_p2}</p>

  <h2>{ui['other_pairs']}</h2>
  {cross}

  <h2>{ui['faq']}</h2>
  <h3>{ui['q_freq']}</h3>
  <p>{ui['a_freq'].format(channel=pair.channel)}</p>
  <h3>{ui['q_source']}</h3>
  <p>{ui['a_source'].format(source=pair.source)}</p>
  <h3>{ui['q_free']}</h3>
  <p>{ui['a_free']}</p>
  <h3>{ui['q_notif']}</h3>
  <p>{ui['a_notif']}</p>

  <footer>
    © {datetime.now(timezone.utc).year} Crypto Prices Live · {ui['source_prefix']}: {pair.source} · {ui['source_on']} <a href="https://github.com/planetapokera/crypto-prices-live">GitHub</a>
  </footer>
</div>
</body>
</html>
"""


def home_html(lang: str, prices: dict[str, float]) -> str:
    ui = UI[lang]
    meta = LANG_META[lang]
    cards = []
    for p in PAIRS:
        price = prices.get(p.price_fn)
        price_str = fmt_price(price) if price is not None else "—"
        cards.append(
            f'<a href="/crypto-prices-live/{lang}/{p.slug}/"><strong>{p.label}</strong>'
            f'<span>{price_str} {p.quote} · {p.channel}</span></a>'
        )
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    bullets = "".join(f"<li>{b}</li>" for b in ui["how_bullets"])
    lang_nav = lang_nav_html(lang, f"{lang}/")
    hreflang = hreflang_links("home", None, None)
    canonical = f"{DOMAIN}/{lang}/"
    return f"""<!doctype html>
<html lang="{meta['html_lang']}" dir="{meta['dir']}">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{ui['home_title']}</title>
<meta name="description" content="{ui['home_desc']}"/>
<link rel="canonical" href="{canonical}"/>
{hreflang}
<meta property="og:title" content="{ui['home_title']}"/>
<meta property="og:description" content="{ui['home_desc']}"/>
{VERIFY_META}
<style>{BASE_CSS}</style>
</head>
<body>
<div class="wrap">
  <header>
    <strong>Crypto Prices Live</strong>
    <a href="https://github.com/planetapokera/crypto-prices-live">GitHub</a>
  </header>
  {lang_nav}
  <h1>{ui['home_h1']}</h1>
  <p>{ui['home_intro']} Snapshot: {ts}.</p>
  <div class="grid">{''.join(cards)}</div>
  <h2>{ui['how_it_works']}</h2>
  <ul>{bullets}</ul>
  <footer>{ui['source_on']} <a href="https://github.com/planetapokera/crypto-prices-live">GitHub</a>. {ui['not_advice']}</footer>
</div>
</body>
</html>
"""


def root_redirect_html() -> str:
    # Browser sends users to their preferred language if we serve the default
    # (ru) homepage but let JS/meta-refresh redirect to a better match.
    langs_js = json.dumps(LANGS)
    return f"""<!doctype html>
<html lang="{DEFAULT_LANG}">
<head>
<meta charset="utf-8"/>
<title>Crypto Prices Live</title>
<meta name="description" content="Crypto & FX prices every minute in Telegram — 6 channels, 9 languages."/>
<link rel="canonical" href="{DOMAIN}/{DEFAULT_LANG}/"/>
{VERIFY_META}
<meta http-equiv="refresh" content="0; url=/crypto-prices-live/{DEFAULT_LANG}/"/>
<script>
(function(){{
  var supported = {langs_js};
  var pref = (navigator.language||'en').toLowerCase();
  var target = '{DEFAULT_LANG}';
  for (var i=0;i<supported.length;i++) {{
    if (pref.indexOf(supported[i]) === 0) {{ target = supported[i]; break; }}
  }}
  location.replace('/crypto-prices-live/' + target + '/');
}})();
</script>
</head>
<body>
<p>Redirecting to <a href="/crypto-prices-live/{DEFAULT_LANG}/">/{DEFAULT_LANG}/</a>…</p>
</body>
</html>
"""


def sitemap(urls: list[str]) -> str:
    body = []
    lastmod = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for u in urls:
        body.append(
            f"<url><loc>{DOMAIN}/{u}</loc><lastmod>{lastmod}</lastmod>"
            f"<changefreq>hourly</changefreq><priority>0.7</priority></url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(body) + "\n</urlset>\n"
    )


# ---------- build ----------

def main() -> None:
    prices = fetch_prices()
    (ROOT / "prices.json").write_text(json.dumps(prices, indent=2))
    urls: list[str] = [""]  # root

    # Root redirect page
    (SITE / "index.html").write_text(root_redirect_html(), encoding="utf-8")

    for lang in LANGS:
        lang_dir = SITE / lang
        lang_dir.mkdir(exist_ok=True)
        (lang_dir / "index.html").write_text(home_html(lang, prices), encoding="utf-8")
        urls.append(f"{lang}/")

        for pair in PAIRS:
            pair_dir = lang_dir / pair.slug
            pair_dir.mkdir(exist_ok=True)
            price = prices.get(pair.price_fn)

            # Pair index = first keyword page content, but at /<lang>/<pair>/
            kws = KEYWORDS[lang][pair.slug]
            first_slug, first_kw = kws[0]
            (pair_dir / "index.html").write_text(
                page_html(lang, pair, first_slug, first_kw, price, prices),
                encoding="utf-8",
            )
            urls.append(f"{lang}/{pair.slug}/")

            for kw_slug, kw in kws:
                kdir = pair_dir / kw_slug
                kdir.mkdir(exist_ok=True)
                (kdir / "index.html").write_text(
                    page_html(lang, pair, kw_slug, kw, price, prices),
                    encoding="utf-8",
                )
                urls.append(f"{lang}/{pair.slug}/{kw_slug}/")

    (SITE / "sitemap.xml").write_text(sitemap(urls), encoding="utf-8")
    (SITE / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n",
        encoding="utf-8",
    )
    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    key = "c9f1a8b7d6e5c4b3a2918273645f0e9d"
    (SITE / f"{key}.txt").write_text(key, encoding="utf-8")

    total = sum(1 for _ in SITE.rglob("*.html"))
    print(f"Built {total} HTML pages, {len(urls)} URLs in sitemap.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate 60 SEO landing pages for the 6 price channels.

Pages: site/index.html + site/{pair}/{keyword-slug}/index.html.
Content: short description, H1 with keyword, live price placeholder updated by
Actions, JSON-LD FinancialProduct, Telegram CTA, cross-links to 5 other channels.

prices.json is refreshed hourly by GitHub Actions and injected into every page
at build time so Googlebot sees fresh numbers.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError

ROOT = Path(__file__).parent
SITE = ROOT / "site"
SITE.mkdir(exist_ok=True)

DOMAIN = "https://planetapokera.github.io/crypto-prices-live"


# ---------- pair definitions ----------

@dataclass
class Pair:
    slug: str                # URL slug, e.g. "btc-usdt"
    base: str                # "BTC"
    quote: str               # "USDT"
    label: str               # "BTC/USDT"
    channel: str             # @btcusdtpriced
    source: str              # "Binance spot"
    price_fn: str            # resolver key
    keywords: list[tuple[str, str]]  # (slug, human-readable keyword)


PAIRS: list[Pair] = [
    Pair(
        "btc-usdt", "BTC", "USDT", "BTC/USDT", "@btcusdtpriced", "Binance spot", "btc_usdt",
        [
            ("btc-usdt-live-price", "BTC USDT live price"),
            ("bitcoin-tether-exchange-rate", "Bitcoin Tether exchange rate"),
            ("kurs-bitkoina-k-usdt", "курс биткоина к USDT"),
            ("cena-bitkoina-onlayn", "цена биткоина онлайн"),
            ("btc-usdt-realtime-ticker", "BTC USDT realtime ticker"),
            ("live-bitcoin-tether-chart", "live Bitcoin Tether chart"),
            ("btc-usdt-telegram-bot", "BTC USDT Telegram bot"),
            ("bitkoin-k-tezeru-kurs-segodnya", "биткоин к тезеру курс сегодня"),
            ("bitcoin-price-feed-api", "Bitcoin price feed API"),
            ("btc-usdt-kazhduyu-minutu", "BTC USDT каждую минуту"),
        ],
    ),
    Pair(
        "btc-usd", "BTC", "USD", "BTC/USD", "@btcusdprice", "Coinbase", "btc_usd",
        [
            ("btc-usd-live-price", "BTC USD live price"),
            ("bitcoin-dollar-exchange-rate", "Bitcoin US Dollar exchange rate"),
            ("kurs-bitkoina-v-dollarakh", "курс биткоина в долларах"),
            ("bitkoin-cena-v-dollarakh-seychas", "биткоин цена в долларах сейчас"),
            ("btc-usd-coinbase-spot", "BTC USD Coinbase spot"),
            ("live-bitcoin-usd-chart", "live Bitcoin USD chart"),
            ("btc-usd-telegram-ticker", "BTC USD Telegram ticker"),
            ("bitkoin-onlayn-kurs-usd", "биткоин онлайн курс USD"),
            ("bitcoin-usd-realtime", "Bitcoin USD realtime"),
            ("btc-usd-kazhduyu-minutu", "BTC USD каждую минуту"),
        ],
    ),
    Pair(
        "btc-rub", "BTC", "RUB", "BTC/RUB", "@btcrubprice",
        "Binance BTCUSDT × MOEX USD/RUB", "btc_rub",
        [
            ("btc-rub-kurs-onlayn", "BTC RUB курс онлайн"),
            ("skolko-stoit-bitkoin-v-rublyakh", "сколько стоит биткоин в рублях"),
            ("bitkoin-rubl-kazhduyu-minutu", "биткоин рубль каждую минуту"),
            ("tsena-bitkoina-v-rublyakh-seychas", "цена биткоина в рублях сейчас"),
            ("btc-rub-birzha-kurs", "BTC RUB биржа курс"),
            ("live-bitcoin-ruble-price", "live Bitcoin Ruble price"),
            ("bitkoin-v-rublyakh-segodnya", "биткоин в рублях сегодня"),
            ("btc-rub-telegram-kanal", "BTC RUB Telegram канал"),
            ("bitkoin-kurs-real-time-rubli", "биткоин курс real time рубли"),
            ("skolko-sеychas-bitkoin-rubl", "сколько сейчас биткоин рубль"),
        ],
    ),
    Pair(
        "ton-usdt", "TON", "USDT", "TON/USDT", "@tonusdprice", "Binance spot", "ton_usdt",
        [
            ("ton-usdt-live-price", "TON USDT live price"),
            ("toncoin-price-realtime", "Toncoin price realtime"),
            ("kurs-ton-k-usdt", "курс TON к USDT"),
            ("ton-open-network-kurs", "TON Open Network курс"),
            ("toncoin-kazhduyu-minutu", "Toncoin каждую минуту"),
            ("ton-usdt-telegram-ticker", "TON USDT Telegram ticker"),
            ("tsena-tonkoina-onlayn", "цена тонкоина онлайн"),
            ("ton-crypto-live-chart", "TON crypto live chart"),
            ("kurs-ton-segodnya", "курс TON сегодня"),
            ("ton-usdt-binance-spot", "TON USDT Binance spot"),
        ],
    ),
    Pair(
        "wld-usdt", "WLD", "USDT", "WLD/USDT", "@wldusdprice", "Binance spot", "wld_usdt",
        [
            ("wld-usdt-live-price", "WLD USDT live price"),
            ("worldcoin-price-realtime", "Worldcoin price realtime"),
            ("kurs-wld-k-usdt", "курс WLD к USDT"),
            ("worldcoin-live-chart", "Worldcoin live chart"),
            ("wld-kazhduyu-minutu", "WLD каждую минуту"),
            ("wld-usdt-telegram-ticker", "WLD USDT Telegram ticker"),
            ("tsena-worldcoin-onlayn", "цена Worldcoin онлайн"),
            ("wld-token-kurs", "WLD токен курс"),
            ("worldcoin-binance-spot", "Worldcoin Binance spot"),
            ("kurs-wld-segodnya", "курс WLD сегодня"),
        ],
    ),
    Pair(
        "usd-rub", "USD", "RUB", "USD/RUB", "@usdrubprice", "MOEX USD000UTSTOM", "usd_rub",
        [
            ("kurs-dollara-k-rublyu-onlayn", "курс доллара к рублю онлайн"),
            ("skolko-stoit-dollar-seychas", "сколько стоит доллар сейчас"),
            ("usd-rub-moskovskaya-birzha", "USD RUB Московская биржа"),
            ("dollar-rubl-kazhduyu-minutu", "доллар рубль каждую минуту"),
            ("usd-rub-live-price", "USD RUB live price"),
            ("kurs-dollara-segodnya-moex", "курс доллара сегодня MOEX"),
            ("dollar-rubl-telegram-kanal", "доллар рубль Telegram канал"),
            ("tsena-dollara-v-rublyakh", "цена доллара в рублях"),
            ("kurs-usd-rub-realtime", "курс USD RUB realtime"),
            ("dollar-rubl-birzha-moskva", "доллар рубль биржа Москва"),
        ],
    ),
]


# ---------- prices ----------

def fetch_prices() -> dict[str, float]:
    """Pull latest snapshot from Binance/Coinbase/MOEX. Best-effort — if anything
    fails we fall back to the previously stored prices.json so the build never
    breaks the site."""
    out: dict[str, float] = {}
    try:
        j = json.loads(urllib.request.urlopen(
            "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10
        ).read())
        out["btc_usdt"] = float(j["price"])
    except Exception:
        pass
    try:
        j = json.loads(urllib.request.urlopen(
            "https://api.binance.com/api/v3/ticker/price?symbol=TONUSDT", timeout=10
        ).read())
        out["ton_usdt"] = float(j["price"])
    except Exception:
        pass
    try:
        j = json.loads(urllib.request.urlopen(
            "https://api.binance.com/api/v3/ticker/price?symbol=WLDUSDT", timeout=10
        ).read())
        out["wld_usdt"] = float(j["price"])
    except Exception:
        pass
    try:
        j = json.loads(urllib.request.urlopen(
            "https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=10
        ).read())
        out["btc_usd"] = float(j["data"]["amount"])
    except Exception:
        pass
    try:
        j = json.loads(urllib.request.urlopen(
            "https://iss.moex.com/iss/engines/currency/markets/selt/securities/"
            "USD000UTSTOM.json?iss.only=marketdata&marketdata.columns=BOARDID,LAST",
            timeout=10,
        ).read())
        for board, last in j["marketdata"]["data"]:
            if board == "CETS" and last is not None:
                out["usd_rub"] = float(last)
                break
    except Exception:
        pass
    if "btc_usdt" in out and "usd_rub" in out:
        out["btc_rub"] = out["btc_usdt"] * out["usd_rub"]
    # merge with cached snapshot
    cached = ROOT / "prices.json"
    if cached.exists():
        prev = json.loads(cached.read_text())
        for k, v in prev.items():
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


# ---------- templates ----------

BASE_CSS = """
:root{--bg:#0b1220;--fg:#e8eef9;--muted:#8fa3c2;--accent:#3ecf8e;--card:#141c32}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
.wrap{max-width:820px;margin:0 auto;padding:32px 20px 80px}
header{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;flex-wrap:wrap;gap:12px}
header a{color:var(--muted);text-decoration:none;font-size:14px}
header a:hover{color:var(--fg)}
h1{font-size:26px;line-height:1.25;margin:0 0 12px}
h2{font-size:20px;margin:28px 0 12px}
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
code{background:#121b33;padding:2px 6px;border-radius:4px}
footer{margin-top:50px;padding-top:24px;border-top:1px solid #243356;color:var(--muted);font-size:13px}
footer a{color:var(--muted)}
"""

ALL_CHANNELS = [
    ("@btcusdtpriced", "BTC/USDT", "btc-usdt"),
    ("@btcusdprice", "BTC/USD", "btc-usd"),
    ("@btcrubprice", "BTC/RUB", "btc-rub"),
    ("@tonusdprice", "TON/USDT", "ton-usdt"),
    ("@wldusdprice", "WLD/USDT", "wld-usdt"),
    ("@usdrubprice", "USD/RUB", "usd-rub"),
]


def cross_grid(current_slug: str) -> str:
    items = []
    for ch, lbl, slug in ALL_CHANNELS:
        if slug == current_slug:
            continue
        items.append(
            f'<a href="/crypto-prices-live/{slug}/"><strong>{lbl}</strong>'
            f'<span>Live price · {ch}</span></a>'
        )
    return "<div class=\"grid\">" + "\n".join(items) + "</div>"


def page_html(pair: Pair, kw_slug: str, kw: str, price: float | None) -> str:
    price_str = fmt_price(price) if price is not None else "—"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    tg_url = f"https://t.me/{pair.channel.lstrip('@')}"
    canonical = f"{DOMAIN}/{pair.slug}/{kw_slug}/"
    json_ld = {
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
    title = f"{kw} — {pair.label} каждую минуту | {pair.channel}"
    # Strip leading @ for meta and keep title under ~60 chars friendly for SERP.
    description = (
        f"{kw}. Live {pair.label} exchange rate, updated every minute from "
        f"{pair.source}. Subscribe to {pair.channel} to get the current "
        f"{pair.base}/{pair.quote} price in your Telegram. Курс {pair.base}/{pair.quote} онлайн."
    )
    context_block = pair_context(pair)
    faq_block = faq_schema(pair, kw)
    cross = cross_grid(pair.slug)
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
<meta name="description" content="{description}"/>
<meta name="keywords" content="{kw}, {pair.label}, {pair.base} {pair.quote}, live price, telegram, {pair.channel}"/>
<link rel="canonical" href="{canonical}"/>
<meta property="og:title" content="{title}"/>
<meta property="og:description" content="{description}"/>
<meta property="og:url" content="{canonical}"/>
<meta property="og:type" content="website"/>
<meta property="og:image" content="{DOMAIN}/og.png"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="theme-color" content="#0b1220"/>
<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(faq_block, ensure_ascii=False)}</script>
<style>{BASE_CSS}</style>
</head>
<body>
<div class="wrap">
  <header>
    <a href="/crypto-prices-live/">← Home</a>
    <a href="{tg_url}">Subscribe in Telegram →</a>
  </header>

  <h1>{kw}</h1>
  <p>Live {pair.label} price — агрегированный курс из источника {pair.source}, обновляется раз в минуту. Ниже актуальное значение. Для получения цены в реальном времени прямо в Telegram подпишитесь на {pair.channel}.</p>

  <div class="price-card">
    <div class="meta">{pair.label} · Source: {pair.source}</div>
    <div class="price">{price_str} <small>{pair.quote}</small></div>
    <div class="meta">Snapshot at {ts} · refreshed hourly by GitHub Actions</div>
    <a class="cta" href="{tg_url}">Смотреть курс каждую минуту → {pair.channel}</a>
  </div>

  {context_block}

  <h2>Курсы в других парах</h2>
  {cross}

  <h2>Часто задаваемые вопросы</h2>
  <h3>Как часто обновляется цена?</h3>
  <p>В канале {pair.channel} — каждую минуту. На этой странице — раз в час (GitHub Actions cron). Если нужен поток в реальном времени — Telegram-канал.</p>
  <h3>Откуда берётся цена?</h3>
  <p>Источник: {pair.source}. Это {pair_source_descr(pair)}.</p>
  <h3>Это бесплатно?</h3>
  <p>Да, подписка на Telegram-канал и доступ к странице полностью бесплатны.</p>
  <h3>Есть ли уведомления?</h3>
  <p>Посты в канале идут в беззвучном режиме — подписчики не получают push-уведомления от каждого минутного поста. Открываете канал — видите свежую цену.</p>

  <footer>
    © {datetime.now(timezone.utc).year} Crypto Prices Live · data from {pair.source} · <a href="https://github.com/planetapokera/crypto-prices-live">source on GitHub</a>
  </footer>
</div>
</body>
</html>
"""


def pair_context(pair: Pair) -> str:
    texts = {
        "BTC/USDT": (
            "<h2>Что такое пара BTC/USDT</h2>"
            "<p>BTC/USDT — самая ликвидная пара на крипторынке. Торгуется на всех "
            "крупных спотовых площадках (Binance, Bybit, OKX, Bitget). USDT (Tether) — "
            "стейблкоин, привязанный к доллару США. Курс BTC/USDT де-факто отражает "
            "стоимость биткоина в долларовом эквиваленте с небольшим дисконтом/премией "
            "к спот-BTC/USD относительно депега USDT.</p>"
            "<p>Наш канал агрегирует цену со спот-рынка Binance — самой ликвидной "
            "биржи по объёму. Обновление раз в минуту, 24/7, без выходных.</p>"
        ),
        "BTC/USD": (
            "<h2>BTC/USD: биткоин к доллару</h2>"
            "<p>BTC/USD — базовая пара для американского рынка. Источник цены — "
            "Coinbase, крупнейшая регулируемая криптобиржа США. В отличие от BTC/USDT, "
            "здесь котируется «настоящий» доллар, без влияния возможного депега "
            "стейблкоинов.</p>"
            "<p>Canal показывает спотовую цену Coinbase с минутной гранулярностью. "
            "Используется трейдерами, следящими за регулируемой ликвидностью США.</p>"
        ),
        "BTC/RUB": (
            "<h2>BTC/RUB: биткоин в рублях</h2>"
            "<p>Для российских пользователей курс BTC/RUB — самый релевантный. "
            "Мы рассчитываем его через кросс-курс: Binance BTC/USDT × MOEX USD/RUB "
            "(Московская биржа, инструмент USD000UTSTOM, board CETS).</p>"
            "<p>Альтернатива — смотреть на P2P-стаканы Bybit или обменники BestChange, "
            "но там спред выше из-за премии за наличный оборот. Биржевой кросс — "
            "лучшая точка отсчёта для объективной оценки.</p>"
        ),
        "TON/USDT": (
            "<h2>TON (Toncoin) — криптовалюта экосистемы The Open Network</h2>"
            "<p>TON — блокчейн, разработанный командой Telegram и переданный сообществу. "
            "Toncoin используется в TON Space кошельке Telegram, в Stars, в играх и "
            "dApps внутри мессенджера. Популярность TON тесно связана с ростом "
            "Telegram-экосистемы.</p>"
            "<p>Мы берём цену со спот-рынка Binance (пара TONUSDT) — "
            "основного рынка для TON по объёму.</p>"
        ),
        "WLD/USDT": (
            "<h2>WLD (Worldcoin) — токен проекта World ID</h2>"
            "<p>Worldcoin — проект Сэма Альтмана (сооснователь OpenAI), выпускающий "
            "токен WLD людям, прошедшим биометрическую верификацию через устройство "
            "Orb. Цель — подтверждение уникальности человека в мире AI-ботов.</p>"
            "<p>Цена WLD/USDT собирается со спот-рынка Binance — основной ликвидной "
            "биржи по Worldcoin.</p>"
        ),
        "USD/RUB": (
            "<h2>USD/RUB на Московской бирже</h2>"
            "<p>Инструмент USD000UTSTOM — это котировка доллара США с расчётами "
            "«завтра» (TOM) на валютной секции MOEX. Торги идут в будние дни с "
            "10:00 до 23:50 МСК. В выходные и ночью курс «замораживается» на "
            "последней цене закрытия.</p>"
            "<p>Это биржевой курс — основа для ЦБ-курса (который вычисляется "
            "как среднее взвешенное), банковских курсов (с маржой 1-3%) и "
            "обменников (с ещё большей маржой).</p>"
        ),
    }
    return texts.get(pair.label, "")


def pair_source_descr(pair: Pair) -> str:
    return {
        "Binance spot": "крупнейшая криптобиржа в мире по спотовому объёму",
        "Coinbase": "регулируемая биржа США, листинг на NASDAQ (COIN)",
        "MOEX USD000UTSTOM": "главная валютная биржа России, board CETS",
        "Binance BTCUSDT × MOEX USD/RUB": (
            "кросс-курс Binance spot BTC/USDT, умноженный на биржевой курс доллара с MOEX"
        ),
    }.get(pair.source, pair.source)


def faq_schema(pair: Pair, kw: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"Как часто обновляется {pair.label}?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"В Telegram-канале {pair.channel} курс {pair.label} обновляется раз в минуту, 24/7.",
                },
            },
            {
                "@type": "Question",
                "name": f"Откуда берётся курс {pair.label}?",
                "acceptedAnswer": {"@type": "Answer", "text": f"Источник: {pair.source}."},
            },
            {
                "@type": "Question",
                "name": "Это бесплатно?",
                "acceptedAnswer": {"@type": "Answer", "text": "Да, подписка и доступ бесплатны."},
            },
        ],
    }


# ---------- homepage ----------

def home_html(prices: dict[str, float]) -> str:
    cards = []
    for p in PAIRS:
        price = prices.get(p.price_fn)
        price_str = fmt_price(price) if price is not None else "—"
        cards.append(
            f'<a href="/crypto-prices-live/{p.slug}/"><strong>{p.label}</strong>'
            f'<span>{price_str} {p.quote} · {p.channel}</span></a>'
        )
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Crypto Prices Live — биткоин, эфир, TON, доллар, рубль каждую минуту</title>
<meta name="description" content="Сеть из 6 Telegram-каналов с минутным обновлением цен. BTC/USDT, BTC/USD, BTC/RUB, TON/USDT, WLD/USDT, USD/RUB. Источники: Binance, Coinbase, MOEX."/>
<link rel="canonical" href="{DOMAIN}/"/>
<style>{BASE_CSS}</style>
</head>
<body>
<div class="wrap">
  <header>
    <strong>Crypto Prices Live</strong>
    <a href="https://github.com/planetapokera/crypto-prices-live">GitHub</a>
  </header>
  <h1>Курсы крипты и валют каждую минуту прямо в Telegram</h1>
  <p>Сеть из 6 независимых каналов. Каждый публикует свежий курс своей пары раз в минуту. Источники: Binance spot, Coinbase, Московская биржа. Snapshot обновлён: {ts}.</p>
  <div class="grid">
    {''.join(cards)}
  </div>
  <h2>Как это работает</h2>
  <ul>
    <li>Каждый канал — один бот-тикер, работающий на отдельном сервере.</li>
    <li>Цена тянется напрямую с биржевого API (Binance, Coinbase, MOEX).</li>
    <li>Публикация — каждые 60 секунд, в беззвучном режиме (без push-уведомлений).</li>
    <li>Посты можно листать как историю цены.</li>
  </ul>
  <footer>
    Open source on <a href="https://github.com/planetapokera/crypto-prices-live">GitHub</a>. Цены не являются финансовой рекомендацией.
  </footer>
</div>
</body>
</html>
"""


# ---------- sitemap ----------

def sitemap(pages: list[str]) -> str:
    body = []
    lastmod = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for p in pages:
        body.append(
            f"<url><loc>{DOMAIN}/{p}</loc><lastmod>{lastmod}</lastmod>"
            f"<changefreq>hourly</changefreq><priority>0.8</priority></url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(body)
        + "\n</urlset>\n"
    )


# ---------- build ----------

def main() -> None:
    prices = fetch_prices()
    (ROOT / "prices.json").write_text(json.dumps(prices, indent=2))
    pages_for_sitemap: list[str] = [""]

    (SITE / "index.html").write_text(home_html(prices), encoding="utf-8")

    for pair in PAIRS:
        pair_dir = SITE / pair.slug
        pair_dir.mkdir(exist_ok=True)
        # pair home redirects to first keyword page
        price = prices.get(pair.price_fn)
        # pair-level index uses first keyword
        first_kw_slug, first_kw = pair.keywords[0]
        (pair_dir / "index.html").write_text(
            page_html(pair, first_kw_slug, f"{pair.label} live price", price),
            encoding="utf-8",
        )
        pages_for_sitemap.append(f"{pair.slug}/")
        for kw_slug, kw in pair.keywords:
            kw_dir = pair_dir / kw_slug
            kw_dir.mkdir(exist_ok=True)
            (kw_dir / "index.html").write_text(
                page_html(pair, kw_slug, kw, price), encoding="utf-8"
            )
            pages_for_sitemap.append(f"{pair.slug}/{kw_slug}/")

    (SITE / "sitemap.xml").write_text(sitemap(pages_for_sitemap), encoding="utf-8")
    (SITE / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n",
        encoding="utf-8",
    )
    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    # IndexNow key file
    key = "c9f1a8b7d6e5c4b3a2918273645f0e9d"
    (SITE / f"{key}.txt").write_text(key, encoding="utf-8")

    print(f"Built {len(pages_for_sitemap)} pages. site/ total:")
    for root, _dirs, files in os.walk(SITE):
        for f in files:
            print(" ", Path(root).relative_to(SITE) / f)


if __name__ == "__main__":
    main()

# crypto-prices-live

Многоязычный статический сайт + IndexNow-пуш — SEO-актив для сети из 6 Telegram-каналов с минутным обновлением курсов (BTC/USDT, BTC/USD, BTC/RUB, TON/USDT, WLD/USDT, USD/RUB).

## Live

- Сетка страниц: **https://planetapokera.github.io/crypto-prices-live/**
- Корневой landing (для верификаций): **https://planetapokera.github.io/** (отдельный репо `planetapokera/planetapokera.github.io`)
- GitHub: **https://github.com/planetapokera/crypto-prices-live**

## Что внутри

- **604 страницы** — 9 языков × (1 главная + 6 pair-индексов + 60 keyword-страниц) + корень.
- **9 языков** (переводы руками): ru, en, es, tr, pt, id, hi, ar, zh.
  - Arabic — RTL (`dir="rtl"`).
  - Каждая языковая группа связана через `<link rel="alternate" hreflang="...">`, плюс `x-default` → `ru`.
  - Переключатель языков в `<header>` каждой страницы. Так как keyword-слаги разные между языками (русские slug'и кириллица в транслите, арабские — `sir-ton-usdt-mubashir` и т.п.), переключение с keyword-страницы на другой язык ведёт на pair-index этого языка (`/<lg>/<pair>/`), а не на несуществующий slug.
- **SEO-обвес на каждой странице**:
  - `<title>`, уникальный `meta description` (включает конкретный ключ), canonical, OpenGraph, Twitter card.
  - JSON-LD `ExchangeRateSpecification` + `FAQPage` + `BreadcrumbList`.
  - Блок «Related searches / Похожие запросы» — внутренние ссылки на 9 остальных keyword-страниц той же пары в том же языке (усиление internal linking).
  - `yandex-verification` + `google-site-verification` (на всех страницах, включая корневой редирект).
- **Custom 404** с JS-fallback: если пользователь попал на несуществующий slug (например перевёл английский slug на AR-путь), редиректит на ближайший валидный URL `/<lang>/<pair>/`.
- **Интерактивный конвертер валют** — JS-виджет на каждой keyword-странице и pair-индексе. Двунаправленное преобразование, кнопка swap. Курс берётся из snapshot страницы.
- **Контент**: 2 абзаца про пару + FAQ (4 вопроса) + сетка кросс-линков на остальные 5 каналов + live-цена из snapshot.
- **sitemap.xml** + **robots.txt** + IndexNow key-файл (`c9f1a8b7d6e5c4b3a2918273645f0e9d.txt`).

## Каналы и источники цен

| Пара      | Канал              | Источник                                         |
|-----------|--------------------|--------------------------------------------------|
| BTC/USDT  | [@btcusdtpriced](https://t.me/btcusdtpriced) | Binance spot `BTCUSDT` |
| BTC/USD   | [@btcusdprice](https://t.me/btcusdprice)     | Coinbase `BTC-USD` |
| BTC/RUB   | [@btcrubprice](https://t.me/btcrubprice)     | Binance `BTCUSDT` × MOEX `USD000UTSTOM` |
| TON/USDT  | [@tonusdprice](https://t.me/tonusdprice)     | Binance spot `TONUSDT` |
| WLD/USDT  | [@wldusdprice](https://t.me/wldusdprice)     | Binance spot `WLDUSDT` |
| USD/RUB   | [@usdrubprice](https://t.me/usdrubprice)     | MOEX `USD000UTSTOM` (CETS TOM) |

## Структура проекта

```
crypto-prices-live/
├── generate.py                          # генератор статики
├── i18n.py                              # UI-строки, ключевые слова, контекст-блоки (9 языков)
├── prices.json                          # snapshot цен (обновляется GitHub Actions)
├── .github/workflows/build.yml          # cron-pipeline (каждый час)
├── .gitignore
├── README.md
└── site/                                # сгенерированные HTML-страницы (публикуются через Pages)
    ├── index.html                       # корневой редирект на язык браузера
    ├── <lang>/index.html                # homepage каждого языка
    ├── <lang>/<pair>/index.html         # pair-индекс
    ├── <lang>/<pair>/<keyword>/         # 10 keyword-страниц на пару
    ├── sitemap.xml
    ├── robots.txt
    └── c9f1a8b7d6e5c4b3a2918273645f0e9d.txt   # IndexNow key
```

## CI (GitHub Actions)

Каждый час (на 17-й минуте) + на каждый push + по manual dispatch:

1. Тянет свежие цены (Binance, Coinbase, MOEX).
2. `python3 generate.py` — пересобирает все 604 страницы.
3. Коммитит `prices.json` + `site/` обратно в main.
4. Публикует `site/` на GitHub Pages.
5. Пингует **IndexNow** → Bing, Yandex, Seznam, Naver (Yep режет Cloudflare).

## Верификация в поисковиках

- **Яндекс.Вебмастер**: токен `e5ad8235e1498a27`. Добавлен в `<head>` всех страниц. Подтверждён на корне `planetapokera.github.io`, sitemap скормлен.
- **Google Search Console**: токен `OI8q2vN1dp3ChHueOuCCzlqUxtmBmFcApUMo30wDKno`. Подтверждён, sitemap скормлен.
- **IndexNow**: общий ключ `c9f1a8b7d6e5c4b3a2918273645f0e9d`. Bing/Yandex/Seznam/Naver — все приняли.

## Локальная разработка

```bash
cd ~/cl/crypto-prices-live
python3 generate.py                 # генерит site/
python3 -m http.server --directory site 8000
open http://localhost:8000/
```

Статическая сборка — ни зависимостей, ни venv. Всё в stdlib + urllib.

## Добавить новый язык

1. В `i18n.py` — добавить язык в `LANGS` и `LANG_META`.
2. Заполнить UI-строки (`UI[lang]`).
3. Заполнить 6 блоков `CONTEXT[lang]` (по одному на пару).
4. Заполнить ключевые слова `KEYWORDS[lang]` — 10 на каждую из 6 пар.
5. `python3 generate.py` — на N пар сгенерится ещё 60 страниц.
6. IndexNow запингует новые URL на следующий hourly run.

## Добавить новое ключевое слово

Просто дописать в `KEYWORDS[lang][pair.slug]` кортеж `(url_slug, human_kw)`. При пересборке страница появится, попадёт в sitemap, IndexNow запингует.

## Обновить верификационные токены

Поменять значения в `generate.py` (constants `VERIFY_META`), пересобрать, запушить.

## Связанные проекты

- **~/cl/price-bots/** — боты-тикеры, публикуют цены в эти 6 Telegram-каналов каждую минуту. Задеплоены на GCP (polymarket-bot VM, 35.228.105.182, `/root/price-bots/`, systemd `price-bots.service`).
- **planetapokera/planetapokera.github.io** — user-level landing с теми же verification-тегами (чтобы Yandex/Google могли проверить права на корень домена).

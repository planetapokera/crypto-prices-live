# crypto-prices-live

SEO landings + live price snapshot for a network of 6 Telegram price-ticker channels.

## Live site

https://planetapokera.github.io/crypto-prices-live/

## Channels

| Пара | Канал | Источник |
|------|-------|----------|
| BTC/USDT | [@btcusdtpriced](https://t.me/btcusdtpriced) | Binance spot |
| BTC/USD | [@btcusdprice](https://t.me/btcusdprice) | Coinbase |
| BTC/RUB | [@btcrubprice](https://t.me/btcrubprice) | Binance × MOEX |
| TON/USDT | [@tonusdprice](https://t.me/tonusdprice) | Binance spot |
| WLD/USDT | [@wldusdprice](https://t.me/wldusdprice) | Binance spot |
| USD/RUB | [@usdrubprice](https://t.me/usdrubprice) | MOEX USD000UTSTOM |

Каждый канал публикует свою пару раз в минуту, беззвучными постами.

## Build

```bash
python3 generate.py
```

Создаёт `site/` с 1 главной + 6 pair-индексами + 60 keyword-страницами + sitemap.xml + robots.txt + IndexNow key-file.

## CI

`.github/workflows/build.yml` пересобирает сайт каждый час, коммитит свежий `prices.json`, деплоит на GitHub Pages и пингует IndexNow (Bing, Yandex, Seznam, Naver, Yep).

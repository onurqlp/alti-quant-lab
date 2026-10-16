# ALTI — Resmî veri kaynakları / uygulama ve erişim matrisi

**Durum tarihi:** 17 Ekim 2026. **Kanıt standardı:** Dokümantasyon erişimi, ağ API çalışması ve kullanıcı hesabında ticaret erişimi birbirinden farklıdır. Bu çalışma ortamında canlı REST çağrıları **DNS erişim hatası** verdi. Dolayısıyla aşağıdaki API'lerin bu kullanıcının hesabında, konumunda veya GitHub Actions runner'ında çalıştığı **teyit edilmedi**. Hiçbir canlı fiyat ya da kazanç uydurulmadı.

| Model | Kaynak ve resmî bağlantı | MVP adaptörü | Giriş/çıkış uygunluğu | Kritik engel |
|---|---|---|---|---|
| B1 Funding | [Binance USDⓈ-M funding history](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History), [funding info](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Info), [mark price](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Mark-Price) | `READ_ONLY_ADAPTER_BUILT`; ilk ağ taraması bekliyor | `ACCESS_UNVERIFIED` | Bölge/hesap erişimi, maker/taker, marjin, hedge ve gerçek funding seyri |
| B1 Funding | [OKX API v5](https://www.okx.com/docs-v5/en/) public funding-rate, funding-rate-history, instruments | `READ_ONLY_ADAPTER_BUILT`; ilk ağ taraması bekliyor | `ACCESS_UNVERIFIED` | Settlement saatleri, tahmini oran timestamp'i, kontrat birimi ve fonlama değişimi |
| B2 Stablecoin | [Binance spot depth](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints), [OKX book](https://www.okx.com/docs-v5/en/) | `SCREEN_ONLY_ADAPTER_BUILT` | `NOT_EXECUTABLE` | Binance depth exchange timestamp içermez; token/chain, itfa, komisyon, transfer, iki taraflı erişim teyitsiz |
| A1 Hisse pairs | [Borsa İstanbul](https://www.borsaistanbul.com/), [SPK](https://spk.gov.tr/) ve gerektiğinde lisanslı data feed | `NOT_CONNECTED` | `ACCESS_UNVERIFIED` | Adjusted close, corporate actions, borçlanabilir hisse, kısa satış, veri lisansı |
| A2 ETF–ETF | [SEC yatırımcı ETF bilgilendirmesi](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-24), ihraççı resmi NAV dokümanları | `NOT_CONNECTED` | `ACCESS_UNVERIFIED` | Dayanak endeks, dividend, fee, FX, NAV yayın gecikmesi, AP mekanizması vs. market trade |
| A3 Cointegration sepet | Lisanslı hisse/ETF verisi + [statsmodels](https://www.statsmodels.org/stable/tsa.html) | Orijinal **synthetic** research core yalnız `legacy/` içinde | `SCREEN_ONLY` / gerçek feed yok | Johansen rank, FDR, walk-forward, validation, OOS, çoklu borrow, likidite |
| T0 Tahvil–repo | [BIST repo ters repo pazarı](https://www.borsaistanbul.com/piyasalar/borclanma-araclari-piyasasi/piyasa-isleyisi/repo-ters-repo-pazari), [menkul kıymet tercihli repo](https://www.borsaistanbul.com/piyasalar/borclanma-araclari-piyasasi/piyasa-isleyisi/menkul-kiymet-tercihli-repo-pazari) | Kavramsal ekran | `ACCESS_UNVERIFIED` | ISIN, dirty price, coupon, YTM, duration/convexity, gerçek haircut, dealer erişimi |

## Teknik veri doğrulama

- Funding `rate` alanları `%` değil, olay başına imzalı **kesir** olarak saklanır (`0.0001` = `%0.01`). API tipinde bozulma/uygunsuz birim için mutlak oran üst eşiği uygulanır; bu tek başına bütün yanlış birim senaryolarını yakalayamaz.
- Binance geçmiş funding event'leri ile güncel `fundingInfo` (varsa) uyumlu değilse karşılaştırma durur. OKX gerçekleşmiş geçmiş ile gelecek event zaman aralığı uyuşmazsa durur. Settlement geçmişindeki interval değişimi `INTERVAL_CHANGED` verir.
- `last_realized_rate_fraction` yalnız tarihsel gerçekleşmiş olay; `indicative_rate_fraction` güncel gösterge. Günlük normalize oran **geçmiş tek olayın koşullu hızı**; vadeli kazanç/tahmin değildir. Borsalar arası settlement zamanı farklıysa bağımsız akışlar üzerinden risksiz fırsat çıkarılmaz.
- Borsaların futures sözleşme birimi ve teminat asset'i kontrol edilir. Bir venue için sembol/quote/margin uyuşmazlığı durumunda veri reddedilir.
- Binance futures `premiumIndex.time` en fazla 120 saniye eski olmalı. OKX tarihsel event saatleri doğrulanır; current funding endpoint doğrudan exchange as-of vermiyorsa bu veriye executable fiyat muamelesi yapılmaz.
- B2 alım yönü ask, satış yönü bid; karşılık gelen 20 kademe derinlik üzerinden 1.000 USDC VWAP hesaplanır. Her iki yön raporlanır. **Net bps ve PnL boş**: teyitli fee, source time ve transfer olmadan sıfır ücret varsayımı yapılmaz.
- TRY/USD/USDT çevrimleri timestamp'li FX ve spread olmadan yapılmaz. B1/B2 aynı kripto teminat riskinde çakışabilir; iki ayrı gelir hanesi oluşturulmaz.
- Piyasaların bölgesel/hesapsal uygunluğu public data indirmekten anlaşılamaz. HTTP 451 `ACCESS_BLOCKED`, 401/403 `ACCESS_UNVERIFIED`, 429 `RATE_LIMITED` olarak raporlanır; diğer zamanlarda `NETWORK_ERROR`. Bu kodlar kullanıcıya işlem yetkisi var demek değildir.

## Piyasa saatleri / maliyetler / izinler

Kripto spot-perp dataları genel olarak 24/7 izlenebilir; ancak funding settlement olayları aralıklı ve değişkendir. Hisse/ETF resmi seansları veri sağlayıcısı ve borsaya göre doğrulanmadıkça `NOT_CONNECTED`, BIST tahvil/repo resmi seans ve dealer erişimi olmadıkça `ACCESS_UNVERIFIED` görünür.

Maker, taker, pozisyon kapama, borrow, FX, liquidation buffer, funding reversal, haircut ve roll maliyeti **onaylı gerçek tarifeler olmadan sayısallaştırılmaz**. Fırsat `NET` alanı boş kalır. Public API kullanım şartları ve yeniden yayınlama lisansı ayrıca doğrulanmalıdır; bir API'nin okunabilir olması public bir sitede tekrar yayınlama izni verildiği anlamına gelmez.

## Aşama geçişleri

1. **Faz 0:** Kaynak şemaları, orijinal sentetik demo ayrımı, 4 smoke ve risk kapıları — hazır.
2. **Faz 1:** Binance/OKX geçmiş funding + metadata + UTC normalizasyonu + mobil site + 30 dakikalık Actions akışı — kodlandı; gerçek bulut API çağrısı/yayın ayrıca doğrulanmalı.
3. **Faz 2:** USDC/USDT iki borsa bid/ask/L2 + timestamp/fee/route engelleri — yalnız ekranlama kodlandı, forward sonuç ve fill yok.
4. **Faz 3:** Pairs/ETF lisanslı veri + formation/validation/OOS + ortak maruziyet — **yapılmadı**.
5. **Faz 4:** Johansen basket ve broker/dealer doğrulanmış tahvil–repo — **yapılmadı**.
6. **Faz 5:** Risk onaylı gerçek forward paper ve kanıtlı fill/simülasyon, 7/14/30 gün net ölçüm — **yapılmadı**. Gerçek işlem API'si bu pakette **hiç yok**.

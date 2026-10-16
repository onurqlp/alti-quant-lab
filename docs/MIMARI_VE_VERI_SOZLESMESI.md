# ALTI — Teknik Mimari ve Verinin Doğruluk Sözleşmesi

## Genel sınır

**Sadece seçilen altı strateji.** Yalnız iki kişi kullanacak olsa bile veri doğruluğu, zaman damgası ve finansal hata önleyici kurallar vazgeçilmezdir. Arayüz basit olabilir; analitik ve kayıt güvenilirliği basitleştirilmez.

## Katmanlar

```
                   READ-ONLY VERİ BAĞLAYICILARI
   Kripto CEX fiyat + funding     Hisse/ETF     Tahvil + repo
                  ↓ validate / normalize
           KAYNAK SÖZLEŞMELERİ ve ZAMAN SENKRONİ
                     ↓       ↓       ↓
           MOTOR A   MOTOR B   MOTOR C
           Pairs,    Funding  Tahvil/repo
           ETF,      Stable
           basket
                     ↓
       STRATEJİ-SINIFINA GÖRE UNIVERSE / VARLIK ETİKETİ
                     ↓
      TEKRAR SAYMA ENGELİ, GENEL RİSK, ERİŞİM, MALİYET
                     ↓
        GÖZLEM LEDGER / İLERİ SHADOW SIMULATOR
                     ↓
       JSON API + PROFESYONEL KARAR PANELİ / RAPOR
```

## Zorunlu kayıt şeması

Tüm veriler kendi veri kaynağını ve hangi saat için geçerli olduğunu taşır. `observed_at` ile `received_at` ayrı alanlardır; tarama zamanı verinin gerçekleştiği zaman yerine geçemez.

```json
{
  "record_type": "market_quote",
  "schema_version": "1.0",
  "source": "NOT_CONNECTED",
  "provider": "NOT_CONNECTED",
  "instrument_id": "PLACEHOLDER",
  "asset_class": "crypto|equity|etf|fixed_income",
  "currency": "TRY|USD|USDT",
  "units": "fraction|percent|bps|price|quantity|annualized_rate",
  "event_at_utc": null,
  "received_at_utc": null,
  "source_delay_ms": null,
  "is_final": false,
  "license_status": "UNVERIFIED",
  "scan_id": null,
  "bid": null,
  "ask": null,
  "bid_size": null,
  "ask_size": null,
  "quality_status": "NO_SOURCE"
}
```

### Funding veri örneği

```json
{
  "record_type": "funding_rate",
  "instrument_id": "BTC-USDT-SWAP",
  "venue": "EXAMPLE_ONLY",
  "rate_fraction_per_event": 0.0001,
  "funding_interval_hours": 8,
  "realized_or_estimated": "ESTIMATED",
  "funding_time_utc": null,
  "next_funding_time_utc": null,
  "settlement_method": "UNVERIFIED",
  "settlement_currency": "USDT",
  "source": "SYNTHETIC_DEMO"
}
```

**Oran birimi zorunludur:** `0.0001` bir kesir olarak 0,01% demek; JSON'da `0.01` ayrı bir yüzdelik kullanım değildir. Fonlama aralığı iki *gerçek timestamp* ve sağlayıcı kurallarıyla doğrulanır. Yan yana iki rate, farklı settlement pencerelerinde olabilir. `realized` ve `predicted` ayrı serilerdir.

### İstatistiksel aday/sinyal

```json
{
  "signal_id": "uuid",
  "strategy": "equity_pairs_trading",
  "engine": "A",
  "universe_version": "YYYY-MM-DD",
  "formed_at_utc": null,
  "formation_end_utc": null,
  "signal_at_utc": null,
  "feature_asof_utc": null,
  "side": "LONG_SPREAD|SHORT_SPREAD|WATCH",
  "status": "RESEARCH",
  "symbols": ["AAA", "BBB"],
  "hedge_coefficients": [],
  "formation_p": null,
  "adjusted_p": null,
  "oos_z": null,
  "quote_freshness_ms": null,
  "short_available": false,
  "market_access_verified": false,
  "estimated_all_in_cost_bps": null,
  "paper_order_allowed": false,
  "real_order_allowed": false,
  "source_ids": [],
  "risk_reasons": []
}
```

### Portföy / muhasebe

- İlk referans 150.000 TRY, ancak `capital_not_deposited=true` olarak oluştur. Para yatırılmış gibi gösterme.
- `cash_balance_try`, `cash_balance_usd`, `cash_balance_usdt`, ayrı; rapor için `fx_mark_source/asof/bid/ask` olmadan birleştirilmez.
- `paper_starting_balance` açıkça DEMO. İşlem `SIGNAL` → `PAPER_PENDING` → `PAPER_FILLED` veya `PAPER_NO_FILL` → `PAPER_CLOSED` akışından geçer.
- Her emir için tüm bacakların quote zamanı, fill/slippage ve ücretleri ayrı. Örnek veride `SYNTHETIC_FILL` ise raporda **sentetik** kalır.
- PnL: realized, unrealized, funding accrual, carry, fees, borrow, FX conversion, tax estimate ve total ayrı alanlar; gözlemsel spread net PnL değildir.
- Duplicate strategy orders: same asset + overlap in effective factor portfolio can be netted only in research exposure analysis, not accidentally opened 3 times.

## Veri kalite kapıları

1. Kaynak gerçekten erişilebilir mi? Kaldırılmış endpoint varsa `SOURCE_UNAVAILABLE`.
2. Ekran/dış API saatleri UTC normalleştirildi mi? Piyasa kapanış takvimi var mı?
3. Bid/ask ters, stale, crossed, sıfır hacimli, enstrüman eşdeğer olmayan veya iş günü kapanışı yok mu?
4. Split, dividend, fon birim pay fiyatı, sepet bileşimi, kur/miktar çarpanı ve kontrat büyüklüğü doğru mu?
5. Funding intervals tarihsel değişimlerde doğru mu? Signed pay/receive açısından açık mı?
6. L2 derinlik yoksa best quote, yüzlerce birim için fill garantilemez.
7. Repo: valör, fiyat, kupon, dirty/clean, duration, convexity, teminat/haircut, katkı maliyeti ve fonlama yenileme riski var mı?
8. Short: işlem tarihi için emir/yetki/borrow kontrolü var mı? Yoksa `ACCESS_BLOCKED`.
9. Her sinyal `model_version`, `source_ids`, `event_time`, `invalidation_reason` tutuyor mu?

## İstatistik araştırma motoru

- Seçilen evren ve aday çiftler FORMATION aşamasında; gelecekteki fiyatlar yalnız ileri testte değerlendirilir.
- Çift seçimi p-değerini manipüle etmez: multiple comparisons → FDR veya ayrılmış discovery/validation/test, gerekliyse çapraz doğrulama.
- Log-price hedge ratio fiyat seviyeleri ve kontrat/para birimi ile uyumlu pozisyon değerine dönüştürülür; saf beta doğrudan emir sayısı değildir.
- Train/test/test-forward verileri ayrılır. Regime değişimini ve split/dividend/corporate action'ları kontrol et.
- Çok varlıklı cointegration: yanlış basit OLS ADF = tam Johansen testi değil. Rank, deterministik terimler ve model seçimleri doğrulanır.
- Z-score giriş/çıkış seviyeleri **parametre araştırmasıdır**, tek bir sabit üzerinden kesin kâr sözü yok.
- Negatif ilişkili iki hisse bile aynı endeks/faktör maruziyetine sahip olabilir. Pozisyon riskini ortak hesapla.

## Funding ve stablecoin

- Cross-venue funding farkı hesaplanırken aynı nominal, aynı sözleşme birimi, gerçek ödeme timestamp'leri, mark/index farkı ve iki yönde quote olmadan ``REAL_EXECUTABLE`` olmaz.
- Funding, yalnız oran farkı diye otomatik kazanılmaz. Delta-neutral hedge spot/forward/funding ile account borrow/collateral sağlanmalı.
- Stablecoin fiyatı dolar karşılığı sabit ve garanti nakit değildir. İtfa yetkisi, zincir, stablecoin sözleşme adresi, merkezi borsa çekimi, kaynak para, dondurma riski ve alarm göz önünde olmalı.
- Market spread pozitif ama issuer riskinde yükseliyorsa sinyalde ayrı `DEPEG_RISK` kırmızı uyarısı; `HEDGE_MARGIN_UNSAFE` ile funding girişini iptal.

## Tahvil-repo

- Tahvil fiyatına (clean/dirty), kupon takvimine, duration/convexity'ye ve repo süresine sahip olmadan iki annualized oran kıyasından para kazanma kararı çıkmaz.
- Repo sözleşmesi, teminat uygunluğu, işlem büyüklüğü ve kurum yetkisi kontrolü olmadan `ACCESS_UNVERIFIED`.
- Bir borçlanma aracında borç faizi düşük olsa da faiz şoku ve margin call potansiyeli çok daha yüksek olabilir.

## Çalışma rejimi ve teknik dağıtım

- İlk demo: yalnız statik, dış API yok, yapay veri.
- Gerçek veri MVP: Python process + SQLite WAL (tek yazıcı) veya Postgres, veri çekme modülü read-only, kaynak retry ve rate-limit, idempotent scan, immutable olay logu.
- Schedule GitHub Actions kullanılırsa beş dakikalık cron kesin süre garantisi sayılmaz; missed run ve last real timestamp ayrı gösterilmeli. Uzun yaşayan gerçek zamanlı akış için yönetilen hizmet/worker gerekebilir.
- Statik dashboard kullanıcı için basit olacak; ancak hassas veri ve API anahtarları hiçbir zaman GitHub Pages, local JavaScript veya repo içine koyulmayacak.
- Dosyalar atomik/transactional yazılır, her raporda `scan_id` ve `last_success_at` bulunur; önceden kaydedilmiş sinyal yeni veriyle doğrulanmadan geçerliymiş gibi gösterilmez.

## En az ama doğru test

Başlangıçta yalnız bir smoke: altı stratejinin kayıtları, yanlış birim/funding dönemi, maliyet sonrası negatif spread, canlı emir kapalı. Daha sonra finansal matematik için kritik sözleşme testleri, yeni eklenen modülün path-temelli CI testi, veri bütünlüğü. Kullanıcı minumum test istiyor ama risk kapıları atlanamaz.

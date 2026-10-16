# ALTI Quant Research Lab

**Durum: Yayına hazır kaynak kodlu salt-okunur araştırma MVP'si; canlı veri ve GitHub Pages yayını henüz bu ortamda doğrulanmadı.** `COIN.LIVE` veya başka repodan tek satır alınmamış veya değiştirilmemiştir. Proje benzersiz `alti-quant-lab` repo ismine tasarlanmıştır.

## Ne var?

- **Tam 6 modül / 3 motor:** `A1` pairs, `A2` ETF–ETF, `A3` basket; `B1` perp funding, `B2` stablecoin; `T0` tahvil–repo. Sekmeler, durum/ret gerekçeleri, maliyet doğrulama ve risk ekranları.
- **B1 resmî read-only kaynak adaptörü:** Binance USDⓈ-M ve OKX funding geçmişi, gerçekleşmiş vs gösterge oranı ayrımı, funding interval, aynı dayanak/USDT kontrat doğrulaması, UTC, veri yaşı, API hataları; iki venue karşılaştırması sadece `WATCH_ONLY`.
- **B2 aşama 2 salt-okunur orderbook ekranlaması:** Binance spot + OKX USDC/USDT 20 kademe, bid/ask, derinlik, iki yön için 1.000 USDC VWAP ve brüt spread. Binance depth veri zamanının yokluğu, transfer, fees, issuer/chain eksikliği nedeniyle `SCREEN_ONLY`; net getiri veya kağıt dolumu yok.
- **Tek sanal kasa:** 150.000 TL referans, %40 rezerv, hipotez başı %0,25 risk ve %20 brüt exposure üst sınırı; gerçek para, gerçek FX hesabı, açık paper pozisyonu, gerçek PnL **yok**.
- **Audit:** `data/audit.jsonl` append-only; `data/recent_observations.json` 14 günlük dönen gözlem görünümü; `site/report.json` atomik snapshot. Scan ID UTC-dakika bazlı idempotent; Actions concurrency ile tek job akışı.
- **Bulut açıkken otomasyon:** GitHub Actions cron `*/30 * * * *` + isteğe bağlı manuel çalıştırma. GitHub schedule gecikebilir veya kaçabilir; **30 dk kesin SLA değildir**. Aynı workflow GitHub Pages statik UI'yi yayınlar.
- **Güvenlik:** Python `urllib` ile **yalnız GET / resmî public market endpoint'leri**. `POST`, private broker/account endpoint, API key, emir, kaldıraç, cüzdan, depozito, fon aktarma, otomatik paper fill **yok**. Frontend borsayla iletişime geçmez.

## İlk yerel çalışma

Python 3.10+ gereklidir; **read-only canlı MVP için pip kurulumu gerekmez**.

```bash
python -m alti.worker
python -m http.server 8080 --directory site
```

`http://localhost:8080` adresini açın. Ağ erişimi yoksa rapor açık bir `NETWORK_ERROR` gösterir ve gerçek veri etiketlemez. `python -m unittest discover -s tests -v` komutuyla 4 kritik smoke testi çalışır.

> Bilgi: Bu çalışmanın üretildiği container dış DNS'e erişemedi; canlı borsa taraması gerçek ağda tekrar gözlemlenmeden `LIVE CONNECTED` yazılmaz.

## GitHub'a yepyeni repo / site olarak yayın

GitHub hesabı: `onurqlp`. Mevcut GitHub bağlantısının araç seti **yeni repo açma/Pages ayarlarını değiştirme** eylemini desteklemiyor. Bu nedenle canlı bir GitHub repo veya çalışan Pages URL'si varmış gibi sunulmuyor. Bu dosyalar ise doğrudan yeni repo için hazırlanmıştır:

1. GitHub'da [yeni depo aç](https://github.com/new?name=alti-quant-lab): isim **`alti-quant-lab`**, visibility **Public**, README / license / .gitignore otomatik ekleme **kapalı**. Halihazırdaki COIN.LIVE depolarına dokunma.
2. Bu ZIP'i aç. Terminal/PowerShell ile **bu README'nin bulunduğu klasörde** şu komutları çalıştır:

```bash
git init
git add .
git commit -m "feat: launch independent read-only ALTI research MVP"
git branch -M main
git remote add origin https://github.com/onurqlp/alti-quant-lab.git
git push -u origin main
```

3. Depodaki `Settings → Pages → Build and deployment → Source: GitHub Actions` seç. `Actions` sekmesinden `ALTI Read-Only Research & Pages` iş akışını `Run workflow` ile çalıştır. **Başarı tamamlanıp Pages dağıtımı doğrulanana kadar şu adres aktif sayılmaz:** `https://onurqlp.github.io/alti-quant-lab/`.
4. `site/report.json` alanlarında `last_successful_scan_utc`, `provider_health`, `funding_records`, `errors` kontrol et. İlk tarama otomatik çalıştı diye piyasa erişimi doğrulandı sayılmaz. Public data endpoint'i / ülke/account düzeni engellenmişse `ACCESS_BLOCKED`/`ACCESS_UNVERIFIED` kalır.

İş akışı bot commit'lerini `[skip ci]` ile işaretler; tek koşuda tarama ve deploy yapılır. Repo'nun Actions workflow write permission politikası veri commit izni vermiyorsa ayarlarda Actions erişimi/iş akışı izinleri incelenir. Cron GitHub altyapısındadır, kişisel bilgisayarınızın açık olması gerekmez.

**Önemli lisans notu:** Public endpoint'e erişim, canlı fiyatların kamuya açık sitede yeniden yayımlanmasına otomatik izin vermez; Binance ve OKX lisans/şartlarını yayınlamadan önce değerlendirin. Gerekirse private dashboard/erişim kontrollü sunucu kullanılmalı; GitHub Pages kendisi üye girişi sağlamaz. GitHub'da public depoya eklenecek hiçbir kullanıcı bakiyesi, parola, key veya özel ticari bilgi olmamalıdır.

## Aşama planı ve kabul kriterleri

| Aşama | Durum | Kanıtlı çıktı |
|---|---|---|
| 0 — Orijinal paket | **Kontrol edildi** | `legacy/lab/demo.py`: sentetik, 6 strateji, canlı veri yok, PnL yok |
| 1 — Gerçek funding adaptörü | **Kod / yerel sözleşme testleri tamam** | GET adaptörleri, normalize event, metadata ve risk kapıları; gerçek API live run bu ortamda doğrulanmadı |
| 2 — Stablecoin izleme | **Salt-okunur ekranlama kodu hazır** | 2 orderbook / spot L2, iki yön, eksik fee/timestamp nedeniyle net NULL |
| 3 — Hisse + ETF | **Not connected** | Data/borrow/lisans anlaşmasına bağlı |
| 4 — Basket + tahvil/repo | **Not connected** | Johansen/OOS ve dealer verisi gerekli |
| 5 — Forward paper | **Henüz yapılmadı** | En az 7–14 gün gerçek kaynaklarla gözlem + sonraki quote/fill doğrulaması gerekir |

## Dizinler

`alti/adapters.py` Binance/OKX B1; `alti/stablecoin.py` B2; `alti/risk.py` ortak paper budget; `alti/worker.py` scan/audit/snapshot; `site/` gerçek gösterim; `config/` araştırma varsayımları; `docs/VERI_VE_ERISIM_MATRISI.md` araştırma kaynakları; `legacy/` **sentetik orijinal demo** korunur, gerçek rapora hiç import edilmez.

**Eldeki kanıt sınırı:** 4 yerel smoke = PASS (adapter mock veriyle); gerçek borsa ağı = bu container'da UNREACHABLE; GitHub Actions CI = çalıştırılmadı; Pages deploy = yapılmadı; gerçek/forward PnL = NULL. Bu durum gerçek işlem tavsiyesi değildir.


## Etkileşimli sentetik Demo V2

Ayrı sayfa: `https://onurqlp.github.io/alti-quant-lab/demo/` (`site/demo/`). Bu sayfada A1, A2, A3, B1, B2 ve T0 için tamamen **SYNTHETIC** örnek dizileri, maliyet sürtünmesi ve tek-kasa risk kaydırıcıları, 7/14/30 günlük örnek gözlem günlüğü ve mobil uyumlu grafikler yer alır. Demo, `report.json` okumaz ve hiçbir piyasa API'sine veya trade endpoint'ine istek yapmaz. Sentetik içerik gerçek geçmişi, ileri paper performansını, garanti getiri veya broker erişimini temsil etmez. Gerçek read-only panel ana dizinde korunur.

Demo-only görünüm değişiklikleri `git commit -m "... [demo-only]"` ile yayınlanır. Bu özel push için `scan` işi (ve içindeki testler) **çalıştırılmaz**; sadece GitHub Pages işi çalışır. Normal zamanlanmış salt-okunur veri taramaları değiştirilmemiştir.

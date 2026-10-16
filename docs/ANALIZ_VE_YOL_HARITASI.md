# ALTI — Altı Seçili Modelin İş/Kuant Analizi

**Hazırlanış:** 16 Ekim 2026. **Kapsam:** Yalnızca Mithat ile ortak listede seçilen 6 strateji. **Bütçe:** 100.000–200.000 TL; karar senaryosu 150.000 TL. **İnsan zamanı:** Kısıtlı. **Birincil amaç:** Tekrarlanabilir, otomasyona elverişli, düşük operasyonlu araştırma ve olası strateji avantajını bulmak. Gerçek getiri garantisi yok.

## 1. Birinci karar: Altı bot değil üç motor

### MOTOR A — İstatistiksel göreli değer
- **2 — Hisse pairs trading:** İki varlığın log fiyatları üzerinden sabit formation döneminde hedge oranı; Engle–Granger test, artık seri, sapmanın ileri dönem davranışı. Strateji, ilişkilerin tekrar yakınsama varsayımı üzerine kuruludur; kesin arbitraj değildir.
- **3 — ETF–ETF:** Aynı altyapının fonlara uyarlanması. Benzer isimli fonlar bile farklı endeks, ağırlık, gider, döviz ve temettü politikası izleyebilir. ETF-NAV yaratma/itfa hakkı genellikle yetkili katılımcılarda olduğundan, bunu doğrudan garantili ETF arbitrajı diye satmayın.
- **6 — İstatistiksel sepet / cointegration:** 3+ varlık için Johansen ve sağlam out-of-sample test gerekebilir. Pairs sisteminin yalnızca β katsayılarını çoğaltarak "cointegration kanıtlandı" denmesi yanlıştır. Sepet, **üçüncü bağımsız kâr motoru değil, araştırma motoru A'nın genişlemesidir**.
- **Birlikte çalışma:** Tek piyasa verisi, tek formasyon/OOS ayrımı, ortak işlem maliyeti ve kısa satış erişim kontrolü; aynı endeks veya tek varlığa aşırı örtüşen riskler için tek konsolide pozisyon limiti. Üç ayrı strateji aynı hareketi "üç fırsat" diye çoğaltamaz.
- **İşlem öncesi engel:** BIST ve/veya yabancı piyasada short/ödünç bulma, nakit teminat, veri lisansı ve komisyon; short yapılamıyorsa yalnız bilgi servisi ya da long-only araştırma, gerçek pairs olarak iddia edilmez.

### MOTOR B — Kripto fiyat/fonlama farkı
- **5 — Funding vadesi/interval farkı:** Her venue için "rate per funding event", `fundingTime`, `nextFundingTime`, gerçekleşmiş vs. tahmini oran, settlement mekanizması, cap/floor ve aynı enstrüman koşulları tutulur. Saatlik %0,01 ile 8 saatlik %0,01, aynı finansal döneme eşlenmeden kıyaslanamaz. `daily_run_rate` yalnız enstantane koşullu hızdır, gelecekteki net kazanç tahmini değildir.
- **4 — Stablecoin fiyat sapması:** Merkezî borsada başka biri aynı varlık için farklı bid/ask sunabilir. Ancak depeg, ihraççı, itfa erişimi, zincir/bridge farklılığı, emir derinliği ve para transferi riskini kontrol etmeden arbitraj değildir. Stablecoin borsada ucuzsa bunun nedeni ödeme/itfa belirsizliği olabilir.
- **Birlikte çalışma:** Funding stratejisinde teminat/marjin olarak kullanılan stablecoin'in fiyat/likidite anomalileri **risk filtresi** olabilir. Stablecoin ekranındaki fiyat farkını hem "getiri" hem funding işlemine "ek kazanç" diye saymayın. Stablecoin alarmı marjın net piyasa değerini etkileyebilir; çoklu borsada sermaye parçalanır.
- **İşlem öncesi engel:** Piyasa ve vadeli ürün erişimi, ülke/hesap uygunluğu, eş zamanlı hedge, komisyon ve funding tersine dönme riski. İlk ürün olarak **ücretli veri/funding normalizasyon servisi** daha düşük sermaye riskiyle sınanabilir.

### MOTOR C — Sabit getiri finansmanı
- **1 — Tahvil–repo:** Tahvil getirisinin repo faizinden yüksek olması *otomatik risksiz arbitraj* değildir. Tahvil vade/duration ve fiyat şoku; kupon, teminat/haircut, fonlama vadesi ve temerrüt etkisi hesaplanır. Repo/tahvil piyasasına **gerçek broker/dealer işlem yetkisi** ve piyasa kotasyonu gereklidir.
- **Birlikte çalışma:** İstatistik motoru A ile ortak zaman damgası, performans ve risk üst yapısını paylaşabilir; **hisse ortalamaya dönüş sinyaliyle aynı işlem motoruna zorlanmamalı**.
- **Öncelik:** Kullanılabilir resmî veri ve kişisel/kurumsal işlem erişimi doğrulanmadan yalnız izleme/analitik olarak tutulmalı. Kurumsal nitelikte veri aboneliği imkânı ayrıca değerlendirilebilir.

## 2. Altı Model Öncelik Matrisi

| Model | İşlem uygulanabilirliği (100–200K TL) | Aynı altyapıyı paylaşma | Operasyon | İlk yapılacak şey |
|---|---|---|---|---|
| Funding interval farkı | Teknik veri tarafı yüksek, kârlı hedge belirsiz | Stablecoin ile ortak kripto data | Düşük/orta | Gerçek timestamp ve rate unit toplama |
| Pairs trading | Short koşullarına bağlı | ETF + basket ile çok yüksek | Orta | Formation/OOS, borçlanabilirlik doğrulaması |
| ETF–ETF | Short ve ETF benzerliğine bağlı | Pairs ile çok yüksek | Orta | Fonların dayanak/gider karşılaştırması |
| Stablecoin fiyat sapması | Erişilen iki likit piyasa ve redemption'a bağlı | Funding risk altyapısıyla orta | Orta/yüksek | Bid/ask, depth, depeg/stress alarmı |
| Cointegration sepet | Veri/istatistik güçlü; çok bacak zor | Pairs ile çok yüksek | Orta/yüksek | Çoklu hipotez ve hedge istikrarı |
| Tahvil–repo | Kurumsal erişim gerektirebilir | Ortak rapor/risk dışında az | Yüksek | Repo ve tahvil erişimini doğrulama |

**Bu matris canlı veriden ölçülmüş başarı tablosu değildir.** Başlangıç önceliklendirmesidir.

## 3. İlk Kombinasyon Önerisi

**Önerilen sprint 1: MOTOR B'nin funding veri/normalizasyon altyapısı + MOTOR A'nın pairs araştırma omurgası.** Bunlar farklı pazarlara dağılarak altyapı bağımlılığı riskini azaltır, teknik değer üretir. İki iş kolundan gerçek işlem kârı varsayılmamalıdır.

**Sprint 2:** ETF veri eşleştirme ve kısa satış kontrolü eklensin; stablecoin ekranı hem ayrı fırsat gözlemi hem teminat risk filtresi olsun. **Sprint 3:** Basket gerçek çok değişkenli test ve bond/repo erişim anlaşmaları hazır olunca ilerlesin.

**Neden altısını baştan tam canlı işlem yapmıyoruz?** Tek sermaye, farklı para birimleri, çoklu işlem saatleri, farklı short/hedge izinleri, teminat ve API güvenilirlik gereksinimi var. Üstelik bazıları gerçek arbitraj değil, mean-reversion betasıdır. İlk günden hepsini aktif etmek portföyde korelasyon ve teknik hata biriktirir.

## 4. 150.000 TL Örnek Bütçe (öneri; piyasa maliyeti doğrulanmalı)

| Kalem | TL | İşlev |
|---|---:|---|
| **Korunan nakit rezerv** | **60.000** | Deneylerden bağımsız, korunur |
| Veri, yazılım, servis, bulut | 25.000 | Lisanslı data / gerekiyorsa VPS / monitoring |
| Research ve küçük ürün pilotu | 20.000 | Funding/data + pairs analitik örneği |
| Pazarlama / abonelik doğrulama | 15.000 | İleri veri veya analitik ürününe ödeme isteği testi |
| Broker/kurumsal veri ve hukuki inceleme | 15.000 | Gerçek short ve repo erişimi, güncel lisans koşulları |
| Beklenmedik operasyon / ikinci sprint | 15.000 | Kanıta bağlı tahsis |
| **Toplam** | **150.000** | |

Gerçek piyasa işlemi için başlangıçta zorunlu kaynak ayrılmadı. Sermayenin tümünü aynı stablecoin, aracı kurum veya borsaya yerleştirme. Finansal yatırım kararı ayrıca ve açık onayla alınır.

## 5. Kasa & Raporlama Nasıl Olmalı?

- **Üç katman:** (i) Araştırma gözlemi; (ii) ileriye dönük shadow/paper; (iii) ancak ayrıca izin verilirse canlı.
- **Rapor:** Sinyal saati, verinin kaynağı, kullanılan saat dilimi, formation/training sınırı, risk kontrolü, quote yaşı, erişim durumu, gerçekleşmeyen fırsat, neden reddedildi, işlem maliyeti varsayımları.
- **Durumlar:** `RESEARCH`, `WATCH`, `COST_BLOCKED`, `ACCESS_BLOCKED`, `DATA_STALE`, `READY_FOR_PAPER`, `PAPER_PENDING_FILL`, `PAPER_FILLED`, `CLOSED`, `INVALIDATED`. `READY_FOR_PAPER` asla `REAL_TRADE` değildir.
- **Sanal dolum:** Sinyalin oluştuğu fiyat ile işlem olmuş kabul edilmez; en erken sonraki zamanlı gerçek bid/ask ve kullanılabilir emir derinliği gerekir. Veri yoksa `NO_FILL`.
- **Kasa:** TRY ve USD ayrı muhasebe defteri; iki para birimi yalnız güncel, timestamp'li ve makaslı FX kuru ile raporlanabilir. Kapalı kağıt pozisyon PnL, açık mark-to-market ve fonlama/borç maliyeti ayrı. `verified_pnl` yoksa "sıfır kâr" denmez, **ölçülemiyor** denir.
- **Birleşik risk:** Tek dayanak, aynı endeks, aynı ihraççı, aynı stablecoin teminatı ve aynı broker karşı tarafı üzerinden konsolide maruziyet. Cointegration ile pairs aynı varlığa zıt sinyal veriyorsa iki ayrı emir üretme.
- **Kapanış:** Hedge bozulması, veri eskiliği, spread'in kaybolması, funding işareti tersine dönmesi, borçlanma imkânsızlığı, kredi/haircut sorunu, depeg/itfa riski.

## 6. Para Kazanma Yolları — Açık Ayrım

1. **Kendi sermayemizle işlem sonucu:** Gerçek pozisyon ve net kâr/zarar; getiri garantisi yok. Kaldıraç zararı hızlandırabilir.
2. **Piyasa veri/analitik aboneliği:** Özellikle funding interval karşılaştırması, doğrulanmış ETF spread ve istatistiksel risk uyarıları için müşteri bulunursa aylık gelir. Bu gelir de müşteri edinimine bağlıdır; hazır kazanç değildir.
3. **Kendi araştırma altyapımız:** Doğrudan para üretmez, karar kalitesini artırır; ürünleştirilirse gelir yaratabilir.

Yalnızca bu **altı** stratejinin analiz/işlem mekaniklerini geliştirin; üçüncü taraf "kripto mining, scalping, kupon avcısı, DEX sandwich" vb. modüller eklemeyin.

## 7. 60 Günlük Sprint ve 'Kapat' Eşikleri

- **Gün 1–10:** Her veri setinin lisans/erişim/latency; stablecoin ihraççı, borsa, repo ve short hakkının envanteri. Düzgün saat, formasyon/OOS ayrımı, kaliteli veriye erişilemiyorsa sistem "erişim yok" gösterir.
- **Gün 11–25:** Motor A: pairs train/OOS, ETF benzerlik filtreleri, basket test altyapısı. Motor B: funding exact event settlement, stablecoin iki venue bid/ask ve depth. Motor C: yalnız data fizibilitesi.
- **Gün 26–45:** Walk-forward + yeniden örnekleme + kötü piyasa rejimleri. Başarı metriklerine tüm masrafları koy. Sahte fırsat/uygulanamayan short ve emirler reddedilsin.
- **Gün 46–60:** Sonraki kotasyonla fill kuralları ve shadow ledger. İşlem öncesi review: minimum numune, kötü durum kayıp, likidite, erişim, fonlama/teminat riski. Yazılım API aboneliği fikri için minimum 3 ödeme sinyali aranabilir; bir yatırım başarısı göstergesi değildir.

**Kill koşulu:** Erişim hukuken/mekanik olarak mümkün değilse; fill maliyetleri teorik avantajı siliyorsa; sadece çoklu denemelerle seçilen aşırı uyumlu strateji ortaya çıkıyorsa; canlı karşılaştırmada sinyal sürekli geç kalıyorsa; risk üst sınırları ihlal ediliyorsa, ilgili strateji `RESEARCH_ONLY`/`DISABLED` olur. Kalan modüller çalışmayı sürdürür.

## 8. Sayısal Mekanik — Yanıltmayan Örnekler

- Funding: Borsa A %0,012/1 saat ile Borsa B %0,032/8 saat **eşit nominal** karşılaştırıldığında basit teorik günlük run-rate A %0,288; B %0,096 olur. Bunlar 24 saat değişmeden sürerse koşullu matematiksel hızdır; sabit gelecek gelir, yıllık faiz veya gerçek net hedge değildir.
- Stablecoin: Ucuz ask 0,9990 USD, pahalı bid 0,9998 USD → brüt yaklaşık 8,0 bps. Toplam komisyon 8 bps + kayma tamponu 6 bps → yaklaşık -6 bps. İki bacak eşzamanlı dolamıyorsa sonuca daha fazla risk eklenir.
- Tahvil–repo: Tahvil yıllık getiri %34 ve repo %31 diye %3 garantili spread çıkarılmaz. Kabaca 3,4 duration'lı tahvilin yield'i +1,5 yüzde puanı değişirse birinci mertebe fiyat etkisi **yaklaşık -%5,1** olur (konveksite/kupon/valör hariç).
- Pairs: Formation Engle–Granger p<0,05 olsa bile 100 aday taradıysanız tesadüfi bulunan sonuçlar artar. Çoklu hipotez kontrolü ve ileri dönük test zorunludur.

## Kaynaklar

Belge tarihine göre başlangıç kaynakları `KAYNAKLAR.md` içindedir. Canlıya alınmadan önce erişim, mevzuat, veri hakları ve API limitleri tekrar araştırılacaktır.

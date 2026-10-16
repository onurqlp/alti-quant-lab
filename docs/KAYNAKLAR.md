# Resmî Kaynaklar, Veri Lisansı ve Teknik Doğrulama

Bu doküman veri sağlayıcı seçimi içindir; **bir API anahtarının mevcut olduğu veya piyasalarda işlem yetkimiz bulunduğu iddia edilmez**.

## Funding — kripto

1. Binance USDⓈ-M Futures Developer Docs: Funding Rate History (`GET /fapi/v1/fundingRate`), Funding Info (`GET /fapi/v1/fundingInfo`), Mark Price (`GET /fapi/v1/premiumIndex`). Kaynak: https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data (eşdeğer yayın yolu: https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data). Funding Info belirli enstrümanların dönem ayarlarını verir. Tek endpoint her ürünün o anki ve geçmiş tüm settlement rejimini garanti etmez.
2. OKX API v5: https://www.okx.com/docs-v5/en/ ; funding-rate history: `GET /api/v5/public/funding-rate-history`. OKX API teknik güncellemeleri: https://www.okx.com/docs-v5/log_en/ . Funding interval 1, 2, 4, 6, 8 saat gibi farklı aralıklara değişebilir; gerçekleşen ve tahmini oran alanlarını karıştırmayın.
3. Ülke/hesap erişimi, vadeli piyasa kullanılabilirliği, emir ve piyasa verisi şartları ayrıca kontrol edilir. 2026 koşulları daha sonra değişebilir.

## ETF / hisse

4. SEC Investor.gov ETF Investor Bulletin: https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-24 . ETF creation/redemption işlemleri yetkili katılımcı mekanizmasıdır; bireysel yatırımcının piyasa fiyatı–NAV sapmasını kesin arbitrajlayabileceği anlamına gelmez.
5. ETF NAV ve referans dayanak verileri için ilgili ihraççı/fonun resmî raporları ve lisanslı piyasa veri sağlayıcıları gerekir. Hisse/ETF karşılaştırması için split, temettü, hak kullanımı, zaman dilimi ve kur uyarlamaları şarttır.
6. Türkiye piyasası için Borsa İstanbul: https://www.borsaistanbul.com/ ve SPK: https://spk.gov.tr/ . Açığa satış kuralları **tarihsel olarak değişebilen SPK kararlarına tabidir**. Örneğin Mart 2026 tarihli kısa dönem açığa satış kısıtları yayınlanmıştır: https://spk.gov.tr/data/69a4a3df8f95db22c4ee7981/2026-11.pdf . Bu örnek Ekim 2026'da aynı yasağın devam ettiği anlamına gelmez; canlı uygulama tarihindeki durum tekrar doğrulanır.

## Tahvil / repo

7. Borsa İstanbul Repo–Ters Repo Pazarı: https://www.borsaistanbul.com/piyasalar/borclanma-araclari-piyasasi/piyasa-isleyisi/repo-ters-repo-pazari . Teminat saklama, yeniden değerleme ve günlük ek teminat süreçleri önemlidir.
8. Borsa İstanbul Menkul Kıymet Tercihli Repo: https://www.borsaistanbul.com/piyasalar/borclanma-araclari-piyasasi/piyasa-isleyisi/menkul-kiymet-tercihli-repo-pazari . İşlemin nominali, oranı, başlangıç/bitiş valörü ve kabul edilen teminat önemlidir.
9. Tahvil fiyat/yield/duration/kupon/dirty price ve repo oranları için yetkili veri/finansal kurum erişimi doğrulanmadan "executable spread" hesaplanmayacaktır.

## Teknoloji / istatistik

10. statsmodels `coint` (Engle–Granger) ve `adfuller` docs: https://www.statsmodels.org/stable/tsa.html . Sadece formasyon p-değeri ve son z-score göstererek kârlılık kanıtlanamaz. Çoklu denemeler için FDR / gerçek dış örneklem kontrolü; çoklu sepetler için Johansen ve deterministik terim seçimi önemli.
11. Veriyle ilgili tüm kayıtlar `source_name`, `provider`, `asof_utc`, `received_utc`, `currency`, `symbol`, `unit`, `session`, `is_final`, `license`, `data_delay_ms`, `scan_id` tutmalıdır. Gerçek kaynak yoksa alan null olarak veya "NOT_CONNECTED" durumunda açıkça gösterilmelidir.

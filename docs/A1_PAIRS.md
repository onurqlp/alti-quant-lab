# A1 — Hisse pairs: çalışma ve kabul sözleşmesi (18.10.2026)

**Amaç:** Benzer iki ABD hissesinin göreli fiyat geçmişinin istatistiksel araştırması. İlk sabit test evreni KO/PEP; yatırım/işlem önerisi değildir.

## Kullanılan veri
- [Alpaca historical stocks bars](https://docs.alpaca.markets/us/reference/stockbars): `adjustment=all` (split, dividend, spin-off) ve `1Day`; `feed=iex` (tam SIP kapsaması değil). Kaynak kişisel araştırma ve veri yeniden dağıtım şartları ayrıca doğrulanmalıdır.
- Tarihli, eşleşen fiyat kapanışları; ortak günlerin dışına taşıma/forward-fill yok. En az 270 eşleşmiş gün, 180 formation, 50 validation, 40 OOS. Engle-Granger testine yalnız 180 formation girer; hedge katsayısı yalnız formation günlerinden hesaplanır.
- OOS ekranı **geriye dönük** ve kurumsal işlem düzeltmeleri geçmişe yansıyabilir. İzleme esnasında biriktirilmiş gerçek forward test sayılmaz. Cointegration p-değeri başarı olasılığı değildir.
- IBKR [shortable availability](https://www.interactivebrokers.com/en/trading/short-securities-availability.php) broker hesabına göre farklıdır; miktar, borrow ücreti, teminat ve kısıtlamalar olmadan gerçek kısa satış/işlem mümkün varsayılamaz.

## Başlatma
ALTI GitHub repo > Settings > Secrets and variables > Actions:
- Secret `ALTI_A1_API_KEY` = kullanıcının yetkili Alpaca market-data API key ID'si.
- Secret `ALTI_A1_API_SECRET` = bu anahtarın secret'ı.
- Variable `ALTI_A1_DATA_RIGHTS` = sadece sağlayıcı izni teyit edildiyse `PERSONAL_RESEARCH_CONFIRMED`.
- Variable `ALTI_A1_PUBLIC_DERIVED_RIGHTS` = sağlayıcıya göre kamuya türetilmiş istatistik yayını **ayrıca yazılı/onaylı** ise `CONFIRMED`; aksi durumda boş bırakın.

ALTI'nin mevcut Actions `publish.yml` taraması A1'i **yalnız bu izinler tamamlandıktan sonra** salt okunur çalıştırır. Kimlik bilgileri kod, URL, report veya loglara yazılmaz. Varsayılan hiçbir yeni API çağrısı yapılmaz.

**Çıkış:**
`site/report.json > a1_research`: SOURCE_REQUIRED / SOURCE_ERROR / RESEARCH_ONLY. `strategies[A1].status` de aynısını gösterir. MAKİNE tarafı otomatik sinyale terfi ettirmez. Verinin gelmesi hâlâ borrow, komisyon, alış/satış, izin, örneklem/forward test ve broker erişimini çözmez. Sanal kasa ve gerçek PnL değişmez.

**Kabul kriteri:** GitHub testi + sağlayıcı bağlantısı + yeterli eşleşmiş gerçek gün + veri kullanım hakkı. Araştırma aşamasından ilerlemek için ayrıca borçlanabilirlik, borrow ücreti, canlı quote/spread, iki bacak fill erişimi ve zamana göre forward validasyon gerekir.

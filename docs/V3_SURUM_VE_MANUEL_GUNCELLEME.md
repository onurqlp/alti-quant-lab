# ALTI · Manuel Güncelleme / Kullanıcı Kontrollü Sürüm Sözleşmesi

**Geçerli ürün sürümü: 1.0.0.** Kaynak yapılandırma dosyası bu sürümü `1.0.0-read-only-mvp` olarak tanımlar. **Bu değişiklik ürün sürümünü yükseltmez.** Tarihli arayüz değişikliğinin kimliği `UI-20261017-01`, tarihi **17 Ekim 2026**. Demo V2, ürün sürümünden bağımsız sentetik örnek sayfadır.

## Kullanıcıdan gelen kesin kurallar

- **Sürüm yükseltmek yalnızca kullanıcının açık onayıyla mümkündür.** Asistan yeni sürümü önerebilir ama `config/research_config.json:version`, `site/release.json:product_version` ve kullanıcıya görünen etiketler onaysız yükseltilmez.
- **Her site güncellemesi:** `site/release.json` dosyasında farklı `site_update_id`, tarih, açıklama, `product_version`, `version_changed: false` ile öne eklenir. Önceki kayıtlar korunur.
- **Her manuel araştırma:** gerçek kaynakların URL, fiyatın zamanı, erişim zamanı, borsa/sözleşme, düzeltme/split, maliyet ve veri kalitesi alanlarını kaydet. Yapılan araştırmanın `manual_research_last_completed_at_utc` tarihi yalnız araştırma gerçekten tamamlandığında yenilenebilir.
- **Piyasa feed'i (`site/report.json:generated_at_utc`) araştırma raporundan ve site güncelleme tarihinden ayrıdır.** 30 dakikalık salt-okunur tarama sürüm numarasını değiştirmez.
- **Karar değişmezliği:** karar anındaki bilgi, uzun/kısa yönler, piyasa, şartlar, sanal miktar ve zaman damgası gelecekte değiştirilmez. Hata düzeltmeleri eski kaydı silmeden yeni bağlantılı kayıt oluşturur.
- **AUTO / SELECT:** iki bağımsız 150.000 TL referans portföyü; birlikte 300.000 TL yatırım iddiası yok. SELECT onayından önceki fiyatlardan geriye dönük giriş yapılmaz. AUTO kuralları strateji sürümüyle sabitlenir.
- **Karar yoksa kâr yazma:** ileri paper fill için sonraki uygulanabilir fiyat/derinlik, tüm bacaklar ve maliyetler gereklidir. Eksik veride `DATA_GAP` veya `UNFILLABLE` olur, 0 ücret/sonsuz likidite varsayılmaz.
- **Kaynak ve yayın tarihi:** ekrana son site güncellemesi, son manuel araştırma, son yayınlanan piyasa verisi ayrı ayrı basılır. Piyasa verisi eskirse “BEKLE” uyarısı kalır.

## Kullanıcının bir sonraki mesajıyla yapılacak işlem

“ALTI sistemini güncelle” mesajında: son dondurulan karar tarihinden başlayıp gerçek piyasa verilerini araştır, eski kararları E1/E2/E3 kanıt seviyesine göre sonuçlandır, AUTO ile SELECT'i ayrı hesapla, yeni fırsatları ve ret sebeplerini ekle; site tarihini ve update ID'yi yenile. Sonraki ürün sürümünü öner, **asla onaysız değiştirme**.

Sürüm önerisi (onaylı değil): **3.0.0**. Bu bir çalışma planı tavsiyesidir; mevcut ürün sürümü hâlâ 1.0.0'dır.

## Bu yayının kapsamı

Yeni başlangıç ekranı + altı temel rehber + 2 sanal portföy açıklaması + sözlük + tarihli sürüm günlüğü. **Yeni ticaret sinyali, ileri paper dolumu, tarihsel simülasyon veya yeni piyasa araştırması yapılmadı.** Eski salt-okunur kaynak görünümü ve sentetik Demo V2 korundu. `[ui-only]` commit'i CI içindeki test ve piyasa taramasını çalıştırmadan GitHub Pages'e yayınlanır; zamanlanmış salt-okunur taramanın kendisine dokunulmaz.

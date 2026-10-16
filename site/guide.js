/* ALTI beginner decision guide. Educational explanations only; no executable orders. */
'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const safe = value => String(value ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const humanDate = date => {
    if (!date) return 'Henüz kaydedilmedi';
    const d = new Date(date.length === 10 ? date + 'T12:00:00+03:00' : date);
    if (Number.isNaN(d.getTime())) return 'Tarih bilinmiyor';
    return d.toLocaleString('tr-TR', {year:'numeric',month:'long',day:'numeric',timeZone:'Europe/Istanbul'});
  };
  const humanDateTime = date => {
    if (!date) return 'Henüz yok';
    const d = new Date(date);
    if(Number.isNaN(d.getTime())) return '—';
    return d.toLocaleString('tr-TR',{dateStyle:'medium',timeStyle:'short',timeZone:'Europe/Istanbul'})+' (Türkiye)';
  };
  const plans = [
    {id:'B1',name:'Borsalar arası fonlama farkı',category:'KRİPTO',icon:'↔',headline:'Aynı kripto sözleşmesinde iki borsayı karşılaştırıyoruz.',
     plain:'Vadeli sözleşmelerde long ve short taraflara dönemsel ödeme yapılabilir. Farkın masraflardan büyük olup olmadığını araştırıyoruz.',
     what:'BTC/ETH USDT teminatlı perpetual sözleşmeler (doğrulanmış aday olursa).',
     where:'Şu an yalnız OKX gözlemleri doğrulanmış olabilir; ikinci borsa ve işlem erişimi kontrol edilmeden yer seçilmiyor.',
     direction:'Fonlamayı net tahsil eden taraf ve fiyat riskini dengeleyen karşı pozisyon; yön henüz belirlenmedi.',
     enter:'İki piyasada eşleşen sözleşme, saat, fiyat, maliyet ve teminat uygunluğu birlikte doğrulanınca.',
     exit:'Önceden kilitlenmiş fonlama/basis eşiği, maliyet, risk veya süre koşulu tetiklendiğinde.',
     why:'Fonlama farkı iki taraftaki maliyetleri karşılayabilir mi?',
     risk:'Fonlama tersine dönebilir; baz farkı açılabilir; short ve marjin/likidasyon riski vardır.',
     blockers:['İkinci borsanın doğrulanmış eş anlı fiyatı','Çift yön komisyon ve hedge maliyeti','İşlem/teminat erişimi','Zaman damgalı uygulanabilir giriş ve çıkış kotasyonu']},
    {id:'B2',name:'Stablecoin fiyat farkı',category:'KRİPTO',icon:'≋',headline:'Aynı sabit değerli varlığın iki piyasadaki fiyatını inceliyoruz.',
     plain:'Bir borsadaki USDC fiyatı diğerinden farklı olabilir. Ucuza almak ve pahalıya satmak bazen kârlı görünebilir ama aktarım, masraf ve zaman farkı sonucu silebilir.',
     what:'USDC/USDT çifti; spot alım/satım uygunluğu doğrulanırsa.',
     where:'İki doğrulanmış spot pazar; şu anda eş zamanlı ve uygulanabilir iki taraflı alım-satım doğrulanmadı.',
     direction:'Teoride düşük ask fiyatından AL, yüksek bid fiyatından SAT; koşullar doğrulanmadan öneri değildir.',
     enter:'Gerçekleştirilebilir miktarda emir defteri, çift taraflı erişim, ücretler ve token transfer rotası doğrulanınca.',
     exit:'İki bacak da uygulanabilir biçimde tamamlandığında veya önceden belirlenen iptal eşiğinde.',
     why:'Görülen spread gerçekten tahsil edilebilir mi?',
     risk:'Spread kapanabilir; transfer gecikebilir; stablecoin değeri sapabilir; fiyat anlık değişebilir.',
     blockers:['Aynı ana ait doğrulanabilir emir defteri','Alış/satış ve aktarım ücretleri','Transfer ağı ve token eşdeğerliği','Miktara uygun derinlik']},
    {id:'A1',name:'İki benzer hisse',category:'HİSSE',icon:'Ⅱ',headline:'Birlikte hareket eden iki hissenin ilişkisindeki sapmayı arıyoruz.',
     plain:'İki hisse genellikle beraber hareket ediyorsa, aralarındaki fiyat ilişkisi geçici olarak bozulabilir. Geri dönüş olabilir ama garanti değildir.',
     what:'Aynı sektör/ekonomik etkiye sahip, tarihsel olarak incelenmiş iki hisse.',
     where:'İlgili hisse borsası ve yetkili aracı kurum; henüz varlık veya kurum doğrulanmadı.',
     direction:'Modelin göreli ucuz bulduğunu LONG, göreli pahalı bulduğunu SHORT; uygunluk onayı olmadan işlem yok.',
     enter:'Önceden belirlenmiş istatistiksel eşik, kısa satış uygunluğu ve maliyet kontrolleri sağlanınca.',
     exit:'Fiyat ilişkisi normale dönünce; ayrıca süre, stop ve ilişki bozulması şartlarında.',
     why:'Fiyat farkı tarihsel dengeden anlamlı biçimde uzaklaşmış mı?',
     risk:'Hisseler birlikte hareket etmeyi bırakabilir; temettü, haber ve açığa satış koşulları riski artırır.',
     blockers:['Düzeltilmiş tarihsel fiyatlar','İstatistiksel ileri dönem doğrulaması','Short/ödünç erişimi','İşlem maliyetleri']},
    {id:'A2',name:'Benzer iki ETF',category:'FON',icon:'◇',headline:'Benzer yatırım fonları arasında gerekçeli fiyat farkı arıyoruz.',
     plain:'Aynı ya da çok benzer varlıkları izleyen ETF’lerin fiyatları birbirinden ayrılabilir. Ayrımın geçici mi yapısal mı olduğunu anlamamız gerekir.',
     what:'Dayanakları, giderleri, para birimleri karşılaştırılmış iki ETF.',
     where:'İlgili ETF’nin işlem gördüğü borsa; isimler ve işlem erişimi henüz belirlenmedi.',
     direction:'Koşullar oluşursa göreli ucuz ETF uzun, göreli pahalı ETF kısa; otomatik öneri yok.',
     enter:'NAV, temettü, FX, işlem saatleri ve maliyet farkları kontrol edildikten sonra model eşiğinde.',
     exit:'Göreli fiyat farkı hedefe döndüğünde veya risk/likidite limiti dolduğunda.',
     why:'Fark piyasa hatası mı, yoksa farklı masraf ve endeksin doğal sonucu mu?',
     risk:'NAV geç açıklanabilir; varlıklar tam aynı olmayabilir; döviz ve short riski bulunur.',
     blockers:['Aynı zamanlı fiyat/NAV','Temettü ve kur düzeltmesi','Kısa satış uygunluğu','Toplam maliyet']},
    {id:'A3',name:'Dengeden çıkan varlık sepeti',category:'İSTATİSTİK',icon:'▤',headline:'Birden çok varlığın birlikte kurduğu denge bozulmuş mu bakıyoruz.',
     plain:'Üç veya daha fazla varlığın fiyatları uzun dönemli bir ilişki gösterebilir. İlişki bozulunca geri dönme ihtimali araştırılır.',
     what:'Tarihsel ilişkisi sınanmış hisse veya ETF sepeti.',
     where:'Sepetteki tüm varlıkların işlem gördüğü doğrulanmış pazarlar; seçim tamamlanmadı.',
     direction:'Sepet ağırlıklarına göre birden fazla long/short bacağı olabilir; hazır yön bulunmuyor.',
     enter:'Geçmiş eğitim, ayrı doğrulama ve dış örneklem kontrolleri geçtiğinde, tüm bacaklar uygunsa.',
     exit:'Sepet artık değeri hedef aralığa döndüğünde; kırılma, zaman veya zarar limitinde.',
     why:'Birlikte hareket etme ilişkisi geçerli mi, yoksa bozuldu mu?',
     risk:'Model geçmişe aşırı uyum gösterebilir; korelasyon kırılırsa tüm bacaklar zarar verebilir.',
     blockers:['Yeterli çoklu varlık verisi','İleri dönem out-of-sample analiz','Bütün bacaklarda likidite','Hedge ve borrow erişimi']},
    {id:'T0',name:'Tahvil ve repo getirisi',category:'FAİZ',icon:'▥',headline:'Tahvil getirisi ile finansman maliyeti arasındaki farkı ölçüyoruz.',
     plain:'Bir tahvilin getirisi cazip görünebilir; ancak onu finanse etmenin ve vade boyunca taşımanın maliyetini bilmeden net kazanç çıkaramayız.',
     what:'ISIN’i, kuponu, fiyatı ve vadesi belirlenmiş tahvil + repo finansmanı.',
     where:'İlgili borçlanma aracı/repo pazarı ve yetkili karşı taraf; bu erişim doğrulanmadı.',
     direction:'Koşula bağlı tahvil pozisyonu ve finansman bacağı; kesin al/sat yönü yok.',
     enter:'Kirli fiyat, getiri, repo kotasyonu, valör, haircut ve risk kontrolleri birlikte doğrulanınca.',
     exit:'Önceden belirlenen finansman vadesinde veya piyasa/faiz riski limiti tetiklendiğinde.',
     why:'Tahvili taşımak, tüm finansman maliyetlerinden sonra anlamlı bir fark bırakıyor mu?',
     risk:'Faiz değişimi tahvil değerini düşürebilir; likidite, teminat ve karşı taraf riski vardır.',
     blockers:['Tarihli tahvil fiyatı ve kuponlar','Uygulanabilir repo kotasyonu','Haircut/teminat bilgisi','Duration ve finansman riski']}
  ];
  const glossary = [
    {term:'LONG',brief:'Yükselirse kazanmayı hedeflemek',detail:'Fiyatın yükseleceği yönde pozisyon almaktır. Düşerse zarar edilebilir.'},
    {term:'SHORT',brief:'Düşerse kazanmayı hedeflemek',detail:'Fiyatın düşeceği yönde pozisyon almaktır. Fiyat yükselirse zarar edilebilir; ödünç/teminat gereksinimleri vardır.'},
    {term:'SPREAD',brief:'İki fiyat arasındaki fark',detail:'Alış ve satış fiyatları veya iki benzer varlığın değerleri arasındaki fark. Brüt fark masrafsız kazanç demek değildir.'},
    {term:'FUNDING',brief:'Vadeli piyasadaki dönemsel ödeme',detail:'Perpetual sözleşmelerde long ve short taraflar arasında dönemsel fonlama ödemesidir. Oran zamanla ve ödeme yönüyle değişebilir.'},
    {term:'PAPER / SANAL',brief:'Gerçek para kullanılmayan kayıt',detail:'Kuralları ve gerçek tarihli verileri izleyen sanal işlem. Uygulanabilir giriş/çıkış verisi yoksa kârı kesinleştiremeyiz.'},
    {term:'STOP',brief:'İşlemi durdurma koşulu',detail:'Fiyat, zarar, süre veya modelin geçersizleşmesi nedeniyle pozisyonu kapatma kuralıdır. Gerçek piyasa kayması yüzünden zararı kesin sınırlandırmaz.'},
    {term:'VWAP',brief:'Miktara göre ortalama işlem fiyatı',detail:'İşlem miktarlarını dikkate alarak hesaplanan ortalama fiyat. Emir defteri derinliği yeterli değilse tek kotasyon yanıltıcı olabilir.'},
    {term:'VERİ TARİHİ',brief:'Fiyatın ait olduğu an',detail:'Piyasa fiyatının oluştuğu zaman ile bizim veriyi gördüğümüz zaman farklı olabilir. Eski fiyat bugünkü işlem kararına dönüştürülemez.'}
  ];
  let latest = null, active = 'B1', release = null;
  const detailLine = (title,value) => `<div class="guide-row"><span>${safe(title)}</span><strong>${safe(value)}</strong></div>`;
  function verdict(code) {
    const s=latest?.strategies?.find(x=>x.id===code);
    if(!s) return 'GÜNCEL KARAR YOK';
    if(code==='B1' && s.data_label==='READ_ONLY_LIVE') return 'GÖZLEM / İŞLEM YOK';
    return 'BEKLE / VERİ EKSİK';
  }
  function renderGuides() {
    const list=$('guide-grid'); if(!list) return;
    list.innerHTML=plans.map(x=>`<button type="button" data-guide="${x.id}" class="guide-tile ${x.id===active?'selected':''}" aria-pressed="${String(x.id===active)}"><div class="guide-tile-top"><span class="guide-symbol" aria-hidden="true">${x.icon}</span><span class="guide-category">${x.category}</span></div><strong>${safe(x.name)}</strong><p>${safe(x.headline)}</p><div class="guide-tile-foot"><span>${safe(verdict(x.id))}</span><span aria-hidden="true">Aç ↗</span></div></button>`).join('');
    list.querySelectorAll('[data-guide]').forEach(button=>button.addEventListener('click',()=>{
      active=button.dataset.guide; renderGuides();renderDetail();
      if(window.matchMedia('(max-width:750px)').matches) $('guide-detail').scrollIntoView({behavior:'smooth',block:'start'});
    }));
  }
  function renderDetail() {
    const el=$('guide-detail'); if(!el)return;
    const x=plans.find(p=>p.id===active),s=latest?.strategies?.find(y=>y.id===active);
    const reasons=active==='B1'&&latest?.provider_health?.some(h=>h.status==='ACCESS_BLOCKED')?
      'Önceki veri kaynaklarında erişim engeli de kaydedildi. Bu bir işlem sinyali değildir.':
      (s?.reason||'Bu model için geçerli, uygulanabilir yeni işlem kaydı bulunmuyor.');
    el.innerHTML=`<div class="guide-detail-head"><div><span class="simple-index">STRATEJİ ${x.id} · ${safe(x.category)}</span><h3>${safe(x.name)}</h3><p>${safe(x.plain)}</p></div><div class="stop-flag">⏸ BEKLE<br><small>DOĞRULANMIŞ GİRİŞ YOK</small></div></div>
      <div class="guide-result"><b>Şimdi ne yapacağız?</b><p>${safe(reasons)} Araştırma sürecek; güncel alım veya satım talimatı bulunmuyor.</p></div>
      <div class="guide-explain-grid"><div class="guide-explain"><div class="guide-explain-number">1</div><h4>Ne alınır, ne satılır?</h4><p>${safe(x.what)}</p><div class="guide-small"><b>Yön:</b> ${safe(x.direction)}</div></div>
      <div class="guide-explain"><div class="guide-explain-number">2</div><h4>Hangi piyasada, ne zaman?</h4><p>${safe(x.where)}</p><div class="guide-small"><b>Giriş:</b> ${safe(x.enter)}</div></div>
      <div class="guide-explain"><div class="guide-explain-number">3</div><h4>Ne zaman kapatılır?</h4><p>${safe(x.exit)}</p><div class="guide-small"><b>Araştırma amacı:</b> ${safe(x.why)}</div></div></div>
      <div class="guide-columns"><div><h4>🛡️ Bu işte ne kaybedebiliriz?</h4><p>${safe(x.risk)}</p></div><div><h4>🔍 İşlemden önce ne eksik?</h4><ul>${x.blockers.map(t=>`<li>${safe(t)}</li>`).join('')}</ul></div></div>
      <div class="instruction-table"><h4>Özet işlem fişi</h4>${detailLine('Hangi varlık?',x.what)}${detailLine('Hangi borsa?', 'Henüz doğrulanmadı')}${detailLine('Al/Sat yönü?', 'Güncel işlem önerisi yok')}${detailLine('Giriş fiyatı?', 'Güncel, uygulanabilir fiyat yok')}${detailLine('Sanal tutar?', 'Pozisyon açılmadı')}${detailLine('Giriş zamanı?', 'Şartlar ve veri doğrulanınca; saat henüz yok')}${detailLine('Çıkış?', x.exit)}${detailLine('Sonuç?', 'İşlem yok — kâr/zarar hesaplanamaz')}</div>
      <p class="guide-legal">Bu rehber stratejinin nasıl işlediğini anlatır. Yukarıdaki kavramsal yön açıklamaları gerçek alım-satım sinyali veya uygulanabilir emir değildir. Ayrıntılı gerçek kaynaklar aşağıdaki araştırma bölümünde bulunur.</p>`;
  }
  function renderGlossary(){
    const el=$('glossary');if(!el)return;
    el.innerHTML=glossary.map(x=>`<details class="term-card"><summary><span><strong>${safe(x.term)}</strong><small>${safe(x.brief)}</small></span><b class="term-more">+</b></summary><p>${safe(x.detail)}</p></details>`).join('');
  }
  function renderMarketSummary() {
    const el=$('data-simple-alert');if(!el)return;
    const t=latest?.last_successful_scan_utc;
    const age=t?Date.now()-new Date(t).getTime():Infinity;
    const recent=age>=0&&age<=90*60000;
    const ok=latest?.live_source_count>0;
    const fresh=ok&&recent;
    el.classList.toggle('data-fresh',fresh);
    el.innerHTML=`<span class="alert-icon">${fresh?'✓':'!'}</span><span><b>${fresh?'Bazı piyasa verileri güncel.':'Yeni bir işlemi doğrulayacak güncel veri yok.'}</b> ${ok?'Son başarılı veri: '+safe(humanDateTime(t))+'. '+(latest.errors?.length?'Bazı kaynaklar hata verdi. ':''):'Doğrulanmış kaynak gözlemi bulunamadı. '}Hiçbir gözlem doğrudan sanal giriş veya alım talimatı sayılmaz.</span>`;
    $('feed-updated').textContent=humanDateTime(latest?.generated_at_utc);
  }
  function renderRelease(data) {
    if(!data) return;
    const ver=data.product_version||'Belirsiz';
    ['system-version','release-number','hero-product-version'].forEach(id=>{if($(id)) $(id).textContent=ver});
    $('quick-version').textContent='Sürüm '+ver+' · '+humanDate(data.site_last_updated_date_tr);
    $('site-updated').textContent=humanDate(data.site_last_updated_date_tr);
    $('research-updated').textContent=humanDateTime(data.manual_research_last_completed_at_utc);
    $('next-version').textContent='Sen onaylamadan değişmez';
    $('release-date').textContent=humanDate(data.site_last_updated_date_tr)+' · '+safe(data.site_update_id);
    $('release-proposal').textContent=safe(data.proposed_next_version)+' (yalnız öneri)';
    $('release-message').textContent='Güncelleme kaydı '+safe(data.site_update_id)+'. Mevcut ürün sürümü değiştirilmedi.';
    $('release-list').innerHTML=(data.published_change_log||[]).map(e=>`<li><span class="release-list-top"><b>${safe(humanDate(e.date))}</b><small>${safe(e.update_id)}</small></span><span>${safe(e.summary)}</span><small>Ürün sürümü: ${safe(e.product_version)} · ${e.version_changed?'Onaylı değişiklik':'Sürüm aynı kaldı'}${e.data_research_performed?' · Manuel araştırma':' · Araştırma güncellemesi değil'}</small></li>`).join('');
  }
  async function loadRelease(){
    try{
      const response=await fetch('release.json',{cache:'no-store'});
      if(!response.ok)throw new Error(String(response.status));
      const data=await response.json();
      if(data.version_policy!=='USER_APPROVAL_REQUIRED'||!Array.isArray(data.published_change_log))throw new Error('Sürüm sözleşmesi doğrulanmadı');
      release=data;renderRelease(data);
    }catch(e){
      $('quick-version').textContent='Sürüm kaydı yüklenemedi';
      $('site-updated').textContent='Doğrulanamadı';
      $('release-list').innerHTML='<li>Sürüm dosyası okunamadı. Sitede yazan tarihe güvenmeyin; GitHub yayın geçmişine bakın.</li>';
    }
  }
  $('copy-command')?.addEventListener('click',async()=>{
    const cmd='ALTI sistemini güncelle. En son tarihli karar kaydından bugüne gerçek kaynakları araştır; AUTO/SELECT sanal portföylerini önceki kararları değiştirmeden değerlendir; yeni raporu tarihli yayımla. Ürün sürümünü artırma, yalnız öner.';
    try{await navigator.clipboard.writeText(cmd);$('copy-command').textContent='Kopyalandı ✓'}
    catch{ $('copy-command').textContent='Kopyalanamadı — komut: ALTI sistemini güncelle';}
  });
  document.addEventListener('alti:report-loaded',event=>{latest=event.detail;renderGuides();renderDetail();renderMarketSummary()});
  document.addEventListener('alti:report-error',()=>{if($('data-simple-alert'))$('data-simple-alert').textContent='Piyasa raporu açılamadı. Yeni işlem kararı oluşturulamaz.';});
  if(window.ALTI_REPORT){latest=window.ALTI_REPORT;renderMarketSummary()}
  renderGuides();renderDetail();renderGlossary();loadRelease();
})();

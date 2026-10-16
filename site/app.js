/* ALTI: presentation only. No direct exchange requests, credentials or trading methods. */
'use strict';
let report = null;
let activeTab = 'B1';
let activeFilter = 'ALL';
const $ = id => document.getElementById(id);
const ESC = v => String(v ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num = (v, d = 2) => (v === null || v === undefined || !Number.isFinite(Number(v))) ? '—' : Number(v).toLocaleString('tr-TR',{minimumFractionDigits:d,maximumFractionDigits:d});
const money = v => v === null || v === undefined ? '—' : '₺'+num(v, 0);
const pc = v => (v===null || v===undefined || !Number.isFinite(Number(v))) ? '—' : (Number(v)*100).toLocaleString('tr-TR',{minimumFractionDigits:4,maximumFractionDigits:5})+'%';
const dt = v => {if(!v)return '—';const x=new Date(v);return Number.isNaN(x.getTime())?'—':x.toLocaleString('tr-TR',{dateStyle:'short',timeStyle:'short',timeZone:'Europe/Istanbul'})+' TSİ'};
const ageMinutes = v => v ? (Date.now()-new Date(v).getTime())/60000 : Infinity;
const titles = {'B1':'Perpetual funding analizi','B2':'Stablecoin fiyat sapması','A1':'Hisse pairs trading','A2':'ETF–ETF göreli değer','A3':'Cointegration sepeti','T0':'Tahvil–repo finansmanı'};
function kv(k, v){return `<div class="kv"><span>${ESC(k)}</span><strong>${ESC(v)}</strong></div>`}
function info(t, warn=false){return `<div class="info-panel ${warn?'warn':''}">${ESC(t)}</div>`}
function empty(title, description){return `<div class="empty-state"><span class="symbol">◇</span><h4>${ESC(title)}</h4><p>${ESC(description)}</p></div>`}
function renderHealth(){
 const success=report?.last_successful_scan_utc, stale=ageMinutes(success)>90;
 const count=report?.live_source_count ?? 0;
 const healthy=count>0&&!stale;
 const status=healthy?(report.errors?.length?'Kısmi gerçek veri':'Gerçek piyasa verisi'):(success?'Son veri güncel değil':'Canlı veri doğrulanmadı');
 $('health-title').textContent=status;
 $('health-description').textContent=healthy?`${count} salt okunur kaynak/enstrüman gözlemi doğrulandı. Emir uygunluğu yok.`:
    count>0?'Tarama sonucu yayınlandı, fakat artık taze değil.': 'Borsa API erişimi henüz doğrulanmadı veya tüm adaptörler hata verdi.';
 $('health-orb').style.background=healthy?'#74e1c3':'#edbf7b';
 $('top-signal').textContent=healthy?'READ-ONLY DATA':stale?'ESKİ / EKSİK VERİ':'VERİ BEKLENİYOR';
 $('top-signal').style.color=healthy?'#74e1c3':'#edbf7b';
 $('last-scan').textContent=dt(report?.generated_at_utc);
 $('last-success').textContent=dt(success);
 $('global-warning').textContent=healthy
   ?'READ_ONLY_LIVE — Gerçek gözlem, doğrulanmış alım-satım fırsatı veya net kâr değildir. Funding gerçekleşmiş ve gösterge oranları ayrı tutulur; ücret, hedge ve erişim bilinmiyor.'
   :'UYARI — Canlı piyasa verisi şu anda doğrulanmadı veya eskidi. Ekrandaki hiçbir değer işlem talimatı değildir. Sanal kasa, gerçek mevduat değildir.';
 $('engine-b-status').textContent=healthy?'SALT OKUNUR AKTİF':'VERİ DOĞRULANMADI';
}
function renderBudget(){
 const p=report?.portfolio??{};
 $('stat-cash').textContent=money(p.reference_capital_try??150000);
 $('stat-reserve').textContent=money(p.protected_reserve_try??60000);
 $('stat-risk').textContent=money(p.paper_hypothesis_risk_limit_try??375);
 $('stat-gross').textContent=money(p.paper_gross_exposure_limit_try??30000);
 const pct=Math.round(100*(p.protected_reserve_try??60000)/(p.reference_capital_try??150000));
 $('risk-protected').style.width=pct+'%';$('legend-reserve').textContent='%'+pct;$('legend-open').textContent='%'+(100-pct);
}
function renderStrategies(){
 const items=report?.strategies||[];
 $('strategy-grid').innerHTML=items.map(s=>`<button type="button" class="strategy ${activeTab===s.id?'active':''}" data-select="${ESC(s.id)}" aria-label="${ESC(s.title)} ayrıntılarını göster">
  <div class="strategy-top"><span class="sid">${ESC(s.id)}</span><span class="sstate">${ESC(s.status)}</span></div>
  <strong>${ESC(s.title)}</strong><p>${ESC(s.reason)}</p></button>`).join('');
 document.querySelectorAll('[data-select]').forEach(btn=>btn.addEventListener('click',()=>selectTab(btn.dataset.select,true)));
}
function svgSeries(vals1, vals2){
 const valid=[...vals1,...vals2].filter(x=>Number.isFinite(x));
 if(valid.length<2)return '<div class="tiny">Grafik için iki gerçekleşmiş funding olayı gerekiyor.</div>';
 let lo=Math.min(...valid),hi=Math.max(...valid);if(hi===lo){hi+=.00001;lo-=.00001}
 const pad=15,W=540,H=155;
 function coords(v){return v.map((x,i)=>`${(pad+i*(W-2*pad)/Math.max(1,v.length-1)).toFixed(1)},${(H-pad-(x-lo)/(hi-lo)*(H-2*pad)).toFixed(1)}`).join(' ')}
 return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Son gerçekleşen olay başına funding oranları, yüzde cinsinden iki seri">
 <line x1="${pad}" y1="${H-pad}" x2="${W-pad}" y2="${H-pad}" stroke="#304458"/><line x1="${pad}" y1="${pad}" x2="${W-pad}" y2="${pad}" stroke="#304458" stroke-dasharray="3 7"/>
 <polyline points="${coords(vals1)}" fill="none" stroke="#74e1c3" stroke-width="2.3" stroke-linejoin="round" stroke-linecap="round"/>
 <polyline points="${coords(vals2)}" fill="none" stroke="#7daefa" stroke-width="2.3" stroke-linejoin="round" stroke-linecap="round"/>
 <text x="${pad}" y="12" fill="#91a5bb" font-size="10">${num(hi*100,4)}%</text><text x="${pad}" y="${H-1}" fill="#91a5bb" font-size="10">${num(lo*100,4)}%</text></svg>`;
}
function renderFunding(){
 const records=report?.funding_records||[];
 const pairs=report?.funding_comparisons||{};
 if(!records.length){
  const errors=report?.errors?.filter(x=>x.symbol?.endsWith('USDT')&&x.symbol!=='USDCUSDT')||[];
  return empty('Doğrulanmış funding kaydı yok',
    'Resmî Binance/OKX salt-okunur API üzerinden veri alınamadı. Erişim veya veri doğrulama hataları aşağıda belirtiliyor.')+
    `<div class="spacer12"></div>${errors.slice(0,6).map(x=>info(`${x.venue} / ${x.symbol} — ${x.status}: ${x.message}`,true)).join('')}`;
 }
 let html=info('ÖNEMLİ: Son gerçekleşmiş fonlama ödemesi ayrı; güncel gösterge oranı ayrı. 24 saate normalize edilen gerçekleşmiş tek olay oranı sadece anlık kıyas hızıdır; gelecekteki 24 saat getirisi değildir.');
 const symbols=[...new Set(records.map(r=>r.symbol))];
 for(const symbol of symbols){
  const arr=records.filter(r=>r.symbol===symbol),cmp=pairs[symbol];
  html+=`<h4 class="section-mini">${ESC(symbol)} · USDⓈ-M / USDT LINEAR</h4><div class="row-of-two">`;
  for(const v of ['BINANCE','OKX']){
   const r=arr.find(x=>x.venue===v);
   if(!r){html+=`<div class="data-card"><h4>${v}</h4>${kv('Kaynak','DOĞRULANAMADI')}${kv('Gerçekleşmiş olay','—')}</div>`;continue}
   const age=r.metadata?.market_quote_age_seconds;
   html+=`<div class="data-card"><div class="engine-head"><h4>${ESC(v)}</h4><span class="inline-status">READ_ONLY_LIVE</span></div>
    ${kv('Son gerçekleşmiş rate',pc(r.last_realized_rate_fraction))}
    ${kv('Gerçekleşme tarihi',dt(r.last_realized_time_utc))}
    ${kv('Funding aralığı',num(r.interval_hours,1)+' saat')}
    ${kv('Sonraki olay zamanı',dt(r.next_funding_time_utc))}
    ${kv('Günlük koşullu hız (geçmiş)',pc(r.daily_observed_run_rate_fraction))}
    ${kv('Anlık gösterge (gerçekleşmemiş)',pc(r.indicative_rate_fraction))}
    ${kv('Oran birimi',r.rate_unit)}
    ${kv('Kaynak quote yaşı',age===null||age===undefined?'DOĞRULANMADI':num(age,0)+' sn')}
    ${kv('Sözleşme çarpanı',r.metadata?.contract_multiplier??'—')}
    <div class="tiny">Ticaret / hesap erişimi: doğrulanmadı. Kaynak: ${ESC(r.interval_source)}. Komisyon ve margin gereksinimleri: bilinmiyor.</div></div>`;
  }
  html+='</div>';
  if(arr.length===2){
   const ba=arr.find(x=>x.venue==='BINANCE'),ok=arr.find(x=>x.venue==='OKX');
   const y1=ba.historical_events.map(x=>x.rate_fraction),y2=ok.historical_events.map(x=>x.rate_fraction);
   html+=`<div class="chart-wrap"><div class="chart-head"><b>Son gerçekleşmiş funding olayları</b><span style="color:#74e1c3">● Binance</span><span style="color:#7daefa">● OKX</span></div>${svgSeries(y1,y2)}<div class="chart-foot"><span>Olay başına oran · iki venue için settlement zamanı farklı olabilir</span><span>Son 12 olay</span></div></div>`;
  }
  html+=`<div class="info-panel warn"><b>NET FIRSAT: DOĞRULANMADI.</b> ${ESC(cmp?.reason??'İki kaynak doğrulanamadı.')} ${cmp?.run_rate_diff_fraction!==null&&cmp?.run_rate_diff_fraction!==undefined?`Normalize geçmiş fark: ${pc(cmp.run_rate_diff_fraction)} / 24 saat koşullu hız.`:''} Bu karşılaştırmadan kesin kazanç, uygulanabilir short veya paper fill çıkarılmaz.</div>`;
 }
 html+=`<h4 class="section-mini">İşlem engelleri</h4><div class="row-of-two"><div class="data-card">${kv('Maker / taker ücret','DOĞRULANMADI')}${kv('İki yönlü hedge','DOĞRULANMADI')}${kv('Baz / marjin / liquidation','DOĞRULANMADI')}</div><div class="data-card">${kv('Türkiye hesap erişimi','DOĞRULANMADI')}${kv('Paper dolumu','PAPER_NO_FILL')}${kv('Net getiri','HESAPLANAMAZ')}</div></div>`;
 return html;
}
function renderStable(){
 const s=report?.stablecoin;
 if(!s)return empty('İki-venue L2 taraması doğrulanmadı','USDC/USDT emir defteri karşılaştırması yalnız gerçek Binance ve OKX kaynakları doğrulandığında görünür. Eksik veri yüzünden örnek fiyat kullanılmaz.');
 const q=s.best_quotes||{};
 let html=info('USDC/USDT fiyat karşılaştırması USD nakit arbitrajı değildir. Binance spot REST depth sonucunda borsa kaynak zaman damgası bulunmadığından quote eşzamanlılığı doğrulanmamıştır.',true);
 html+='<div class="row-of-two">';
 for(const v of ['BINANCE','OKX']){
   const x=q[v]||{};
   html+=`<div class="data-card"><h4>${v} · USDC/USDT</h4>${kv('Bid / satış',num(x.bid,5))}${kv('Ask / alış',num(x.ask,5))}${kv('Bid derinlik ilk kademe',num(x.bid_qty_base,2)+' USDC')}${kv('Ask derinlik ilk kademe',num(x.ask_qty_base,2)+' USDC')}${kv('Kaynak zaman damgası',v==='BINANCE'?'YOK':dt(s.okx_book_asof_utc))}</div>`;
 }
 html+='</div><h4 class="section-mini">İki yönlü sepet kotasyonu · 1.000 USDC ekranı</h4><div class="row-of-two">';
 for(const r of s.routes||[]){
  html+=`<div class="data-card"><h4>${ESC(r.buy_venue)} → ${ESC(r.sell_venue)}</h4>${kv('Alış VWAP',num(r.buy_vwap,6))}${kv('Satış VWAP',num(r.sell_vwap,6))}${kv('Brüt kotasyon farkı',r.gross_spread_bps===null?'DERİNLİK YETERSİZ':num(r.gross_spread_bps,2)+' bps')}${kv('Net fark','BİLİNMİYOR')}${kv('Gerçek fill','YOK')}${kv('Durum',r.status)}</div>`;
 }
 html+='</div>'+info('İtfa yetkisi, zincir/kontrat eşdeğerliği, komisyon, transfer rotası, anlık eşzamanlı dolum ve USDT değer riski doğrulanmadan izleme dışında sonuç üretilemez.',true);
 return html;
}
const extra={
 'A1':'Aynı sektör / piyasa / para birimi evreni, split/temettü düzeltilmiş fiyat, borrow erişimi ve Engle–Granger + FDR kontrolü gerekir. Formation, validation ve OOS ayrı tutulacak.',
 'A2':'ETF kıyaslamasında aynı endeks, replikasyon, gider oranı, döviz, temettü ve NAV gecikmesi doğrulanmalı. AP yaratma/itfa arbitrajı varsayılmaz.',
 'A3':'Çok değişkenli Johansen rank / deterministik terim / walk-forward + dış örneklem gerekir. Başlangıç paketindeki residual ADF yalnız SCREEN_ONLY idi.',
 'T0':'ISIN, clean/dirty fiyat, kupon, vadeler, modified duration/convexity, teminat haircut, repo başlangıç/bitiş valörü ve dealer erişimi gerekir. Yield – repo faiz farkı kilitli kâr değildir.'
};
function renderResearch(code){
 const s=(report?.strategies||[]).find(x=>x.id===code);
 return empty('Erişim ve araştırma doğrulaması bekleniyor',s?.reason||'Bu strateji için henüz lisanslı gerçek veri yok.')+
 `<div class="info-panel">${ESC(extra[code]||'Canlı veri / test sonucu olmadan pozisyon hesaplanmaz.')}</div><div class="row-of-two" style="margin-top:14px"><div class="data-card">${kv('Veri kaynağı','NOT_CONNECTED')}${kv('Formation dönemi','BAŞLATILMADI')}${kv('Dış örneklem','BAŞLATILMADI')}${kv('Kaynak zamanı','—')}</div><div class="data-card">${kv('Kısa satış erişimi','DOĞRULANMADI')}${kv('Maliyet / komisyon','BİLİNMİYOR')}${kv('İleri paper','PAPER_NO_FILL')}${kv('Net PnL','HESAPLANAMAZ')}</div></div>`;
}
function renderWorkspace(){
 $('workspace-title').textContent=titles[activeTab];
 const mode=(report?.strategies||[]).find(s=>s.id===activeTab)?.data_label||'NOT_CONNECTED';
 $('workspace-mode').textContent=mode;
 document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.tab===activeTab)));
 $('work-content').innerHTML=activeTab==='B1'?renderFunding():activeTab==='B2'?renderStable():renderResearch(activeTab);
}
function renderLogs(){
 const all=report?.recent_observations||[];
 const rows=activeFilter==='ALL'?all:all.filter(e=>e.kind===activeFilter);
 $('log-total').textContent=rows.length;
 document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('active',x.dataset.filter===activeFilter));
 $('log-rows').innerHTML=rows.length ? rows.slice(0,45).map(e=>`<tr><td>${ESC(dt(e.time_utc))}</td><td>${ESC(e.strategy)}</td><td><span class="event-status ${e.kind==='WATCH_ONLY'?'watching':e.kind==='SOURCE_ERROR'?'error':''}">${ESC(e.kind)}</span></td><td>${ESC([e.venue,e.symbol].filter(Boolean).join(' / ')||'—')}</td><td>${ESC(e.reason)}</td></tr>`).join('') : '<tr><td colspan="5">Bu filtrede son 14 günden kayıt yok. İlk tarama bekleniyor olabilir.</td></tr>';
}
function selectTab(next, scroll=false){
 if(!titles[next])return;
 activeTab=next;renderStrategies();renderWorkspace();
 if(scroll)$('arastirma').scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth'});
}
function renderAll(){renderHealth();renderBudget();renderStrategies();renderWorkspace();renderLogs()}
async function load(){
 $('refresh').disabled=true;
 try{
  const response=await fetch(`report.json?v=${Date.now()}`,{cache:'no-store'});
  if(!response.ok)throw new Error('HTTP '+response.status);
  const data=await response.json();
  if(!Array.isArray(data.strategies)||data.strategies.length!==6||data.live_orders_enabled!==false)throw new Error('Rapor güvenlik sözleşmesi geçersiz');
  report=data;renderAll();
 }catch(err){
  if(!report){$('health-title').textContent='Yayın verisi açılamadı';$('health-description').textContent='Rapor okunamadı: '+err.message;
    $('work-content').innerHTML=empty('Rapor bağlantısı yok','Önce python -m alti.worker, sonra yerel sunucu veya GitHub Pages yayını gerekiyor.');}
  else{$('global-warning').textContent='Yeni rapor yüklenemedi; görünen son snapshot geçmişe ait olabilir. Güncel işlem kararı için kullanmayın.';}
 }finally{$('refresh').disabled=false}
}
$('refresh').addEventListener('click',load);
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>selectTab(b.dataset.tab)));
document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{activeFilter=b.dataset.filter;renderLogs()}));
load();

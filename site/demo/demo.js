/* ALTI Demo V2: static educational illustration. No endpoints, credentials, order APIs or synthetic fills. */
(() => {
'use strict';
const $ = id => document.getElementById(id);
const fmt = (n,d=0) => Number(n).toLocaleString('tr-TR',{minimumFractionDigits:d,maximumFractionDigits:d});
const lira = n => '₺'+fmt(n);
const esc = x => String(x ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const colors = ['#70dfc4','#88aafa','#edbc83'];
const N=33, xs=Array.from({length:N},(_,i)=>i);
const synth=(base,drift,wave,phase=0)=>xs.map(i=>base+drift*i+Math.sin(i*.47+phase)*wave+Math.cos(i*.19+phase)*wave*.43);
const p1=synth(100,.22,1.9),p2=synth(100,.20,2.1,.4);
const spread=xs.map(i=>1.65*Math.sin(i*.44)+.27*Math.cos(i*.97)-.055*i);
const fundingA=xs.map(i=>.014+.009*Math.sin(i*.62)+.002*Math.cos(i*.25));
const fundingB=xs.map(i=>.009+.006*Math.sin(i*.58+.8)-.002*Math.cos(i*.37));
const stableA=xs.map(i=>.99984+.00010*Math.sin(i*.53)+.000045*Math.cos(i*.24));
const stableB=xs.map(i=>1.00006+.00009*Math.cos(i*.51+.6)-.00004*Math.sin(i*.19));
const assets={
 A1:{engine:'A',name:'Hisse pairs trading',short:'İki hissede ortak trend / geçici ayrışma',title:'Hisse pairs · KO / PEP',blurb:'Normalize fiyatlar, formation hedge oranı ve artığın geri dönme hipotezi.',status:'WATCH_ONLY',badge:'İZLE',
 chartTitle:'Normalize fiyat endeksi',plotNote:'Örnek log-regresyon ve z-score; gerçek hisse fiyatı, gerçek p-değeri veya gerçekleşmiş test değildir.',
 labels:['KO · sentetik','PEP · sentetik'],series:[p1,p2],residual:spread,secondaryLabel:'Hedge residual · örnek z-score',
 metrics:[['Örnek z-score','−1,68','Giriş sinyali değildir'],['Formation','120 seans','Varsayımsal'],['OOS','20 seans','Kurgusal, doğrulanmadı']],
 fields:[['Evren','Aynı sektör · ABD'],['Araştırma','EG + ADF + FDR'],['Formation / test','120 / 40 / 20'],['Short erişimi','DOĞRULANMADI'],['Veri zamanı','SENTETİK'],['Paper durumu','PAPER_NO_FILL']],
 rationale:'Benzer ekonomik faktörlere bağlı iki fiyatın, tek başına yüksek korelasyon değil kalıcı ilişki ve dış örneklemle sınanacak geçici ayrışması.',
 blockers:'Gerçek adjusted close, kurumsal olay, ödünç/short uygunluğu, maliyet ve ardışık zamanlı doldurulabilir quote yok.',
 costs:[['Spread (örnek)','5 bps'],['Komisyon (örnek)','7 bps'],['Borrow / slippage','Bilinmiyor']],gross:31,frictionBase:12},
 A2:{engine:'A',name:'ETF–ETF göreli değer',short:'Benzer endekslerin maliyetli fiyat farkı',title:'ETF göreli değer · SPY / IVV',blurb:'Benchmark, NAV, gider oranı, para birimi ve dağıtımları eşleştir.',status:'REJECTED',badge:'RET',
 chartTitle:'Endekse normalleştirilmiş ETF fiyatları',plotNote:'ETF isimleri gerçek ürün örnekleridir; grafikte gösterilen fiyatların tamamı sentetiktir.',
 labels:['SPY · sentetik','IVV · sentetik'],series:[synth(100,.17,1.30,.25),synth(100,.168,1.36,.42)],residual:xs.map(i=>.17*Math.sin(i*.72)-.08*Math.cos(i*.28)),secondaryLabel:'Göreli fark · baz puan (örnek)',
 metrics:[['Göreli ekran farkı','8 bps','İllüstratif'],['Net toplam gider','Bilinmiyor','Gerçek fon verisi yok'],['NAV gecikmesi','Doğrulanmadı','Trade-ready değil']],
 fields:[['Endeks eşleşmesi','Doğrulanmalı'],['Replikasyon','Doğrulanmalı'],['Temettü / döviz','Düzeltme gerekir'],['AP yaratma / itfa','Yetki varsayılmaz'],['Piyasa verisi','SENTETİK'],['Paper durumu','PAPER_NO_FILL']],
 rationale:'Benzer dayanaklı fonlarda fiyat, toplam gider, nakit dağıtımı ve NAV kaynaklı sapmaları ayrıştırıp ekonomik anlamlı net göreli farkı araştırır.',
 blockers:'İki ETF aynı şey değildir; gerçek bid/ask, açık pozisyon / short erişimi, ex-dividend takvimi ve NAV güncelliği yok.',
 costs:[['İki yönlü spread','6 bps'],['Komisyon (örnek)','4 bps'],['Borç / temettü','Bilinmiyor']],gross:8,frictionBase:10},
 A3:{engine:'A',name:'İstatistiksel sepet',short:'Çok değişkenli cointegration ekranı',title:'İstatistiksel sepet · XLF / KBE / KRE',blurb:'Birden fazla bileşenin ortak denge ilişkisine dair ekran hipotezi.',status:'WATCH_ONLY',badge:'İZLE',
 chartTitle:'Sepet bileşenleri · normalize seri',plotNote:'Üç varlık birlikte gösterilir; Johansen rank, deterministik terim ve OOS sonucu doğrulanmış değildir.',
 labels:['XLF · sentetik','KBE · sentetik','KRE · sentetik'],series:[synth(100,.14,1.8,0),synth(100,.145,2.1,.6),synth(100,.135,2.4,1.15)],residual:xs.map(i=>1.05*Math.sin(i*.43+.1)+.56*Math.sin(i*.19)),secondaryLabel:'Sepet residual · yalnız SCREEN_ONLY',
 metrics:[['Sepet bileşeni','3','Örnek evren'],['Johansen rank','Bilinmiyor','CONFIRMED değil'],['OOS kontrolü','Yok','Model dondurulmadı']],
 fields:[['Ön eleme','SCREEN_ONLY'],['Test ailesi','Johansen + OOS'],['Rank seçimi','YAPILMADI'],['Faktör overlap','Risk kapısı'],['Veri zamanı','SENTETİK'],['Paper durumu','PAPER_NO_FILL']],
 rationale:'Üçlü ilişki iki ayrı pair olarak sayılmaz. Ortak faktör ve kovaryans, tekrar eden kısa pozisyonlar ve rank seçim hatalarıyla incelenir.',
 blockers:'Johansen rank, rejim kırılması, bakış ileri hatası, gerçek sepet lot büyüklüğü ve borrow bulunmadığından trade-ready değildir.',
 costs:[['Üç bacak spread','10 bps'],['Komisyon (örnek)','8 bps'],['Hedge / borrow','Bilinmiyor']],gross:24,frictionBase:18},
 B1:{engine:'B',name:'Funding interval farkı',short:'Perpetual fonlama olayları / zaman farkı',title:'Perpetual funding · BTCUSDT',blurb:'Gerçekleşmiş funding ile tahmini oranı ayırarak iki venue ve ödeme zamanını karşılaştır.',status:'WATCH_ONLY',badge:'İZLE',
 chartTitle:'Fonlama olay oranları (%)',plotNote:'Tüm rakamlar sentetiktir. Olay aralıkları ve settlement takvimleri eşit kabul edilmez.',
 labels:['Venue A · sentetik','Venue B · sentetik'],series:[fundingA,fundingB],residual:fundingA.map((a,i)=>(a-fundingB[i])),secondaryLabel:'Normalize fark · puan (ekran)',
 metrics:[['Son örnek A','%0,014','Ödeme gerçekleşmedi'],['Son örnek B','%0,009','Ödeme gerçekleşmedi'],['İleri net gelir','UNKNOWN','İki hedge de eksik']],
 fields:[['Oran birimi','Fraction → yüzde'],['Olay aralığı','8s vs 4s · örnek'],['Funding zamanı','Eşlenebilir değil'],['Realized / estimated','AYRI'],['Veri zamanı','SENTETİK'],['Paper durumu','PAPER_NO_FILL']],
 rationale:'Yalnız gerçekleşmiş event-based fonlama oranlarını aynı takvim bazında görüntüleyip farklı sıklıktaki sözleşmelerin görünür farkını araştırır.',
 blockers:'Gerçek borsa erişimi, güncel ücret tarifi, iki tarafa da margin, likidite, likidasyon tamponu ve zaman uyumlu hedge doğrulanmadı.',
 costs:[['Açılış + kapanış','8 bps'],['Basis / slippage','Bilinmiyor'],['Kredi / margin riski','Bilinmiyor']],gross:11,frictionBase:8},
 B2:{engine:'B',name:'Stablecoin fiyat sapması',short:'Peg, iki yönlü kotasyon ve L2 derinlik',title:'Stablecoin · USDC / USDT',blurb:'Bid / ask, emir defteri ve itfa erişimi olmadan fiyat sapması arbitraj değildir.',status:'REJECTED',badge:'RET',
 chartTitle:'İki venue · örnek bid / ask izi',plotNote:'Bid/ask değerleri ve USDC/USDT eşdeğerlik varsayımı yalnız sentetik görselleştirmedir.',
 labels:['Venue A · sentetik','Venue B · sentetik'],series:[stableA,stableB],residual:stableA.map((a,i)=>(stableB[i]-a)*10000),secondaryLabel:'Kurgusal peg farkı · bps',
 metrics:[['Örnek alış','0,99986','USDT / USDC'],['Örnek satış','1,00004','USDT / USDC'],['L2 derinlik','Yetersiz','Varsayımsal 1.000 USDC']],
 fields:[['Token / issuer','Doğrulanmalı'],['Chain / contract','Doğrulanmalı'],['L2 / quote ts','Sentetik'],['İtfa yetkisi','DOĞRULANMADI'],['Transfer rotası','DOĞRULANMADI'],['Paper durumu','PAPER_NO_FILL']],
 rationale:'İki platformda aynı ekonomik enstrümanın aynı anda işlem yapılabilir karşı bid/ask fiyatları ve boyutları incelenir.',
 blockers:'Eşleşen kontrat, itfa, zincir-transfer ve derinlik koşulları yok. %2 peg sapması %2 garantili kazanç değildir.',
 costs:[['Cross-book spread','5 bps'],['Komisyon (örnek)','8 bps'],['Transfer / redemption','Bilinmiyor']],gross:9,frictionBase:13},
 T0:{engine:'C',name:'Tahvil–repo finansman farkı',short:'Tahvil finansmanı, haircut ve faiz şoku',title:'Tahvil–repo · örnek TRY yapı',blurb:'Teminat haircut ve duration şoku dahil olmadan yıllık faiz farkı kazanç değildir.',status:'REJECTED',badge:'ERİŞİM YOK',
 chartTitle:'Örnek tahvil YTM / repo oranı (%)',plotNote:'Gerçek ISIN ve işlem yapılabilir dealer kotasyonu bulunmaz. YTM − repo farkı kilitlenmiş getiri değildir.',
 labels:['Tahvil YTM · sentetik','Repo · sentetik'],series:[synth(33,-.031,.66,.3),synth(32.4,-.02,.51,.65)],residual:xs.map(i=>.6-.011*i+.30*Math.sin(i*.25)),secondaryLabel:'YTM − repo · örnek puan',
 metrics:[['Örnek vade','35 gün','Gerçek repo kotasyonu yok'],['Duration','3,1','Temsili yıldır'],['Haircut','%10','Dealer onaysız']],
 fields:[['ISIN','YOK / ÖRNEK'],['Dirty / clean','Bilinmiyor'],['Modified duration','3,1 · sentetik'],['Konveksite','13 · sentetik'],['Repo erişimi','DOĞRULANMADI'],['Paper durumu','PAPER_NO_FILL']],
 rationale:'Tahvil nakit akışı, dirty/clean fiyat, repo roll, haircut finansman kapasitesi ve faiz şoku birlikte değerlendirilir.',
 blockers:'Valör ve dealer erişimi yok; YTM finansman spreadi risksiz değil. Günlük fiyat marjı ve teminat çağrısı hesaplanmadan uygulanamaz.',
 costs:[['Repo başlangıç/bitiş','Doğrulanmalı'],['Margin / haircut','%10 · örnek'],['Likidite / roll','Bilinmiyor']],gross:60,frictionBase:20}
};
const engineNames={A:'İSTATİSTİKSEL GÖRELİ DEĞER',B:'KRİPTO FARKLARI',C:'SABİT GETİRİLİ FİNANSMAN'};
const keys=['A1','A2','A3','B1','B2','T0'];
const state={active:'B1',engine:'ALL',chart:'primary',friction:12,period:14,status:'ALL',reserve:40,risk:25};
function strategyCards(){
 const root=$('strategyCards');root.innerHTML=keys.map(k=>{const a=assets[k];return `<button type="button" class="strategy-card${k===state.active?' selected':''}" data-strategy="${k}" aria-pressed="${String(k===state.active)}" ${state.engine!=='ALL'&&a.engine!==state.engine?'hidden':''}><div class="strategy-header"><span class="strategy-code">${k} / MOTOR ${a.engine}</span><span class="state ${a.status==='WATCH_ONLY'?'watch':'blocked'}">${a.badge}</span></div><h3>${esc(a.name)}</h3><p>${esc(a.short)}</p><div class="strategy-bottom"><span>SYNTHETIC / NO FILL</span><span aria-hidden="true">↗</span></div></button>`}).join('');
 root.querySelectorAll('[data-strategy]').forEach(b=>b.addEventListener('click',()=>{state.active=b.dataset.strategy;state.chart='primary';renderTerminal();strategyCards();if(window.innerWidth<700)$('terminal').scrollIntoView({block:'start',behavior:window.matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'})}));
}
function svgChart(a){
 const lines=state.chart==='primary'?a.series:[a.residual];
 const width=760,height=270,L=48,R=16,T=19,B=36,w=width-L-R,h=height-T-B;
 let values=lines.flat().filter(Number.isFinite);if(!values.length) return '';
 let min=Math.min(...values),max=Math.max(...values);let range=Math.max((max-min),.000005),buffer=range*.12;min-=buffer;max+=buffer;range=max-min;
 const x=i=>L+i*w/(N-1),y=v=>T+h-(v-min)/range*h;
 const isSmall=Math.abs(max)<.1;
 const formatAxis=v=>isSmall?fmt(v,4):Math.abs(v)<10?fmt(v,2):fmt(v,1);
 let svg=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(state.chart==='primary'?a.chartTitle:a.secondaryLabel)} - tüm çizgiler sentetiktir"><defs><linearGradient id="chartGlow" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#70dfc4" stop-opacity=".15"/><stop offset="1" stop-color="#70dfc4" stop-opacity="0"/></linearGradient></defs>`;
 for(let i=0;i<5;i++){let pos=T+i*h/4;svg+=`<line x1="${L}" y1="${pos}" x2="${width-R}" y2="${pos}" stroke="#314354" stroke-dasharray="${i===4?'0':'3 6'}" opacity=".65"/><text x="${L-9}" y="${pos+4}" font-size="10" fill="#8094a8" text-anchor="end">${formatAxis(max-i*range/4)}</text>`}
 for(let i=0;i<5;i++){let xi=L+i*w/4;svg+=`<text x="${xi}" y="${height-9}" font-size="10" fill="#8499aa" text-anchor="middle">T${Math.round(i*(N-1)/4)+1}</text>`}
 if(min<0&&max>0){const zero=y(0);svg+=`<line x1="${L}" y1="${zero}" x2="${width-R}" y2="${zero}" stroke="#e4ae82" stroke-width="1" opacity=".5"/>`}
 lines.forEach((series,i)=>{let points=series.map((v,j)=>[x(j),y(v)]);let color=state.chart==='primary'?colors[i]:colors[0];let d=points.map((p,j)=>`${j?'L':'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
 if(i===0){const fill=d+` L${x(N-1)},${T+h} L${L},${T+h} Z`;svg+=`<path d="${fill}" fill="url(#chartGlow)"/>`}
 svg+=`<path d="${d}" fill="none" stroke="${color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/><circle cx="${x(N-1)}" cy="${y(series[N-1])}" r="4.2" fill="${color}" stroke="#0a1520" stroke-width="2"/>`;
 });
 return svg+'</svg>';
}
function renderTerminal(){
 const a=assets[state.active];$('terminalEngine').textContent=`MOTOR ${a.engine} / ${engineNames[a.engine]}`;$('terminalTitle').textContent=a.title;$('terminalBlurb').textContent=a.blurb;$('terminalVerdict').textContent=a.status;
 $('plotEyebrow').textContent=`${state.active} / SENTETİK ARAŞTIRMA PENCERESİ`;$('plotTitle').textContent=state.chart==='primary'?a.chartTitle:a.secondaryLabel;$('plotNote').textContent=a.plotNote;
 $('plotLegend').innerHTML=(state.chart==='primary'?a.labels:[a.secondaryLabel]).map((n,i)=>`<span style="--c:${colors[i]}">${esc(n)}</span>`).join('');$('chart').innerHTML=svgChart(a);
 $('instrumentMetrics').innerHTML=a.metrics.map(m=>`<div class="mini-metric"><small>${esc(m[0])}</small><strong>${esc(m[1])}</strong><span>${esc(m[2])}</span></div>`).join('');
 $('modelRationale').textContent=a.rationale;$('modelBlockers').textContent=a.blockers;
 $('detailFields').innerHTML=a.fields.map(([k,v])=>`<div class="field"><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('');
 $('costLines').innerHTML=a.costs.map(([k,v])=>`<div class="cost-line"><span>${esc(k)}</span><b>${esc(v)}</b></div>`).join('');
 document.querySelectorAll('[data-chart]').forEach(b=>{const active=b.dataset.chart===state.chart;b.classList.toggle('selected',active);b.setAttribute('aria-pressed',String(active))});
 renderImpact();
}
function renderImpact(){
 const a=assets[state.active];const cost=a.frictionBase+state.friction,delta=a.gross-cost,box=$('impactBox');$('frictionValue').textContent=state.friction+' bps';
 box.classList.toggle('bad',delta<=0);
 box.innerHTML=`<strong>${delta<=0?'Maliyet ekranı: RED':'Maliyet ekranı: İNCELE'}</strong><div>Örnek sapma ${a.gross} bps − şablon maliyeti ${a.frictionBase} bps − ek sürtünme ${state.friction} bps = <b>${delta>0?'+':''}${delta} bps</b>.</div><div style="margin-top:5px">Bu hesap <b>net getiri, işlem sinyali veya paper kârı değildir.</b> Quote, hedge ve erişim kapıları hâlâ kapalı.</div>`;
}
function renderRisk(){
 const c=150000,reserve=c*state.reserve/100,limit=c*state.risk/10000,cap=Math.min(c*.20,c-reserve);
 $('topCapital').textContent=lira(c);$('topReserve').textContent=lira(reserve);$('topRisk').textContent=lira(limit);$('topGross').textContent=lira(cap);
 $('reserveMoney').textContent=lira(reserve);$('availableMoney').textContent=lira(c-reserve);$('reserveBar').style.width=state.reserve+'%';$('freeBar').style.width=(100-state.reserve)+'%';$('reservePct').textContent='%'+state.reserve;$('riskPct').textContent='%'+fmt(state.risk/100,2);
 $('reserveDesc').textContent='%'+state.reserve+' koruma varsayımı';$('riskDesc').textContent='Kasanın %'+fmt(state.risk/100,2)+'\'i';$('maxExposure').textContent=lira(cap);
 const shares=[['A','İstatistiksel göreli değer',35,'#81a9fa'],['B','Kripto farkları',40,'#6cdbc4'],['C','Sabit getirili finansman',25,'#d8b17d']];
 $('engineExposure').innerHTML=shares.map(([k,name,p,color])=>`<div class="exposure-row"><div class="exposure-header"><b>MOTOR ${k}</b><span>${name} · ${p}%</span></div><div class="exposure-track"><div class="exposure-fill" style="width:${p}%;--bar:${color}"></div></div><div style="font-size:10px;color:#829aac;margin-top:6px">Temsili risk payı: ${lira(limit*p/100)} / hipotez tavanı</div></div>`).join('');
}
const eventTemplates=[
 ['B1','BTCUSDT · Venue A/B','WATCH_ONLY','Funding interval aynı takvimde eşleşmedi; takip açık.'],
 ['A1','KO / PEP','REJECTED','Gerçek ödünç/short erişimi doğrulanmadı.'],
 ['B2','USDC/USDT','SOURCE_ERROR','Emir defteri boyutu ve quote zamanı eksik.'],
 ['A2','SPY / IVV','REJECTED','Gider oranı ve spread net avantajı aşabilir.'],
 ['A3','XLF / KBE / KRE','WATCH_ONLY','Johansen rank doğrulaması ve OOS gerekli.'],
 ['T0','Tahvil / repo','REJECTED','Dealer kotasyonu ve haircut bilgisi yok.'],
 ['B1','ETHUSDT · Venue A/B','PAPER_NO_FILL','Sonraki gerçekleşebilir quote olmadan fill yok.'],
 ['A1','KO / PEP','WATCH_ONLY','Örnek residual rejim değişimi için izlemede.'],
 ['B2','USDC/USDT','REJECTED','Peg farkı iki yönlü derinlik maliyetinden küçük.'],
 ['A3','XLF / KBE / KRE','REJECTED','Faktör örtüşmesi ile risk tavanı aşılıyor.'],
 ['T0','Tahvil / repo','SOURCE_ERROR','Gerçek temiz/kirli fiyat feedi bulunmuyor.']
];
const records=Array.from({length:30},(_,i)=>{const e=eventTemplates[(i*7+3)%eventTemplates.length];let date=new Date(Date.UTC(2026,9,16-i,12,0,0));return {date:date.toISOString().slice(0,10),strategy:e[0],instrument:e[1],status:e[2],reason:e[3]}});
const statusNames={WATCH_ONLY:'İZLE',REJECTED:'REDDEDİLDİ',SOURCE_ERROR:'VERİ HATASI',PAPER_NO_FILL:'PAPER_NO_FILL'};
function renderJournal(){
 const source=records.slice(0,state.period),visible=state.status==='ALL'?source:source.filter(r=>r.status===state.status);
 $('journalTotal').textContent=visible.length;$('journalRejected').textContent=visible.filter(r=>r.status==='REJECTED'||r.status==='SOURCE_ERROR').length;
 $('journalCaption').textContent=`Örnek zaman aralığı: 16.10.2026 tarihinden geriye ${state.period} gün · ${visible.length} satır · güncel tarama değil.`;
 $('journalBody').innerHTML=visible.length?visible.map(r=>`<tr><td>${esc(r.date)}</td><td><b>${esc(r.strategy)}</b></td><td>${esc(r.instrument)}</td><td><span class="table-status ${esc(r.status)}">${esc(statusNames[r.status])}</span></td><td>${esc(r.reason)}</td></tr>`).join(''):'<tr><td colspan="5">Bu filtrede sentetik örnek olay yok.</td></tr>';
 document.querySelectorAll('[data-period]').forEach(b=>{const on=Number(b.dataset.period)===state.period;b.classList.toggle('selected',on);b.setAttribute('aria-pressed',String(on))});
}
function bind(){
 $('engineFilters').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{state.engine=b.dataset.engine;const a=assets[state.active];if(state.engine!=='ALL'&&a.engine!==state.engine){state.active=keys.find(k=>assets[k].engine===state.engine);state.chart='primary'};document.querySelectorAll('[data-engine]').forEach(x=>{let on=x.dataset.engine===state.engine;x.classList.toggle('selected',on);x.setAttribute('aria-pressed',String(on))});strategyCards();renderTerminal()}));
 document.querySelectorAll('[data-chart]').forEach(b=>b.addEventListener('click',()=>{state.chart=b.dataset.chart;renderTerminal()}));
 $('friction').addEventListener('input',e=>{state.friction=Number(e.target.value);renderImpact()});
 $('reserveSlider').addEventListener('input',e=>{state.reserve=Number(e.target.value);renderRisk()});
 $('riskSlider').addEventListener('input',e=>{state.risk=Number(e.target.value);renderRisk()});
 $('periodFilters').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{state.period=Number(b.dataset.period);renderJournal()}));
 $('statusFilter').addEventListener('change',e=>{state.status=e.target.value;renderJournal()});
}
strategyCards();renderTerminal();renderRisk();renderJournal();bind();
})();

"""Build an explicitly synthetic/offline example research dashboard."""
from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path

import numpy as np

from .core import (StrategyFinding, formation_zscore, basket_residual_diagnostic,
                   funding_interval_comparison, stablecoin_quote_screen,
                   bond_repo_screen, portfolio_risk_preview)

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output'


def fake_series(seed=20261016, n=300):
    """Non-market artificial sample. No live API or downloadable price claim."""
    rng=np.random.default_rng(seed)
    market=np.cumsum(rng.normal(0,.013,n))
    transient=np.zeros(n)
    for i in range(1,n):transient[i]=.78*transient[i-1]+rng.normal(0,.012)
    x=100*np.exp(market)
    y=83*np.exp(1.03*market+transient)
    etf_1=50*np.exp(market*.88+rng.normal(0,.004,n))
    etf_2=52*np.exp(market*.90+rng.normal(0,.005,n))
    bx=27*np.exp(market*.55+rng.normal(0,.004,n))
    by=42*np.exp(market*.32+rng.normal(0,.004,n))
    bz=74*np.exp(.65*np.log(bx/27)+.50*np.log(by/42)+transient*.28)
    return x,y,etf_1,etf_2,bx,by,bz


def analyze():
    x,y,e1,e2,bx,by,bz=fake_series()
    stat1=formation_zscore(y,x)
    stat2=formation_zscore(e2,e1)
    basket=basket_residual_diagnostic(bz,[bx,by])
    funding=funding_interval_comparison(venue_a='DEMO EXCHANGE A',a_rate=.00012,a_interval_hours=1,
                                       venue_b='DEMO EXCHANGE B',b_rate=.00032,b_interval_hours=8,
                                       quote_age_seconds=20)
    stable=stablecoin_quote_screen(buy_ask=.9990,sell_bid=.9998,buy_ask_size=25000,
                                    sell_bid_size=20000,notional_usd=5000,fee_bps_total=8,
                                    slippage_bps_buffer=6,quote_age_seconds=2)
    bond=bond_repo_screen(annual_bond_yield_pct=34,annual_repo_rate_pct=31,
                          duration_years=3.4,yield_shock_pct_points=1.5,
                          repo_haircut_pct=12,dealer_access=False)
    findings=[
       StrategyFinding('pairs','Borsa hisseleri pairs trading','A — Statistical',stat1['status'],
                       'Demo formation co-integration only; does not verify shorting access or executable trade.',stat1),
       StrategyFinding('etf','ETF–ETF göreli değer','A — Statistical',stat2['status'],
                       'Demo ETF-like synthetic samples; relative spread, not AP creation/redemption arbitrage.',stat2),
       StrategyFinding('basket','İstatistiksel sepet / cointegration','A — Statistical',basket['status'],
                       'Only residual ADF screen, NOT a formal Johansen cointegration or validated multi-leg execution.',basket),
       StrategyFinding('funding','Perpetual funding interval farkı','B — Crypto',funding['status'],
                       'Historical/illustrative event rate normalization only, no guaranteed future payments.',funding),
       StrategyFinding('stable','Stablecoin fiyat sapması','B — Crypto',stable['status'],
                       'Quote comparison, no simultaneous fill or guaranteed redemption.',stable),
       StrategyFinding('bond','Tahvil–repo finansman farkı','C — Fixed Income',bond['status'],
                       'No dealer access or executable bond/repo quotes: observational proxy only.',bond),
    ]
    data={
        'generated_at_utc':datetime.now(timezone.utc).isoformat(),
        'mode':'SYNTHETIC_DEMO_ONLY',
        'market_data_connected':False,
        'live_orders_enabled':False,
        'verified_pnl':None,
        'paper_equity_curve':None,
        'portfolio':portfolio_risk_preview(capital_try=150_000,reserve_pct=40,
                                           paper_trade_risk_pct=.25,max_exposure_pct=20),
        'findings':[f.to_dict() for f in findings],
        'limitations':['No OHLC executable fills','No brokers/bank endpoints connected',
                       'No multiple-testing correction','No orders and no credentials',
                       'Synthetic price samples only','Pair/basket findings are statistical diagnostics only',
                       'Fees and tax are not represented in pair/ETF diagnostics']
    }
    return data


def build_html(data):
    finding_cards='\n'.join(
        '<article class="card"><div class="line"><span class="tag">'+escape(f['engine'])+'</span><span class="status">'+escape(f['status'])+'</span></div>'+
        '<h2>'+escape(f['strategy'])+'</h2><p>'+escape(f['explanation'])+'</p><details><summary>Analiz metrikleri (demo)</summary><pre>'+escape(json.dumps(f['detail'],ensure_ascii=False,indent=2))+'</pre></details></article>'
        for f in data['findings'])
    return '''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ALTI | Research Lab</title>
<style>body{font-family:Inter,system-ui,Arial,sans-serif;background:#0e1724;color:#e6edf3;margin:0;line-height:1.6}main{max-width:1050px;margin:auto;padding:35px 20px 80px}h1{font-size:clamp(32px,5vw,60px);line-height:1.05;margin:23px 0}h2{font-size:19px}p,small{color:#a4b4c4}small,.kicker,.tag{letter-spacing:.1em;font-size:11px}.kicker{color:#f2c086;font-weight:800}.warning{border:1px solid #daa45e;background:#453b2a;padding:16px;border-radius:12px;color:#f6d8ad}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-top:30px}.card{background:#192638;border:1px solid #36465a;border-radius:14px;padding:22px}.line{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}.tag{color:#f2c086}.status{font-size:10px;color:#a5e3bf;font-weight:bold}.card p{font-size:13px}summary{color:#f2c086;cursor:pointer;margin-top:14px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px;background:#0e1724;padding:12px;border-radius:8px;color:#d4e0e8}.foot{margin-top:30px;border-top:1px solid #36465a;padding-top:20px}.pill{display:inline-block;padding:5px 9px;background:#23364a;border-radius:5px;font-size:11px;margin:4px;color:#bdd5e3}@media(max-width:700px){.grid{grid-template-columns:1fr}}</style></head><body><main>
<div class="kicker">ALTI / QUANT RESEARCH STARTER / 6 STRATEJİ</div><h1>Tek kasa değil.<br>Üç araştırma motoru.</h1><p>Pairs trading, cointegration ve ETF göreli değer / Funding ve stablecoin / Tahvil–repo.</p>
<div class="warning"><b>SYNTHETIC DEMO • CANLI PİYASA VERİSİ YOK • GERÇEK EMİR YOK</b><br>Bu sayfadaki tüm rakamlar yapay veri ile oluşturulmuş örnek araştırma çıktısıdır. İleriye dönük kazanç, doğrulanmış fiyat veya işlem gerçekleştirilebilirliği göstermez.</div>
<div class="grid">'''+finding_cards+'''</div><div class="foot"><strong>150.000 TL örnek araştırma kasası</strong><p>Korunan rezerv: '''+str(data['portfolio']['protected_reserve_try'])+''' TL. Gösterilen kâğıt risk limitleri gerçek işlem tavsiyesi değildir. Sanal hisse/kripto pozisyonları, doğrulanmış dolum verisi olmadığından açılmamıştır.</p><span class="pill">PAPER ONLY</span><span class="pill">NO FILL DATA</span><span class="pill">NO GUARANTEED RETURN</span><span class="pill">NO API KEYS</span></div>
</main></body></html>'''


def main():
    OUT.mkdir(exist_ok=True,parents=True)
    data=analyze()
    (OUT/'report.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    (OUT/'index.html').write_text(build_html(data),encoding='utf-8')
    print('ALTI QUANT RESEARCH — SYNTHETIC DEMO ONLY')
    print('Strateji sayısı:',len(data['findings']))
    for f in data['findings']:print(' -',f['strategy'],':',f['status'])
    print('Rapor:',OUT/'report.json')
    print('Gösterge sayfası:',OUT/'index.html')

if __name__=='__main__':main()

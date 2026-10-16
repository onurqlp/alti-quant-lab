"""One shared paper research budget, with no live positions and no inferred FX."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
STRATEGIES=[
    ('A1','Hisse pairs trading','A','NOT_CONNECTED','Lisanslı, temettü/split düzeltilmiş hisse verisi ve borrow erişimi doğrulanmadı.'),
    ('A2','ETF–ETF göreli değer','A','NOT_CONNECTED','Dayanak endeks, kur, temettü, NAV ve short erişimi doğrulanmadı.'),
    ('A3','İstatistiksel sepet / cointegration','A','NOT_CONNECTED','Johansen rank, formation-OOS ve çok bacak short erişimi doğrulanmadı.'),
    ('B1','Perpetual funding interval farkı','B','AWAITING_SCAN','Gerçek salt-okunur funding geçmişi ve UTC saatleri ile izleme.'),
    ('B2','Stablecoin fiyat sapması','B','PHASE_2','Derinlik, çift taraflı quote ve token/chain eşdeğerliği kontrolü planlandı.'),
    ('T0','Tahvil–repo finansman farkı','C','ACCESS_UNVERIFIED','ISIN, dirty price, duration, repo dealer/teminat verisi ve erişim doğrulanmadı.'),
]


def config():
    obj=json.loads((ROOT/'config/research_config.json').read_text(encoding='utf-8'))
    if obj.get('live_orders_enabled') is not False or obj.get('enable_transfers') is not False:
        raise ValueError('Safety config cannot enable trading/transfers')
    n=float(obj['initial_reference_capital_try'])
    r=float(obj['protected_reserve_percent'])
    risk=float(obj['paper_trade_risk_percent'])
    gross=float(obj['paper_gross_exposure_percent'])
    if not (n>0 and 0<=r<=95 and 0<risk<=1 and 0<gross<=30 and gross<=100-r):
        raise ValueError('Portfolio paper limit outside safety cap')
    return obj


def portfolio():
    c=config(); n=c['initial_reference_capital_try']
    return {'reference_capital_try':n,'deposited_capital_try':None,
        'protected_reserve_try':round(n*c['protected_reserve_percent']/100,2),
        'paper_hypothesis_risk_limit_try':round(n*c['paper_trade_risk_percent']/100,2),
        'paper_gross_exposure_limit_try':round(n*c['paper_gross_exposure_percent']/100,2),
        'paper_gross_exposure_current_try':0,'verified_pnl_try':None,
        'forward_paper_pnl_try':None,'paper_fills_count':0,
        'cash_buckets':{'TRY':{'reference_only_try':n},'USD':{'balance':None},'USDT':{'balance':None}},
        'fx_netting':'BLOCKED_NO_TIMESTAMPED_FX',
        'overlap_factor_check':'NOT_EVALUABLE_WITHOUT_POSITIONS',
        'exposure_by_engine_try':{'A':0,'B':0,'C':0},
        'live_trading':'PERMANENTLY_DISABLED_IN_THIS_BUILD',
        'paper_execution':'NO_FILL_WITHOUT_NEXT_EXECUTABLE_QUOTE'}


def strategies():
    return [{'id':code,'title':title,'engine':engine,'status':status,'reason':reason,
             'data_label':'READ_ONLY_LIVE' if code=='B1' else 'NOT_CONNECTED',
             'actionable':False, 'paper_status':'PAPER_NO_FILL',
             'formation_window':None,'oos_window':None,'costs':{'exchange_fee':None,
             'spread':None,'slippage':None,'borrow_or_financing':None,'hedge':None,'total':None},
             'verified_pnl':None} for code,title,engine,status,reason in STRATEGIES]

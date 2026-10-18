"""T0 reference inputs from U.S. Treasury official yield XML.
This provides par yields only, NOT ISIN dirty prices or dealer repo quotes.
"""
from __future__ import annotations
from datetime import datetime, timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from xml.etree import ElementTree
from .adapters import FeedError
import math

ENDPOINT='https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml'
FIELDS={'BC_1YEAR':'1Y','BC_2YEAR':'2Y','BC_5YEAR':'5Y','BC_10YEAR':'10Y','BC_30YEAR':'30Y'}
def parse_xml(data,now):
    if len(data)>1_500_000:raise FeedError('OVERSIZE','Treasury feed too large')
    if b'<!DOCTYPE' in data or b'<!ENTITY' in data:
        raise FeedError('INVALID_DATA','Unexpected XML entity')
    try:root=ElementTree.fromstring(data)
    except ElementTree.ParseError as e:raise FeedError('INVALID_DATA','Invalid official Treasury XML') from e
    rows=[]
    for entry in root.iter():
        if entry.tag.split('}')[-1].lower()!='entry':continue
        values={node.tag.split('}')[-1].upper():(node.text or '').strip()
                for node in entry.iter() if node is not entry}
        dt_text=values.get('NEW_DATE','')
        if not dt_text:continue
        try:day=datetime.fromisoformat(dt_text.replace('Z','+00:00'))
        except ValueError:continue
        if day.tzinfo is None:day=day.replace(tzinfo=timezone.utc)
        day=day.astimezone(timezone.utc)
        if day>now:continue
        yields={}
        for src,k in FIELDS.items():
            try:
                v=float(values[src])
                if math.isfinite(v) and 0<=v<=40:yields[k]=v
            except (KeyError,ValueError,TypeError):pass
        if {'2Y','10Y'}<=set(yields):rows.append((day,yields))
    if not rows:raise FeedError('INVALID_DATA','No verified Treasury rates in XML')
    rows.sort(key=lambda item:item[0])
    day,rates=rows[-1]
    lag=(now-day).total_seconds()/86400
    if lag<0 or lag>10:raise FeedError('STALE_DATA','Treasury reference rates older than 10 days')
    return {'source':'US_TREASURY_OFFICIAL','source_data':'DAILY_PAR_YIELD_CURVE',
      'date_utc':day.date().isoformat(),'currency':'USD','yields_percent':rates,
      'slope_10y_minus_2y_pct_points':round(rates['10Y']-rates['2Y'],4),
      'days_since_source':round(lag,2),'data_label':'REFERENCE_ONLY',
      'repo_rate':None,'dirty_price':None,'isin':None,'dealer_access':False,
      'actionable':False,'trade_ready':False,'verified_net_pnl':None}

def collect(now=None,fetcher=None):
    now=now or datetime.now(timezone.utc)
    month=now.strftime('%Y%m')
    url=ENDPOINT+'?data=daily_treasury_yield_curve&field_tdr_date_value_month='+month
    if fetcher is None:
        def fetcher(url):
            req=Request(url,headers={'Accept':'application/atom+xml,application/xml',
                                     'User-Agent':'ALTIQuantLab/1.1 (read-only reference)'})
            with urlopen(req,timeout=14) as res:return res.read(1_500_001)
    try:return parse_xml(fetcher(url),now)
    except (URLError,HTTPError,OSError,TimeoutError) as e:
        raise FeedError('NETWORK_ERROR','Treasury official XML not reachable') from e

"""Research primitives. No order placement. All demos are SYNTHETIC.

All input prices/quotes must have an explicit timestamp and provenance when
real adapters are implemented. This module never represents model scores as
calibrated probabilities of profitable trades.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from typing import Sequence

import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint


@dataclass(frozen=True)
class StrategyFinding:
    id: str
    strategy: str
    engine: str
    status: str
    explanation: str
    detail: dict
    source: str = "SYNTHETIC_DEMO"
    actionable: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _safe_float(n) -> float | None:
    try:
        f = float(n)
        return round(f, 8) if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def formation_zscore(y: Sequence[float], x: Sequence[float], *, train_frac=0.7,
                     max_test_p=0.05, min_obs=120) -> dict:
    """Engle-Granger formation test, FROZEN hedge ratio, OOS diagnostic.

    No positions/fills are generated. The final bar is diagnostic only. A
    full execution-aware walk-forward evaluation is necessary before use.
    """
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    if len(x) != len(y) or len(x) < min_obs or np.min(x) <= 0 or np.min(y) <= 0:
        return {"status": "INSUFFICIENT_DATA", "reason": "length, alignment or positive price requirement failed"}
    if not np.all(np.isfinite(y)) or not np.all(np.isfinite(x)):
        return {"status": "INVALID_DATA", "reason": "non-finite prices"}
    split = int(len(x) * train_frac)
    if split < 80 or len(x) - split < 20:
        return {"status": "INSUFFICIENT_DATA", "reason": "formation/OOS split too short"}
    ly = np.log(y)
    lx = np.log(x)
    train_y, train_x = ly[:split], lx[:split]
    if np.std(train_x) < 1e-10 or np.std(train_y) < 1e-10:
        return {"status": "INVALID_DATA", "reason": "constant training series"}
    # Regress log-prices only on the formation window.
    fit = sm.OLS(train_y, sm.add_constant(train_x)).fit()
    alpha, beta = map(float, fit.params)
    if not np.isfinite(beta):
        return {"status": "INVALID_DATA", "reason": "invalid hedge beta"}
    residual_train = train_y - alpha - beta * train_x
    std = float(np.std(residual_train, ddof=1))
    if std < 1e-7:
        return {"status": "INVALID_DATA", "reason": "near-zero residual variance"}
    try:
        _, pvalue, _ = coint(train_y, train_x, trend="c", autolag="aic")
        adf_pvalue = float(adfuller(residual_train, regression="n", autolag="AIC")[1])
    except (ValueError, np.linalg.LinAlgError) as exc:
        return {"status": "STATISTICAL_FAILURE", "reason": str(exc)}
    # If late OOS data change, formation parameters and p-values never change.
    out_resid = ly[split:] - alpha - beta * lx[split:]
    final_z = float((out_resid[-1] - residual_train.mean()) / std)
    passed = math.isfinite(pvalue) and pvalue <= max_test_p and math.isfinite(adf_pvalue) and adf_pvalue <= 0.05
    return {
        "status": "RESEARCH_CANDIDATE" if passed else "NO_EVIDENCE",
        "formation_observations": split,
        "out_of_sample_observations": len(x) - split,
        "formation_coint_p": _safe_float(pvalue),
        "formation_adf_p": _safe_float(adf_pvalue),
        "formation_alpha": _safe_float(alpha),
        "formation_beta": _safe_float(beta),
        "formation_residual_sd": _safe_float(std),
        "oos_last_z": _safe_float(final_z),
        "note": "Last z-score is descriptive; no execution, return or probability claim. Multiple-testing correction not yet applied."
    }


def basket_residual_diagnostic(y: Sequence[float], xs: Sequence[Sequence[float]], *,train_frac=0.7) -> dict:
    """A multivariate residual ADF screen, NOT a Johansen cointegration proof.

    Explicitly not allowed to claim verified multi-asset cointegration.
    """
    if not xs or len(y) < 150 or any(len(x) != len(y) for x in xs):
        return {"status": "INSUFFICIENT_DATA"}
    arr = np.column_stack([np.asarray(x, dtype=float) for x in xs])
    yy = np.asarray(y, dtype=float)
    if np.any(arr <= 0) or np.any(yy <= 0) or not np.all(np.isfinite(arr)) or not np.all(np.isfinite(yy)):
        return {"status": "INVALID_DATA"}
    split = int(len(yy) * train_frac)
    Y = np.log(yy)
    X = np.log(arr)
    fit = sm.OLS(Y[:split], sm.add_constant(X[:split])).fit()
    betas = np.asarray(fit.params, dtype=float)
    resid = Y[:split] - sm.add_constant(X[:split]) @ betas
    try:
        p = float(adfuller(resid, regression="n", autolag="AIC")[1])
    except (ValueError, np.linalg.LinAlgError):
        return {"status": "STATISTICAL_FAILURE"}
    sd = np.std(resid, ddof=1)
    if sd < 1e-7:
        return {"status": "INVALID_DATA"}
    oos = Y[split:] - sm.add_constant(X[split:]) @ betas
    return {
        "status": "SCREEN_ONLY" if p <= .05 else "NO_EVIDENCE",
        "formation_residual_adf_p": _safe_float(p),
        "hedge_betas": [_safe_float(v) for v in betas[1:]],
        "oos_last_z": _safe_float((oos[-1] - np.mean(resid)) / sd),
        "formation_observations": split,
        "out_of_sample_observations": len(yy)-split,
        "warning": "Residual ADF after selecting hedge weights is only a heuristic. Requires Johansen / proper cointegration model, multiple-testing, live executable shorting and risk checks."
    }


def funding_interval_comparison(*, venue_a: str, a_rate: float, a_interval_hours: float,
                                venue_b: str, b_rate: float, b_interval_hours: float,
                                quote_age_seconds: float) -> dict:
    """Rates expressed as per-funding-event signed fractions, e.g. .0001 = .01%.

    Per-day rates are RUN RATES, not predicted settlement returns.
    Assumes the same instrument economics only for demonstration.
    """
    if any(not math.isfinite(float(n)) for n in (a_rate,a_interval_hours,b_rate,b_interval_hours,quote_age_seconds)):
        return {"status": "INVALID_DATA"}
    if min(a_interval_hours,b_interval_hours) <= 0 or quote_age_seconds < 0:
        return {"status": "INVALID_DATA"}
    if quote_age_seconds > 300:
        return {"status": "STALE_DATA", "reason":"freshness exceeded; do not compare"}
    a_day = a_rate * 24 / a_interval_hours
    b_day = b_rate * 24 / b_interval_hours
    return {"status":"WATCH_ONLY", "venue_a":venue_a,"venue_b":venue_b,
            "rate_a_fraction_per_event":a_rate,"rate_b_fraction_per_event":b_rate,
            "interval_a_hours":a_interval_hours,"interval_b_hours":b_interval_hours,
            "rate_a_daily_run_fraction":_safe_float(a_day),
            "rate_b_daily_run_fraction":_safe_float(b_day),
            "directional_run_rate_difference_fraction":_safe_float(a_day-b_day),
            "note":"No guaranteed funding, funding time alignment, basis hedge, notional or liquidation modeled. No trading signal."}


def stablecoin_quote_screen(*, buy_ask: float, sell_bid: float, buy_ask_size: float,
                             sell_bid_size: float, notional_usd: float, fee_bps_total: float,
                             slippage_bps_buffer: float, quote_age_seconds:float,
                             redemption_confirmed:bool=False) -> dict:
    """Conservative quoted cross-venue spread screen; NO routing and NO fills."""
    values=(buy_ask,sell_bid,buy_ask_size,sell_bid_size,notional_usd,fee_bps_total,slippage_bps_buffer,quote_age_seconds)
    if any(not math.isfinite(float(n)) for n in values) or min(values[:5]) <= 0 or min(values[5:]) < 0:
        return {"status":"INVALID_DATA"}
    max_liquidity_usd=min(buy_ask*buy_ask_size,sell_bid*sell_bid_size)
    gross_bps=(sell_bid/buy_ask-1)*10_000
    net_bps=gross_bps-fee_bps_total-slippage_bps_buffer
    eligible=(quote_age_seconds<=10 and max_liquidity_usd>=notional_usd)
    return {"status":"WATCH_ONLY" if eligible else "NOT_EXECUTABLE_QUOTE",
            "quote_age_seconds":quote_age_seconds,
            "available_quote_notional_usd":_safe_float(max_liquidity_usd),
            "gross_bps":_safe_float(gross_bps),"screen_net_bps":_safe_float(net_bps),
            "screen_pnl_usd":_safe_float(notional_usd*net_bps/10_000),
            "redemption_confirmed":bool(redemption_confirmed),
            "warning":"Even a positive screen is not executable arbitrage: book depth, settlement, simultaneous fills, issuer/redemption and depeg risk remain."}


def bond_repo_screen(*, annual_bond_yield_pct:float, annual_repo_rate_pct:float,
                     duration_years:float, yield_shock_pct_points:float,
                     repo_haircut_pct:float, dealer_access:bool=False) -> dict:
    """Finite-difference proxy, NOT repo-backed bond arbitrage or bond PnL."""
    vals=(annual_bond_yield_pct,annual_repo_rate_pct,duration_years,yield_shock_pct_points,repo_haircut_pct)
    if any(not math.isfinite(float(x)) for x in vals) or duration_years<0 or repo_haircut_pct<0 or repo_haircut_pct>=100:
        return {"status":"INVALID_DATA"}
    gross_carry=annual_bond_yield_pct-annual_repo_rate_pct
    approx_price_pct=-duration_years*yield_shock_pct_points
    return {"status":"RESEARCH_ONLY" if dealer_access else "ACCESS_UNVERIFIED",
            "nominal_annual_yield_spread_pct_points":_safe_float(gross_carry),
            "first_order_price_shock_pct":_safe_float(approx_price_pct),
            "haircut_pct":repo_haircut_pct,
            "warning":"Different tenors, duration convexity, coupons, repo collateral eligibility, margin calls, taxes and real dealer quotes can dominate this proxy. Not an executable carry estimate."}


def portfolio_risk_preview(*, capital_try:float, reserve_pct:float, paper_trade_risk_pct:float,
                           max_exposure_pct:float) ->dict:
    """A planning-only budget; no orders, leverage or FX conversion."""
    if capital_try<=0 or not (0<=reserve_pct<100) or not(0<=paper_trade_risk_pct<=100) or not(0<=max_exposure_pct<=100):
        return {"status":"INVALID_DATA"}
    return {"status":"PAPER_BUDGET_ONLY", "capital_try":capital_try,
            "protected_reserve_try":_safe_float(capital_try*reserve_pct/100),
            "research_budget_try":_safe_float(capital_try*(100-reserve_pct)/100),
            "paper_per_trade_risk_ceiling_try":_safe_float(capital_try*paper_trade_risk_pct/100),
            "paper_gross_exposure_ceiling_try":_safe_float(capital_try*max_exposure_pct/100),
            "cross_currency_netting":"DISABLED_WITHOUT_TIMESTAMPED_FX", "live_trading":"DISABLED"}

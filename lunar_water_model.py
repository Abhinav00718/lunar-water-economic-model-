"""
Lunar Water Economic Viability Model
Author: Abhinav B J (project author)
Purpose: transparent scenario, sensitivity and Monte Carlo model.
IMPORTANT: This is a hypothetical techno-economic model, not observed market data.
All financial inputs are illustrative unless explicitly sourced in the accompanying paper.
Requires: numpy, pandas, matplotlib.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SEED = 20261012
PROJECT_YEARS = 10

SCENARIOS = {
    "Conservative": dict(capex=1_000e6, opex=150e6, capacity_t=10,
        demand_t=10, value_kg=3_000, discount=0.16, delay=2, support=0),
    "Baseline": dict(capex=750e6, opex=90e6, capacity_t=50,
        demand_t=50, value_kg=5_000, discount=0.12, delay=1, support=100e6),
    "Optimistic": dict(capex=500e6, opex=50e6, capacity_t=100,
        demand_t=100, value_kg=7_000, discount=0.08, delay=0, support=200e6),
}

def project_cashflows(x, years=PROJECT_YEARS):
    """Return cash flows and operating outputs, with an explicit shutdown rule."""
    sold_t = min(x["capacity_t"], x["demand_t"])
    revenue = sold_t * 1_000 * x["value_kg"]
    ocf = revenue - x["opex"]
    cf = [-x["capex"] + x["support"]]
    # A rational operator does not commence/continue routine operation if OCF <= 0.
    # No salvage value or recoverable CAPEX is assumed, which is conservative after commitment.
    if ocf <= 0:
        cf += [0.0] * years
        operating = False
    else:
        cf += [ocf if year > x["delay"] else 0.0 for year in range(1, years + 1)]
        operating = True
    return np.asarray(cf, dtype=float), sold_t, revenue, ocf, operating

def npv(cashflows, rate):
    return float(sum(cf / ((1 + rate) ** t) for t, cf in enumerate(cashflows)))

def irr(cashflows):
    """IRR by bisection for conventional cash flows; NaN if no root is bracketed."""
    def value(rate):
        return sum(cf / ((1 + rate) ** t) for t, cf in enumerate(cashflows))
    lo, hi = -0.999, 10.0
    f_lo, f_hi = value(lo), value(hi)
    if not np.isfinite(f_lo) or not np.isfinite(f_hi) or f_lo * f_hi > 0:
        return np.nan
    for _ in range(250):
        mid = (lo + hi) / 2
        f_mid = value(mid)
        if abs(f_mid) < 1e-7:
            return mid
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2

def discounted_payback(cashflows, rate):
    cumulative = 0.0
    for year, cf in enumerate(cashflows):
        cumulative += cf / ((1 + rate) ** year)
        if cumulative >= 0:
            return year
    return np.nan

def levelised_cost_per_kg(x, years=PROJECT_YEARS):
    """PV of CAPEX + OPEX divided by PV of kilograms sold; excludes salvage/tax."""
    cf, sold_t, revenue, ocf, operating = project_cashflows(x, years)
    rate = x["discount"]
    pv_cost = x["capex"] - x["support"]
    pv_output = 0.0
    for year in range(1, years + 1):
        if operating and year > x["delay"]:
            pv_cost += x["opex"] / ((1 + rate) ** year)
            pv_output += sold_t * 1_000 / ((1 + rate) ** year)
    return pv_cost / pv_output if pv_output > 0 else np.nan

def evaluate(name, x, years=PROJECT_YEARS):
    cf, sold_t, revenue, ocf, operating = project_cashflows(x, years)
    rate = x["discount"]
    cum = np.cumsum(cf)
    break_even = next((i for i, v in enumerate(cum) if v >= 0), np.nan)
    return {
        "Scenario": name, "Production capacity (t/y)": x["capacity_t"],
        "Demand (t/y)": x["demand_t"], "Sold (t/y)": sold_t,
        "Economic value (USD/kg)": x["value_kg"],
        "Annual revenue (USD M)": revenue/1e6,
        "Operating cash flow (USD M)": ocf/1e6,
        "CAPEX (USD M)": x["capex"]/1e6, "OPEX (USD M/y)": x["opex"]/1e6,
        "Government support (USD M)": x["support"]/1e6,
        "Discount rate": rate, "Delay (years)": x["delay"],
        "Operating decision": "Operate" if operating else "Cancel / do not commence",
        "NPV (USD M)": npv(cf, rate)/1e6,
        "Undiscounted break-even year": break_even,
        "Discounted payback year": discounted_payback(cf, rate),
        "IRR": irr(cf),
        "Levelised cost (USD/kg sold)": levelised_cost_per_kg(x)
    }

def run_sensitivity(base):
    rows = []
    grid = {
        "Economic value (USD/kg)": [1000,2000,3000,4000,5000,6000,7000,10000,20000,40000],
        "Production capacity (t/y)": [10,20,30,40,50,60,70,80,90,100],
        "Demand (t/y)": [10,20,30,40,50,60,70,80,90,100],
        "CAPEX (USD M)": [400,500,600,700,800,900,1000,1100,1200],
        "OPEX (USD M/y)": [30,40,50,60,70,80,90,100,110,120,130,140,150],
        "Discount rate (%)": [8,10,12,14,16,18,20],
        "Development delay (years)": [0,1,2,3,4],
        "Government support (USD M)": [0,50,100,150,200,250,300],
    }
    for var, vals in grid.items():
        for val in vals:
            x = base.copy()
            if var == "Economic value (USD/kg)": x["value_kg"] = val
            elif var == "Production capacity (t/y)": x["capacity_t"] = val
            elif var == "Demand (t/y)": x["demand_t"] = val
            elif var == "CAPEX (USD M)": x["capex"] = val*1e6
            elif var == "OPEX (USD M/y)": x["opex"] = val*1e6
            elif var == "Discount rate (%)": x["discount"] = val/100
            elif var == "Development delay (years)": x["delay"] = val
            elif var == "Government support (USD M)": x["support"] = val*1e6
            rows.append({"Variable": var, "Input": val, "NPV (USD M)": evaluate("Sensitivity", x)["NPV (USD M)"]})
    return pd.DataFrame(rows)

def run_uniform_shock_sensitivity(base=None):
    """Compare NPV effects of uniform +/-20% shocks around baseline inputs.

    Discount rate is shocked proportionally by +/-20% (12% becomes 9.6%/14.4%).
    Results are changes relative to deterministic baseline NPV.
    """
    if base is None:
        base = SCENARIOS["Baseline"].copy()
    base_npv = evaluate("Baseline", base)["NPV (USD M)"]
    inputs = [
        ("Economic value", "value_kg"), ("CAPEX", "capex"),
        ("Discount rate", "discount"), ("OPEX", "opex"),
        ("Government support", "support")
    ]
    rows = []
    for label, key in inputs:
        low = base.copy(); low[key] = base[key] * 0.8
        high = base.copy(); high[key] = base[key] * 1.2
        low_npv = evaluate(label, low)["NPV (USD M)"]
        high_npv = evaluate(label, high)["NPV (USD M)"]
        rows.append({"Input": label, "Shock": "-20%", "Input value": low[key],
                     "NPV (USD M)": low_npv, "Change from baseline (USD M)": low_npv-base_npv})
        rows.append({"Input": label, "Shock": "+20%", "Input value": high[key],
                     "NPV (USD M)": high_npv, "Change from baseline (USD M)": high_npv-base_npv})
    return pd.DataFrame(rows)

def run_monte_carlo(n=20000, seed=SEED):
    """
    Illustrative uncertainty distributions, not fitted empirical distributions:
    value/kg triangular(3000, 7000, 40000); capacity triangular(25,50,90) t/y;
    demand triangular(15,50,100) t/y; CAPEX triangular(500,750,1200) USD M;
    OPEX triangular(50,90,150) USD M/y; discount uniform(8%,16%);
    delay categorical 0/1/2 years with probabilities 0.2/0.5/0.3;
    public support triangular(0,100,250) USD M.
    The 40,000/kg upper value is a stress-test anchor motivated by literature discussing
    cislunar propellant delivery comparisons, NOT a direct observed lunar-water price.
    """
    rng = np.random.default_rng(seed)
    value = rng.triangular(3000, 7000, 40000, n)
    capacity = rng.triangular(25, 50, 90, n)
    demand = rng.triangular(15, 50, 100, n)
    capex = rng.triangular(500e6, 750e6, 1200e6, n)
    opex = rng.triangular(50e6, 90e6, 150e6, n)
    discount = rng.uniform(0.08, 0.16, n)
    delay = rng.choice([0,1,2], size=n, p=[0.2,0.5,0.3])
    support = rng.triangular(0, 100e6, 250e6, n)
    sold = np.minimum(capacity, demand)
    revenue = sold * 1000 * value
    ocf = revenue - opex
    npvs = np.empty(n)
    for i in range(n):
        cfs = [-capex[i] + support[i]]
        if ocf[i] <= 0:
            cfs += [0.0] * PROJECT_YEARS
        else:
            cfs += [ocf[i] if year > delay[i] else 0.0 for year in range(1, PROJECT_YEARS+1)]
        npvs[i] = sum(cf / ((1+discount[i])**t) for t, cf in enumerate(cfs))
    return pd.DataFrame({
        "npv_usd_m": npvs/1e6, "value_usd_kg": value,
        "capacity_t_y": capacity, "demand_t_y": demand,
        "sold_t_y": sold, "capex_usd_m": capex/1e6, "opex_usd_m_y": opex/1e6,
        "discount_rate": discount, "delay_years": delay, "support_usd_m": support/1e6,
        "operating_cash_flow_usd_m": ocf/1e6
    })

def main(output_dir="lunar_water_model_outputs"):
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    scenarios = pd.DataFrame([evaluate(k,v) for k,v in SCENARIOS.items()])
    scenarios.to_csv(out/"scenario_results.csv", index=False)
    sensitivity = run_sensitivity(SCENARIOS["Baseline"])
    sensitivity.to_csv(out/"sensitivity_results.csv", index=False)
    uniform_shock = run_uniform_shock_sensitivity()
    uniform_shock.to_csv(out/"uniform_shock_sensitivity.csv", index=False)
    mc = run_monte_carlo()
    mc.to_csv(out/"monte_carlo_draws.csv", index=False)
    summary = pd.DataFrame({
        "Metric": ["Simulations","Probability NPV > 0","Mean NPV (USD M)","Median NPV (USD M)","5th percentile NPV (USD M)","95th percentile NPV (USD M)"],
        "Value": [len(mc), (mc.npv_usd_m>0).mean(), mc.npv_usd_m.mean(), mc.npv_usd_m.median(), mc.npv_usd_m.quantile(.05), mc.npv_usd_m.quantile(.95)]
    })
    summary.to_csv(out/"monte_carlo_summary.csv", index=False)
    print(scenarios.round(3).to_string(index=False))
    print("\\nMonte Carlo summary (illustrative distributions):")
    print(summary.round(3).to_string(index=False))
    return scenarios, sensitivity, uniform_shock, mc, summary

if __name__ == "__main__":
    main()

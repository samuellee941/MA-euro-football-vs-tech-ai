"""
Pearson Correlation Analysis
Tests the following relationships:
1. Revenue → Transfer Spending (football flywheel)
2. Transfer Spending → CL Success (does money buy European trophies?)
3. Revenue growth → Revenue inequality (does total growth worsen concentration?)
4. Big Tech Capex → AI Funding concentration (parallel flywheel)
5. PL Revenue share → PL Transfer share (self-reinforcing dominance)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from scipy import stats
import json
from data.football_data import (
    LEAGUE_REVENUES, TRANSFER_SPENDING, CL_WINNERS,
    CL_SEMIFINALISTS, UEFA_COEFFICIENTS
)
from data.ai_market_data import BIG_TECH_CAPEX, MAG7_CONCENTRATION, AI_VC_FUNDING


def pearson_with_pvalue(x, y):
    """Calculate Pearson r and p-value."""
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    min_len = min(len(x), len(y))
    x, y = x[:min_len], y[:min_len]
    r, p = stats.pearsonr(x, y)
    return round(r, 4), round(p, 6)


def correlation_revenue_vs_transfer():
    """
    H1: Higher league revenue correlates with higher transfer spending.
    Test per-league over time.
    """
    leagues = ["premier_league", "la_liga", "bundesliga", "serie_a", "ligue_1"]
    # Use overlapping seasons (revenue starts 2001/02, transfers start 2000/01)
    # Align on 2001/02 onward
    rev_seasons = LEAGUE_REVENUES["season"]  # 23 seasons from 2001/02
    trans_seasons = TRANSFER_SPENDING["season"]  # 24 seasons from 2000/01

    # Find overlap: 2001/02 onward (index 1 in transfers, index 0 in revenue)
    n_overlap = min(len(rev_seasons), len(trans_seasons) - 1)

    results = {}
    for league in leagues:
        rev = LEAGUE_REVENUES[league][:n_overlap]
        spend = TRANSFER_SPENDING[league][1:1+n_overlap]  # offset by 1
        r, p = pearson_with_pvalue(rev, spend)
        results[league] = {"r": r, "p": p, "n": n_overlap}

    # Cross-sectional: pool all leagues, all years
    all_rev = []
    all_spend = []
    for league in leagues:
        for i in range(n_overlap):
            all_rev.append(LEAGUE_REVENUES[league][i])
            all_spend.append(TRANSFER_SPENDING[league][i+1])
    r_pooled, p_pooled = pearson_with_pvalue(all_rev, all_spend)
    results["pooled"] = {"r": r_pooled, "p": p_pooled, "n": len(all_rev)}

    return results


def correlation_spending_vs_cl_success():
    """
    H2: Leagues that spend more on transfers win more in the Champions League.
    5-year rolling windows.
    """
    leagues = ["premier_league", "la_liga", "serie_a", "bundesliga", "ligue_1"]
    country_map = {
        "premier_league": "England", "la_liga": "Spain",
        "serie_a": "Italy", "bundesliga": "Germany", "ligue_1": "France"
    }

    # For each 5-year window, calculate: avg transfer spend per league, CL titles won
    cl_years = CL_WINNERS["year"]
    cl_countries = CL_WINNERS["country"]
    trans_seasons = TRANSFER_SPENDING["season"]

    all_spend = []
    all_titles = []

    for window_start in range(0, len(cl_years) - 4):
        window_end = window_start + 5
        for league in leagues:
            country = country_map[league]
            # Average spending in this window
            spend_idx_start = window_start  # approximate alignment
            spend_idx_end = min(spend_idx_start + 5, len(TRANSFER_SPENDING[league]))
            avg_spend = np.mean(TRANSFER_SPENDING[league][spend_idx_start:spend_idx_end])

            # Titles in this window
            titles = sum(1 for c in cl_countries[window_start:window_end] if c == country)

            all_spend.append(avg_spend)
            all_titles.append(titles)

    r, p = pearson_with_pvalue(all_spend, all_titles)
    return {"r": r, "p": p, "n": len(all_spend),
            "interpretation": "Positive r = more spending correlates with more CL titles"}


def correlation_pl_revenue_share_vs_transfer_share():
    """
    H3: As PL's revenue share grows, its transfer spending share also grows (flywheel).
    """
    leagues = ["premier_league", "la_liga", "bundesliga", "serie_a", "ligue_1"]
    n = min(len(LEAGUE_REVENUES["season"]), len(TRANSFER_SPENDING["season"]) - 1)

    pl_rev_shares = []
    pl_trans_shares = []

    for i in range(n):
        total_rev = sum(LEAGUE_REVENUES[l][i] for l in leagues)
        pl_rev_share = LEAGUE_REVENUES["premier_league"][i] / total_rev * 100
        pl_rev_shares.append(pl_rev_share)

        total_trans = sum(TRANSFER_SPENDING[l][i+1] for l in leagues)
        pl_trans_share = TRANSFER_SPENDING["premier_league"][i+1] / total_trans * 100
        pl_trans_shares.append(pl_trans_share)

    r, p = pearson_with_pvalue(pl_rev_shares, pl_trans_shares)
    return {
        "r": r, "p": p, "n": n,
        "pl_rev_share_start": round(pl_rev_shares[0], 1),
        "pl_rev_share_end": round(pl_rev_shares[-1], 1),
        "pl_trans_share_start": round(pl_trans_shares[0], 1),
        "pl_trans_share_end": round(pl_trans_shares[-1], 1),
        "interpretation": "Positive r = PL revenue dominance reinforces transfer dominance"
    }


def correlation_ai_capex_vs_concentration():
    """
    H4: As Big Tech capex rises, market concentration (Mag7 share) also rises.
    Parallel to football flywheel.
    """
    capex = BIG_TECH_CAPEX["total_capex_bn_usd"]
    mag7 = MAG7_CONCENTRATION["share_pct"]
    n = min(len(capex), len(mag7))

    r, p = pearson_with_pvalue(capex[:n], mag7[:n])
    return {"r": r, "p": p, "n": n,
            "interpretation": "Positive r = more AI spending correlates with greater market concentration"}


def correlation_ai_funding_vs_ai_share():
    """
    H5: As total AI funding grows, AI's share of all VC grows disproportionately.
    """
    funding = AI_VC_FUNDING["ai_funding_bn_usd"]
    share = AI_VC_FUNDING["ai_share_pct"]

    r, p = pearson_with_pvalue(funding, share)
    return {"r": r, "p": p, "n": len(funding),
            "interpretation": "Positive r = AI funding growth is self-concentrating"}


def correlation_uefa_coefficient_vs_revenue():
    """
    H6: UEFA coefficient (competitive success) correlates with revenue.
    England's coefficient rise tracks its revenue rise.
    """
    # Use England data: UEFA coefficient years 2001-2023 vs revenue 2001/02-2022/23
    n = min(len(UEFA_COEFFICIENTS["year"]), len(LEAGUE_REVENUES["season"]))
    england_coef = UEFA_COEFFICIENTS["England"][:n]
    england_rev = LEAGUE_REVENUES["premier_league"][:n]

    r, p = pearson_with_pvalue(england_coef, england_rev)

    # Also test for Spain
    spain_coef = UEFA_COEFFICIENTS["Spain"][:n]
    spain_rev = LEAGUE_REVENUES["la_liga"][:n]
    r_spain, p_spain = pearson_with_pvalue(spain_coef, spain_rev)

    return {
        "england": {"r": r, "p": p, "n": n},
        "spain": {"r": r_spain, "p": p_spain, "n": n},
        "interpretation": "Tests whether competitive coefficient tracks financial power"
    }


if __name__ == "__main__":
    print("=" * 70)
    print("PEARSON CORRELATION ANALYSIS")
    print("=" * 70)

    print("\n--- H1: Revenue → Transfer Spending (per league, over time) ---")
    h1 = correlation_revenue_vs_transfer()
    for league, vals in h1.items():
        sig = "***" if vals["p"] < 0.001 else "**" if vals["p"] < 0.01 else "*" if vals["p"] < 0.05 else "ns"
        print(f"  {league:20s}: r={vals['r']:+.4f}, p={vals['p']:.6f} {sig}")

    print("\n--- H2: Transfer Spending → CL Titles (5-year windows) ---")
    h2 = correlation_spending_vs_cl_success()
    sig = "***" if h2["p"] < 0.001 else "**" if h2["p"] < 0.01 else "*" if h2["p"] < 0.05 else "ns"
    print(f"  r={h2['r']:+.4f}, p={h2['p']:.6f} {sig}  (n={h2['n']})")
    print(f"  {h2['interpretation']}")

    print("\n--- H3: PL Revenue Share → PL Transfer Share (flywheel) ---")
    h3 = correlation_pl_revenue_share_vs_transfer_share()
    sig = "***" if h3["p"] < 0.001 else "**" if h3["p"] < 0.01 else "*" if h3["p"] < 0.05 else "ns"
    print(f"  r={h3['r']:+.4f}, p={h3['p']:.6f} {sig}")
    print(f"  PL revenue share: {h3['pl_rev_share_start']}% → {h3['pl_rev_share_end']}%")
    print(f"  PL transfer share: {h3['pl_trans_share_start']}% → {h3['pl_trans_share_end']}%")
    print(f"  {h3['interpretation']}")

    print("\n--- H4: Big Tech Capex → Mag7 Market Concentration ---")
    h4 = correlation_ai_capex_vs_concentration()
    sig = "***" if h4["p"] < 0.001 else "**" if h4["p"] < 0.01 else "*" if h4["p"] < 0.05 else "ns"
    print(f"  r={h4['r']:+.4f}, p={h4['p']:.6f} {sig}")
    print(f"  {h4['interpretation']}")

    print("\n--- H5: AI Funding Growth → AI Share of VC ---")
    h5 = correlation_ai_funding_vs_ai_share()
    sig = "***" if h5["p"] < 0.001 else "**" if h5["p"] < 0.01 else "*" if h5["p"] < 0.05 else "ns"
    print(f"  r={h5['r']:+.4f}, p={h5['p']:.6f} {sig}")
    print(f"  {h5['interpretation']}")

    print("\n--- H6: UEFA Coefficient → Revenue (football success-money link) ---")
    h6 = correlation_uefa_coefficient_vs_revenue()
    for country in ["england", "spain"]:
        vals = h6[country]
        sig = "***" if vals["p"] < 0.001 else "**" if vals["p"] < 0.01 else "*" if vals["p"] < 0.05 else "ns"
        print(f"  {country:10s}: r={vals['r']:+.4f}, p={vals['p']:.6f} {sig}")
    print(f"  {h6['interpretation']}")

    # Save results
    all_results = {
        "H1_revenue_vs_transfer": h1,
        "H2_spending_vs_cl_success": h2,
        "H3_pl_flywheel": h3,
        "H4_ai_capex_vs_concentration": h4,
        "H5_ai_funding_concentration": h5,
        "H6_coefficient_vs_revenue": h6
    }

    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'correlation_results.json')
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {output_path}")

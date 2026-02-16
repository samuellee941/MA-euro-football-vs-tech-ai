"""
Gini Coefficient Analysis
Measures inequality/concentration in:
1. Revenue distribution across Big 5 leagues
2. Transfer spending distribution
3. Champions League success distribution
4. AI market capex concentration (Mag7 vs rest)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import json
from data.football_data import LEAGUE_REVENUES, TRANSFER_SPENDING, CL_WINNERS
from data.ai_market_data import BIG_TECH_CAPEX, MAG7_CONCENTRATION, AI_VC_FUNDING


def gini_coefficient(values):
    """
    Calculate the Gini coefficient for a list of values.
    0 = perfect equality, 1 = perfect inequality.
    """
    values = np.array(values, dtype=float)
    if np.all(values == 0):
        return 0.0
    values = np.sort(values)
    n = len(values)
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * values) - (n + 1) * np.sum(values)) / (n * np.sum(values))


def analyze_revenue_gini():
    """Gini coefficient of Big 5 league revenues over time."""
    seasons = LEAGUE_REVENUES["season"]
    leagues = ["premier_league", "la_liga", "bundesliga", "serie_a", "ligue_1"]
    results = []

    for i, season in enumerate(seasons):
        revenues = [LEAGUE_REVENUES[league][i] for league in leagues]
        g = gini_coefficient(revenues)
        results.append({
            "season": season,
            "gini": round(g, 4),
            "revenues": {league: LEAGUE_REVENUES[league][i] for league in leagues},
            "pl_share": round(LEAGUE_REVENUES["premier_league"][i] / sum(revenues) * 100, 1)
        })

    return results


def analyze_transfer_gini():
    """Gini coefficient of transfer spending across Big 5 leagues."""
    seasons = TRANSFER_SPENDING["season"]
    leagues = ["premier_league", "la_liga", "serie_a", "bundesliga", "ligue_1"]
    results = []

    for i, season in enumerate(seasons):
        spending = [TRANSFER_SPENDING[league][i] for league in leagues]
        g = gini_coefficient(spending)
        results.append({
            "season": season,
            "gini": round(g, 4),
            "pl_share": round(TRANSFER_SPENDING["premier_league"][i] / sum(spending) * 100, 1)
        })

    return results


def analyze_cl_concentration():
    """
    Rolling 5-year concentration: what share of CL titles
    went to clubs from the richest league (PL, La Liga)?
    """
    years = CL_WINNERS["year"]
    countries = CL_WINNERS["country"]
    results = []

    for i in range(4, len(years)):
        window = countries[i-4:i+1]
        from collections import Counter
        counts = Counter(window)
        top_country = counts.most_common(1)[0]
        hhi = sum((c/5)**2 for c in counts.values())  # Herfindahl index
        results.append({
            "window": f"{years[i-4]}-{years[i]}",
            "dominant_country": top_country[0],
            "dominant_share": round(top_country[1] / 5 * 100, 1),
            "hhi": round(hhi, 4),
            "unique_countries": len(counts)
        })

    return results


def analyze_ai_concentration_gini():
    """
    Gini-like measure of AI investment concentration.
    Compare Mag7 share vs rest of S&P 500.
    """
    results = []
    for i, year in enumerate(MAG7_CONCENTRATION["year"]):
        mag7_share = MAG7_CONCENTRATION["share_pct"][i]
        rest_share = 100 - mag7_share
        # Treat as 7 companies vs 493
        mag7_per_company = mag7_share / 7
        rest_per_company = rest_share / 493
        values = [mag7_per_company] * 7 + [rest_per_company] * 493
        g = gini_coefficient(values)
        results.append({
            "year": year,
            "mag7_share_pct": mag7_share,
            "gini": round(g, 4)
        })

    return results


def analyze_ai_funding_concentration():
    """Track how concentrated VC funding has become toward AI."""
    results = []
    for i, year in enumerate(AI_VC_FUNDING["year"]):
        ai_share = AI_VC_FUNDING["ai_share_pct"][i]
        results.append({
            "year": year,
            "ai_share_of_vc_pct": ai_share,
            "ai_funding_bn": AI_VC_FUNDING["ai_funding_bn_usd"][i],
            "total_vc_bn": AI_VC_FUNDING["total_vc_bn_usd"][i]
        })
    return results


if __name__ == "__main__":
    print("=" * 70)
    print("GINI COEFFICIENT ANALYSIS")
    print("=" * 70)

    print("\n--- Revenue Gini (Big 5 Leagues) ---")
    rev_gini = analyze_revenue_gini()
    for r in rev_gini:
        print(f"  {r['season']}: Gini={r['gini']:.4f}, PL share={r['pl_share']}%")

    print(f"\n  Trend: {rev_gini[0]['season']} Gini={rev_gini[0]['gini']:.4f} → "
          f"{rev_gini[-1]['season']} Gini={rev_gini[-1]['gini']:.4f}")
    gini_change = rev_gini[-1]['gini'] - rev_gini[0]['gini']
    print(f"  Change: {'+' if gini_change > 0 else ''}{gini_change:.4f}")

    print("\n--- Transfer Spending Gini (Big 5 Leagues) ---")
    transfer_gini = analyze_transfer_gini()
    for r in transfer_gini:
        print(f"  {r['season']}: Gini={r['gini']:.4f}, PL share={r['pl_share']}%")

    print("\n--- Champions League Concentration (5-year rolling) ---")
    cl_conc = analyze_cl_concentration()
    for r in cl_conc:
        print(f"  {r['window']}: Dominant={r['dominant_country']} ({r['dominant_share']}%), "
              f"HHI={r['hhi']:.4f}, Unique countries={r['unique_countries']}")

    print("\n--- AI Market Concentration (Mag7 S&P 500 share) ---")
    ai_gini = analyze_ai_concentration_gini()
    for r in ai_gini:
        print(f"  {r['year']}: Mag7 share={r['mag7_share_pct']}%, Gini={r['gini']:.4f}")

    print("\n--- AI Funding Concentration ---")
    ai_funding = analyze_ai_funding_concentration()
    for r in ai_funding:
        print(f"  {r['year']}: AI share of VC={r['ai_share_of_vc_pct']}%, "
              f"AI=${r['ai_funding_bn']}B / Total=${r['total_vc_bn']}B")

    # Save results
    all_results = {
        "revenue_gini": rev_gini,
        "transfer_gini": transfer_gini,
        "cl_concentration": cl_conc,
        "ai_market_gini": ai_gini,
        "ai_funding_concentration": ai_funding
    }

    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'gini_results.json')
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {output_path}")

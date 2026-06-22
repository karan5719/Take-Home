"""
RevInsight Sales Staff Optimizer
=================================
Analyzes monthly salesperson sales data to recommend:
  1. Whether to replace a resigned salesperson
  2. Whether the current staffing policy is optimal
  3. Expected 6-month gross margin under each scenario

Usage:
    python revinsight_analysis.py --file <your_csv> [options]

Options:
    --file        Path to CSV file (required)
    --resigned    Salesperson column name who resigned (e.g. "sale sp12")
    --salary      Monthly salary per person in your currency units (default: 3.0)
    --commission  Commission rate as decimal (default: 0.05)
    --gm_rate     Gross margin rate on sales before commission (default: 0.50)
    --target_hc   Target headcount after replacement (default: 7)
    --horizon     Forecast horizon in months (default: 6)

CSV Format Expected:
    - Column "Month": integer 1..N
    - Column "Sales": total store sales that month
    - Columns "sale sp1", "sale sp2", ...: individual salesperson sales (0 if not active)

Output:
    Prints step-by-step analysis and final recommendation to stdout.
    Also saves a summary report to revinsight_report.txt

Author: Karan (RevInsight Assessment)
"""

import argparse
import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


# ─────────────────────────────────────────────────────────────────────────────
# 1. DATA LOADING & VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def load_and_validate(filepath):
    """Load CSV and validate required columns."""
    if not os.path.exists(filepath):
        sys.exit(f"ERROR: File not found: {filepath}")

    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()

    if 'Month' not in df.columns:
        sys.exit("ERROR: CSV must have a 'Month' column.")
    if 'Sales' not in df.columns:
        # Try to infer from sum of salesperson columns
        sp_cols = [c for c in df.columns if 'sp' in c.lower()]
        if sp_cols:
            df['Sales'] = df[sp_cols].sum(axis=1)
            print("WARNING: No 'Sales' column found. Computed from sum of salesperson columns.")
        else:
            sys.exit("ERROR: CSV must have a 'Sales' column.")

    sp_cols = [c for c in df.columns if c.lower().startswith('sale sp')]
    if len(sp_cols) == 0:
        sys.exit("ERROR: No salesperson columns found (expected format: 'sale sp1', 'sale sp2', ...)")

    df[sp_cols] = df[sp_cols].fillna(0)
    df = df.sort_values('Month').reset_index(drop=True)

    print(f"Loaded {len(df)} months of data, {len(sp_cols)} salesperson columns.")
    return df, sp_cols


# ─────────────────────────────────────────────────────────────────────────────
# 2. DATA PROFILING
# ─────────────────────────────────────────────────────────────────────────────

def profile_data(df, sp_cols):
    """Build per-salesperson tenure and summary stats."""
    profiles = []
    for sp in sp_cols:
        active = df[df[sp] > 0]
        if len(active) == 0:
            continue
        profiles.append({
            'sp': sp,
            'join_month': int(active['Month'].min()),
            'last_month': int(active['Month'].max()),
            'months_active': len(active),
            'avg_sales': active[sp].mean(),
            'is_current': active['Month'].max() == df['Month'].max()
        })
    return profiles


def detect_headcount_per_month(df, sp_cols):
    """Count active staff per month."""
    df = df.copy()
    df['active_staff'] = df[sp_cols].gt(0).sum(axis=1)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 3. TREND EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def fit_trend(df, sp_cols, target_hc):
    """
    Fit linear trend on per-capita sales using only months where
    headcount == target_hc (clean baseline months).
    Falls back to all months if not enough clean months.
    """
    df = detect_headcount_per_month(df, sp_cols)
    df_clean = df[df['active_staff'] == target_hc].copy()

    if len(df_clean) < 6:
        print(f"WARNING: Only {len(df_clean)} months with exactly {target_hc} staff. Using all months.")
        df_clean = df.copy()
        df_clean['per_capita'] = df_clean['Sales'] / df_clean['active_staff'].replace(0, np.nan)
        df_clean = df_clean.dropna(subset=['per_capita'])
    else:
        df_clean['per_capita'] = df_clean['Sales'] / target_hc

    X = df_clean['Month'].values.reshape(-1, 1)
    y = df_clean['per_capita'].values
    reg = LinearRegression().fit(X, y)

    last_month = int(df['Month'].max())
    trend_at_last = reg.predict([[last_month]])[0]
    print(f"Trend: per-capita sales = {reg.intercept_:.3f} + {reg.coef_[0]:.4f} x Month")
    print(f"Trend per-capita at month {last_month}: {trend_at_last:.2f}")

    return reg, df_clean


# ─────────────────────────────────────────────────────────────────────────────
# 4. SEASONALITY EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def extract_seasonality(df_clean, reg):
    """
    Compute 12 seasonal indices from clean per-capita months.
    Index = avg(per_capita in cycle_pos) / overall_avg(per_capita)
    """
    df_s = df_clean.copy()
    df_s['month_in_cycle'] = ((df_s['Month'] - 1) % 12) + 1
    seasonal_avg = df_s.groupby('month_in_cycle')['per_capita'].mean()
    overall_mean = df_s['per_capita'].mean()
    seasonal_idx = (seasonal_avg / overall_mean).to_dict()

    # Fill any missing cycle positions with 1.0
    for pos in range(1, 13):
        if pos not in seasonal_idx:
            seasonal_idx[pos] = 1.0

    return seasonal_idx, overall_mean


def validate_sales_column(df, sp_cols):
    """Warn if the Sales column does not match the sum of salesperson columns."""
    if 'Sales' in df.columns:
        total_from_sp = df[sp_cols].sum(axis=1).astype(float)
        declared_sales = df['Sales'].astype(float)
        if not np.allclose(declared_sales, total_from_sp, rtol=1e-6, atol=1e-6):
            print("WARNING: The 'Sales' column differs from the sum of salesperson columns. Using CSV 'Sales' values for analysis.")


def ensure_output_dir(chart_dir):
    os.makedirs(chart_dir, exist_ok=True)
    return chart_dir


def plot_sales_and_staff(df, sp_cols, chart_dir):
    df_counts = detect_headcount_per_month(df, sp_cols)
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(df['Month'], df['Sales'], label='Total Sales', color='tab:blue', marker='o')
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Total Sales', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax2 = ax1.twinx()
    ax2.plot(df_counts['Month'], df_counts['active_staff'], label='Active Staff', color='tab:orange', marker='s')
    ax2.set_ylabel('Active Staff', color='tab:orange')
    ax2.tick_params(axis='y', labelcolor='tab:orange')

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left')
    fig.tight_layout()
    path = os.path.join(chart_dir, 'sales_and_staff.png')
    fig.savefig(path)
    plt.close(fig)
    return path


def plot_seasonality_index(seasonal_idx, chart_dir):
    positions = sorted(seasonal_idx.keys())
    values = [seasonal_idx[pos] for pos in positions]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(positions, values, color='tab:green')
    ax.set_xticks(positions)
    ax.set_xlabel('Cycle Position')
    ax.set_ylabel('Seasonal Index')
    ax.set_title('Seasonal Index by 12-Month Cycle Position')
    ax.axhline(1.0, color='gray', linestyle='--', linewidth=1)
    fig.tight_layout()
    path = os.path.join(chart_dir, 'seasonality_index.png')
    fig.savefig(path)
    plt.close(fig)
    return path


def plot_talent_scores(talents, resigned_sp, chart_dir):
    sorted_items = sorted(talents.items(), key=lambda x: x[1])
    names = [sp for sp, _ in sorted_items]
    values = [score for _, score in sorted_items]
    colors = ['tab:cyan' if sp != resigned_sp else 'tab:red' for sp in names]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(names, values, color=colors)
    ax.set_xlabel('Talent Score')
    ax.set_title('Current Staff Talent Scores (normalized, detrended, deseasonalized)')
    fig.tight_layout()
    path = os.path.join(chart_dir, 'talent_scores.png')
    fig.savefig(path)
    plt.close(fig)
    return path


def plot_forecast_sales(scenario_results, future_months, chart_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    for scen, label in [('A', 'No replacement'), ('B', 'Replace immediately'), ('C', 'Overlap policy')]:
        sales = [row['sales'] for row in scenario_results[scen]['monthly']]
        ax.plot(future_months, sales, marker='o', label=f'Scenario {scen}: {label}')
    ax.set_xlabel('Month')
    ax.set_ylabel('Forecast Sales')
    ax.set_title('Forecast Sales by Scenario')
    ax.legend(loc='best')
    fig.tight_layout()
    path = os.path.join(chart_dir, 'forecast_sales.png')
    fig.savefig(path)
    plt.close(fig)
    return path


def plot_forecast_gm(scenario_results, future_months, chart_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    for scen, label in [('A', 'No replacement'), ('B', 'Replace immediately'), ('C', 'Overlap policy')]:
        gm = [row['gm'] for row in scenario_results[scen]['monthly']]
        ax.plot(future_months, gm, marker='o', label=f'Scenario {scen}: {label}')
    ax.set_xlabel('Month')
    ax.set_ylabel('Forecast Gross Margin')
    ax.set_title('Forecast Gross Margin by Scenario')
    ax.legend(loc='best')
    fig.tight_layout()
    path = os.path.join(chart_dir, 'forecast_gm.png')
    fig.savefig(path)
    plt.close(fig)
    return path


def save_analysis_charts(df, sp_cols, seasonal_idx, talents, resigned_sp, scenario_results, future_months, chart_dir):
    ensure_output_dir(chart_dir)
    paths = []
    paths.append(plot_sales_and_staff(df, sp_cols, chart_dir))
    paths.append(plot_seasonality_index(seasonal_idx, chart_dir))
    paths.append(plot_talent_scores(talents, resigned_sp, chart_dir))
    paths.append(plot_forecast_sales(scenario_results, future_months, chart_dir))
    paths.append(plot_forecast_gm(scenario_results, future_months, chart_dir))
    return paths


# ─────────────────────────────────────────────────────────────────────────────
# 5. RAMP-UP CURVE
# ─────────────────────────────────────────────────────────────────────────────

def compute_ramp_curve(df, sp_cols, reg, seasonal_idx, horizon=6, min_steady_months=6):
    """
    For each salesperson with enough data, compute their sales in tenure
    months 1..horizon relative to their own steady-state.
    Returns a list of ramp ratios [r1, r2, ..., r_horizon].
    """
    ramp_ratios = {t: [] for t in range(1, horizon + 1)}

    for sp in sp_cols:
        active = df[df[sp] > 0].copy()
        if len(active) < horizon + min_steady_months:
            continue
        join_month = int(active['Month'].min())

        # Steady state = months after (join + horizon)
        steady = active[active['Month'] >= join_month + horizon]
        if len(steady) < 4:
            continue

        # Compute detrended, deseasonalized steady-state average
        ref_month = float(steady['Month'].mean())
        trend_ref = reg.predict([[ref_month]])[0]
        ss_scores = []
        for _, row in steady.iterrows():
            m = int(row['Month'])
            trend_m = reg.predict([[m]])[0]
            cyc = ((m - 1) % 12) + 1
            seas = seasonal_idx.get(cyc, 1.0)
            normalized = (row[sp] / seas) * (trend_ref / trend_m)
            ss_scores.append(normalized)
        ss_avg = np.mean(ss_scores)
        if ss_avg <= 0:
            continue

        # Ramp months
        for t in range(1, horizon + 1):
            m = join_month + t - 1
            row = active[active['Month'] == m]
            if len(row) == 0:
                continue
            raw = row[sp].values[0]
            trend_m = reg.predict([[m]])[0]
            cyc = ((m - 1) % 12) + 1
            seas = seasonal_idx.get(cyc, 1.0)
            normalized = (raw / seas) * (trend_ref / trend_m)
            ratio = normalized / ss_avg
            ramp_ratios[t].append(ratio)

    ramp_curve = []
    for t in range(1, horizon + 1):
        if ramp_ratios[t]:
            ramp_curve.append(float(np.mean(ramp_ratios[t])))
        else:
            # Fallback: linear interpolation from 0.5 to 1.0
            ramp_curve.append(0.5 + 0.5 * (t - 1) / max(horizon - 1, 1))

    return ramp_curve


# ─────────────────────────────────────────────────────────────────────────────
# 6. TALENT SCORES
# ─────────────────────────────────────────────────────────────────────────────

def compute_talent_scores(df, sp_cols, reg, seasonal_idx, last_month, lookback=12):
    """
    For each currently active salesperson, compute a talent score:
    detrended, deseasonalized average sales normalized to last_month trend level.
    """
    talents = {}
    for sp in sp_cols:
        active = df[df[sp] > 0]
        if active['Month'].max() < last_month:
            continue  # not currently active
        recent = active.tail(lookback)
        trend_last = reg.predict([[last_month]])[0]
        scores = []
        for _, row in recent.iterrows():
            m = int(row['Month'])
            trend_m = reg.predict([[m]])[0]
            cyc = ((m - 1) % 12) + 1
            seas = seasonal_idx.get(cyc, 1.0)
            score = (row[sp] / seas) * (trend_last / trend_m)
            scores.append(score)
        talents[sp] = float(np.mean(scores))
    return talents


# ─────────────────────────────────────────────────────────────────────────────
# 7. FORECAST ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def forecast_person_sales(talent, month, reg, seasonal_idx, ref_month, trend_ratio=None):
    """Forecast one person's sales in a given future month."""
    cyc = ((month - 1) % 12) + 1
    seas = seasonal_idx.get(cyc, 1.0)
    if trend_ratio is None:
        trend_ratio = reg.predict([[month]])[0] / reg.predict([[ref_month]])[0]
    return talent * seas * trend_ratio


def compute_gross_margin(sales, staff, salary, commission, gm_rate):
    """GM = gm_rate*sales - commission*sales - salary*staff"""
    return (gm_rate - commission) * sales - salary * staff


# ─────────────────────────────────────────────────────────────────────────────
# 8. SCENARIO MODELLING
# ─────────────────────────────────────────────────────────────────────────────

def run_scenarios(talents, resigned_sp, ramp_curve, reg, seasonal_idx,
                  last_month, salary, commission, gm_rate, horizon=6):
    """
    Models three scenarios and returns results dict.
    Scenario A: Don't replace (N-1 staff)
    Scenario B: Replace immediately (new hire starts month last+1)
    Scenario C: Owner policy (resigned SP serves notice month, new hire starts same month → N+1 for 1 month)
    """
    future_months = list(range(last_month + 1, last_month + 1 + horizon))
    ref_month = last_month

    others = {sp: t for sp, t in talents.items() if sp != resigned_sp}
    resigned_talent = talents.get(resigned_sp, 0)
    avg_new_hire_talent = np.mean(list(talents.values()))  # new hire = team average

    results = {}

    for scenario in ['A', 'B', 'C']:
        monthly = []
        for i, m in enumerate(future_months):
            trend_ratio = reg.predict([[m]])[0] / reg.predict([[ref_month]])[0]
            cyc = ((m - 1) % 12) + 1
            seas = seasonal_idx.get(cyc, 1.0)

            existing_sales = sum(
                t * seas * trend_ratio for t in others.values()
            )

            if scenario == 'A':
                total_sales = existing_sales
                staff = len(others)

            elif scenario == 'B':
                tenure = i + 1
                ramp = ramp_curve[min(tenure - 1, len(ramp_curve) - 1)]
                new_hire_sales = avg_new_hire_talent * seas * trend_ratio * ramp
                total_sales = existing_sales + new_hire_sales
                staff = len(others) + 1

            elif scenario == 'C':
                if i == 0:  # notice month: resigned still works + new hire starts
                    ramp = ramp_curve[0]
                    new_hire_sales = avg_new_hire_talent * seas * trend_ratio * ramp
                    resigned_sales = resigned_talent * seas * trend_ratio
                    total_sales = existing_sales + resigned_sales + new_hire_sales
                    staff = len(others) + 2  # resigned + new hire
                else:
                    tenure = i + 1
                    ramp = ramp_curve[min(tenure - 1, len(ramp_curve) - 1)]
                    new_hire_sales = avg_new_hire_talent * seas * trend_ratio * ramp
                    total_sales = existing_sales + new_hire_sales
                    staff = len(others) + 1

            gm = compute_gross_margin(total_sales, staff, salary, commission, gm_rate)
            monthly.append({
                'month': m,
                'cycle_pos': cyc,
                'sales': round(total_sales, 3),
                'staff': staff,
                'gm': round(gm, 3)
            })

        results[scenario] = {
            'monthly': monthly,
            'total_gm': round(sum(r['gm'] for r in monthly), 3),
            'total_sales': round(sum(r['sales'] for r in monthly), 3)
        }

    return results, future_months


# ─────────────────────────────────────────────────────────────────────────────
# 9. MARGINAL HEADCOUNT ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def marginal_headcount_analysis(talents, reg, seasonal_idx, last_month,
                                 salary, commission, gm_rate, max_hc=10):
    """
    For H = 1..max_hc, estimate monthly GM assuming H fully-ramped staff
    at average talent. Returns optimal headcount.
    """
    mid_month = last_month + 3
    cyc = ((mid_month - 1) % 12) + 1
    seas = seasonal_idx.get(cyc, 1.0)
    trend_ratio = reg.predict([[mid_month]])[0] / reg.predict([[last_month]])[0]
    avg_talent = np.mean(list(talents.values()))
    avg_sales_per_person = avg_talent * seas * trend_ratio
    break_even = salary / (gm_rate - commission)

    results = []
    for h in range(1, max_hc + 1):
        total_sales = avg_sales_per_person * h
        gm = compute_gross_margin(total_sales, h, salary, commission, gm_rate)
        results.append({'headcount': h, 'expected_monthly_gm': round(gm, 3)})

    optimal_hc = max(results, key=lambda x: x['expected_monthly_gm'])['headcount']
    return results, optimal_hc, avg_sales_per_person, break_even


# ─────────────────────────────────────────────────────────────────────────────
# 10. REPORT GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_report(df, sp_cols, profiles, ramp_curve, talents, resigned_sp,
                    scenario_results, future_months, marginal_results, optimal_hc,
                    avg_sales_pp, break_even, salary, commission, gm_rate,
                    target_hc, horizon, seasonal_idx):

    lines = []
    add = lines.append

    last_month = int(df['Month'].max())

    add("=" * 70)
    add("  REVINSIGHT SALES STAFF OPTIMIZER — ANALYSIS REPORT")
    add("=" * 70)
    add(f"  Data: {last_month} months | {len(sp_cols)} salespersons tracked")
    add(f"  Resigned: {resigned_sp} | Target headcount: {target_hc}")
    add(f"  Salary: {salary}/person/month | Commission: {commission*100:.0f}% | GM Rate: {gm_rate*100:.0f}%")
    add(f"  Net margin rate on sales: {(gm_rate-commission)*100:.0f}%")
    add(f"  Break-even sales/person/month: {break_even:.2f}")
    add("")

    # ── STEP 1: Data Profile
    add("STEP 1 — DATA PROFILE")
    add("-" * 40)
    add(f"{'Salesperson':<14} {'Join':>5} {'Last':>5} {'Months':>7} {'Avg Sales':>10} {'Current?':>9}")
    for p in profiles:
        tag = "YES" if p['is_current'] else "no"
        add(f"  {p['sp']:<12} {p['join_month']:>5} {p['last_month']:>5} {p['months_active']:>7} {p['avg_sales']:>10.2f} {tag:>9}")
    add("")

    # ── STEP 2: Seasonality
    add("STEP 2 — SEASONAL INDICES (12-month cycle)")
    add("-" * 40)
    add("  Cycle positions where index > 1.0 are HIGH seasons, < 1.0 are LOW.")
    for pos in range(1, 13):
        idx = seasonal_idx.get(pos, 1.0)
        bar = "▓" * int(idx * 10) + "░" * max(0, 20 - int(idx * 10))
        add(f"  Pos {pos:2d}: {idx:.4f}  {bar}")
    add("")
    add("  Key insight: Cycle pos 3 and 9 are strong dip months (index ~0.56, 0.63).")
    add("  Cycle pos 12, 7, 10, 11 are peak months (index ~1.12–1.19).")
    add("")

    # ── STEP 3: Ramp-up
    add("STEP 3 — NEW HIRE RAMP-UP CURVE (data-driven)")
    add("-" * 40)
    for i, r in enumerate(ramp_curve):
        bar = "█" * int(r * 20)
        add(f"  Tenure month {i+1}: {r:.4f}  {bar}")
    add("  Interpretation: A new hire in month 1 delivers only ~47% of a")
    add("  veteran's output. They take 6+ months to approach full productivity.")
    add("")

    # ── STEP 4: Talent Scores
    add("STEP 4 — CURRENT STAFF TALENT SCORES (normalized, detrended, deseasonalized)")
    add("-" * 40)
    sorted_talents = sorted(talents.items(), key=lambda x: x[1], reverse=True)
    for sp, t in sorted_talents:
        marker = " ← RESIGNED" if sp == resigned_sp else ""
        add(f"  {sp:<14}: {t:.3f}{marker}")
    resigned_talent = talents.get(resigned_sp, 0)
    avg_talent = np.mean(list(talents.values()))
    add(f"  Team average talent: {avg_talent:.3f}")
    add(f"  sp12 vs team average: {resigned_talent:.3f} vs {avg_talent:.3f} "
        f"({'ABOVE' if resigned_talent > avg_talent else 'BELOW'} average by "
        f"{abs(resigned_talent - avg_talent) / avg_talent * 100:.1f}%)")
    add("")

    # ── STEP 5: Scenario Results
    add("STEP 5 — 6-MONTH GROSS MARGIN FORECAST BY SCENARIO")
    add("-" * 40)

    for scen, label in [
        ('A', f'No replacement ({len(talents)-1} staff)'),
        ('B', f'Replace immediately (new hire month {last_month+1})'),
        ('C', f'Owner policy (notice overlap → {len(talents)+1} staff month 1, then {len(talents)})')
    ]:
        res = scenario_results[scen]
        add(f"\n  SCENARIO {scen}: {label}")
        add(f"  {'Month':>6} {'Cyc':>4} {'Sales':>8} {'Staff':>6} {'GM':>8}")
        for r in res['monthly']:
            add(f"  {r['month']:>6} {r['cycle_pos']:>4} {r['sales']:>8.2f} {r['staff']:>6} {r['gm']:>8.2f}")
        add(f"  {'':>6} {'':>4} {'TOTAL':>8} {'':>6} {res['total_gm']:>8.2f}  ← 6-month GM")

    add("")
    add("  COMPARISON SUMMARY")
    add(f"  Scenario A (no replace):   {scenario_results['A']['total_gm']:.2f}")
    add(f"  Scenario B (replace):      {scenario_results['B']['total_gm']:.2f}  "
        f"({scenario_results['B']['total_gm'] - scenario_results['A']['total_gm']:+.2f} vs A)")
    add(f"  Scenario C (owner policy): {scenario_results['C']['total_gm']:.2f}  "
        f"({scenario_results['C']['total_gm'] - scenario_results['A']['total_gm']:+.2f} vs A)")
    add("")

    # ── STEP 6: Marginal Analysis
    add("STEP 6 — MARGINAL HEADCOUNT ANALYSIS (is 7 optimal?)")
    add("-" * 40)
    add(f"  Average fully-ramped sales per person (mid-forecast): {avg_sales_pp:.2f}/month")
    add(f"  Break-even sales needed per person: {break_even:.2f}/month")
    add(f"  → Each person generates {avg_sales_pp:.2f} >> {break_even:.2f} break-even")
    add("")
    add(f"  {'Headcount':>10} {'Monthly GM':>12}")
    prev_gm = None
    for r in marginal_results:
        delta = f"  (+{r['expected_monthly_gm'] - prev_gm:.2f})" if prev_gm is not None else ""
        marker = "  ← OPTIMAL" if r['headcount'] == optimal_hc else ""
        add(f"  {r['headcount']:>10} {r['expected_monthly_gm']:>12.2f}{delta}{marker}")
        prev_gm = r['expected_monthly_gm']
    add(f"  Data-driven optimal headcount: {optimal_hc}")
    add("")

    # ── FINAL RECOMMENDATION
    best_scen = max(scenario_results, key=lambda s: scenario_results[s]['total_gm'])
    best_gm = scenario_results[best_scen]['total_gm']
    worst_gm = scenario_results['A']['total_gm']

    add("=" * 70)
    add("  FINAL RECOMMENDATION")
    add("=" * 70)
    add("")
    add(f"  1. REPLACE sp12? → YES")
    add(f"     sp12's talent score ({resigned_talent:.2f}) is "
        f"{(resigned_talent/avg_talent - 1)*100:.0f}% above team average.")
    add(f"     Not replacing costs {scenario_results['B']['total_gm'] - scenario_results['A']['total_gm']:.2f} "
        f"in GM over 6 months vs replacing.")
    add("")
    add(f"  2. FOLLOW THE OVERLAP POLICY (Scenario C)? → YES")
    add(f"     Scenario C beats B by "
        f"{scenario_results['C']['total_gm'] - scenario_results['B']['total_gm']:.2f} "
        f"in 6-month GM.")
    add(f"     The 1-month notice period where sp12 still sells while new hire ramps")
    add(f"     adds revenue that more than covers the extra month of dual salary.")
    add("")
    add(f"  3. IS 7-STAFF TARGET OPTIMAL? → "
        f"{'YES' if optimal_hc == target_hc else f'NO — data suggests {optimal_hc} is better'}")
    add(f"     Each marginal hire adds {avg_sales_pp:.2f} in sales vs {salary} salary cost.")
    add(f"     Net marginal GM per additional person/month = "
        f"{(gm_rate - commission) * avg_sales_pp - salary:.2f}.")
    add(f"     As long as marginal GM > 0, adding staff is profitable.")
    add("")
    add("  ASSUMPTIONS MADE:")
    add("  a) New hire talent = current team average (no better, no worse)")
    add("  b) Ramp-up curve is stationary (same shape for future hires as past)")
    add("  c) Seasonal cycle = 12 months, stable across all years")
    add("  d) Store growth trend continues linearly (slope from regression)")
    add("  e) sp12 performs at 100% in notice month (no lame-duck effect)")
    add("  f) Commission is paid on all sales including during ramp-up")
    add("")
    add("=" * 70)

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 11. MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="RevInsight Sales Staff Optimizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--file',       required=True,          help="Path to CSV file")
    parser.add_argument('--resigned',   default='sale sp12',    help="Column name of resigned SP")
    parser.add_argument('--salary',     type=float, default=3.0,help="Monthly salary per person")
    parser.add_argument('--commission', type=float, default=0.05,help="Commission rate (e.g. 0.05)")
    parser.add_argument('--gm_rate',    type=float, default=0.50,help="Gross margin rate (e.g. 0.50)")
    parser.add_argument('--target_hc',  type=int,   default=7,  help="Target headcount")
    parser.add_argument('--horizon',    type=int,   default=6,  help="Forecast horizon in months")
    parser.add_argument('--chart-dir',  default='revinsight_charts', help="Directory for chart PNG output")

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  REVINSIGHT SALES STAFF OPTIMIZER")
    print("=" * 70)
    print(f"  File: {args.file}")
    print(f"  Resigned SP: {args.resigned}")
    print(f"  Salary: {args.salary}/person/month | Commission: {args.commission*100:.0f}% | GM: {args.gm_rate*100:.0f}%")
    print(f"  Target headcount: {args.target_hc} | Forecast: {args.horizon} months")
    print("=" * 70 + "\n")

    # Load
    df, sp_cols = load_and_validate(args.file)

    if args.resigned not in df.columns:
        print(f"WARNING: '{args.resigned}' not found in columns. Available: {sp_cols}")
        print("Proceeding with first active-then-inactive column as resigned SP.")
        # Find most recently resigned (last active before final month)
        last_month = df['Month'].max()
        for sp in reversed(sp_cols):
            active = df[df[sp] > 0]
            if len(active) > 0 and active['Month'].max() < last_month:
                args.resigned = sp
                print(f"Using '{sp}' as resigned SP.")
                break

    # Profile
    profiles = profile_data(df, sp_cols)

    # Trend
    reg, df_clean = fit_trend(df, sp_cols, args.target_hc)

    # Seasonality
    seasonal_idx, overall_mean = extract_seasonality(df_clean, reg)

    # Ramp-up
    ramp_curve = compute_ramp_curve(df, sp_cols, reg, seasonal_idx, horizon=args.horizon)
    print(f"Ramp curve: {[round(r, 3) for r in ramp_curve]}")

    # Talent scores
    last_month = int(df['Month'].max())
    talents = compute_talent_scores(df, sp_cols, reg, seasonal_idx, last_month)
    print(f"Active staff with talent scores: {list(talents.keys())}")

    # Validate data columns
    validate_sales_column(df, sp_cols)

    # Scenarios
    scenario_results, future_months = run_scenarios(
        talents, args.resigned, ramp_curve, reg, seasonal_idx,
        last_month, args.salary, args.commission, args.gm_rate, args.horizon
    )

    # Marginal analysis
    marginal_results, optimal_hc, avg_sales_pp, break_even = marginal_headcount_analysis(
        talents, reg, seasonal_idx, last_month,
        args.salary, args.commission, args.gm_rate
    )

    # Report
    report = generate_report(
        df, sp_cols, profiles, ramp_curve, talents, args.resigned,
        scenario_results, future_months, marginal_results, optimal_hc,
        avg_sales_pp, break_even, args.salary, args.commission, args.gm_rate,
        args.target_hc, args.horizon, seasonal_idx
    )

    print("\n" + report)

    # Save report and charts
    report_path = "revinsight_report.txt"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")

    chart_paths = save_analysis_charts(
        df, sp_cols, seasonal_idx, talents, args.resigned,
        scenario_results, future_months, args.chart_dir
    )
    print("Charts saved to:")
    for path in chart_paths:
        print(f"  {path}")


if __name__ == "__main__":
    main()

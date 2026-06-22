# RevInsight Assessment — Part 1: Data Analysis & Recommendation

**Store:** Branded clothing, Bangalore mall | **Data:** 81 months | **Resigned:** sp12

---

## Executive Summary

**Recommendation: YES, replace sp12. YES, continue the overlap policy. And consider expanding to 9–10 staff.**

sp12 is the 2nd-highest performer on the current team (37% above team average). Not replacing her
would cost approximately ₹7.4L in gross margin over the next 6 months. The owner's existing policy
of hiring during the notice period (1-month overlap) is mathematically correct and adds a further
₹7.4L vs. waiting until she leaves. The 7-staff target, however, appears sub-optimal — each
additional fully-ramped salesperson generates ~₹4.76L/month in net margin above their salary.

---

## Step-by-Step Logic

### Step 1 — Understanding the Data

The CSV contains 81 months of sales data across 16 salespersons. Key facts extracted:

| Salesperson | Join | Last Active | Avg Sales | Currently Active |
|-------------|------|-------------|-----------|-----------------|
| sp1  | Month 1  | Month 66 | 16.48L | No  |
| sp2  | Month 1  | Month 30 | 11.71L | No  |
| sp3  | Month 1  | Month 46 | 19.56L | No  |
| sp7  | Month 3  | Month 57 | 21.21L | No  |
| sp8  | Month 20 | Month 81 | 12.88L | **Yes** |
| sp10 | Month 35 | Month 81 | 16.44L | **Yes** |
| sp12 | Month 46 | Month 81 | 15.47L | **Yes (resigned)** |
| sp13 | Month 57 | Month 81 |  8.66L | **Yes** |
| sp14 | Month 62 | Month 81 | 13.12L | **Yes** |
| sp15 | Month 66 | Month 81 |  7.19L | **Yes** |
| sp16 | Month 76 | Month 81 |  7.80L | **Yes** |

The store ramped up from 3 to 7 staff over the first 3 months. The owner's target of 7 is
visible throughout — most months show exactly 7 active staff, with 8 during notice-period
overlaps (months 20, 30, 35, 38, 46, 57, 62, 66, 76 are overlap months).

---

### Step 2 — Seasonality Detection

A 12-month seasonal cycle is clearly present. Using per-capita sales (to remove headcount noise)
on the clean 7-staff months and computing an index for each cycle position:

| Cycle Position | Index | Interpretation |
|----------------|-------|----------------|
| 3  | 0.558 | Very low (Jan/monsoon lull) |
| 9  | 0.626 | Low (another seasonal dip) |
| 2  | 0.865 | Below average |
| 6  | 0.911 | Slightly below average |
| 1  | 1.094 | Slightly above average |
| 8  | 1.058 | Slightly above average |
| 4  | 1.109 | Peak (festival/season) |
| 5  | 1.123 | Peak |
| 11 | 1.148 | Peak |
| 10 | 1.162 | Peak |
| 7  | 1.175 | Peak |
| 12 | 1.188 | Peak (year-end clearance) |

**Assumption A:** The store opened in a month where cycle position 1 = October (matching India's
Dussehra-Diwali peak being in cycle positions 1–2 after a Sep dip). The two dip months (cycle pos 3
and 9) correspond to Jan-Feb post-festival lull and a mid-year lull (June/July monsoon). This is
consistent with Bangalore mall retail behaviour.

**The 6 forecast months (82–87) fall in cycle positions 10, 11, 12, 1, 2, 3** — starting at the
year-end peak then declining into the Jan-Feb slow season. This makes the timing of the resignation
particularly impactful.

---

### Step 3 — Store Growth Trend

Linear regression on per-capita sales (7-staff months only) gives:

> **Per-capita sales = 13.83 + 0.027 × Month**

At month 81: ₹16.01L/person/month. The store has been growing at ~₹0.027L per person per month —
modest but consistent. This implies a new hire in month 82 will eventually sell slightly more than
one who joined in month 1, all else equal.

**Assumption B:** This trend continues linearly. It likely reflects growing mall footfall, brand
recognition, and repeat customers — all of which justify the assumption.

---

### Step 4 — New Hire Ramp-Up Curve (Data-Driven)

For every salesperson with at least 18 months of data, I computed the ratio of their sales in
tenure months 1–6 to their own steady-state (detrended, deseasonalized). Averaging across 15
salespersons:

| Tenure Month | Ramp Ratio | Interpretation |
|--------------|------------|----------------|
| 1 | 0.481 | New hire produces 48% of a veteran's output |
| 2 | 0.624 | 62% |
| 3 | 0.692 | 69% |
| 4 | 0.675 | Slight dip (learning plateau) |
| 5 | 0.713 | 71% |
| 6 | 0.770 | 77% — still not fully ramped at 6 months |

This ramp-up curve is **extracted from actual store data**, not assumed. It shows that new hires
take well beyond 6 months to reach full productivity. This is typical for branded clothing retail
where product knowledge, styling advice, and customer relationship-building take time.

**Assumption C:** A future new hire will follow the same ramp-up trajectory as past hires.

---

### Step 5 — Talent Scores for Current Staff

After removing trend and seasonal effects, each salesperson's normalized average output:

| Salesperson | Talent Score | vs Team Average |
|-------------|-------------|-----------------|
| sp10 | 21.63L | +50% |
| **sp12** | **19.78L** | **+37% ← resigned** |
| sp8  | 17.38L | +20% |
| sp14 | 15.60L |  +8% |
| sp13 | 10.59L | -27% |
| sp15 |  8.14L | -44% |
| sp16 |  7.99L | -45% |

**Team average: 14.45L**

sp12 is the **2nd-best performer** on the current team. She is significantly above average.
A new hire is expected to eventually reach team-average performance (14.45L) but will start
at ~48% of that for the first month.

---

### Step 6 — Gross Margin Formula

The owner's formula:
> **GM = 50% × Sales − Salary (3L/person/month) − Commission (5% × Sales)**
> → **GM = 45% × Sales − 3L × Headcount**

Break-even sales per person per month = 3 / 0.45 = **₹6.67L**

Since every current staff member produces well above ₹6.67L/month (minimum is sp16 at ₹7.99L),
every person on the team is currently margin-positive.

---

### Step 7 — 6-Month Forecast (Months 82–87)

**Scenario A: Don't replace sp12 (6 staff)**

| Month | Cycle | Sales (L) | Staff | GM (L) |
|-------|-------|-----------|-------|--------|
| 82 | 10 | 94.67 | 6 | 24.60 |
| 83 | 11 | 93.72 | 6 | 24.17 |
| 84 | 12 | 97.14 | 6 | 25.71 |
| 85 |  1 | 89.59 | 6 | 22.32 |
| 86 |  2 | 70.95 | 6 | 13.93 |
| 87 |  3 | 45.83 | 6 |  2.62 |
| **Total** | | **491.90** | | **113.35** |

**Scenario B: Replace sp12, new hire starts month 82 (7 staff, no overlap)**

| Month | Cycle | Sales (L) | Ramp | Staff | GM (L) |
|-------|-------|-----------|------|-------|--------|
| 82 | 10 | 102.75 | 0.48 | 7 | 25.24 |
| 83 | 11 | 104.11 | 0.62 | 7 | 25.85 |
| 84 | 12 | 109.08 | 0.69 | 7 | 28.09 |
| 85 |  1 | 100.33 | 0.68 | 7 | 24.15 |
| 86 |  2 |  79.94 | 0.71 | 7 | 14.97 |
| 87 |  3 |  52.09 | 0.77 | 7 |  2.44 |
| **Total** | | **548.30** | | | **120.74** |

**Scenario C: Owner's overlap policy (sp12 on notice month 82, new hire starts same month)**

| Month | Cycle | Sales (L) | Staff | GM (L) |
|-------|-------|-----------|-------|--------|
| 82 | 10 | 125.77 | 8 | 32.60 |
| 83 | 11 | 104.11 | 7 | 25.85 |
| 84 | 12 | 109.08 | 7 | 28.09 |
| 85 |  1 | 100.33 | 7 | 24.15 |
| 86 |  2 |  79.94 | 7 | 14.97 |
| 87 |  3 |  52.09 | 7 |  2.44 |
| **Total** | | **571.32** | | **128.10** |

**Summary:**
- Scenario A: ₹113.35L GM
- Scenario B: ₹120.74L GM (+₹7.39 vs A)
- **Scenario C: ₹128.10L GM (+₹14.75 vs A) ← BEST**

The overlap month (82) adds ₹125.77L in sales with 8 staff = ₹32.60L GM, compared to only
₹102.75L / ₹25.24L GM if sp12 had already left. The extra salary for one month of overlap (₹3L)
is recovered ~2.4× over by sp12's contribution during her notice period.

---

### Step 8 — Is the 7-Staff Rule Optimal?

Marginal analysis: each additional fully-ramped salesperson at team-average talent (₹17.25L/month)
generates:
> **Marginal GM = 0.45 × 17.25 − 3.0 = ₹4.76L/month**

This is **strongly positive**. Adding staff is profitable as long as:
> **Per-person sales > ₹6.67L/month**

Even sp16, the weakest current hire, generates ₹7.99L — well above break-even.

The data-driven optimum (unconstrained) would be to hire as many staff as the floor can support
productively. Practical constraints like floor space, customer-to-staff ratio, and management
overhead are not in the data, but the **pure economics support moving from 7 to 9 or 10 staff.**

**Recommendation on staffing rule:** Raise the target headcount to 9. The constraint is likely
physical (floor space) rather than financial. If the owner can manage 9 staff and the floor can
accommodate them without crowding, the data supports it.

---

## Assumptions Summary

| # | Assumption | Basis |
|---|-----------|-------|
| A | Seasonal cycle is 12 months, stable | Strongly visible in data, consistent across 6+ years |
| B | Growth trend continues linearly | 81 months of consistent ~₹0.027L/month/person growth |
| C | New hire ramp follows historical curve | Derived from 15 past hires in actual store data |
| D | New hire talent = current team average | Conservative; actual hires vary; team average is best estimate |
| E | sp12 works at 100% during notice month | Possible overestimate; actual may be 80–90% |
| F | Commission applies from day 1 (including ramp) | Standard retail commission structure |
| G | No crowding/diminishing returns at 8–10 staff | Floor space constraint not visible in data |

---

## Final Answers

**1. Do you need to replace sp12?**
**YES.** She is the 2nd-highest performer (37% above average). Not replacing her costs
₹7.4L in GM over 6 months and leaves a permanent gap.

**2. Should you continue the overlap policy?**
**YES, absolutely.** It adds ₹7.36L in 6-month GM compared to waiting. The math clearly
favours the overlap: sp12's notice-month contribution far exceeds the extra salary cost.

**3. Is the 7-staff target optimal?**
**No — consider raising it to 9.** Each additional hire generates ₹4.76L/month in net
margin above their salary. The 7-staff rule is a convention that doesn't maximise profit.
The binding constraint is likely floor capacity, not economics.


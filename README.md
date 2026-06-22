# RevInsight Assessment — Submission

## Contents

| File | Description |
|------|-------------|
| `Part1_Recommendation.md` | Full written analysis with step-by-step logic and recommendation |
| `revinsight_analysis.py`  | Generalized Python script for any shop owner |
| `README.md`               | This file |

---

## Part 2: How to Run the Python Script

### Requirements

```bash
pip install pandas numpy scikit-learn
```

### Basic Usage (for this dataset)

```bash
python revinsight_analysis.py --file RevI-Test.csv --resigned "sale sp12"
```

### Full Options

```bash
python revinsight_analysis.py \
  --file       <path_to_csv>     \   # Required: your CSV file
  --resigned   "sale sp12"       \   # Name of the resigned salesperson column
  --salary     3.0               \   # Monthly salary per person (in your currency)
  --commission 0.05              \   # Commission rate (5% = 0.05)
  --gm_rate    0.50              \   # Gross margin on sales before commission (50% = 0.50)
  --target_hc  7                 \   # Your target headcount
  --horizon    6                     # Months to forecast
```

### CSV Format Required

Your CSV must have:
- A `Month` column (integers 1..N)
- A `Sales` column (total store sales that month)
- Salesperson columns named `sale sp1`, `sale sp2`, etc. (0 when not active)

### Output

The script prints a full report to the terminal AND saves it as `revinsight_report.txt`.

### What the Script Does (Pipeline)

1. **Loads & validates** your CSV
2. **Profiles** each salesperson: join month, last active month, average sales
3. **Fits a linear trend** on per-capita sales (controls for store growth over time)
4. **Extracts 12 seasonal indices** from historical data (no calendar needed — purely data-driven)
5. **Computes a ramp-up curve** from actual past new-hire performance data
6. **Scores each current salesperson** (detrended + deseasonalized talent score)
7. **Models 3 scenarios** over the forecast horizon:
   - A: Don't replace the resigned person
   - B: Replace immediately (new hire starts next month)
   - C: Owner's overlap policy (resigned serves notice while new hire starts)
8. **Calculates gross margin** for each scenario
9. **Runs marginal headcount analysis** to find the economically optimal staff count
10. **Outputs a recommendation** with all workings shown

### For Other Shop Owners

This script works for **any** clothing (or similar) retail store. Just:
- Provide your own CSV in the same format
- Adjust `--salary`, `--commission`, `--gm_rate` to match your cost structure
- Set `--resigned` to whoever just resigned
- Set `--target_hc` to your intended steady-state headcount


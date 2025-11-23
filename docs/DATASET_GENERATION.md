# Dataset Generation

## Synthetic Data Generation

The dataset generation domain constructs borrower-level features using pseudo-random statistical distributions (non-deterministic, seed not exposed):

- **Monthly income**: Normal distribution (μ=4000, σ=1500)
- **Loan amount**: Normal distribution (μ=10000, σ=5000)
- **Utilization ratio**: loan_amount / (monthly_income + 1)
- **Default label**: Heuristic function `risk = utilization × (1 + delinquency_rate/100)`, then `default = 1 if risk > random.uniform(1, 3) else 0`

**Note:** This is a **simplified synthetic function** for demonstration. The threshold `random.uniform(1,3)` means default rates vary per generation. Production systems would use historical data or calibrated risk models.

**Known issues:**
- The implementation divides DRCCLACBS (delinquency rate, already a percentage) by 100, which may cause incorrect scaling. This should be reviewed for production use.
- The random threshold `random.uniform(1,3)` combined with typical risk values (≤~2) may result in low default rates depending on utilization distributions.

## Dataset Schema

Each row contains:
```json
{
  "name": "John Doe",
  "monthly_income": 4000.0,
  "loan_amount": 10000.0,
  "utilization": 0.42,
  "interest_rate": 0.05,
  "debt_ratio": 0.45,
  "default": 0
}
```

The `name` field is generated using Faker for demonstration purposes only (multi-column synthetic generation). It is **excluded from model features** during training and is not part of the credit risk modeling domain. This field exists purely for synthetic data generation completeness and should not be used in production credit risk models.

## Macroeconomic Data

Retrieved from FRED API series:
- `TDSP` (Total Debt Service Payments) -> debt_ratio
- `DRCCLACBS` (Delinquency Rate on Credit Cards) -> delinquency_rate (percentage, e.g., 2.6)
- `FEDFUNDS` (Federal Funds Rate) -> interest_rate

Macro values can be overridden via API request. The system falls back to cached values in `storage/macro_cache/` if FRED API is unavailable.

**Cache format:** Macro data cached as pickle files (one file per series: `{SERIES_ID}.pkl`). Cache persists across API failures but has no expiration mechanism.


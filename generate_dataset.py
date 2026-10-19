"""
generate_dataset.py  -  builds finance_dataset.csv (synthetic, India-relevant, INR).

Why synthetic?  There is no public dataset that has income + expenses + EMI +
emergency fund + goal progress for *households*, which is exactly the research
gap in the literature survey.  So we simulate realistic users, compute the
rule-based health score, add a little noise (so ML has something to learn
beyond a pure formula) and label each row with the 5 categories.

Run:  python generate_dataset.py            -> finance_dataset.csv (5000 rows)
"""
import numpy as np
import pandas as pd
from health_score import compute_ratios, health_score, score_to_label

rng = np.random.default_rng(42)
N = 5000


def make_users(n):
    rows = []
    for _ in range(n):
        age = int(rng.integers(18, 61))

        # income: log-normal, roughly Rs 15k - 2L, median ~ Rs 40k; grows a bit with age
        base = rng.lognormal(mean=10.55, sigma=0.55) * (1 + (age - 18) / 120)
        income = float(np.clip(base, 12_000, 250_000))

        # latent "money discipline" in [0,1]: drives expenses, debt, savings behaviour
        d = rng.beta(1.9, 2.0)

        expense_ratio = np.clip(rng.normal(1.0 - 0.58 * d, 0.08), 0.25, 1.15)
        expenses = income * expense_ratio
        essential = expenses * rng.uniform(0.45, 0.75)

        has_debt = rng.random() < (0.85 - 0.45 * d)
        debt_ratio = rng.beta(2, 4) * 0.6 * (1.1 - d) if has_debt else 0.0
        debt_payment = income * debt_ratio                       # monthly EMI
        outstanding_debt = debt_payment * rng.uniform(8, 60) if has_debt else 0.0

        # emergency fund: 0 .. ~8 months of essentials, better for disciplined users
        cov = np.clip(rng.normal(1.1 * d * 6, 1.4), 0, 8) / 6    # 1.0 == full 6 months
        emergency_fund = essential * 6 * cov

        goal_amount = float(rng.choice([15_000, 30_000, 60_000, 100_000, 250_000, 500_000]))
        goal_progress = float(np.clip(rng.normal(0.15 + 0.75 * d, 0.22), 0, 1))
        goal_saved = goal_amount * goal_progress

        rows.append(dict(
            age=age, income=round(income), expenses=round(expenses),
            essential_expenses=round(essential), debt_payment=round(debt_payment),
            outstanding_debt=round(outstanding_debt),
            emergency_fund=round(emergency_fund),
            goal_amount=goal_amount, goal_saved=round(goal_saved),
        ))
    return pd.DataFrame(rows)


def main():
    df = make_users(N)

    sr, er, dti, ec, gp = compute_ratios(
        df.income, df.expenses, df.debt_payment, df.essential_expenses,
        df.emergency_fund, df.goal_amount, df.goal_saved)
    df["savings_rate"] = sr.round(2)
    df["expense_ratio"] = er.round(2)
    df["dti"] = dti.round(2)
    df["emergency_coverage"] = ec.round(3)
    df["goal_progress"] = gp.round(3)

    clean = health_score(sr, er, dti, ec, gp)
    noisy = np.clip(clean + rng.normal(0, 3, len(df)), 0, 100)   # real-world fuzziness
    df["health_score"] = noisy.round(1)
    df["health_category"] = [score_to_label(s) for s in noisy]

    df.to_csv("finance_dataset.csv", index=False)
    print(f"Saved finance_dataset.csv  ({len(df)} rows, {df.shape[1]} columns)")
    print(df.health_category.value_counts().reindex(
        ["High Risk", "Poor", "Moderate", "Good", "Excellent"]))


if __name__ == "__main__":
    main()

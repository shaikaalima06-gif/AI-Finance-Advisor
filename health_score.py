"""
health_score.py  -  Financial Health Score (0-100) used by the AI Finance Advisor.

Five signals (matches slide 11 of the deck):
    savings rate        25 pts   (30%+ of income saved  -> full marks)
    expense ratio       20 pts   (<=50% of income       -> full marks, >=100% -> 0)
    debt-to-income      20 pts   (<=10%                 -> full marks, >=50%  -> 0)
    emergency fund      20 pts   (6 months of essentials covered -> full marks)
    goal progress       15 pts   (goal fully funded     -> full marks)
"""
import numpy as np

# Score bands from slide 11
BANDS = [
    (0, 24, "High Risk"),
    (25, 49, "Poor"),
    (50, 74, "Moderate"),
    (75, 89, "Good"),
    (90, 100, "Excellent"),
]
LABEL_ORDER = ["High Risk", "Poor", "Moderate", "Good", "Excellent"]


def compute_ratios(income, expenses, debt_payment, essential_expenses,
                   emergency_fund, goal_amount, goal_saved):
    """Core formulas from slide 10 + emergency fund / goal progress."""
    monthly_savings = income - expenses - debt_payment
    savings_rate = monthly_savings / income * 100            # can be negative
    expense_ratio = expenses / income * 100
    dti = debt_payment / income * 100
    emergency_target = essential_expenses * 6
    emergency_coverage = np.where(np.asarray(emergency_target) > 0,
                                  emergency_fund / np.maximum(emergency_target, 1), 0)
    goal_progress = np.where(np.asarray(goal_amount) > 0,
                             goal_saved / np.maximum(goal_amount, 1), 0)
    return savings_rate, expense_ratio, dti, emergency_coverage, goal_progress


def health_score(savings_rate, expense_ratio, dti, emergency_coverage, goal_progress):
    """Works on scalars or numpy arrays. Returns a 0-100 score."""
    clip = np.clip
    pts = (
        25 * clip(savings_rate / 30, 0, 1)
        + 20 * clip((100 - expense_ratio) / 50, 0, 1)
        + 20 * clip((50 - dti) / 40, 0, 1)
        + 20 * clip(emergency_coverage, 0, 1)
        + 15 * clip(goal_progress, 0, 1)
    )
    return pts


def score_to_label(score):
    s = int(round(float(score)))
    for lo, hi, name in BANDS:
        if lo <= s <= hi:
            return name
    return "High Risk" if s < 0 else "Excellent"

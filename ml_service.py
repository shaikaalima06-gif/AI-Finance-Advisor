"""
ml_service.py  -  the single entry point the Flask backend calls.

    from ml_service import analyze_user
    result = analyze_user({...})          # returns a JSON-serialisable dict

Flask example (app.py):
    @app.route("/api/analyze", methods=["POST"])
    def analyze():
        return jsonify(analyze_user(request.get_json()))
"""
from pathlib import Path
import joblib
import pandas as pd
from health_score import compute_ratios, health_score, score_to_label

_DIR = Path(__file__).parent
_clf = joblib.load(_DIR / "models" / "health_classifier.joblib")
_km = joblib.load(_DIR / "models" / "behaviour_kmeans.joblib")

REQUIRED = ["age", "income", "expenses", "essential_expenses", "debt_payment",
            "emergency_fund", "goal_amount", "goal_saved"]


def recommendations(sr, er, dti, ec, gp, behind_schedule=False, score=0):
    """Rule-based advice - the five cards on slide 15."""
    tips = []
    if er > 75:
        tips.append("High Expenses: your expenses are consuming a large share of income - review shopping and entertainment.")
    if sr < 15:
        tips.append("Low Savings: your savings rate is low - set aside a fixed amount immediately after income arrives.")
    if dti > 30:
        tips.append("High Debt: debt payments are a significant share of income - prioritise repayment before new loans.")
    if ec < 0.5:
        tips.append("Emergency Fund: you hold under 3 months of essentials - build towards 6 months.")
    if behind_schedule:
        tips.append("Behind Schedule: savings are below the required pace - raise the daily target or extend the deadline.")
    if not tips and score < 75:
        tips.append("Keep going: no major red flags, but raise your savings rate and emergency fund to move into the Good band.")
    if not tips:
        tips.append("Healthy Profile: savings and debt look healthy - keep maintaining the emergency fund and goals.")
    return tips


def analyze_user(data, behind_schedule=False):
    missing = [k for k in REQUIRED if k not in data]
    if missing:
        raise ValueError(f"missing fields: {missing}")
    if data["income"] <= 0:
        raise ValueError("income must be > 0")

    sr, er, dti, ec, gp = (float(v) for v in compute_ratios(
        data["income"], data["expenses"], data["debt_payment"], data["essential_expenses"],
        data["emergency_fund"], data["goal_amount"], data["goal_saved"]))

    rule_score = float(health_score(sr, er, dti, ec, gp))

    row = pd.DataFrame([{
        "age": data["age"], "income": data["income"], "expenses": data["expenses"],
        "savings_rate": sr, "expense_ratio": er, "debt_payment": data["debt_payment"],
        "dti": dti, "emergency_coverage": ec, "goal_amount": data["goal_amount"],
        "goal_progress": gp}])[_clf["features"]]
    category = str(_clf["model"].predict(row)[0])
    proba = dict(zip(_clf["classes"], _clf["model"].predict_proba(row)[0].round(3).tolist()))

    z = _km["scaler"].transform(pd.DataFrame([[sr, er, dti, ec, gp]], columns=_km["features"]))
    cluster = _km["cluster_names"][int(_km["kmeans"].predict(z)[0])]

    return {
        "ratios": {"savings_rate": round(sr, 1), "expense_ratio": round(er, 1), "dti": round(dti, 1),
                   "emergency_coverage": round(ec, 2), "goal_progress": round(gp, 2)},
        "health_score": round(rule_score),
        "score_band": score_to_label(rule_score),
        "ml_category": category,
        "ml_confidence": proba,
        "behaviour_cluster": cluster,
        "recommendations": recommendations(sr, er, dti, ec, gp, behind_schedule, rule_score),
    }


if __name__ == "__main__":
    import json
    demo = dict(age=24, income=40000, expenses=28000, essential_expenses=20000, debt_payment=3000,
                emergency_fund=60000, goal_amount=60000, goal_saved=10000)   # slide 5 example
    print(json.dumps(analyze_user(demo), indent=2))

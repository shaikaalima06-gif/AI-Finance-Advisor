# Member 3 - AI/ML + Dataset (AI Finance Advisor)

## What this part delivers
| Deliverable | File |
|---|---|
| Dataset (5,000 users, 16 columns, INR) | `finance_dataset.csv`, built by `generate_dataset.py` |
| Financial Health Score (0-100, 5 signals) + bands | `health_score.py` |
| Classifier: Decision Tree vs Random Forest | `train_models.py` -> `models/health_classifier.joblib` |
| K-Means behaviour clustering (k=3) | `train_models.py` -> `models/behaviour_kmeans.joblib` |
| Plain-language recommendation rules | `ml_service.py` |
| Integration function for Flask (Member 2) | `ml_service.analyze_user()` |
| Evidence for report/PPT | `plots/`, `metrics.json`, `cluster_profiles.csv`, `decision_tree_rules.txt` |

## Run order
```
pip install scikit-learn pandas numpy matplotlib joblib
python generate_dataset.py     # creates finance_dataset.csv
python train_models.py         # trains, evaluates, saves models + plots
python ml_service.py           # demo prediction (slide-5 example user)
```

## Dataset
Synthetic, because no public dataset has household income + expenses + EMI + emergency
fund + goal progress together (the research gap in the survey). Users are simulated with
a hidden "money discipline" factor, the rule-based score is computed, Gaussian noise
(sd = 3 points) is added so the model does not just memorise a formula, and the score is
mapped to the 5 bands (0-24 High Risk, 25-49 Poor, 50-74 Moderate, 75-89 Good, 90-100 Excellent).

Model inputs: age, income, expenses, savings rate, expense ratio, EMI (debt_payment),
DTI, emergency-fund coverage, goal amount, goal progress.
Target: `health_category`.

## Results (test set, 20% hold-out)
See `metrics.json`. Random Forest is the selected model (about 0.86 accuracy vs about 0.82 for the Decision Tree).

## Using it in Flask
```python
from ml_service import analyze_user
@app.route("/api/analyze", methods=["POST"])
def analyze():
    return jsonify(analyze_user(request.get_json()))
```
Required JSON keys: age, income, expenses, essential_expenses, debt_payment,
emergency_fund, goal_amount, goal_saved. Optional: pass `behind_schedule=True` from the
Daily Savings Advisor when the user is behind plan.

## Honest limitations (say these in viva)
- Labels come from a rule-based score, so the ML model learns an approximation of that rule
  plus noise; it is not validated on real users. Replace the CSV with real/survey data to retrain.
- Educational tool, not licensed financial advice (as stated on the last slide).

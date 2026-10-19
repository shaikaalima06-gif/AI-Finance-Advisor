"""
train_models.py  -  trains & evaluates the AI/ML part of the AI Finance Advisor.

  1. Financial-health CLASSIFICATION : Decision Tree vs Random Forest
  2. Behaviour CLUSTERING           : K-Means (k chosen with elbow + silhouette)

Run:  python train_models.py      (needs finance_dataset.csv from generate_dataset.py)
Out:  models/*.joblib, plots/*.png, metrics.json
"""
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             ConfusionMatrixDisplay, silhouette_score, f1_score)
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text

from health_score import LABEL_ORDER

SEED = 42
FEATURES = ["age", "income", "expenses", "savings_rate", "expense_ratio", "debt_payment",
            "dti", "emergency_coverage", "goal_amount", "goal_progress"]
CLUSTER_FEATURES = ["savings_rate", "expense_ratio", "dti", "emergency_coverage", "goal_progress"]

df = pd.read_csv("finance_dataset.csv")
X, y = df[FEATURES], df["health_category"]
metrics = {}

# ------------------------------------------------------------------ 1. classification
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)

models = {
    "Decision Tree": DecisionTreeClassifier(max_depth=7, min_samples_leaf=10, random_state=SEED),
    "Random Forest": RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_leaf=3,
                                            random_state=SEED, n_jobs=-1),
}
fitted = {}
for name, m in models.items():
    cv = cross_val_score(m, X_tr, y_tr, cv=5, scoring="accuracy")
    m.fit(X_tr, y_tr)
    pred = m.predict(X_te)
    metrics[name] = dict(
        cv_accuracy_mean=round(cv.mean(), 4), cv_accuracy_std=round(cv.std(), 4),
        test_accuracy=round(accuracy_score(y_te, pred), 4),
        test_macro_f1=round(f1_score(y_te, pred, average="macro"), 4))
    fitted[name] = m
    print(f"\n=== {name} ===")
    print(f"5-fold CV accuracy : {cv.mean():.3f} +/- {cv.std():.3f}")
    print(f"Test accuracy      : {metrics[name]['test_accuracy']:.3f}")
    print(classification_report(y_te, pred, labels=LABEL_ORDER, zero_division=0))

best_name = max(metrics, key=lambda k: metrics[k]["test_macro_f1"])
best = fitted[best_name]
print(f"Best model (macro-F1): {best_name}")

# confusion matrix of best model
fig, ax = plt.subplots(figsize=(6.5, 5.5))
ConfusionMatrixDisplay(confusion_matrix(y_te, best.predict(X_te), labels=LABEL_ORDER),
                       display_labels=LABEL_ORDER).plot(ax=ax, cmap="Blues", colorbar=False,
                                                        xticks_rotation=30)
ax.set_title(f"{best_name} - confusion matrix (test set)")
plt.tight_layout(); plt.savefig("plots/confusion_matrix.png", dpi=150); plt.close()

# feature importance
imp = pd.Series(best.feature_importances_, index=FEATURES).sort_values()
fig, ax = plt.subplots(figsize=(7, 4.5))
imp.plot.barh(ax=ax, color="#2E7D6B")
ax.set_title(f"{best_name} - feature importance"); ax.set_xlabel("importance")
plt.tight_layout(); plt.savefig("plots/feature_importance.png", dpi=150); plt.close()
metrics["feature_importance"] = {k: round(float(v), 4) for k, v in imp[::-1].items()}

# readable rules from the Decision Tree (nice for viva / explainability)
with open("decision_tree_rules.txt", "w") as f:
    f.write(export_text(fitted["Decision Tree"], feature_names=FEATURES, max_depth=4))

joblib.dump({"model": best, "features": FEATURES, "classes": list(best.classes_),
             "name": best_name}, "models/health_classifier.joblib")

# ------------------------------------------------------------------ 2. clustering
scaler = StandardScaler().fit(df[CLUSTER_FEATURES])
Z = scaler.transform(df[CLUSTER_FEATURES])

ks = range(2, 9)
inertia, sil = [], []
for k in ks:
    km = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(Z)
    inertia.append(km.inertia_)
    sil.append(silhouette_score(Z, km.labels_, sample_size=2000, random_state=SEED))

fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
ax[0].plot(list(ks), inertia, "o-", color="#2E7D6B"); ax[0].set_title("Elbow method")
ax[0].set_xlabel("k"); ax[0].set_ylabel("inertia")
ax[1].plot(list(ks), sil, "o-", color="#C0562B"); ax[1].set_title("Silhouette score")
ax[1].set_xlabel("k")
plt.tight_layout(); plt.savefig("plots/kmeans_k_selection.png", dpi=150); plt.close()

K = 3   # slide 14 shows three behaviour groups
km = KMeans(n_clusters=K, n_init=20, random_state=SEED).fit(Z)
df["cluster_id"] = km.labels_

# name clusters by their average savings rate: highest -> Healthy, lowest -> High Risk
order = df.groupby("cluster_id")["savings_rate"].mean().sort_values(ascending=False).index.tolist()
names = {order[0]: "Financially Healthy", order[1]: "Average Behaviour", order[2]: "High Risk"}
df["behaviour_cluster"] = df["cluster_id"].map(names)

profile = df.groupby("behaviour_cluster")[CLUSTER_FEATURES + ["income"]].mean().round(2)
profile["users"] = df.behaviour_cluster.value_counts()
print("\n=== K-Means cluster profiles (k=3) ===\n", profile)
profile.to_csv("cluster_profiles.csv")
metrics["kmeans"] = dict(k=K, silhouette=round(float(sil[K - 2]), 4),
                         sizes=df.behaviour_cluster.value_counts().to_dict())

fig, ax = plt.subplots(figsize=(7, 5))
colors = {"Financially Healthy": "#2E7D6B", "Average Behaviour": "#E0A526", "High Risk": "#C0392B"}
for n, g in df.groupby("behaviour_cluster"):
    ax.scatter(g.savings_rate, g.expense_ratio, s=6, alpha=.5, label=n, color=colors[n])
ax.set_xlabel("savings rate (%)"); ax.set_ylabel("expense ratio (%)")
ax.set_title("K-Means behaviour clusters (k=3)"); ax.legend(markerscale=3)
plt.tight_layout(); plt.savefig("plots/clusters.png", dpi=150); plt.close()

joblib.dump({"kmeans": km, "scaler": scaler, "features": CLUSTER_FEATURES,
             "cluster_names": {int(k): v for k, v in names.items()}}, "models/behaviour_kmeans.joblib")

json.dump(metrics, open("metrics.json", "w"), indent=2)
print("\nSaved: models/, plots/, metrics.json, cluster_profiles.csv, decision_tree_rules.txt")

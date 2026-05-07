"""
ABIYAMO - Hybrid Risk Scoring Model
=====================================
Trains an XGBoost classifier on synthetic ANC data.
Combines with rule-based guardrails to form the
complete hybrid risk engine.

Outputs:
- abiyamo_model.pkl         : Trained XGBoost model
- abiyamo_encoder.pkl       : Label encoders for categorical vars
- abiyamo_model_report.txt  : Full evaluation report
- abiyamo_feature_importance.png
- abiyamo_confusion_matrix.png
"""

import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder
from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, f1_score
)
from xgboost import XGBClassifier

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

print("=" * 60)
print("ABIYAMO - Hybrid Risk Scoring Model Training")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 60)


# ─────────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────────

df = pd.read_csv("abiyamo_anc_synthetic.csv")
print(f"\nDataset loaded: {df.shape[0]} records, {df.shape[1]} columns")


# ─────────────────────────────────────────────────
# 2. FEATURE ENGINEERING
# ─────────────────────────────────────────────────

# Ordinal encode urine protein (meaningful order)
protein_order = ["negative", "trace", "1+", "2+", "3+"]
protein_encoder = OrdinalEncoder(categories=[protein_order])
df["urine_protein_enc"] = protein_encoder.fit_transform(df[["urine_protein"]])

# Label encode facility level and geo zone
facility_encoder = LabelEncoder()
geo_encoder = LabelEncoder()
df["facility_level_enc"] = facility_encoder.fit_transform(df["facility_level"])
df["geo_zone_enc"] = geo_encoder.fit_transform(df["geo_zone"])

# Derived features (add clinical signal)
df["pulse_pressure"]    = df["sbp_mmhg"] - df["dbp_mmhg"]
df["map"]               = ((2 * df["dbp_mmhg"]) + df["sbp_mmhg"]) / 3  # Mean Arterial Pressure
df["fh_ga_diff"]        = df["fundal_height_cm"] - df["gestational_age_wks"]  # FH lag indicator
df["anaemia_severity"]  = pd.cut(df["hemoglobin_gdl"],
                                  bins=[0, 7, 9, 11, 20],
                                  labels=[3, 2, 1, 0]).astype(int)  # 3=severe, 0=normal
df["hypertension_flag"] = ((df["sbp_mmhg"] >= 140) | (df["dbp_mmhg"] >= 90)).astype(int)
df["severe_htn_flag"]   = ((df["sbp_mmhg"] >= 160) | (df["dbp_mmhg"] >= 110)).astype(int)
df["symptom_burden"]    = (
    df["symptom_headache"] + df["symptom_oedema"] +
    df["symptom_rfm"] + df["symptom_bleeding"] + df["symptom_epigastric"]
)
df["third_trimester"]   = (df["gestational_age_wks"] >= 28).astype(int)
df["grand_multipara"]   = (df["parity"] >= 5).astype(int)
df["obese"]             = (df["bmi"] >= 30).astype(int)

# Feature set for model
FEATURES = [
    # Core clinical
    "age", "parity", "previous_cs", "previous_loss",
    "gestational_age_wks", "sbp_mmhg", "dbp_mmhg",
    "hemoglobin_gdl", "bmi", "fundal_height_cm",
    "urine_protein_enc", "hiv_status", "malaria_status", "gdm_risk",
    # Symptoms
    "symptom_headache", "symptom_oedema", "symptom_rfm",
    "symptom_bleeding", "symptom_epigastric",
    # Categorical encoded
    "facility_level_enc", "geo_zone_enc",
    # Derived features
    "pulse_pressure", "map", "fh_ga_diff", "anaemia_severity",
    "hypertension_flag", "severe_htn_flag", "symptom_burden",
    "third_trimester", "grand_multipara", "obese"
]

TARGET = "risk_category"

# Encode target (ordinal: Low=0, Moderate=1, High=2, Critical=3)
risk_order = ["Low", "Moderate", "High", "Critical"]
risk_encoder = LabelEncoder()
risk_encoder.classes_ = np.array(risk_order)
df["risk_encoded"] = df[TARGET].map({v: i for i, v in enumerate(risk_order)})

X = df[FEATURES]
y = df["risk_encoded"]

print(f"\nFeatures used: {len(FEATURES)}")
print(f"Target classes: {risk_order}")
print(f"\nClass distribution:")
for cat in risk_order:
    count = (df[TARGET] == cat).sum()
    print(f"  {cat:<12}: {count}")


# ─────────────────────────────────────────────────
# 3. TRAIN / TEST SPLIT
# ─────────────────────────────────────────────────

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTrain size : {len(X_train)}")
print(f"Test size  : {len(X_test)}")


# ─────────────────────────────────────────────────
# 4. TRAIN XGBOOST MODEL
# ─────────────────────────────────────────────────

print("\nTraining XGBoost model...")

model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    use_label_encoder=False,
    eval_metric="mlogloss",
    random_state=42,
    n_jobs=-1
)

model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=False
)

print("Training complete.")


# ─────────────────────────────────────────────────
# 5. EVALUATE
# ─────────────────────────────────────────────────

y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
f1_macro = f1_score(y_test, y_pred, average="macro")
f1_weighted = f1_score(y_test, y_pred, average="weighted")

print(f"\n{'='*40}")
print("MODEL PERFORMANCE")
print(f"{'='*40}")
print(f"Accuracy        : {accuracy:.4f} ({accuracy*100:.1f}%)")
print(f"F1 (macro)      : {f1_macro:.4f}")
print(f"F1 (weighted)   : {f1_weighted:.4f}")

# Cross-validation
cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
print(f"\n5-Fold CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

# Per-class report
print(f"\nPer-Class Report:")
print(classification_report(
    y_test, y_pred,
    target_names=risk_order,
    digits=3
))


# ─────────────────────────────────────────────────
# 6. RULE-BASED GUARDRAILS
#    Applied AFTER ML scoring to catch critical cases
# ─────────────────────────────────────────────────

def apply_rule_guardrails(row, ml_prediction):
    """
    Clinical rules that override ML output.
    Returns final risk level (0=Low, 1=Moderate, 2=High, 3=Critical)
    """
    # CRITICAL overrides
    if row["sbp_mmhg"] >= 160 or row["dbp_mmhg"] >= 110:
        return 3  # Critical

    if row["hemoglobin_gdl"] < 7.0:
        return 3  # Critical

    if (row["symptom_bleeding"] == 1 and
        row["previous_cs"] == 1 and
        row["gestational_age_wks"] > 24):
        return 3  # Critical

    # HIGH overrides
    if (row["sbp_mmhg"] >= 140 and
        row["urine_protein_enc"] >= 3):  # 2+ or 3+
        return max(ml_prediction, 2)

    if row["hemoglobin_gdl"] < 9.0:
        return max(ml_prediction, 2)

    # Otherwise trust ML
    return ml_prediction

# Apply hybrid logic on test set
X_test_df = X_test.copy()
hybrid_predictions = []
for idx, row in X_test_df.iterrows():
    ml_pred = model.predict(row.values.reshape(1, -1))[0]
    hybrid_pred = apply_rule_guardrails(row, ml_pred)
    hybrid_predictions.append(hybrid_pred)

hybrid_predictions = np.array(hybrid_predictions)

hybrid_accuracy = accuracy_score(y_test, hybrid_predictions)
hybrid_f1 = f1_score(y_test, hybrid_predictions, average="weighted")

print(f"\n{'='*40}")
print("HYBRID MODEL PERFORMANCE (Rules + ML)")
print(f"{'='*40}")
print(f"Accuracy        : {hybrid_accuracy:.4f} ({hybrid_accuracy*100:.1f}%)")
print(f"F1 (weighted)   : {hybrid_f1:.4f}")
print(f"\nHybrid Per-Class Report:")
print(classification_report(
    y_test, hybrid_predictions,
    target_names=risk_order,
    digits=3
))


# ─────────────────────────────────────────────────
# 7. VISUALISATIONS
# ─────────────────────────────────────────────────

TEAL   = "#007B85"
ORANGE = "#E8620A"
DARK   = "#1A1A2E"
COLORS = [TEAL, ORANGE, "#2E8B57", "#8B0000"]

# -- 7a. Feature Importance
importances = pd.Series(model.feature_importances_, index=FEATURES)
importances = importances.sort_values(ascending=True).tail(20)

fig, ax = plt.subplots(figsize=(10, 8))
bars = ax.barh(importances.index, importances.values, color=TEAL, edgecolor="white", linewidth=0.5)
ax.set_title("ABIYAMO - Feature Importance (Top 20)", fontsize=14, fontweight="bold", color=DARK, pad=15)
ax.set_xlabel("Importance Score", fontsize=11, color=DARK)
ax.tick_params(colors=DARK, labelsize=9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_facecolor("#F9F9F9")
fig.patch.set_facecolor("white")
plt.tight_layout()
plt.savefig("abiyamo_feature_importance.png", dpi=150, bbox_inches="tight")
plt.close()
print("\nSaved: abiyamo_feature_importance.png")

# -- 7b. Confusion Matrix (Hybrid)
cm = confusion_matrix(y_test, hybrid_predictions)
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(
    cm, annot=True, fmt="d", cmap="YlOrRd",
    xticklabels=risk_order, yticklabels=risk_order,
    linewidths=0.5, ax=ax
)
ax.set_title("ABIYAMO - Hybrid Model Confusion Matrix", fontsize=13, fontweight="bold", color=DARK, pad=15)
ax.set_xlabel("Predicted Risk", fontsize=11, color=DARK)
ax.set_ylabel("Actual Risk", fontsize=11, color=DARK)
plt.tight_layout()
plt.savefig("abiyamo_confusion_matrix.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: abiyamo_confusion_matrix.png")

# -- 7c. Risk Distribution Bar Chart
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
risk_vals = df["risk_category"].value_counts().reindex(risk_order)

axes[0].bar(risk_order, risk_vals.values, color=[TEAL, ORANGE, "#2E8B57", "#8B0000"], edgecolor="white")
axes[0].set_title("Dataset Risk Distribution", fontsize=12, fontweight="bold", color=DARK)
axes[0].set_ylabel("Count", color=DARK)
axes[0].set_facecolor("#F9F9F9")
axes[0].spines["top"].set_visible(False)
axes[0].spines["right"].set_visible(False)
for i, v in enumerate(risk_vals.values):
    axes[0].text(i, v + 3, str(v), ha="center", fontsize=10, color=DARK)

# Hemoglobin by risk category
for i, cat in enumerate(risk_order):
    vals = df[df["risk_category"] == cat]["hemoglobin_gdl"]
    axes[1].scatter([i]*len(vals), vals, alpha=0.3, color=COLORS[i], s=10)
axes[1].boxplot(
    [df[df["risk_category"] == cat]["hemoglobin_gdl"].values for cat in risk_order],
    positions=range(4), patch_artist=True,
    boxprops=dict(facecolor="white", color=DARK),
    medianprops=dict(color=ORANGE, linewidth=2),
    whiskerprops=dict(color=DARK),
    capprops=dict(color=DARK)
)
axes[1].set_xticks(range(4))
axes[1].set_xticklabels(risk_order)
axes[1].set_title("Hemoglobin Distribution by Risk Category", fontsize=12, fontweight="bold", color=DARK)
axes[1].set_ylabel("Hemoglobin (g/dL)", color=DARK)
axes[1].axhline(y=11, color=TEAL, linestyle="--", alpha=0.7, label="Mild anaemia threshold")
axes[1].axhline(y=7, color="#8B0000", linestyle="--", alpha=0.7, label="Severe anaemia threshold")
axes[1].legend(fontsize=8)
axes[1].set_facecolor("#F9F9F9")
axes[1].spines["top"].set_visible(False)
axes[1].spines["right"].set_visible(False)

fig.patch.set_facecolor("white")
plt.tight_layout()
plt.savefig("abiyamo_risk_analysis.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: abiyamo_risk_analysis.png")


# ─────────────────────────────────────────────────
# 8. SAVE MODEL & ENCODERS
# ─────────────────────────────────────────────────

with open("abiyamo_model.pkl", "wb") as f:
    pickle.dump(model, f)

encoders = {
    "protein_encoder": protein_encoder,
    "facility_encoder": facility_encoder,
    "geo_encoder": geo_encoder,
    "risk_encoder": risk_encoder,
    "risk_order": risk_order,
    "features": FEATURES
}
with open("abiyamo_encoders.pkl", "wb") as f:
    pickle.dump(encoders, f)

print("\nSaved: abiyamo_model.pkl")
print("Saved: abiyamo_encoders.pkl")


# ─────────────────────────────────────────────────
# 9. SAVE REPORT
# ─────────────────────────────────────────────────

report_lines = [
    "=" * 60,
    "ABIYAMO - Model Evaluation Report",
    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    "=" * 60,
    f"\nXGBoost Model Accuracy   : {accuracy*100:.1f}%",
    f"XGBoost F1 (weighted)    : {f1_weighted:.4f}",
    f"5-Fold CV Accuracy       : {cv_scores.mean()*100:.1f}% (+/- {cv_scores.std()*100:.1f}%)",
    f"\nHybrid Model Accuracy    : {hybrid_accuracy*100:.1f}%",
    f"Hybrid F1 (weighted)     : {hybrid_f1:.4f}",
    "\n--- FEATURES USED ---",
    *[f"  {f}" for f in FEATURES],
    "\n--- RULE GUARDRAILS ---",
    "  Critical: SBP >= 160 OR DBP >= 110",
    "  Critical: Hemoglobin < 7.0 g/dL",
    "  Critical: Bleeding + Previous CS + GA > 24wks",
    "  High:     SBP >= 140 AND Urine Protein 2+ or 3+",
    "  High:     Hemoglobin < 9.0 g/dL",
    "\n" + "=" * 60
]

with open("abiyamo_model_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

print("Saved: abiyamo_model_report.txt")
print("\n" + "=" * 60)
print("ABIYAMO model training complete.")
print("=" * 60)

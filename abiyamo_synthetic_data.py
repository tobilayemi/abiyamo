"""
ABIYAMO - Synthetic ANC Dataset Generator
==========================================
Generates realistic synthetic Antenatal Care (ANC) records
calibrated to Nigerian clinical distributions.

Outputs:
- abiyamo_anc_synthetic.csv  : Full dataset (1000 records)
- abiyamo_anc_summary.txt    : Distribution summary report
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

N = 1000  # number of records

# ─────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def bernoulli(p):
    return np.random.binomial(1, p, N)

def choice_weighted(options, weights):
    return np.random.choice(options, size=N, p=weights)


# ─────────────────────────────────────────────────
# 1. DEMOGRAPHIC VARIABLES
# ─────────────────────────────────────────────────

patient_ids = [f"ABY-{str(i).zfill(5)}" for i in range(1, N+1)]

# Age: 15-45, peak around 22-28 (Nigerian ANC profile)
age = np.clip(np.random.normal(loc=26, scale=6, size=N).astype(int), 15, 45)

# Parity: 0-8, higher parity more common in Nigeria
parity = np.random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8],
                           size=N,
                           p=[0.25, 0.22, 0.18, 0.14, 0.09, 0.06, 0.03, 0.02, 0.01])

# Previous CS (more likely with higher parity and age)
prev_cs_prob = np.where(parity >= 1, 0.18, 0.05)
previous_cs = np.array([bernoulli(p)[0] for p in prev_cs_prob])

# Previous pregnancy loss
prev_loss_prob = np.where(parity >= 2, 0.25, 0.10)
previous_loss = np.array([bernoulli(p)[0] for p in prev_loss_prob])

# Facility level
facility_level = choice_weighted(
    ["PHC", "Secondary", "Tertiary"],
    [0.60, 0.30, 0.10]
)

# Geopolitical zone
geo_zone = choice_weighted(
    ["North-West", "North-East", "North-Central", "South-West", "South-East", "South-South"],
    [0.25, 0.15, 0.15, 0.20, 0.12, 0.13]
)


# ─────────────────────────────────────────────────
# 2. CLINICAL MEASUREMENTS
# ─────────────────────────────────────────────────

# Gestational Age (weeks): 8-40
gestational_age = np.clip(np.random.normal(loc=26, scale=9, size=N).astype(int), 8, 40)

# Blood Pressure
# SBP: normal ~115, elevated in ~15% of Nigerian pregnancies
sbp_base = np.random.normal(loc=116, scale=14, size=N)
# Add hypertensive cases
hypertensive_idx = np.random.choice(N, size=int(N * 0.15), replace=False)
sbp_base[hypertensive_idx] += np.random.normal(35, 12, len(hypertensive_idx))
sbp = np.clip(sbp_base, 80, 200).astype(int)

dbp_base = np.random.normal(loc=74, scale=10, size=N)
dbp_base[hypertensive_idx] += np.random.normal(22, 8, len(hypertensive_idx))
dbp = np.clip(dbp_base, 50, 130).astype(int)

# Hemoglobin (g/dL): anaemia very common in Nigeria (~35-40% of pregnant women)
hb_base = np.random.normal(loc=10.8, scale=1.8, size=N)
# Some severe anaemia cases
severe_anaemia_idx = np.random.choice(N, size=int(N * 0.08), replace=False)
hb_base[severe_anaemia_idx] = np.random.normal(6.2, 0.8, len(severe_anaemia_idx))
hemoglobin = np.clip(hb_base, 4.0, 15.0).round(1)

# BMI (kg/m²): mean ~24 in pregnant Nigerian women
bmi = np.clip(np.random.normal(loc=24.5, scale=4.5, size=N), 16.0, 45.0).round(1)

# Fundal Height (cm): correlates with gestational age ± clinical variation
fundal_height_expected = gestational_age  # 1cm per week approximation
fundal_height_noise = np.random.normal(0, 2.5, N)
fundal_height = np.clip(fundal_height_expected + fundal_height_noise, 10, 40).round(1)

# Urine Protein (dipstick)
# Negative in most, elevated in hypertensive cases
protein_options = ["negative", "trace", "1+", "2+", "3+"]
urine_protein = []
for i in range(N):
    if i in hypertensive_idx and sbp[i] >= 140:
        p = np.random.choice(protein_options, p=[0.30, 0.20, 0.20, 0.20, 0.10])
    else:
        p = np.random.choice(protein_options, p=[0.75, 0.12, 0.07, 0.04, 0.02])
    urine_protein.append(p)
urine_protein = np.array(urine_protein)


# ─────────────────────────────────────────────────
# 3. COMORBIDITIES
# ─────────────────────────────────────────────────

# HIV prevalence ~1.5% in Nigerian pregnant women (PMTCT context)
hiv_status = bernoulli(0.015)

# Malaria: ~25% in endemic zones, ~8% overall
malaria_base_prob = np.where(
    np.isin(geo_zone, ["South-South", "South-East", "North-West"]), 0.28, 0.10
)
malaria_status = np.array([bernoulli(p)[0] for p in malaria_base_prob])

# Gestational Diabetes (screening indicator): ~5%
gdm_risk = bernoulli(0.05)


# ─────────────────────────────────────────────────
# 4. SYMPTOMS
# ─────────────────────────────────────────────────

# Headache: more common in hypertensive cases
headache_prob = np.where(sbp >= 140, 0.55, 0.12)
symptom_headache = np.array([bernoulli(p)[0] for p in headache_prob])

# Oedema: common in pre-eclampsia and late pregnancy
oedema_prob = np.where((sbp >= 140) & (gestational_age > 28), 0.60,
              np.where(gestational_age > 28, 0.20, 0.08))
symptom_oedema = np.array([bernoulli(p)[0] for p in oedema_prob])

# Reduced fetal movement (third trimester concern)
rfm_prob = np.where(gestational_age >= 28, 0.10, 0.01)
symptom_rfm = np.array([bernoulli(p)[0] for p in rfm_prob])

# Vaginal bleeding
bleeding_prob = np.where(
    (previous_cs == 1) & (gestational_age > 24), 0.08,
    np.where(gestational_age < 12, 0.07, 0.03)
)
symptom_bleeding = np.array([bernoulli(p)[0] for p in bleeding_prob])

# Epigastric pain (HELLP/severe pre-eclampsia marker)
epigastric_prob = np.where(sbp >= 160, 0.30, 0.04)
symptom_epigastric = np.array([bernoulli(p)[0] for p in epigastric_prob])


# ─────────────────────────────────────────────────
# 5. RULE-BASED RISK CLASSIFICATION
#    (Ground truth labels for ML training)
# ─────────────────────────────────────────────────

def classify_risk(i):
    """
    Hybrid rule engine based on WHO ANC guidelines
    and Nigerian clinical protocols.
    Returns: (risk_category, primary_condition, icd11_code)
    """
    sbp_val = sbp[i]
    dbp_val = dbp[i]
    hb_val  = hemoglobin[i]
    ga      = gestational_age[i]
    prot    = urine_protein[i]
    bmi_val = bmi[i]
    fh      = fundal_height[i]

    # ── CRITICAL ──────────────────────────────────────────────────────────
    # Severe pre-eclampsia
    if sbp_val >= 160 or dbp_val >= 110:
        if prot in ["2+", "3+"]:
            return ("Critical", "Severe Pre-eclampsia", "JA24.3")
        if symptom_headache[i] or symptom_oedema[i] or symptom_epigastric[i]:
            return ("Critical", "Severe Hypertension in Pregnancy", "JA24.3")

    # Severe anaemia
    if hb_val < 7.0:
        return ("Critical", "Severe Anaemia in Pregnancy", "JA43")

    # Antepartum haemorrhage with prior CS
    if symptom_bleeding[i] and previous_cs[i] and ga > 24:
        return ("Critical", "Antepartum Haemorrhage / Placenta Risk", "JA60")

    # ── HIGH ──────────────────────────────────────────────────────────────
    # Pre-eclampsia
    if sbp_val >= 140 and prot in ["2+", "3+"]:
        return ("High", "Pre-eclampsia", "JA24.2")

    # Moderate-severe anaemia
    if hb_val < 9.0:
        return ("High", "Moderate-Severe Anaemia", "JA42")

    # Fetal growth restriction (fundal height lagging by >4cm)
    if fh < (ga - 4) and ga >= 20:
        return ("High", "Fetal Growth Restriction", "JA65")

    # Reduced fetal movement in 3rd trimester
    if symptom_rfm[i] and ga >= 28:
        return ("High", "Reduced Fetal Movement", "JA65")

    # Malaria in pregnancy
    if malaria_status[i]:
        return ("High", "Malaria in Pregnancy", "1A44.Z")

    # HIV in pregnancy
    if hiv_status[i]:
        return ("High", "HIV in Pregnancy - PMTCT Required", "1C62.Z")

    # ── MODERATE ──────────────────────────────────────────────────────────
    # Gestational hypertension
    if sbp_val >= 140 or dbp_val >= 90:
        return ("Moderate", "Gestational Hypertension", "JA24.1")

    # Mild anaemia
    if hb_val < 11.0:
        return ("Moderate", "Mild Anaemia in Pregnancy", "JA42")

    # Grand multiparity risk
    if parity[i] >= 5:
        return ("Moderate", "Grand Multiparity", "JA00")

    # Obese pregnancy
    if bmi_val >= 30:
        return ("Moderate", "Obesity in Pregnancy", "JA00")

    # Gestational diabetes risk
    if gdm_risk[i] and bmi_val >= 27:
        return ("Moderate", "Gestational Diabetes Risk", "JA63")

    # Previous CS without complications
    if previous_cs[i]:
        return ("Moderate", "Previous Caesarean Section", "JA00")

    # ── LOW ───────────────────────────────────────────────────────────────
    return ("Low", "Routine ANC - No Significant Risk", "Z34")


# Apply classification
risk_results = [classify_risk(i) for i in range(N)]
risk_category   = [r[0] for r in risk_results]
primary_condition = [r[1] for r in risk_results]
icd11_code      = [r[2] for r in risk_results]


# ─────────────────────────────────────────────────
# 6. ASSEMBLE DATAFRAME
# ─────────────────────────────────────────────────

df = pd.DataFrame({
    "patient_id":         patient_ids,
    "age":                age,
    "parity":             parity,
    "previous_cs":        previous_cs,
    "previous_loss":      previous_loss,
    "facility_level":     facility_level,
    "geo_zone":           geo_zone,
    "gestational_age_wks": gestational_age,
    "sbp_mmhg":           sbp,
    "dbp_mmhg":           dbp,
    "hemoglobin_gdl":     hemoglobin,
    "bmi":                bmi,
    "fundal_height_cm":   fundal_height,
    "urine_protein":      urine_protein,
    "hiv_status":         hiv_status,
    "malaria_status":     malaria_status,
    "gdm_risk":           gdm_risk,
    "symptom_headache":   symptom_headache,
    "symptom_oedema":     symptom_oedema,
    "symptom_rfm":        symptom_rfm,
    "symptom_bleeding":   symptom_bleeding,
    "symptom_epigastric": symptom_epigastric,
    "risk_category":      risk_category,
    "primary_condition":  primary_condition,
    "icd11_code":         icd11_code,
})

# ─────────────────────────────────────────────────
# 7. SAVE CSV
# ─────────────────────────────────────────────────

df.to_csv("abiyamo_anc_synthetic.csv", index=False)

# ─────────────────────────────────────────────────
# 8. SUMMARY REPORT
# ─────────────────────────────────────────────────

report = []
report.append("=" * 60)
report.append("ABIYAMO - Synthetic ANC Dataset Summary")
report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
report.append(f"Total Records: {N}")
report.append("=" * 60)

report.append("\n--- RISK DISTRIBUTION ---")
risk_counts = df["risk_category"].value_counts()
for cat in ["Critical", "High", "Moderate", "Low"]:
    count = risk_counts.get(cat, 0)
    pct = round(count / N * 100, 1)
    report.append(f"  {cat:<12}: {count:>4}  ({pct}%)")

report.append("\n--- TOP CONDITIONS ---")
cond_counts = df["primary_condition"].value_counts().head(10)
for cond, count in cond_counts.items():
    report.append(f"  {cond:<45}: {count}")

report.append("\n--- KEY CLINICAL STATS ---")
report.append(f"  Mean Age                : {df['age'].mean():.1f} yrs")
report.append(f"  Mean Gestational Age    : {df['gestational_age_wks'].mean():.1f} wks")
report.append(f"  Mean Hemoglobin         : {df['hemoglobin_gdl'].mean():.1f} g/dL")
report.append(f"  Anaemia (Hb < 11)       : {(df['hemoglobin_gdl'] < 11).sum()} ({(df['hemoglobin_gdl'] < 11).mean()*100:.1f}%)")
report.append(f"  Severe Anaemia (Hb < 7) : {(df['hemoglobin_gdl'] < 7).sum()} ({(df['hemoglobin_gdl'] < 7).mean()*100:.1f}%)")
report.append(f"  Hypertension (SBP≥140)  : {(df['sbp_mmhg'] >= 140).sum()} ({(df['sbp_mmhg'] >= 140).mean()*100:.1f}%)")
report.append(f"  HIV Positive            : {df['hiv_status'].sum()} ({df['hiv_status'].mean()*100:.1f}%)")
report.append(f"  Malaria Positive        : {df['malaria_status'].sum()} ({df['malaria_status'].mean()*100:.1f}%)")

report.append("\n--- FACILITY DISTRIBUTION ---")
for fac, count in df["facility_level"].value_counts().items():
    report.append(f"  {fac:<15}: {count}")

report.append("\n--- ICD-11 CODE DISTRIBUTION ---")
icd_counts = df["icd11_code"].value_counts()
for code, count in icd_counts.items():
    report.append(f"  {code:<12}: {count}")

report.append("\n" + "=" * 60)
report.append("Files saved:")
report.append("  abiyamo_anc_synthetic.csv")
report.append("=" * 60)

report_text = "\n".join(report)
print(report_text)

with open("abiyamo_anc_summary.txt", "w", encoding="utf-8") as f:
    f.write(report_text)

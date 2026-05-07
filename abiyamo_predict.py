"""
ABIYAMO - Patient Risk Prediction Interface
============================================
Takes ANC input for a single patient and returns:
  - Risk Category (Low / Moderate / High / Critical)
  - Primary Condition
  - ICD-11 Code
  - Danger Explanation
  - Immediate Clinical Actions
  - Referral Recommendation

Usage:
  python abiyamo_predict.py
"""

import pickle
import numpy as np
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────────
# LOAD MODEL & ENCODERS
# ─────────────────────────────────────────────────

with open("abiyamo_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("abiyamo_encoders.pkl", "rb") as f:
    enc = pickle.load(f)

protein_encoder  = enc["protein_encoder"]
facility_encoder = enc["facility_encoder"]
geo_encoder      = enc["geo_encoder"]
risk_order       = enc["risk_order"]
FEATURES         = enc["features"]


# ─────────────────────────────────────────────────
# CLINICAL ACTION LIBRARY
# ─────────────────────────────────────────────────

CLINICAL_GUIDANCE = {
    "Critical": {
        "Severe Pre-eclampsia": {
            "icd11": "JA24.3",
            "explanation": "Severely elevated blood pressure with protein in urine. High risk of seizure (eclampsia), stroke, and fetal compromise.",
            "actions": [
                "Administer magnesium sulphate (MgSO4) immediately per protocol",
                "Give antihypertensive (Hydralazine or Nifedipine) if SBP >= 160",
                "Insert IV line and monitor urine output",
                "Do NOT leave patient alone",
                "Prepare for emergency delivery if gestation allows"
            ],
            "referral": "EMERGENCY referral to secondary/tertiary facility NOW"
        },
        "Severe Hypertension in Pregnancy": {
            "icd11": "JA24.3",
            "explanation": "Severely elevated blood pressure with danger signs. Immediate risk of eclamptic seizure.",
            "actions": [
                "Lay patient on left side, protect airway",
                "Administer antihypertensive immediately",
                "Administer MgSO4 as seizure prophylaxis",
                "Monitor BP every 15 minutes",
                "Fetal heart rate assessment"
            ],
            "referral": "EMERGENCY referral to secondary/tertiary facility NOW"
        },
        "Severe Anaemia in Pregnancy": {
            "icd11": "JA43",
            "explanation": "Critically low hemoglobin. High risk of heart failure, preterm labour, and maternal death.",
            "actions": [
                "Assess for signs of cardiac decompensation (breathlessness, tachycardia)",
                "Insert IV line",
                "Arrange urgent blood transfusion",
                "Treat underlying cause (malaria, hookworm, sickle cell)",
                "Oxygen supplementation if available"
            ],
            "referral": "URGENT referral to facility with blood bank"
        },
        "Antepartum Haemorrhage / Placenta Risk": {
            "icd11": "JA60",
            "explanation": "Vaginal bleeding with prior CS raises risk of placenta praevia or abruption. Life-threatening for mother and baby.",
            "actions": [
                "Do NOT perform vaginal examination",
                "Insert large-bore IV line",
                "Monitor maternal vitals every 5-10 minutes",
                "Fetal heart rate assessment immediately",
                "Keep patient nil by mouth"
            ],
            "referral": "EMERGENCY referral to tertiary facility with theatre capability"
        }
    },
    "High": {
        "Pre-eclampsia": {
            "icd11": "JA24.2",
            "explanation": "Elevated BP with significant proteinuria. Risk of progression to severe pre-eclampsia and eclampsia.",
            "actions": [
                "Confirm BP reading after 15 minutes rest",
                "Repeat urine protein test",
                "Initiate antihypertensive if BP persistently >= 150/100",
                "Assess fetal wellbeing",
                "Review at minimum weekly until delivery"
            ],
            "referral": "Urgent referral to secondary facility within 24 hours"
        },
        "Moderate-Severe Anaemia": {
            "icd11": "JA42",
            "explanation": "Hemoglobin below 9 g/dL. Significant risk of maternal complications and poor fetal growth.",
            "actions": [
                "Test for malaria, sickle cell, and hookworm",
                "Start oral iron and folate immediately",
                "Nutritional counselling (iron-rich foods)",
                "Recheck hemoglobin in 4 weeks",
                "Consider parenteral iron if oral not tolerated"
            ],
            "referral": "Referral to secondary facility if Hb < 8 g/dL or not improving"
        },
        "Fetal Growth Restriction": {
            "icd11": "JA65",
            "explanation": "Fundal height lagging behind gestational age. Baby may not be growing adequately.",
            "actions": [
                "Refer for obstetric ultrasound to confirm",
                "Assess maternal nutrition and weight gain",
                "Screen for hypertension and anaemia",
                "Increase ANC frequency to every 2 weeks",
                "Counsel on danger signs of reduced movement"
            ],
            "referral": "Referral for ultrasound within 1 week"
        },
        "Reduced Fetal Movement": {
            "icd11": "JA65",
            "explanation": "Reduced fetal movement in the third trimester may indicate fetal distress.",
            "actions": [
                "Perform fetal heart rate auscultation immediately",
                "Advise kick count monitoring (>10 movements in 2 hours)",
                "Assess for other danger signs",
                "If FHR abnormal: emergency referral"
            ],
            "referral": "Urgent referral if fetal heart rate abnormal or movement absent"
        },
        "Malaria in Pregnancy": {
            "icd11": "1A44.Z",
            "explanation": "Active malaria in pregnancy risks maternal anaemia, low birth weight, and preterm labour.",
            "actions": [
                "Initiate artemisinin-based therapy (ACT) per trimester protocol",
                "Check hemoglobin",
                "Ensure ITN (insecticide treated net) use",
                "Monitor for treatment response in 48 hours",
                "Continue IPTp-SP schedule"
            ],
            "referral": "Referral if severe malaria features (altered consciousness, high fever, severe anaemia)"
        },
        "HIV in Pregnancy - PMTCT Required": {
            "icd11": "1C62.Z",
            "explanation": "HIV positive status requires PMTCT protocol to protect baby from mother-to-child transmission.",
            "actions": [
                "Confirm ART enrollment and adherence",
                "Viral load assessment if not done recently",
                "Counsel on exclusive breastfeeding vs replacement feeding",
                "Partner HIV testing",
                "Infant prophylaxis plan at delivery"
            ],
            "referral": "Referral to PMTCT-capable facility if not enrolled in ART"
        }
    },
    "Moderate": {
        "Gestational Hypertension": {
            "icd11": "JA24.1",
            "explanation": "Elevated blood pressure without proteinuria. Requires close monitoring for progression to pre-eclampsia.",
            "actions": [
                "Confirm BP on second reading after 15 minutes rest",
                "Check urine protein",
                "Advise rest and reduced salt intake",
                "Return in 1 week for BP recheck",
                "Educate on danger signs: headache, visual changes, oedema"
            ],
            "referral": "Refer to secondary facility if BP rises or symptoms develop"
        },
        "Mild Anaemia in Pregnancy": {
            "icd11": "JA42",
            "explanation": "Hemoglobin below normal for pregnancy. Requires treatment to prevent worsening.",
            "actions": [
                "Start oral iron (ferrous sulphate) and folic acid",
                "Dietary counselling: beans, green leafy vegetables, meat",
                "Treat malaria if present",
                "Recheck hemoglobin at next ANC visit",
                "Deworming if indicated"
            ],
            "referral": "No immediate referral. Review at next scheduled visit"
        },
        "Grand Multiparity": {
            "icd11": "JA00",
            "explanation": "Five or more previous pregnancies increases risk of postpartum haemorrhage, malpresentation, and obstructed labour.",
            "actions": [
                "Increase ANC frequency in third trimester",
                "Confirm fetal presentation at 36 weeks",
                "Delivery plan discussion (facility delivery strongly advised)",
                "Counsel on active management of third stage of labour",
                "Family planning counselling postpartum"
            ],
            "referral": "Plan delivery at secondary facility minimum"
        },
        "Obesity in Pregnancy": {
            "icd11": "JA00",
            "explanation": "BMI >= 30 in pregnancy increases risk of gestational diabetes, hypertension, and caesarean section.",
            "actions": [
                "GDM screening (glucose tolerance test)",
                "Dietary and physical activity counselling",
                "Monitor BP at each visit",
                "Fetal growth monitoring",
                "Thromboprophylaxis discussion"
            ],
            "referral": "Referral if GDM confirmed or BP rises"
        },
        "Gestational Diabetes Risk": {
            "icd11": "JA63",
            "explanation": "BMI and risk factors suggest possible gestational diabetes. Needs confirmation.",
            "actions": [
                "Arrange oral glucose tolerance test (OGTT)",
                "Dietary counselling (reduce refined carbohydrates)",
                "Monitor fetal growth",
                "Self-monitoring of blood glucose if test positive",
                "Educate on signs of hyperglycaemia"
            ],
            "referral": "Referral for OGTT and specialist review if confirmed"
        },
        "Previous Caesarean Section": {
            "icd11": "JA00",
            "explanation": "Previous uterine scar increases risk of uterine rupture and placenta praevia in current pregnancy.",
            "actions": [
                "Confirm number and type of previous CS",
                "Screen for placenta praevia (ultrasound if available)",
                "Delivery plan: facility delivery mandatory",
                "Educate on danger signs: bleeding, severe abdominal pain",
                "Do not allow labour to become prolonged"
            ],
            "referral": "Plan delivery at secondary or tertiary facility"
        }
    },
    "Low": {
        "Routine ANC - No Significant Risk": {
            "icd11": "Z34",
            "explanation": "No significant risk factors identified at this visit. Continue routine antenatal care.",
            "actions": [
                "Continue scheduled ANC visits",
                "Maintain iron and folic acid supplementation",
                "Tetanus toxoid immunisation as per schedule",
                "IPTp-SP (intermittent preventive treatment for malaria)",
                "Birth preparedness counselling"
            ],
            "referral": "No referral needed. Next scheduled ANC visit as planned"
        }
    }
}

def get_guidance(risk_cat, condition):
    """Retrieve clinical guidance for a given risk category and condition."""
    cat_guidance = CLINICAL_GUIDANCE.get(risk_cat, {})
    if condition in cat_guidance:
        return cat_guidance[condition]
    # Fallback
    return {
        "icd11": "Z34",
        "explanation": "Please review with a senior clinician.",
        "actions": ["Seek senior clinical review"],
        "referral": "Use clinical judgment"
    }


# ─────────────────────────────────────────────────
# RULE-BASED GUARDRAILS (same as training)
# ─────────────────────────────────────────────────

def apply_rule_guardrails(patient, ml_prediction):
    sbp = patient["sbp_mmhg"]
    dbp = patient["dbp_mmhg"]
    hb  = patient["hemoglobin_gdl"]
    prot_enc = patient["urine_protein_enc"]
    bleed = patient["symptom_bleeding"]
    prev_cs = patient["previous_cs"]
    ga = patient["gestational_age_wks"]

    if sbp >= 160 or dbp >= 110:
        return 3
    if hb < 7.0:
        return 3
    if bleed == 1 and prev_cs == 1 and ga > 24:
        return 3
    if sbp >= 140 and prot_enc >= 3:
        return max(ml_prediction, 2)
    if hb < 9.0:
        return max(ml_prediction, 2)
    return ml_prediction


# ─────────────────────────────────────────────────
# CONDITION RESOLVER
# Maps risk level + clinical profile to condition name
# ─────────────────────────────────────────────────

def resolve_condition(patient, risk_level):
    sbp  = patient["sbp_mmhg"]
    dbp  = patient["dbp_mmhg"]
    hb   = patient["hemoglobin_gdl"]
    prot = patient["urine_protein_raw"]
    ga   = patient["gestational_age_wks"]
    rfm  = patient["symptom_rfm"]
    bleed = patient["symptom_bleeding"]
    prev_cs = patient["previous_cs"]
    mal  = patient["malaria_status"]
    hiv  = patient["hiv_status"]
    bmi  = patient["bmi"]
    par  = patient["parity"]
    gdm  = patient["gdm_risk"]
    fh   = patient["fundal_height_cm"]
    head = patient["symptom_headache"]
    oed  = patient["symptom_oedema"]
    epi  = patient["symptom_epigastric"]

    if risk_level == 3:
        if (sbp >= 160 or dbp >= 110) and prot in ["2+", "3+"]:
            return "Severe Pre-eclampsia"
        if sbp >= 160 or dbp >= 110:
            return "Severe Hypertension in Pregnancy"
        if hb < 7.0:
            return "Severe Anaemia in Pregnancy"
        if bleed and prev_cs and ga > 24:
            return "Antepartum Haemorrhage / Placenta Risk"

    if risk_level == 2:
        if sbp >= 140 and prot in ["2+", "3+"]:
            return "Pre-eclampsia"
        if hb < 9.0:
            return "Moderate-Severe Anaemia"
        if fh < (ga - 4) and ga >= 20:
            return "Fetal Growth Restriction"
        if rfm and ga >= 28:
            return "Reduced Fetal Movement"
        if mal:
            return "Malaria in Pregnancy"
        if hiv:
            return "HIV in Pregnancy - PMTCT Required"

    if risk_level == 1:
        if sbp >= 140 or dbp >= 90:
            return "Gestational Hypertension"
        if hb < 11.0:
            return "Mild Anaemia in Pregnancy"
        if par >= 5:
            return "Grand Multiparity"
        if bmi >= 30:
            return "Obesity in Pregnancy"
        if gdm and bmi >= 27:
            return "Gestational Diabetes Risk"
        if prev_cs:
            return "Previous Caesarean Section"

    return "Routine ANC - No Significant Risk"


# ─────────────────────────────────────────────────
# FEATURE BUILDER
# ─────────────────────────────────────────────────

def build_features(patient):
    """Convert raw patient input into model feature vector."""
    prot_enc = protein_encoder.transform([[patient["urine_protein_raw"]]])[0][0]
    fac_enc  = facility_encoder.transform([patient["facility_level"]])[0]
    geo_enc  = geo_encoder.transform([patient["geo_zone"]])[0]

    sbp = patient["sbp_mmhg"]
    dbp = patient["dbp_mmhg"]
    hb  = patient["hemoglobin_gdl"]
    ga  = patient["gestational_age_wks"]
    fh  = patient["fundal_height_cm"]
    bmi = patient["bmi"]

    if hb >= 11:
        anaemia_sev = 0
    elif hb >= 9:
        anaemia_sev = 1
    elif hb >= 7:
        anaemia_sev = 2
    else:
        anaemia_sev = 3

    row = {
        "age":                  patient["age"],
        "parity":               patient["parity"],
        "previous_cs":          patient["previous_cs"],
        "previous_loss":        patient["previous_loss"],
        "gestational_age_wks":  ga,
        "sbp_mmhg":             sbp,
        "dbp_mmhg":             dbp,
        "hemoglobin_gdl":       hb,
        "bmi":                  bmi,
        "fundal_height_cm":     fh,
        "urine_protein_enc":    prot_enc,
        "hiv_status":           patient["hiv_status"],
        "malaria_status":       patient["malaria_status"],
        "gdm_risk":             patient["gdm_risk"],
        "symptom_headache":     patient["symptom_headache"],
        "symptom_oedema":       patient["symptom_oedema"],
        "symptom_rfm":          patient["symptom_rfm"],
        "symptom_bleeding":     patient["symptom_bleeding"],
        "symptom_epigastric":   patient["symptom_epigastric"],
        "facility_level_enc":   fac_enc,
        "geo_zone_enc":         geo_enc,
        "pulse_pressure":       sbp - dbp,
        "map":                  ((2 * dbp) + sbp) / 3,
        "fh_ga_diff":           fh - ga,
        "anaemia_severity":     anaemia_sev,
        "hypertension_flag":    int(sbp >= 140 or dbp >= 90),
        "severe_htn_flag":      int(sbp >= 160 or dbp >= 110),
        "symptom_burden":       sum([
                                    patient["symptom_headache"],
                                    patient["symptom_oedema"],
                                    patient["symptom_rfm"],
                                    patient["symptom_bleeding"],
                                    patient["symptom_epigastric"]
                                ]),
        "third_trimester":      int(ga >= 28),
        "grand_multipara":      int(patient["parity"] >= 5),
        "obese":                int(bmi >= 30),
    }
    return pd.DataFrame([row])[FEATURES]


# ─────────────────────────────────────────────────
# PREDICT FUNCTION
# ─────────────────────────────────────────────────

RISK_LABELS = {0: "LOW", 1: "MODERATE", 2: "HIGH", 3: "CRITICAL"}
RISK_COLORS = {
    "LOW":      "\033[92m",   # Green
    "MODERATE": "\033[93m",   # Yellow
    "HIGH":     "\033[91m",   # Red
    "CRITICAL": "\033[95m"    # Magenta
}
RESET = "\033[0m"
BOLD  = "\033[1m"

def predict(patient):
    """
    Run hybrid prediction for a single patient.
    Returns structured risk output.
    """
    X = build_features(patient)
    ml_pred = model.predict(X)[0]
    ml_proba = model.predict_proba(X)[0]

    # Attach encoded protein for guardrail
    patient["urine_protein_enc"] = X["urine_protein_enc"].values[0]

    final_pred = apply_rule_guardrails(patient, ml_pred)
    risk_label = RISK_LABELS[final_pred]
    risk_name  = risk_order[final_pred]
    condition  = resolve_condition(patient, final_pred)
    guidance   = get_guidance(risk_name, condition)

    return {
        "risk_level":    final_pred,
        "risk_label":    risk_label,
        "risk_name":     risk_name,
        "condition":     condition,
        "icd11_code":    guidance["icd11"],
        "explanation":   guidance["explanation"],
        "actions":       guidance["actions"],
        "referral":      guidance["referral"],
        "ml_pred":       ml_pred,
        "rule_override": final_pred != ml_pred,
        "probabilities": {risk_order[i]: round(float(p), 3) for i, p in enumerate(ml_proba)}
    }


def print_result(patient_id, result):
    """Pretty print the Abiyamo risk output to terminal."""
    color = RISK_COLORS.get(result["risk_label"], "")
    print("\n" + "=" * 60)
    print(f"{BOLD}ABIYAMO RISK ASSESSMENT{RESET}")
    print(f"Patient ID : {patient_id}")
    print(f"Timestamp  : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    print(f"\n{BOLD}RISK CATEGORY:{RESET} {color}{BOLD}{result['risk_label']}{RESET}")
    print(f"{BOLD}Condition    :{RESET} {result['condition']}")
    print(f"{BOLD}ICD-11 Code  :{RESET} {result['icd11_code']}")

    if result["rule_override"]:
        print(f"\n  [Rule Override Applied: ML={RISK_LABELS[result['ml_pred']]} -> Final={result['risk_label']}]")

    print(f"\n{BOLD}EXPLANATION:{RESET}")
    print(f"  {result['explanation']}")

    print(f"\n{BOLD}IMMEDIATE ACTIONS:{RESET}")
    for i, action in enumerate(result["actions"], 1):
        print(f"  {i}. {action}")

    print(f"\n{BOLD}REFERRAL:{RESET}")
    print(f"  {result['referral']}")

    print(f"\n{BOLD}Risk Probabilities (ML):{RESET}")
    for cat, prob in result["probabilities"].items():
        bar = "█" * int(prob * 30)
        print(f"  {cat:<10}: {bar:<30} {prob:.1%}")

    print("=" * 60)


# ─────────────────────────────────────────────────
# TEST CASES
# ─────────────────────────────────────────────────

test_patients = [
    {
        "id": "TEST-001",
        "label": "Severe Pre-eclampsia Case",
        "data": {
            "age": 28, "parity": 2, "previous_cs": 0, "previous_loss": 0,
            "facility_level": "Secondary", "geo_zone": "South-West",
            "gestational_age_wks": 34, "sbp_mmhg": 168, "dbp_mmhg": 112,
            "hemoglobin_gdl": 10.5, "bmi": 26.2, "fundal_height_cm": 33.0,
            "urine_protein_raw": "3+", "hiv_status": 0, "malaria_status": 0,
            "gdm_risk": 0, "symptom_headache": 1, "symptom_oedema": 1,
            "symptom_rfm": 0, "symptom_bleeding": 0, "symptom_epigastric": 1
        }
    },
    {
        "id": "TEST-002",
        "label": "Severe Anaemia Case",
        "data": {
            "age": 22, "parity": 1, "previous_cs": 0, "previous_loss": 0,
            "facility_level": "PHC", "geo_zone": "North-West",
            "gestational_age_wks": 24, "sbp_mmhg": 108, "dbp_mmhg": 70,
            "hemoglobin_gdl": 5.8, "bmi": 21.5, "fundal_height_cm": 23.0,
            "urine_protein_raw": "negative", "hiv_status": 0, "malaria_status": 1,
            "gdm_risk": 0, "symptom_headache": 0, "symptom_oedema": 0,
            "symptom_rfm": 0, "symptom_bleeding": 0, "symptom_epigastric": 0
        }
    },
    {
        "id": "TEST-003",
        "label": "Mild Anaemia / Routine Case",
        "data": {
            "age": 24, "parity": 0, "previous_cs": 0, "previous_loss": 0,
            "facility_level": "PHC", "geo_zone": "South-East",
            "gestational_age_wks": 18, "sbp_mmhg": 112, "dbp_mmhg": 72,
            "hemoglobin_gdl": 10.2, "bmi": 23.0, "fundal_height_cm": 17.5,
            "urine_protein_raw": "negative", "hiv_status": 0, "malaria_status": 0,
            "gdm_risk": 0, "symptom_headache": 0, "symptom_oedema": 0,
            "symptom_rfm": 0, "symptom_bleeding": 0, "symptom_epigastric": 0
        }
    },
    {
        "id": "TEST-004",
        "label": "Low Risk Routine ANC",
        "data": {
            "age": 26, "parity": 1, "previous_cs": 0, "previous_loss": 0,
            "facility_level": "PHC", "geo_zone": "North-Central",
            "gestational_age_wks": 20, "sbp_mmhg": 114, "dbp_mmhg": 74,
            "hemoglobin_gdl": 11.8, "bmi": 23.5, "fundal_height_cm": 20.2,
            "urine_protein_raw": "negative", "hiv_status": 0, "malaria_status": 0,
            "gdm_risk": 0, "symptom_headache": 0, "symptom_oedema": 0,
            "symptom_rfm": 0, "symptom_bleeding": 0, "symptom_epigastric": 0
        }
    }
]

if __name__ == "__main__":
    print(f"\n{BOLD}ABIYAMO - Hybrid ANC Risk Scoring Engine{RESET}")
    print(f"Running {len(test_patients)} test cases...\n")

    for case in test_patients:
        print(f"\n>>> {case['label']}")
        result = predict(case["data"])
        print_result(case["id"], result)

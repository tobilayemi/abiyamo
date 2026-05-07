"""
ABIYAMO - Web Interface
========================
Flask web app for ANC risk scoring.
Run: python app.py
Visit: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

# ── Load model & encoders ──────────────────────────────────────
with open("abiyamo_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("abiyamo_encoders.pkl", "rb") as f:
    enc = pickle.load(f)

protein_encoder  = enc["protein_encoder"]
facility_encoder = enc["facility_encoder"]
geo_encoder      = enc["geo_encoder"]
risk_order       = enc["risk_order"]
FEATURES         = enc["features"]

# ── Clinical guidance library ──────────────────────────────────
CLINICAL_GUIDANCE = {
    "Critical": {
        "Severe Pre-eclampsia": {
            "icd11": "JA24.3", "color": "#8B0000",
            "explanation": "Severely elevated blood pressure with protein in urine. High risk of seizure (eclampsia), stroke, and fetal compromise.",
            "actions": ["Administer magnesium sulphate (MgSO4) immediately per protocol", "Give antihypertensive (Hydralazine or Nifedipine) if SBP ≥ 160", "Insert IV line and monitor urine output", "Do NOT leave patient alone", "Prepare for emergency delivery if gestation allows"],
            "referral": "EMERGENCY referral to secondary/tertiary facility NOW"
        },
        "Severe Hypertension in Pregnancy": {
            "icd11": "JA24.3", "color": "#8B0000",
            "explanation": "Severely elevated blood pressure with danger signs. Immediate risk of eclamptic seizure.",
            "actions": ["Lay patient on left side, protect airway", "Administer antihypertensive immediately", "Administer MgSO4 as seizure prophylaxis", "Monitor BP every 15 minutes", "Fetal heart rate assessment"],
            "referral": "EMERGENCY referral to secondary/tertiary facility NOW"
        },
        "Severe Anaemia in Pregnancy": {
            "icd11": "JA43", "color": "#8B0000",
            "explanation": "Critically low hemoglobin. High risk of heart failure, preterm labour, and maternal death.",
            "actions": ["Assess for signs of cardiac decompensation (breathlessness, tachycardia)", "Insert IV line", "Arrange urgent blood transfusion", "Treat underlying cause (malaria, hookworm, sickle cell)", "Oxygen supplementation if available"],
            "referral": "URGENT referral to facility with blood bank"
        },
        "Antepartum Haemorrhage / Placenta Risk": {
            "icd11": "JA60", "color": "#8B0000",
            "explanation": "Vaginal bleeding with prior CS raises risk of placenta praevia or abruption. Life-threatening for mother and baby.",
            "actions": ["Do NOT perform vaginal examination", "Insert large-bore IV line", "Monitor maternal vitals every 5-10 minutes", "Fetal heart rate assessment immediately", "Keep patient nil by mouth"],
            "referral": "EMERGENCY referral to tertiary facility with theatre capability"
        }
    },
    "High": {
        "Pre-eclampsia": {
            "icd11": "JA24.2", "color": "#C0392B",
            "explanation": "Elevated BP with significant proteinuria. Risk of progression to severe pre-eclampsia and eclampsia.",
            "actions": ["Confirm BP reading after 15 minutes rest", "Repeat urine protein test", "Initiate antihypertensive if BP persistently ≥ 150/100", "Assess fetal wellbeing", "Review at minimum weekly until delivery"],
            "referral": "Urgent referral to secondary facility within 24 hours"
        },
        "Moderate-Severe Anaemia": {
            "icd11": "JA42", "color": "#C0392B",
            "explanation": "Hemoglobin below 9 g/dL. Significant risk of maternal complications and poor fetal growth.",
            "actions": ["Test for malaria, sickle cell, and hookworm", "Start oral iron and folate immediately", "Nutritional counselling (iron-rich foods)", "Recheck hemoglobin in 4 weeks", "Consider parenteral iron if oral not tolerated"],
            "referral": "Referral to secondary facility if Hb < 8 g/dL or not improving"
        },
        "Fetal Growth Restriction": {
            "icd11": "JA65", "color": "#C0392B",
            "explanation": "Fundal height lagging behind gestational age. Baby may not be growing adequately.",
            "actions": ["Refer for obstetric ultrasound to confirm", "Assess maternal nutrition and weight gain", "Screen for hypertension and anaemia", "Increase ANC frequency to every 2 weeks", "Counsel on danger signs of reduced movement"],
            "referral": "Referral for ultrasound within 1 week"
        },
        "Reduced Fetal Movement": {
            "icd11": "JA65", "color": "#C0392B",
            "explanation": "Reduced fetal movement in the third trimester may indicate fetal distress.",
            "actions": ["Perform fetal heart rate auscultation immediately", "Advise kick count monitoring (>10 movements in 2 hours)", "Assess for other danger signs", "If FHR abnormal: emergency referral"],
            "referral": "Urgent referral if fetal heart rate abnormal or movement absent"
        },
        "Malaria in Pregnancy": {
            "icd11": "1A44.Z", "color": "#C0392B",
            "explanation": "Active malaria in pregnancy risks maternal anaemia, low birth weight, and preterm labour.",
            "actions": ["Initiate artemisinin-based therapy (ACT) per trimester protocol", "Check hemoglobin", "Ensure ITN (insecticide treated net) use", "Monitor for treatment response in 48 hours", "Continue IPTp-SP schedule"],
            "referral": "Referral if severe malaria features present"
        },
        "HIV in Pregnancy - PMTCT Required": {
            "icd11": "1C62.Z", "color": "#C0392B",
            "explanation": "HIV positive status requires PMTCT protocol to protect baby from mother-to-child transmission.",
            "actions": ["Confirm ART enrollment and adherence", "Viral load assessment if not done recently", "Counsel on infant feeding options", "Partner HIV testing", "Infant prophylaxis plan at delivery"],
            "referral": "Referral to PMTCT-capable facility if not enrolled in ART"
        }
    },
    "Moderate": {
        "Gestational Hypertension": {
            "icd11": "JA24.1", "color": "#E8620A",
            "explanation": "Elevated blood pressure without proteinuria. Requires close monitoring for progression to pre-eclampsia.",
            "actions": ["Confirm BP on second reading after 15 minutes rest", "Check urine protein", "Advise rest and reduced salt intake", "Return in 1 week for BP recheck", "Educate on danger signs: headache, visual changes, oedema"],
            "referral": "Refer to secondary facility if BP rises or symptoms develop"
        },
        "Mild Anaemia in Pregnancy": {
            "icd11": "JA42", "color": "#E8620A",
            "explanation": "Hemoglobin below normal for pregnancy. Requires treatment to prevent worsening.",
            "actions": ["Start oral iron (ferrous sulphate) and folic acid", "Dietary counselling: beans, green leafy vegetables, meat", "Treat malaria if present", "Recheck hemoglobin at next ANC visit", "Deworming if indicated"],
            "referral": "No immediate referral. Review at next scheduled visit"
        },
        "Grand Multiparity": {
            "icd11": "JA00", "color": "#E8620A",
            "explanation": "Five or more previous pregnancies increases risk of PPH, malpresentation, and obstructed labour.",
            "actions": ["Increase ANC frequency in third trimester", "Confirm fetal presentation at 36 weeks", "Delivery plan discussion (facility delivery strongly advised)", "Counsel on active management of third stage of labour", "Family planning counselling postpartum"],
            "referral": "Plan delivery at secondary facility minimum"
        },
        "Obesity in Pregnancy": {
            "icd11": "JA00", "color": "#E8620A",
            "explanation": "BMI ≥ 30 in pregnancy increases risk of gestational diabetes, hypertension, and caesarean section.",
            "actions": ["GDM screening (glucose tolerance test)", "Dietary and physical activity counselling", "Monitor BP at each visit", "Fetal growth monitoring", "Thromboprophylaxis discussion"],
            "referral": "Referral if GDM confirmed or BP rises"
        },
        "Gestational Diabetes Risk": {
            "icd11": "JA63", "color": "#E8620A",
            "explanation": "BMI and risk factors suggest possible gestational diabetes. Needs confirmation.",
            "actions": ["Arrange oral glucose tolerance test (OGTT)", "Dietary counselling (reduce refined carbohydrates)", "Monitor fetal growth", "Self-monitoring of blood glucose if test positive", "Educate on signs of hyperglycaemia"],
            "referral": "Referral for OGTT and specialist review if confirmed"
        },
        "Previous Caesarean Section": {
            "icd11": "JA00", "color": "#E8620A",
            "explanation": "Previous uterine scar increases risk of uterine rupture and placenta praevia.",
            "actions": ["Confirm number and type of previous CS", "Screen for placenta praevia (ultrasound if available)", "Delivery plan: facility delivery mandatory", "Educate on danger signs: bleeding, severe abdominal pain", "Do not allow labour to become prolonged"],
            "referral": "Plan delivery at secondary or tertiary facility"
        }
    },
    "Low": {
        "Routine ANC - No Significant Risk": {
            "icd11": "Z34", "color": "#007B85",
            "explanation": "No significant risk factors identified at this visit. Continue routine antenatal care.",
            "actions": ["Continue scheduled ANC visits", "Maintain iron and folic acid supplementation", "Tetanus toxoid immunisation as per schedule", "IPTp-SP (intermittent preventive treatment for malaria)", "Birth preparedness counselling"],
            "referral": "No referral needed. Next scheduled ANC visit as planned"
        }
    }
}

def get_guidance(risk_cat, condition):
    cat_guidance = CLINICAL_GUIDANCE.get(risk_cat, {})
    if condition in cat_guidance:
        return cat_guidance[condition]
    return {"icd11": "Z34", "color": "#007B85", "explanation": "Review with senior clinician.", "actions": ["Seek senior clinical review"], "referral": "Use clinical judgment"}

def apply_rule_guardrails(patient, ml_prediction):
    if patient["sbp_mmhg"] >= 160 or patient["dbp_mmhg"] >= 110:
        return 3
    if patient["hemoglobin_gdl"] < 7.0:
        return 3
    if patient["symptom_bleeding"] == 1 and patient["previous_cs"] == 1 and patient["gestational_age_wks"] > 24:
        return 3
    if patient["sbp_mmhg"] >= 140 and patient["urine_protein_enc"] >= 3:
        return max(ml_prediction, 2)
    if patient["hemoglobin_gdl"] < 9.0:
        return max(ml_prediction, 2)
    return ml_prediction

def resolve_condition(patient, risk_level):
    sbp=patient["sbp_mmhg"]; dbp=patient["dbp_mmhg"]; hb=patient["hemoglobin_gdl"]
    prot=patient["urine_protein_raw"]; ga=patient["gestational_age_wks"]
    if risk_level == 3:
        if (sbp >= 160 or dbp >= 110) and prot in ["2+", "3+"]: return "Severe Pre-eclampsia"
        if sbp >= 160 or dbp >= 110: return "Severe Hypertension in Pregnancy"
        if hb < 7.0: return "Severe Anaemia in Pregnancy"
        if patient["symptom_bleeding"] and patient["previous_cs"] and ga > 24: return "Antepartum Haemorrhage / Placenta Risk"
    if risk_level == 2:
        if sbp >= 140 and prot in ["2+", "3+"]: return "Pre-eclampsia"
        if hb < 9.0: return "Moderate-Severe Anaemia"
        if patient["fundal_height_cm"] < (ga - 4) and ga >= 20: return "Fetal Growth Restriction"
        if patient["symptom_rfm"] and ga >= 28: return "Reduced Fetal Movement"
        if patient["malaria_status"]: return "Malaria in Pregnancy"
        if patient["hiv_status"]: return "HIV in Pregnancy - PMTCT Required"
    if risk_level == 1:
        if sbp >= 140 or dbp >= 90: return "Gestational Hypertension"
        if hb < 11.0: return "Mild Anaemia in Pregnancy"
        if patient["parity"] >= 5: return "Grand Multiparity"
        if patient["bmi"] >= 30: return "Obesity in Pregnancy"
        if patient["gdm_risk"] and patient["bmi"] >= 27: return "Gestational Diabetes Risk"
        if patient["previous_cs"]: return "Previous Caesarean Section"
    return "Routine ANC - No Significant Risk"

def build_features(patient):
    prot_enc = protein_encoder.transform([[patient["urine_protein_raw"]]])[0][0]
    fac_enc  = facility_encoder.transform([patient["facility_level"]])[0]
    geo_enc  = geo_encoder.transform([patient["geo_zone"]])[0]
    sbp=patient["sbp_mmhg"]; dbp=patient["dbp_mmhg"]; hb=patient["hemoglobin_gdl"]
    ga=patient["gestational_age_wks"]; fh=patient["fundal_height_cm"]; bmi=patient["bmi"]
    anaemia_sev = 3 if hb < 7 else (2 if hb < 9 else (1 if hb < 11 else 0))
    row = {
        "age": patient["age"], "parity": patient["parity"],
        "previous_cs": patient["previous_cs"], "previous_loss": patient["previous_loss"],
        "gestational_age_wks": ga, "sbp_mmhg": sbp, "dbp_mmhg": dbp,
        "hemoglobin_gdl": hb, "bmi": bmi, "fundal_height_cm": fh,
        "urine_protein_enc": prot_enc, "hiv_status": patient["hiv_status"],
        "malaria_status": patient["malaria_status"], "gdm_risk": patient["gdm_risk"],
        "symptom_headache": patient["symptom_headache"], "symptom_oedema": patient["symptom_oedema"],
        "symptom_rfm": patient["symptom_rfm"], "symptom_bleeding": patient["symptom_bleeding"],
        "symptom_epigastric": patient["symptom_epigastric"],
        "facility_level_enc": fac_enc, "geo_zone_enc": geo_enc,
        "pulse_pressure": sbp - dbp, "map": ((2*dbp)+sbp)/3,
        "fh_ga_diff": fh - ga, "anaemia_severity": anaemia_sev,
        "hypertension_flag": int(sbp >= 140 or dbp >= 90),
        "severe_htn_flag": int(sbp >= 160 or dbp >= 110),
        "symptom_burden": sum([patient["symptom_headache"], patient["symptom_oedema"],
                               patient["symptom_rfm"], patient["symptom_bleeding"], patient["symptom_epigastric"]]),
        "third_trimester": int(ga >= 28), "grand_multipara": int(patient["parity"] >= 5),
        "obese": int(bmi >= 30),
    }
    patient["urine_protein_enc"] = prot_enc
    return pd.DataFrame([row])[FEATURES]

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/app")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json
        patient = {
            "age": int(data["age"]), "parity": int(data["parity"]),
            "previous_cs": int(data["previous_cs"]), "previous_loss": int(data["previous_loss"]),
            "facility_level": data["facility_level"], "geo_zone": data["geo_zone"],
            "gestational_age_wks": int(data["gestational_age_wks"]),
            "sbp_mmhg": int(data["sbp_mmhg"]), "dbp_mmhg": int(data["dbp_mmhg"]),
            "hemoglobin_gdl": float(data["hemoglobin_gdl"]), "bmi": float(data["bmi"]),
            "fundal_height_cm": float(data["fundal_height_cm"]),
            "urine_protein_raw": data["urine_protein"],
            "hiv_status": int(data["hiv_status"]), "malaria_status": int(data["malaria_status"]),
            "gdm_risk": int(data["gdm_risk"]),
            "symptom_headache": int(data["symptom_headache"]),
            "symptom_oedema": int(data["symptom_oedema"]),
            "symptom_rfm": int(data["symptom_rfm"]),
            "symptom_bleeding": int(data["symptom_bleeding"]),
            "symptom_epigastric": int(data["symptom_epigastric"]),
        }
        X = build_features(patient)
        ml_pred  = int(model.predict(X)[0])
        ml_proba = model.predict_proba(X)[0]
        final    = apply_rule_guardrails(patient, ml_pred)
        risk_name = risk_order[final]
        condition = resolve_condition(patient, final)
        guidance  = get_guidance(risk_name, condition)

        return jsonify({
            "success": True,
            "risk_level": final,
            "risk_name": risk_name,
            "condition": condition,
            "icd11_code": guidance["icd11"],
            "color": guidance["color"],
            "explanation": guidance["explanation"],
            "actions": guidance["actions"],
            "referral": guidance["referral"],
            "rule_override": final != ml_pred,
            "probabilities": {risk_order[i]: round(float(p)*100, 1) for i, p in enumerate(ml_proba)},
            "timestamp": datetime.now().strftime("%d %b %Y  %H:%M"),
            "patient_id": data.get("patient_id", "N/A")
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  ABIYAMO Web Interface")
    print("  http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)

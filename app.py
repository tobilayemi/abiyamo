"""
ABIYAMO - Web Interface
========================
Flask web app for ANC risk scoring.
Run: python app.py
Visit: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

import json

import anc_fhir
import anc_form

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
            "icd11": "JA24.1", "color": "#8B0000",
            "explanation": "Severely elevated blood pressure with protein in urine. High risk of seizure (eclampsia), stroke, and fetal compromise.",
            "actions": ["Administer magnesium sulphate (MgSO4) immediately per protocol", "Give antihypertensive (Hydralazine or Nifedipine) if SBP ≥ 160", "Insert IV line and monitor urine output", "Do NOT leave patient alone", "Prepare for emergency delivery if gestation allows"],
            "referral": "EMERGENCY referral to secondary/tertiary facility NOW"
        },
        "Severe Hypertension in Pregnancy": {
            "icd11": "JA23", "color": "#8B0000",
            "explanation": "Severely elevated blood pressure with danger signs. Immediate risk of eclamptic seizure.",
            "actions": ["Lay patient on left side, protect airway", "Administer antihypertensive immediately", "Administer MgSO4 as seizure prophylaxis", "Monitor BP every 15 minutes", "Fetal heart rate assessment"],
            "referral": "EMERGENCY referral to secondary/tertiary facility NOW"
        },
        "Severe Anaemia in Pregnancy": {
            "icd11": "JB64.0", "color": "#8B0000",
            "explanation": "Critically low hemoglobin. High risk of heart failure, preterm labour, and maternal death.",
            "actions": ["Assess for signs of cardiac decompensation (breathlessness, tachycardia)", "Insert IV line", "Arrange urgent blood transfusion", "Treat underlying cause (malaria, hookworm, sickle cell)", "Oxygen supplementation if available"],
            "referral": "URGENT referral to facility with blood bank"
        },
        "Antepartum Haemorrhage / Placenta Risk": {
            "icd11": "JA41.Z", "color": "#8B0000",
            "explanation": "Vaginal bleeding with prior CS raises risk of placenta praevia or abruption. Life-threatening for mother and baby.",
            "actions": ["Do NOT perform vaginal examination", "Insert large-bore IV line", "Monitor maternal vitals every 5-10 minutes", "Fetal heart rate assessment immediately", "Keep patient nil by mouth"],
            "referral": "EMERGENCY referral to tertiary facility with theatre capability"
        }
    },
    "High": {
        "Pre-eclampsia": {
            "icd11": "JA24.0", "color": "#C0392B",
            "explanation": "Elevated BP with significant proteinuria. Risk of progression to severe pre-eclampsia and eclampsia.",
            "actions": ["Confirm BP reading after 15 minutes rest", "Repeat urine protein test", "Initiate antihypertensive if BP persistently ≥ 150/100", "Assess fetal wellbeing", "Review at minimum weekly until delivery"],
            "referral": "Urgent referral to secondary facility within 24 hours"
        },
        "Moderate-Severe Anaemia": {
            "icd11": "JB64.0", "color": "#C0392B",
            "explanation": "Hemoglobin below 9 g/dL. Significant risk of maternal complications and poor fetal growth.",
            "actions": ["Test for malaria, sickle cell, and hookworm", "Start oral iron and folate immediately", "Nutritional counselling (iron-rich foods)", "Recheck hemoglobin in 4 weeks", "Consider parenteral iron if oral not tolerated"],
            "referral": "Referral to secondary facility if Hb < 8 g/dL or not improving"
        },
        "Fetal Growth Restriction": {
            "icd11": "JA86.4", "color": "#C0392B",
            "explanation": "Fundal height lagging behind gestational age. Baby may not be growing adequately.",
            "actions": ["Refer for obstetric ultrasound to confirm", "Assess maternal nutrition and weight gain", "Screen for hypertension and anaemia", "Increase ANC frequency to every 2 weeks", "Counsel on danger signs of reduced movement"],
            "referral": "Referral for ultrasound within 1 week"
        },
        "Reduced Fetal Movement": {
            "icd11": "JA86.Y", "color": "#C0392B",
            "explanation": "Reduced fetal movement in the third trimester may indicate fetal distress.",
            "actions": ["Perform fetal heart rate auscultation immediately", "Advise kick count monitoring (>10 movements in 2 hours)", "Assess for other danger signs", "If FHR abnormal: emergency referral"],
            "referral": "Urgent referral if fetal heart rate abnormal or movement absent"
        },
        "Malaria in Pregnancy": {
            "icd11": "JB63.6", "color": "#C0392B",
            "explanation": "Active malaria in pregnancy risks maternal anaemia, low birth weight, and preterm labour.",
            "actions": ["Initiate artemisinin-based therapy (ACT) per trimester protocol", "Check hemoglobin", "Ensure ITN (insecticide treated net) use", "Monitor for treatment response in 48 hours", "Continue IPTp-SP schedule"],
            "referral": "Referral if severe malaria features present"
        },
        "HIV in Pregnancy - PMTCT Required": {
            "icd11": "JB63.7", "color": "#C0392B",
            "explanation": "HIV positive status requires PMTCT protocol to protect baby from mother-to-child transmission.",
            "actions": ["Confirm ART enrollment and adherence", "Viral load assessment if not done recently", "Counsel on infant feeding options", "Partner HIV testing", "Infant prophylaxis plan at delivery"],
            "referral": "Referral to PMTCT-capable facility if not enrolled in ART"
        }
    },
    "Moderate": {
        "Gestational Hypertension": {
            "icd11": "JA23", "color": "#E8620A",
            "explanation": "Elevated blood pressure without proteinuria. Requires close monitoring for progression to pre-eclampsia.",
            "actions": ["Confirm BP on second reading after 15 minutes rest", "Check urine protein", "Advise rest and reduced salt intake", "Return in 1 week for BP recheck", "Educate on danger signs: headache, visual changes, oedema"],
            "referral": "Refer to secondary facility if BP rises or symptoms develop"
        },
        "Mild Anaemia in Pregnancy": {
            "icd11": "JB64.0", "color": "#E8620A",
            "explanation": "Hemoglobin below normal for pregnancy. Requires treatment to prevent worsening.",
            "actions": ["Start oral iron (ferrous sulphate) and folic acid", "Dietary counselling: beans, green leafy vegetables, meat", "Treat malaria if present", "Recheck hemoglobin at next ANC visit", "Deworming if indicated"],
            "referral": "No immediate referral. Review at next scheduled visit"
        },
        "Grand Multiparity": {
            "icd11": "QA4A", "color": "#E8620A",
            "explanation": "Five or more previous pregnancies increases risk of PPH, malpresentation, and obstructed labour.",
            "actions": ["Increase ANC frequency in third trimester", "Confirm fetal presentation at 36 weeks", "Delivery plan discussion (facility delivery strongly advised)", "Counsel on active management of third stage of labour", "Family planning counselling postpartum"],
            "referral": "Plan delivery at secondary facility minimum"
        },
        "Obesity in Pregnancy": {
            "icd11": "JB64.2", "color": "#E8620A",
            "explanation": "BMI ≥ 30 in pregnancy increases risk of gestational diabetes, hypertension, and caesarean section.",
            "actions": ["GDM screening (glucose tolerance test)", "Dietary and physical activity counselling", "Monitor BP at each visit", "Fetal growth monitoring", "Thromboprophylaxis discussion"],
            "referral": "Referral if GDM confirmed or BP rises"
        },
        "Gestational Diabetes Risk": {
            "icd11": "QA43.Z", "color": "#E8620A",
            "explanation": "BMI and risk factors suggest possible gestational diabetes. Needs confirmation.",
            "actions": ["Arrange oral glucose tolerance test (OGTT)", "Dietary counselling (reduce refined carbohydrates)", "Monitor fetal growth", "Self-monitoring of blood glucose if test positive", "Educate on signs of hyperglycaemia"],
            "referral": "Referral for OGTT and specialist review if confirmed"
        },
        "Previous Caesarean Section": {
            "icd11": "JA84.2", "color": "#E8620A",
            "explanation": "Previous uterine scar increases risk of uterine rupture and placenta praevia.",
            "actions": ["Confirm number and type of previous CS", "Screen for placenta praevia (ultrasound if available)", "Delivery plan: facility delivery mandatory", "Educate on danger signs: bleeding, severe abdominal pain", "Do not allow labour to become prolonged"],
            "referral": "Plan delivery at secondary or tertiary facility"
        }
    },
    "Low": {
        "Routine ANC - No Significant Risk": {
            "icd11": "QA42.Z", "color": "#007B85",
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
    return {"icd11": "QA43.Z", "color": "#007B85", "explanation": "Review with senior clinician.", "actions": ["Seek senior clinical review"], "referral": "Use clinical judgment"}

def apply_rule_guardrails(values, ml_prediction):
    # Fixed clinical thresholds live in anc_form.RULES (kind "guardrail"), so the
    # web form and the /early-warning page explain exactly the rules applied here.
    return max(ml_prediction, anc_form.guardrail_floor(values))

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

def form_context():
    return dict(
        schema=anc_form.client_schema(),
        sections=anc_form.SECTIONS,
        fields=anc_form.FIELDS,
        rules=anc_form.RULES,
        field_role=anc_form.field_role,
        field_detects=anc_form.field_detects,
        alert_detects=anc_form.alert_detects,
        section_watch={s["id"]: anc_form.section_watch(s["id"]) for s in anc_form.SECTIONS},
        section_rules={s["id"]: anc_form.rules_for_section(s["id"]) for s in anc_form.SECTIONS},
        model_fields={s["id"]: anc_form.model_only_fields(s["id"]) for s in anc_form.SECTIONS},
        section_titles={s["id"]: s["title"] for s in anc_form.SECTIONS},
    )

@app.route("/app")
def index():
    return render_template("index.html", **form_context())

@app.route("/early-warning")
def early_warning():
    return render_template("early_warning.html", **form_context())

@app.route("/sw.js")
def service_worker():
    # Served from the site root so the worker can cache /app for offline use.
    resp = send_from_directory("static", "sw.js", mimetype="application/javascript")
    resp.headers["Cache-Control"] = "no-cache"
    return resp

def assess(values):
    """Score one visit from validated values. Shared by the web form and the FHIR API."""
    patient = {k: values[k] for k in anc_form.FIELDS if k in values and k != "urine_protein"}
    patient["urine_protein_raw"] = values["urine_protein"]
    X = build_features(patient)
    ml_pred  = int(model.predict(X)[0])
    ml_proba = model.predict_proba(X)[0]
    final    = apply_rule_guardrails(values, ml_pred)
    risk_name = risk_order[final]
    condition = resolve_condition(patient, final)
    guidance  = get_guidance(risk_name, condition)
    return {
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
        "model_risk_name": risk_order[ml_pred],
        "warning_signs": anc_form.warning_signs(values),
        "probabilities": {risk_order[i]: round(float(p)*100, 1) for i, p in enumerate(ml_proba)},
        "timestamp": datetime.now().strftime("%d %b %Y  %H:%M"),
        "patient_id": values.get("patient_id", ""),
    }

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)
    values, errors = anc_form.validate(data)
    if errors:
        return jsonify({"success": False, "error": "Some entries need fixing.",
                        "errors": errors}), 400
    try:
        result = assess(values)
    except Exception:
        app.logger.exception("Assessment failed")
        return jsonify({"success": False,
                        "error": "The assessment could not be run. Please try again."}), 500
    if request.args.get("format") == "fhir":
        # Same assessment, returned as a FHIR R4 Bundle (the form's "Download FHIR record")
        return fhir_json(anc_fhir.to_bundle(values, result, raw=data))
    return jsonify(result)

# ── FHIR R4 interface (see docs/fhir.md) ──────────────────────────────
def fhir_json(resource, status=200):
    resp = app.response_class(json.dumps(resource, ensure_ascii=False, indent=2), status=status,
                              mimetype="application/fhir+json")
    return resp

def fhir_base():
    return request.url_root.rstrip("/") + "/fhir"

@app.route("/fhir/metadata")
def fhir_metadata():
    return fhir_json(anc_fhir.capability_statement(fhir_base()))

@app.route("/fhir/OperationDefinition/abiyamo-assess")
def fhir_operation_definition():
    return fhir_json(anc_fhir.operation_definition(fhir_base()))

@app.route("/fhir/$assess", methods=["POST"])
def fhir_assess():
    bundle = request.get_json(force=True, silent=True)
    defaults = {k: request.args[k] for k in ("facility_level", "geo_zone") if request.args.get(k)}
    try:
        raw = anc_fhir.from_bundle(bundle, defaults)
    except anc_fhir.FhirInputError as e:
        return fhir_json(anc_fhir.operation_outcome({}, str(e)), 400)
    values, errors = anc_form.validate(raw)
    if errors:
        return fhir_json(anc_fhir.operation_outcome(errors), 422)
    try:
        result = assess(values)
    except Exception:
        app.logger.exception("FHIR assessment failed")
        return fhir_json(anc_fhir.operation_outcome({}, "The assessment could not be run."), 500)
    return fhir_json(anc_fhir.to_bundle(values, result, raw=raw))

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  ABIYAMO Web Interface")
    print("  http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)

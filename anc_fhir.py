"""
ABIYAMO - FHIR R4 interface
============================
Lets facility EMRs exchange ANC assessments with Abiyamo using HL7 FHIR R4 (4.0.1),
the version served by OpenMRS's FHIR2 module.

  to_bundle(values, result)  ANC entries + risk result  ->  FHIR Bundle (collection):
                             Patient, Organization, Device, one Observation per entry,
                             and a RiskAssessment whose `basis` points to those Observations.
  from_bundle(bundle)        FHIR Bundle of Observations from an EMR  ->  form values,
                             which then go through the same validation and scoring as the web form.

Every LOINC and SNOMED CT code below was checked against the HL7 terminology server
(tx.fhir.org). Entries with no standard code use Abiyamo's local code system.
"""

import uuid
from datetime import datetime, timezone

FHIR_VERSION = "4.0.1"
LOINC = "http://loinc.org"
SCT = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"
ICD11 = "http://id.who.int/icd/release/11/mms"
OBS_CATEGORY = "http://terminology.hl7.org/CodeSystem/observation-category"
DATA_ABSENT = "http://terminology.hl7.org/CodeSystem/data-absent-reason"
RISK_PROBABILITY = "http://terminology.hl7.org/CodeSystem/risk-probability"
LOCAL = "https://github.com/tobilayemi/abiyamo/fhir/CodeSystem"
LOCAL_ANC = LOCAL + "/anc"
LOCAL_FACILITY = LOCAL + "/facility-level"
LOCAL_ZONE = LOCAL + "/nigeria-geopolitical-zone"
LOCAL_RISK = LOCAL + "/risk-level"
ANC_NUMBER = "https://github.com/tobilayemi/abiyamo/fhir/NamingSystem/anc-number"

# field: (system, code, display, category, ucum unit, unit label, value type)
QUANTITIES = {
    "age":                 (LOINC, "30525-0", "Age", "survey", "a", "years", "integer"),
    "gestational_age_wks": (LOINC, "49051-6", "Gestational age in weeks", "exam", "wk", "weeks", "integer"),
    "parity":              (LOINC, "11977-6", "[#] Parity", "survey", None, None, "integer"),
    "bmi":                 (LOINC, "39156-5", "Body mass index (BMI) [Ratio]", "vital-signs", "kg/m2", "kg/m2", "decimal"),
    "fundal_height_cm":    (LOINC, "11881-0", "Uterus Fundal height Tape measure", "exam", "cm", "cm", "decimal"),
    "hemoglobin_gdl":      (LOINC, "718-7", "Hemoglobin [Mass/volume] in Blood", "laboratory", "g/dL", "g/dL", "decimal"),
}
BP_PANEL = (LOINC, "85354-9", "Blood pressure panel with all children optional")
SBP = (LOINC, "8480-6", "Systolic blood pressure")
DBP = (LOINC, "8462-4", "Diastolic blood pressure")

# Yes/no history and danger signs: Observation.code is the finding, value is true/false.
BOOLEANS = {
    "previous_cs":        (SCT, "161805006", "Past pregnancy history of cesarean section"),
    "previous_loss":      (LOCAL_ANC, "previous-pregnancy-loss", "Previous pregnancy loss (miscarriage or stillbirth)"),
    "gdm_risk":           (LOCAL_ANC, "gdm-risk-factors", "Risk factors for gestational diabetes present"),
    "symptom_headache":   (SCT, "25064002", "Headache"),
    "symptom_oedema":     (SCT, "267038008", "Edema"),
    "symptom_rfm":        (SCT, "276369006", "Reduced fetal movement"),
    "symptom_bleeding":   (SCT, "289530006", "Vaginal bleeding"),
    "symptom_epigastric": (SCT, "79922009", "Epigastric pain"),
}

# Positive / negative / not tested
TESTS = {
    "hiv_status":     (LOINC, "80387-4", "HIV 1+2 Ab [Presence] in Serum, Plasma or Blood by Rapid immunoassay"),
    "malaria_status": (LOINC, "50687-3", "Plasmodium sp Ag [Presence] in Blood"),
}
TEST_ALIASES = {  # other common LOINC codes accepted on import
    "hiv_status": {"75622-1", "68961-2", "7917-8", "31201-7", "49580-4"},
    "malaria_status": {"51587-4", "46094-9", "76772-3"},
}
POSITIVE = (SCT, "10828004", "Positive")
NEGATIVE = (SCT, "260385009", "Negative")

URINE_PROTEIN = (LOINC, "20454-5", "Protein [Presence] in Urine by Test strip")
PROTEIN_VALUES = {
    "negative": (SCT, "260385009", "Negative"),
    "trace":    (SCT, "260405006", "Trace"),
    "1+":       (SCT, "260347006", "+"),
    "2+":       (SCT, "260348001", "++"),
    "3+":       (SCT, "260349009", "+++"),
}

# Official ICD-11 MMS titles for the codes the guidance library uses (verified on tx.fhir.org)
ICD11_TITLES = {
    "JA23": "Gestational hypertension",
    "JA24.0": "Mild to moderate pre-eclampsia",
    "JA24.1": "Severe pre-eclampsia",
    "JA41.Z": "Antepartum haemorrhage, unspecified",
    "JA84.2": "Maternal care due to uterine scar from previous surgery",
    "JA86.4": "Maternal care for fetal growth restriction",
    "JA86.Y": "Maternal care for other specified fetal problems",
    "JB63.6": "Protozoal diseases complicating pregnancy, childbirth or the puerperium",
    "JB63.7": "Human immunodeficiency disease complicating pregnancy, childbirth or the puerperium",
    "JB64.0": "Anaemia complicating pregnancy, childbirth or the puerperium",
    "JB64.2": "Endocrine, nutritional or metabolic diseases complicating pregnancy, childbirth or the puerperium",
    "QA42.Z": "Supervision of normal pregnancy, unspecified",
    "QA43.Z": "Supervision of high-risk pregnancy, unspecified",
    "QA4A": "Problems related to multiparity",
}

# Abiyamo's four levels; the HL7 risk-probability scale has no "critical", so that one is local only.
HL7_RISK = {"Low": "low", "Moderate": "moderate", "High": "high"}


def _coding(t):
    return {"system": t[0], "code": t[1], "display": t[2]}


def _concept(t, text=None):
    c = {"coding": [_coding(t)]}
    if text:
        c["text"] = text
    return c


def _category(code):
    return [{"coding": [{"system": OBS_CATEGORY, "code": code}]}]


def _ref(entry):
    return {"reference": entry["fullUrl"]}


def _entry(resource):
    uid = str(uuid.uuid4())
    resource["id"] = uid
    return {"fullUrl": "urn:uuid:" + uid, "resource": resource}


def _now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ── Export ───────────────────────────────────────────────────────────────────
def to_bundle(values, result, raw=None):
    """
    values: validated values from anc_form.validate
    result: the assessment dict returned by app.assess
    raw:    the submitted form values (used to tell "not tested" from "negative")
    """
    raw = raw or {}
    when = _now()
    entries = []

    org = _entry({
        "resourceType": "Organization",
        "type": [
            _concept((LOCAL_FACILITY, values["facility_level"], values["facility_level"])),
            _concept((LOCAL_ZONE, values["geo_zone"], values["geo_zone"] + " geopolitical zone")),
        ],
        "address": [{"country": "NG", "text": values["geo_zone"] + " geopolitical zone, Nigeria"}],
    })
    patient_res = {"resourceType": "Patient", "managingOrganization": _ref(org)}
    if values.get("patient_id"):
        patient_res["identifier"] = [{"system": ANC_NUMBER, "value": values["patient_id"]}]
    patient = _entry(patient_res)
    device = _entry({
        "resourceType": "Device",
        "deviceName": [{"name": "Abiyamo ANC risk model", "type": "model-name"}],
        "version": [{"value": "1.0"}],
    })
    entries += [patient, org]

    def obs(code_t, category, **value):
        res = {"resourceType": "Observation", "status": "final", "category": _category(category),
               "code": _concept(code_t), "subject": _ref(patient), "effectiveDateTime": when}
        res.update(value)
        e = _entry(res)
        entries.append(e)
        return e

    observations = []
    for fid, (sys_, code, display, cat, unit, label, vtype) in QUANTITIES.items():
        v = values[fid]
        if unit is None:
            observations.append(obs((sys_, code, display), cat, valueInteger=int(v)))
        else:
            q = {"value": int(v) if vtype == "integer" else float(v), "unit": label, "system": UCUM, "code": unit}
            observations.append(obs((sys_, code, display), cat, valueQuantity=q))

    def mmhg(v):
        return {"value": int(v), "unit": "mmHg", "system": UCUM, "code": "mm[Hg]"}
    observations.append(obs(BP_PANEL, "vital-signs", component=[
        {"code": _concept(SBP), "valueQuantity": mmhg(values["sbp_mmhg"])},
        {"code": _concept(DBP), "valueQuantity": mmhg(values["dbp_mmhg"])},
    ]))

    observations.append(obs(URINE_PROTEIN, "laboratory",
                            valueCodeableConcept=_concept(PROTEIN_VALUES[values["urine_protein"]])))

    for fid, code_t in TESTS.items():
        if str(raw.get(fid, "")).lower() == "not_tested":
            observations.append(obs(code_t, "laboratory", dataAbsentReason={
                "coding": [{"system": DATA_ABSENT, "code": "not-performed", "display": "Not Performed"}]}))
        else:
            observations.append(obs(code_t, "laboratory", valueCodeableConcept=_concept(
                POSITIVE if values[fid] == 1 else NEGATIVE)))

    for fid, code_t in BOOLEANS.items():
        observations.append(obs(code_t, "survey", valueBoolean=bool(values[fid])))

    # Risk assessment
    level = result["risk_name"]
    risk_codings = [{"system": LOCAL_RISK, "code": level.lower(), "display": level}]
    if level in HL7_RISK:
        risk_codings.insert(0, {"system": RISK_PROBABILITY, "code": HL7_RISK[level]})
    icd = result["icd11_code"]
    outcome = {"text": result["condition"]}
    if icd in ICD11_TITLES:
        outcome["coding"] = [{"system": ICD11, "code": icd, "display": ICD11_TITLES[icd]}]
    prediction = {"outcome": outcome, "qualitativeRisk": {"coding": risk_codings, "text": level}}
    if not result["rule_override"]:
        prediction["probabilityDecimal"] = round(result["probabilities"][level] / 100, 3)
    alerts = [w for w in result["warning_signs"] if w["kind"] != "signal"]
    if alerts:
        prediction["rationale"] = "; ".join(f"{w['effect']}: {w['title']} ({w['threshold']})" for w in alerts)

    notes = [{"text": "Clinical decision support only. The final decision rests with the attending health worker."}]
    if result["rule_override"]:
        notes.append({"text": f"A fixed clinical threshold raised the level above the risk model's rating "
                              f"({result['model_risk_name']})."})
    notes.append({"text": "Risk model probabilities: " + ", ".join(
        f"{k} {v}%" for k, v in result["probabilities"].items())})

    risk = _entry({
        "resourceType": "RiskAssessment",
        "status": "final",
        "code": {"text": "Antenatal care risk assessment"},
        "subject": _ref(patient),
        "occurrenceDateTime": when,
        "performer": _ref(device),
        "method": {"text": "Abiyamo: fixed clinical thresholds plus gradient-boosted classifier"},
        "basis": [_ref(o) for o in observations],
        "prediction": [prediction],
        "mitigation": result["referral"] + " Actions: " + "; ".join(result["actions"]),
        "note": notes,
    })
    entries += [device, risk]

    return {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "meta": {"lastUpdated": when},
        "type": "collection",
        "timestamp": when,
        "entry": entries,
    }


# ── Import ───────────────────────────────────────────────────────────────────
class FhirInputError(ValueError):
    pass


def _codes(concept):
    return {(c.get("system"), c.get("code")) for c in (concept or {}).get("coding", [])}


def _has(concept, t):
    return (t[0], t[1]) in _codes(concept)


def _quantity(res, expect_unit=None):
    q = res.get("valueQuantity")
    if q is None:
        if "valueInteger" in res:
            return res["valueInteger"]
        return None
    v = q.get("value")
    unit = q.get("code") or q.get("unit")
    if expect_unit == "g/dL" and unit in ("g/L",):
        v = v / 10
    if expect_unit == "wk" and unit in ("d",):
        v = round(v / 7)
    return v


def _yes_no(res):
    if "valueBoolean" in res:
        return "yes" if res["valueBoolean"] else "no"
    cc = res.get("valueCodeableConcept")
    if cc:
        if _has(cc, POSITIVE) or _has(cc, (SCT, "373066001", "")):   # 373066001 = Yes
            return "yes"
        if _has(cc, NEGATIVE) or _has(cc, (SCT, "373067005", "")):   # 373067005 = No
            return "no"
    return None


def from_bundle(bundle, defaults=None):
    """
    Read a FHIR Bundle (or a list of resources) of ANC Observations into form values.
    defaults: values for anything the bundle doesn't carry (e.g. facility_level/geo_zone
              configured once per facility).
    Returns raw form values (strings), ready for anc_form.validate.
    """
    if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
        raise FhirInputError("Expected a FHIR Bundle resource.")
    resources = [e.get("resource") or {} for e in bundle.get("entry", [])]
    raw = dict(defaults or {})

    for res in resources:
        rt = res.get("resourceType")
        if rt == "Patient":
            for ident in res.get("identifier", []):
                if ident.get("value"):
                    raw.setdefault("patient_id", ident["value"])
                    break
        elif rt == "Organization":
            for t in res.get("type", []):
                for c in t.get("coding", []):
                    if c.get("system") == LOCAL_FACILITY:
                        raw["facility_level"] = c.get("code")
                    elif c.get("system") == LOCAL_ZONE:
                        raw["geo_zone"] = c.get("code")
        elif rt == "Observation":
            if res.get("status") in ("entered-in-error", "cancelled"):
                continue
            code = res.get("code", {})
            if _has(code, BP_PANEL):
                for comp in res.get("component", []):
                    if _has(comp.get("code"), SBP):
                        raw["sbp_mmhg"] = _quantity(comp)
                    elif _has(comp.get("code"), DBP):
                        raw["dbp_mmhg"] = _quantity(comp)
                continue
            if _has(code, SBP):
                raw["sbp_mmhg"] = _quantity(res)
                continue
            if _has(code, DBP):
                raw["dbp_mmhg"] = _quantity(res)
                continue
            if _has(code, URINE_PROTEIN):
                cc = res.get("valueCodeableConcept") or {}
                for key, t in PROTEIN_VALUES.items():
                    if _has(cc, t):
                        raw["urine_protein"] = key
                if "urine_protein" not in raw and res.get("valueString"):
                    raw["urine_protein"] = res["valueString"].strip().lower().replace("neg", "negative")
                continue
            matched = False
            for fid, t in QUANTITIES.items():
                if _has(code, t):
                    raw[fid] = _quantity(res, t[4])
                    matched = True
            for fid, t in TESTS.items():
                loinc = {c for s, c in _codes(code) if s == LOINC}
                if _has(code, t) or loinc & TEST_ALIASES[fid]:
                    reason = _codes(res.get("dataAbsentReason"))
                    if (DATA_ABSENT, "not-performed") in reason:
                        raw[fid] = "not_tested"
                    else:
                        yn = _yes_no(res)
                        if yn:
                            raw[fid] = "positive" if yn == "yes" else "negative"
                    matched = True
            if matched:
                continue
            for fid, t in BOOLEANS.items():
                if _has(code, t):
                    yn = _yes_no(res)
                    if yn:
                        raw[fid] = yn

    return {k: ("" if v is None else str(v)) for k, v in raw.items()}


def operation_outcome(errors, status_text="Some entries are missing or invalid."):
    """FHIR OperationOutcome listing each problem by form field."""
    issues = [{"severity": "error", "code": "required" if "required" in msg else "value",
               "diagnostics": f"{fid}: {msg}", "expression": [fid]} for fid, msg in errors.items()]
    if not issues:
        issues = [{"severity": "error", "code": "invalid", "diagnostics": status_text}]
    return {"resourceType": "OperationOutcome", "issue": issues}


def capability_statement(base_url):
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2026-11-17",
        "publisher": "Abiyamo",
        "kind": "instance",
        "software": {"name": "Abiyamo ANC early warning", "version": "1.0"},
        "implementation": {"description": "Abiyamo ANC risk assessment", "url": base_url},
        "fhirVersion": FHIR_VERSION,
        "format": ["json"],
        "rest": [{
            "mode": "server",
            "documentation": "POST a Bundle of ANC Observations (and optionally Patient and Organization) "
                             "to $assess. The response is a Bundle containing a RiskAssessment.",
            "operation": [{"name": "assess", "definition": base_url + "/OperationDefinition/abiyamo-assess"}],
        }],
    }


def operation_definition(base_url):
    return {
        "resourceType": "OperationDefinition",
        "id": "abiyamo-assess",
        "url": base_url + "/OperationDefinition/abiyamo-assess",
        "name": "AbiyamoAssess",
        "title": "Abiyamo ANC risk assessment",
        "status": "active",
        "kind": "operation",
        "description": "Scores an antenatal care visit. Input: a Bundle of Observations using the LOINC and "
                       "SNOMED CT codes Abiyamo documents. Output: a Bundle with the Observations and a "
                       "RiskAssessment.",
        "code": "assess",
        "system": True,
        "type": False,
        "instance": False,
        "parameter": [
            {"name": "resource", "use": "in", "min": 1, "max": "1", "type": "Bundle",
             "documentation": "ANC Observations for one visit"},
            {"name": "return", "use": "out", "min": 1, "max": "1", "type": "Bundle",
             "documentation": "Observations plus the RiskAssessment"},
        ],
    }

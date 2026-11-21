"""
ABIYAMO - ANC form definition and early-warning rules
======================================================
Single source of truth for:
  * the ANC form sections and fields shown in the step-by-step web form,
  * the validation ranges used both in the browser and on the server,
  * the early-warning rules: which entries raise which alerts.

app.py uses RULES for its clinical guardrails, and the web form and the
/early-warning page render straight from these tables, so the explanation
reviewers see always matches the logic that actually runs.
"""

import math

RISK_NAMES = ["Low", "Moderate", "High", "Critical"]

# ── Form sections (one page / step each) ─────────────────────────────────────
SECTIONS = [
    {
        "id": "mother",
        "title": "Mother & visit",
        "short": "Mother",
        "intro": "Who the mother is and where she is being seen today.",
        "fields": ["patient_id", "age", "facility_level", "geo_zone"],
    },
    {
        "id": "history",
        "title": "Pregnancy & history",
        "short": "History",
        "intro": "This pregnancy, and what happened in earlier ones.",
        "fields": ["gestational_age_wks", "parity", "previous_cs", "previous_loss", "gdm_risk"],
    },
    {
        "id": "vitals",
        "title": "Vital signs & measurements",
        "short": "Vitals",
        "intro": "Measurements taken at this visit.",
        "fields": ["sbp_mmhg", "dbp_mmhg", "bmi", "fundal_height_cm"],
    },
    {
        "id": "tests",
        "title": "Test results",
        "short": "Tests",
        "intro": "Laboratory and rapid test results from this visit or the ANC card.",
        "fields": ["hemoglobin_gdl", "urine_protein", "hiv_status", "malaria_status"],
    },
    {
        "id": "symptoms",
        "title": "Danger signs today",
        "short": "Danger signs",
        "intro": "Ask the mother about each of these, even if she has not mentioned them.",
        "fields": ["symptom_headache", "symptom_oedema", "symptom_rfm",
                   "symptom_bleeding", "symptom_epigastric"],
    },
]

YES_NO = [
    {"value": "yes", "label": "Yes", "score": 1},
    {"value": "no", "label": "No", "score": 0},
]

TEST_RESULT = [
    {"value": "positive", "label": "Positive", "score": 1},
    {"value": "negative", "label": "Negative", "score": 0},
    {"value": "not_tested", "label": "Not tested", "score": 0,
     "note": "scored as negative"},
]

# ── Fields ───────────────────────────────────────────────────────────────────
# min/max          hard limits: values outside are impossible and block "Next".
# check_min/max    soft limits: unusual values get a "please double-check" note.
FIELDS = {
    "patient_id": {
        "label": "Patient ID / ANC number", "noun": "patient ID", "type": "text",
        "required": False, "max_length": 40, "placeholder": "PHC-2026-001",
        "help": "Use the ANC card number, not her name.",
    },
    "age": {
        "label": "Age", "noun": "maternal age", "unit": "years", "type": "int",
        "required": True, "min": 12, "max": 55, "check_min": 15, "check_max": 45,
        "placeholder": "27",
    },
    "facility_level": {
        "label": "Facility level", "type": "select", "required": True, "remember": True,
        "options": [
            {"value": "PHC", "label": "Primary health centre (PHC)"},
            {"value": "Secondary", "label": "Secondary (general hospital)"},
            {"value": "Tertiary", "label": "Tertiary (teaching hospital / FMC)"},
        ],
    },
    "geo_zone": {
        "label": "Geopolitical zone", "type": "select", "required": True, "remember": True,
        "options": [{"value": z, "label": z} for z in
                    ["North-Central", "North-East", "North-West",
                     "South-East", "South-South", "South-West"]],
    },
    "gestational_age_wks": {
        "label": "Gestational age", "noun": "gestational age", "unit": "weeks",
        "type": "int", "required": True, "min": 4, "max": 45,
        "check_min": 8, "check_max": 42, "placeholder": "28",
        "help": "Whole weeks, from LMP or ultrasound.",
    },
    "parity": {
        "label": "Parity", "noun": "parity", "type": "int", "required": True,
        "min": 0, "max": 20, "check_max": 10, "placeholder": "0",
        "help": "Number of previous births, not counting this pregnancy.",
    },
    "previous_cs": {
        "label": "Previous caesarean section?", "short_label": "Previous CS",
        "type": "choice", "required": True, "options": YES_NO,
    },
    "previous_loss": {
        "label": "Previous pregnancy loss?", "short_label": "Previous loss",
        "type": "choice", "required": True, "options": YES_NO,
        "help": "Miscarriage or stillbirth.",
    },
    "gdm_risk": {
        "label": "Diabetes risk factors?", "short_label": "Diabetes risk factors",
        "type": "choice", "required": True, "options": YES_NO,
        "help": "For example: diabetes in a previous pregnancy, a previous very large "
                "baby, or a parent or sibling with diabetes.",
    },
    "sbp_mmhg": {
        "label": "Systolic BP", "noun": "systolic BP", "unit": "mmHg", "type": "int",
        "required": True, "min": 50, "max": 260, "check_min": 80, "check_max": 200,
        "placeholder": "120", "help": "The top number. Usual range in pregnancy: 90 to 139 mmHg.",
    },
    "dbp_mmhg": {
        "label": "Diastolic BP", "noun": "diastolic BP", "unit": "mmHg", "type": "int",
        "required": True, "min": 30, "max": 160, "check_min": 50, "check_max": 130,
        "placeholder": "80", "help": "The bottom number. Usual range in pregnancy: 60 to 89 mmHg.",
    },
    "bmi": {
        "label": "BMI", "noun": "BMI", "unit": "kg/m²", "type": "decimal",
        "required": True, "min": 12, "max": 70, "check_min": 16, "check_max": 45,
        "placeholder": "24.0", "helper": "bmi",
    },
    "fundal_height_cm": {
        "label": "Fundal height", "noun": "fundal height", "unit": "cm", "type": "decimal",
        "required": True, "min": 5, "max": 50, "placeholder": "28",
        "help": "Symphysis-fundal height in centimetres. Leave blank before 20 weeks.",
    },
    "hemoglobin_gdl": {
        "label": "Haemoglobin (Hb)", "noun": "haemoglobin", "unit": "g/dL", "type": "decimal",
        "required": True, "min": 2, "max": 22, "check_min": 5, "check_max": 17,
        "placeholder": "11.0", "helper": "pcv",
    },
    "urine_protein": {
        "label": "Urine protein (dipstick)", "short_label": "Urine protein",
        "type": "choice", "required": True,
        "options": [
            {"value": "negative", "label": "Neg"},
            {"value": "trace", "label": "Trace"},
            {"value": "1+", "label": "1+"},
            {"value": "2+", "label": "2+"},
            {"value": "3+", "label": "3+"},
        ],
    },
    "hiv_status": {
        "label": "HIV test", "short_label": "HIV", "type": "choice",
        "required": True, "options": TEST_RESULT,
    },
    "malaria_status": {
        "label": "Malaria test", "short_label": "Malaria", "type": "choice",
        "required": True, "options": TEST_RESULT, "help": "RDT or microscopy.",
    },
    "symptom_headache": {
        "label": "Headache", "type": "choice", "required": True, "options": YES_NO,
    },
    "symptom_oedema": {
        "label": "Swelling (oedema)", "type": "choice", "required": True, "options": YES_NO,
        "help": "Of the face, hands or legs.",
    },
    "symptom_rfm": {
        "label": "Reduced fetal movement", "type": "choice", "required": True,
        "options": YES_NO, "help": "Baby moving less than usual.",
    },
    "symptom_bleeding": {
        "label": "Vaginal bleeding", "type": "choice", "required": True, "options": YES_NO,
    },
    "symptom_epigastric": {
        "label": "Upper abdominal (epigastric) pain", "short_label": "Epigastric pain",
        "type": "choice", "required": True, "options": YES_NO,
    },
}

# Fields that only feed the risk model as context, or are not scored at all.
RECORD_ONLY = {"patient_id"}

# ── Checks across entries (mirrored in templates/index.html via client_schema) ──
LOGIC = {
    # Fundal height is usually not measurable before this; blank is allowed and the
    # model is given the gestational age instead (i.e. growth assumed on track).
    "fh_required_from_weeks": 20,
    # Mothers cannot feel fetal movements before this.
    "movement_from_weeks": 16,
    # Youngest plausible age at first birth: parity above age minus this is impossible.
    "min_age_at_first_birth": 11,
    "messages": {
        "cs_needs_birth": "Parity is 0, but a previous caesarean section means at least one previous birth. "
                          "Correct the parity or this answer.",
        "parity_impossible": "A parity of {parity} isn't possible for a mother aged {age}. Check the age and parity.",
        "movement_too_early": "Fetal movements can't be felt before {weeks} weeks, and this pregnancy is "
                              "{ga} weeks. Check the gestational age, or answer No.",
        "fh_required": "Fundal height is required from {weeks} weeks.",
    },
}


def _msg(key, **kw):
    text = LOGIC["messages"][key]
    for k, v in kw.items():
        text = text.replace("{" + k + "}", str(v))
    return text

# ── Early-warning rules ──────────────────────────────────────────────────────
# kind:
#   guardrail  fixed clinical threshold. Raises the risk level to at least `floor`
#              whatever the ML model says (used by app.apply_rule_guardrails).
#   flag       warning sign with a named condition and guidance. The ML model sets
#              the overall level; the flag is always shown on the result.
#   signal     danger sign the ML model weighs, with no fixed threshold.
# group: only the most serious triggered rule in a group is shown, so Hb 6.5
#        reads "Severe anaemia" rather than three anaemia alerts.
# when:  {"all": [...]} or {"any": [...]} of [variable, operator, value].
#        Variables are form fields plus the derived values in derive().
RULES = [
    # Guardrails → Critical
    {"id": "severe_htn", "kind": "guardrail", "floor": 3, "group": "bp",
     "title": "Severe hypertension", "detects": "Severe pre-eclampsia / severe hypertension",
     "icd11": "JA24.1 / JA23", "threshold": "Systolic ≥ 160 or diastolic ≥ 110 mmHg",
     "when": {"any": [["sbp_mmhg", ">=", 160], ["dbp_mmhg", ">=", 110]]}},
    {"id": "aph", "kind": "guardrail", "floor": 3, "group": "bleeding",
     "title": "Bleeding after a previous caesarean",
     "detects": "Antepartum haemorrhage / placenta praevia", "icd11": "JA41.Z",
     "threshold": "Vaginal bleeding + previous CS + more than 24 weeks",
     "when": {"all": [["symptom_bleeding", "==", 1], ["previous_cs", "==", 1],
                      ["gestational_age_wks", ">", 24]]}},
    {"id": "severe_anaemia", "kind": "guardrail", "floor": 3, "group": "anaemia",
     "title": "Severe anaemia", "detects": "Severe anaemia in pregnancy", "icd11": "JB64.0",
     "threshold": "Hb below 7 g/dL",
     "when": {"all": [["hemoglobin_gdl", "<", 7]]}},
    # Guardrails → at least High
    {"id": "pre_eclampsia", "kind": "guardrail", "floor": 2, "group": "bp",
     "title": "High BP with protein in urine", "detects": "Pre-eclampsia", "icd11": "JA24.0",
     "threshold": "Systolic ≥ 140 mmHg with urine protein 2+ or 3+",
     "when": {"all": [["sbp_mmhg", ">=", 140], ["protein_level", ">=", 3]]}},
    {"id": "mod_anaemia", "kind": "guardrail", "floor": 2, "group": "anaemia",
     "title": "Moderate to severe anaemia", "detects": "Moderate to severe anaemia", "icd11": "JB64.0",
     "threshold": "Hb below 9 g/dL",
     "when": {"all": [["hemoglobin_gdl", "<", 9]]}},
    # Warning signs (flags)
    {"id": "fgr", "kind": "flag", "group": "growth",
     "title": "Fundal height behind dates", "detects": "Fetal growth restriction",
     "icd11": "JA86.4",
     "threshold": "From 20 weeks, fundal height more than 4 cm below gestational age",
     "when": {"all": [["gestational_age_wks", ">=", 20], ["fh_lag", ">", 4]]}},
    {"id": "rfm", "kind": "flag", "group": "fetal",
     "title": "Reduced fetal movement", "detects": "Possible fetal distress", "icd11": "JA86.Y",
     "threshold": "Reduced movement at 28 weeks or more",
     "when": {"all": [["symptom_rfm", "==", 1], ["gestational_age_wks", ">=", 28]]}},
    {"id": "malaria", "kind": "flag", "group": "malaria",
     "title": "Malaria positive", "detects": "Malaria in pregnancy", "icd11": "JB63.6",
     "threshold": "Positive malaria test",
     "when": {"all": [["malaria_status", "==", 1]]}},
    {"id": "hiv", "kind": "flag", "group": "hiv",
     "title": "HIV positive", "detects": "PMTCT protocol needed", "icd11": "JB63.7",
     "threshold": "Positive HIV test",
     "when": {"all": [["hiv_status", "==", 1]]}},
    {"id": "gest_htn", "kind": "flag", "group": "bp",
     "title": "Raised blood pressure", "detects": "Gestational hypertension", "icd11": "JA23",
     "threshold": "Systolic ≥ 140 or diastolic ≥ 90 mmHg",
     "when": {"any": [["sbp_mmhg", ">=", 140], ["dbp_mmhg", ">=", 90]]}},
    {"id": "low_bp", "kind": "flag", "group": "bp_low",
     "title": "Low blood pressure", "detects": "Hypotension (possible bleeding, sepsis or dehydration)",
     "threshold": "Systolic below 90 or diastolic below 60 mmHg",
     "when": {"any": [["sbp_mmhg", "<", 90], ["dbp_mmhg", "<", 60]]}},
    {"id": "mild_anaemia", "kind": "flag", "group": "anaemia",
     "title": "Anaemia", "detects": "Mild anaemia in pregnancy", "icd11": "JB64.0",
     "threshold": "Hb below 11 g/dL",
     "when": {"all": [["hemoglobin_gdl", "<", 11]]}},
    {"id": "grand_multip", "kind": "flag", "group": "parity",
     "title": "Five or more previous births", "detects": "Grand multiparity", "icd11": "QA4A",
     "threshold": "Parity 5 or more",
     "when": {"all": [["parity", ">=", 5]]}},
    {"id": "obesity", "kind": "flag", "group": "bmi",
     "title": "BMI 30 or above", "detects": "Obesity in pregnancy", "icd11": "JB64.2",
     "threshold": "BMI ≥ 30",
     "when": {"all": [["bmi", ">=", 30]]}},
    {"id": "gdm", "kind": "flag", "group": "gdm",
     "title": "Diabetes risk factors with BMI ≥ 27", "detects": "Gestational diabetes risk",
     "icd11": "QA43.Z", "threshold": "Diabetes risk factors and BMI ≥ 27",
     "when": {"all": [["gdm_risk", "==", 1], ["bmi", ">=", 27]]}},
    {"id": "prev_cs", "kind": "flag", "group": "scar",
     "title": "Previous caesarean section", "detects": "Uterine scar risks", "icd11": "JA84.2",
     "threshold": "Any previous CS",
     "when": {"all": [["previous_cs", "==", 1]]}},
    # Danger signs weighed by the model only
    {"id": "headache", "kind": "signal", "group": "headache",
     "title": "Headache", "detects": "Pre-eclampsia warning symptom",
     "threshold": "Reported today", "when": {"all": [["symptom_headache", "==", 1]]}},
    {"id": "oedema", "kind": "signal", "group": "oedema",
     "title": "Swelling (oedema)", "detects": "Pre-eclampsia warning symptom",
     "threshold": "Reported today", "when": {"all": [["symptom_oedema", "==", 1]]}},
    {"id": "epigastric", "kind": "signal", "group": "epigastric",
     "title": "Epigastric pain", "detects": "Pre-eclampsia warning symptom",
     "threshold": "Reported today", "when": {"all": [["symptom_epigastric", "==", 1]]}},
    {"id": "bleeding", "kind": "signal", "group": "bleeding",
     "title": "Vaginal bleeding", "detects": "Possible haemorrhage or miscarriage",
     "threshold": "Reported today", "when": {"all": [["symptom_bleeding", "==", 1]]}},
    {"id": "rfm_any", "kind": "signal", "group": "fetal",
     "title": "Reduced fetal movement", "detects": "Fetal wellbeing concern",
     "threshold": "Reported before 28 weeks", "when": {"all": [["symptom_rfm", "==", 1]]}},
    {"id": "gdm_factors", "kind": "signal", "group": "gdm",
     "title": "Diabetes risk factors", "detects": "Gestational diabetes risk",
     "threshold": "Risk factors present", "when": {"all": [["gdm_risk", "==", 1]]}},
    {"id": "prev_loss", "kind": "signal", "group": "loss",
     "title": "Previous pregnancy loss", "detects": "Recurrent loss risk",
     "threshold": "Any previous miscarriage or stillbirth",
     "when": {"all": [["previous_loss", "==", 1]]}},
]

KIND_RANK = {"guardrail": 3, "flag": 2, "signal": 1}

# Derived variables map back to the form fields they come from.
DERIVED_FROM = {
    "protein_level": ["urine_protein"],
    "fh_lag": ["gestational_age_wks", "fundal_height_cm"],
}

PROTEIN_LEVELS = [o["value"] for o in FIELDS["urine_protein"]["options"]]


def _rule_fields(rule):
    out = []
    for cond in next(iter(rule["when"].values())):
        for f in DERIVED_FROM.get(cond[0], [cond[0]]):
            if f not in out:
                out.append(f)
    return out


def _section_of(field_id):
    for s in SECTIONS:
        if field_id in s["fields"]:
            return s["id"]
    return None


for _r in RULES:
    _r["fields"] = _rule_fields(_r)
    _r["sections"] = sorted({_section_of(f) for f in _r["fields"]},
                            key=lambda sid: [s["id"] for s in SECTIONS].index(sid))
    _r["rank"] = KIND_RANK[_r["kind"]] * 10 + _r.get("floor", 0)
    if _r["kind"] == "guardrail":
        _r["effect"] = ("Critical alert" if _r["floor"] == 3 else "High alert")
    elif _r["kind"] == "flag":
        _r["effect"] = "Warning sign"
    else:
        _r["effect"] = "Noted"


def field_role(field_id):
    """Strongest way a field feeds the early warning system."""
    if field_id in RECORD_ONLY:
        return "record"
    kinds = {r["kind"] for r in RULES if field_id in r["fields"]}
    for k in ("guardrail", "flag"):
        if k in kinds:
            return k
    return "model"


def field_detects(field_id):
    """What a field helps detect, most serious first, without duplicates."""
    seen, out = set(), []
    for r in sorted(RULES, key=lambda r: -r["rank"]):
        if field_id in r["fields"] and r["detects"] not in seen:
            seen.add(r["detects"])
            out.append(r["detects"])
    return out


def alert_detects(field_id):
    """What a field helps detect through alerts and warning signs (not 'noted' signals)."""
    seen, out = set(), []
    for r in sorted(RULES, key=lambda r: -r["rank"]):
        if r["kind"] != "signal" and field_id in r["fields"] and r["detects"] not in seen:
            seen.add(r["detects"])
            out.append(r["detects"])
    return out


def section_watch(section_id):
    """Everything the early warning system checks for using this section's entries."""
    seen, out = set(), []
    for r in rules_for_section(section_id):
        if r["kind"] != "signal" and r["detects"] not in seen:
            seen.add(r["detects"])
            out.append(r["detects"])
    return out


def rules_for_section(section_id):
    """Rules that use at least one entry from this section, most serious first."""
    fields = next(s["fields"] for s in SECTIONS if s["id"] == section_id)
    return sorted((r for r in RULES if set(r["fields"]) & set(fields)),
                  key=lambda r: -r["rank"])


def model_only_fields(section_id):
    """Entries in this section that feed the ML model but no fixed rule."""
    fields = next(s["fields"] for s in SECTIONS if s["id"] == section_id)
    return [f for f in fields if field_role(f) == "model"]


# ── Parsing & validation (mirrored in templates/index.html) ──────────────────
_TRUE = {"1", "yes", "true", "positive", "on"}
_FALSE = {"0", "no", "false", "negative", "not_tested", "off"}


def _fmt(n):
    return ("%g" % n) if isinstance(n, (int, float)) else str(n)


def _range_error(f, value):
    unit = (" " + f["unit"]) if f.get("unit") else ""
    return (f"{_fmt(value)}{unit} isn't a realistic {f['noun']}. "
            f"Enter a value from {_fmt(f['min'])} to {_fmt(f['max'])}{unit}.")


def validate(payload):
    """
    Check a submitted form. Returns (values, errors).
    values: scored values ready for the model (ints/floats/strings).
    errors: {field_id: message} for anything missing or impossible.
    """
    values, errors = {}, {}
    payload = payload or {}

    for fid, f in FIELDS.items():
        raw = payload.get(fid)
        raw = "" if raw is None else str(raw).strip()
        if raw == "" and fid == "fundal_height_cm":
            ga = values.get("gestational_age_wks")
            if ga is not None and ga < LOGIC["fh_required_from_weeks"]:
                values[fid] = float(ga)        # not measurable yet: assume growth on track
                continue
            if ga is not None:
                errors[fid] = _msg("fh_required", weeks=LOGIC["fh_required_from_weeks"])
                continue
        if raw == "":
            if f.get("required"):
                errors[fid] = f"{f.get('short_label', f['label']).rstrip('?')} is required."
            elif f["type"] == "text":
                values[fid] = ""
            continue

        t = f["type"]
        if t == "text":
            raw = "".join(ch for ch in raw if ch.isprintable())
            if len(raw) > f["max_length"]:
                errors[fid] = f"Keep this under {f['max_length']} characters."
            else:
                values[fid] = raw
        elif t in ("int", "decimal"):
            try:
                num = float(raw)
            except ValueError:
                errors[fid] = "Enter a number."
                continue
            if not math.isfinite(num):
                errors[fid] = "Enter a number."
            elif t == "int" and num != int(num):
                errors[fid] = "Enter a whole number."
            elif num < f["min"] or num > f["max"]:
                errors[fid] = _range_error(f, int(num) if t == "int" else num)
            else:
                values[fid] = int(num) if t == "int" else num
        elif t == "select":
            allowed = [o["value"] for o in f["options"]]
            if raw in allowed:
                values[fid] = raw
            else:
                errors[fid] = "Choose one of the options."
        elif t == "choice":
            allowed = {o["value"]: o for o in f["options"]}
            if fid == "urine_protein":
                if raw in allowed:
                    values[fid] = raw
                else:
                    errors[fid] = "Choose one of the options."
            elif raw.lower() in _TRUE:
                values[fid] = 1
            elif raw.lower() in _FALSE:
                values[fid] = 0
            else:
                errors[fid] = "Choose one of the options."

    # Checks across entries: answers that contradict each other
    sbp, dbp = values.get("sbp_mmhg"), values.get("dbp_mmhg")
    if sbp is not None and dbp is not None and dbp >= sbp:
        errors["dbp_mmhg"] = (f"Diastolic must be lower than systolic ({sbp} mmHg). "
                              "Check the reading.")
        values.pop("dbp_mmhg", None)

    age, parity = values.get("age"), values.get("parity")
    if age is not None and parity is not None and parity > age - LOGIC["min_age_at_first_birth"]:
        errors["parity"] = _msg("parity_impossible", parity=parity, age=age)
        values.pop("parity", None)
    elif values.get("previous_cs") == 1 and parity == 0:
        errors["previous_cs"] = _msg("cs_needs_birth")
        values.pop("previous_cs", None)

    ga = values.get("gestational_age_wks")
    if values.get("symptom_rfm") == 1 and ga is not None and ga < LOGIC["movement_from_weeks"]:
        errors["symptom_rfm"] = _msg("movement_too_early", weeks=LOGIC["movement_from_weeks"], ga=ga)
        values.pop("symptom_rfm", None)

    return values, errors


# ── Rule evaluation (mirrored in templates/index.html) ───────────────────────
def derive(values):
    v = dict(values)
    if "urine_protein" in v and v["urine_protein"] in PROTEIN_LEVELS:
        v["protein_level"] = PROTEIN_LEVELS.index(v["urine_protein"])
    if "gestational_age_wks" in v and "fundal_height_cm" in v:
        v["fh_lag"] = v["gestational_age_wks"] - v["fundal_height_cm"]
    return v


_OPS = {
    ">=": lambda a, b: a >= b, ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b, "<": lambda a, b: a < b,
    "==": lambda a, b: a == b,
}


def _cond_true(v, cond):
    var, op, ref = cond
    return var in v and _OPS[op](v[var], ref)


def rule_fires(rule, values):
    v = derive(values)
    mode, conds = next(iter(rule["when"].items()))
    results = [_cond_true(v, c) for c in conds]
    return all(results) if mode == "all" else any(results)


def triggered_rules(values, dedupe=True):
    """
    Rules that fire for these values, most serious first.
    Within a group only the most serious rule is kept, plus any other alert rule
    that brings in a different entry (e.g. BP 165/100 with protein 2+ keeps both
    "Severe hypertension" and "High BP with protein in urine").
    """
    fired = sorted((r for r in RULES if rule_fires(r, values)), key=lambda r: -r["rank"])
    if not dedupe:
        return fired
    kept, out = {}, []
    for r in fired:
        group = kept.get(r["group"])
        if group is None:
            kept[r["group"]] = [r]
            out.append(r)
            continue
        covered = set().union(*(k["fields"] for k in group))
        if r["kind"] == "guardrail" and not set(r["fields"]) <= covered:
            group.append(r)
            out.append(r)
    return out


def guardrail_floor(values):
    """Lowest risk level the fixed clinical rules allow (0 = no constraint)."""
    floors = [r["floor"] for r in RULES if r["kind"] == "guardrail" and rule_fires(r, values)]
    return max(floors, default=0)


def warning_signs(values):
    """Triggered rules shaped for the API response."""
    titles = {s["id"]: s["title"] for s in SECTIONS}
    out = []
    for r in triggered_rules(values):
        out.append({
            "id": r["id"], "kind": r["kind"], "title": r["title"],
            "detects": r["detects"], "threshold": r["threshold"],
            "effect": r["effect"], "icd11": r.get("icd11"),
            "floor": RISK_NAMES[r["floor"]] if r.get("floor") else None,
            "fields": r["fields"],
            "sections": [{"id": s, "title": titles[s]} for s in r["sections"]],
        })
    return out


# ── What the browser needs ───────────────────────────────────────────────────
def client_schema():
    return {
        "sections": SECTIONS,
        "fields": FIELDS,
        "rules": [{k: r[k] for k in ("id", "kind", "floor", "group", "title", "detects",
                                     "threshold", "effect", "icd11", "when", "fields",
                                     "sections", "rank") if k in r}
                  for r in RULES],
        "derived_from": DERIVED_FROM,
        "logic": LOGIC,
        "protein_levels": PROTEIN_LEVELS,
        "risk_names": RISK_NAMES,
    }

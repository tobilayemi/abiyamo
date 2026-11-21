# Abiyamo FHIR R4 interface

Abiyamo exchanges ANC assessments with facility EMRs using **HL7 FHIR R4 (4.0.1)**, the version served by the OpenMRS FHIR2 module (`/openmrs/ws/fhir2/R4/`). Reference guide for future alignment: the WHO Antenatal Care FHIR Implementation Guide (draft v0.3.0, `build.fhir.org/ig/WorldHealthOrganization/smart-anc`).

Code: [`anc_fhir.py`](../anc_fhir.py). Every LOINC, SNOMED CT and ICD-11 code below was checked against the HL7 terminology server (tx.fhir.org).

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/fhir/metadata` | CapabilityStatement |
| `GET` | `/fhir/OperationDefinition/abiyamo-assess` | Definition of the `$assess` operation |
| `POST` | `/fhir/$assess` | Send a Bundle of ANC Observations, receive a Bundle with a RiskAssessment |
| `POST` | `/predict?format=fhir` | Form JSON in, FHIR Bundle out (used by the "Download FHIR record" button) |

`$assess` accepts `Content-Type: application/fhir+json`. Facility level and geopolitical zone can come from an `Organization` in the bundle or as query parameters, e.g. `?facility_level=PHC&geo_zone=North-Central`, set once per facility.

Responses:
- `200`: a `collection` Bundle with Patient, Organization, 18 Observations, Device and RiskAssessment.
- `422`: an OperationOutcome listing each missing or invalid entry. Missing observations are never assumed negative.
- `400`: the body is not a Bundle.

## Entry mapping

| Form entry | FHIR | Code |
| --- | --- | --- |
| Age | Observation, valueQuantity `a` | LOINC 30525-0 |
| Gestational age | Observation, valueQuantity `wk` (days accepted on input) | LOINC 49051-6 |
| Parity | Observation, valueInteger | LOINC 11977-6 |
| Systolic / diastolic BP | Observation BP panel with components, `mm[Hg]` (separate observations accepted on input) | LOINC 85354-9 · 8480-6 · 8462-4 |
| BMI | Observation, valueQuantity `kg/m2` | LOINC 39156-5 |
| Fundal height | Observation, valueQuantity `cm` | LOINC 11881-0 |
| Haemoglobin | Observation, valueQuantity `g/dL` (g/L accepted on input) | LOINC 718-7 |
| Urine protein (dipstick) | Observation, valueCodeableConcept | LOINC 20454-5; SNOMED Negative 260385009, Trace 260405006, + 260347006, ++ 260348001, +++ 260349009 |
| HIV test | Observation, Positive 10828004 / Negative 260385009; not tested = `dataAbsentReason: not-performed` | LOINC 80387-4 (also accepts 75622-1, 68961-2, 7917-8, 31201-7, 49580-4) |
| Malaria test | as HIV | LOINC 50687-3 (also accepts 51587-4, 46094-9, 76772-3) |
| Previous caesarean section | Observation, valueBoolean | SNOMED 161805006 |
| Headache · oedema · reduced fetal movement · vaginal bleeding · epigastric pain | Observation, valueBoolean | SNOMED 25064002 · 267038008 · 276369006 · 289530006 · 79922009 |
| Previous pregnancy loss | Observation, valueBoolean | Local `previous-pregnancy-loss` |
| Diabetes risk factors | Observation, valueBoolean | Local `gdm-risk-factors` |
| Facility level, geopolitical zone | Organization.type | Local code systems |
| Patient ID / ANC number | Patient.identifier | — |

## Risk result → RiskAssessment

| Field | Content |
| --- | --- |
| `basis` | References to every Observation used |
| `prediction.outcome` | Named condition with its ICD-11 MMS code |
| `prediction.qualitativeRisk` | Abiyamo level (local code system), plus HL7 `risk-probability` for Low, Moderate and High. HL7 has no "critical" level |
| `prediction.probabilityDecimal` | Model probability for the final level. Omitted when a fixed clinical threshold overrode the model |
| `prediction.rationale` | The alerts that fired, with thresholds |
| `mitigation` | Referral decision and immediate actions |
| `performer` | Device: Abiyamo ANC risk model 1.0 |

## Validation done

- All output resources (Bundle and its entries, OperationOutcome, CapabilityStatement, OperationDefinition) parse as valid FHIR using the `fhir.resources` R4B models.
- An exported Bundle sent back to `$assess` gives the identical result.
- An EMR-style Bundle (separate BP observations, Hb in g/L, other HIV/malaria LOINC codes) is read and scored correctly.

## Not done yet

- Testing against a live EMR (e.g. an OpenMRS FHIR2 sandbox) and the official HL7 validator with profiles.
- **SMART on FHIR** launch, to open Abiyamo inside the EMR with the patient pre-filled.
- **CDS Hooks**, to show Abiyamo alerts as cards inside the EMR.
- Authentication on the FHIR endpoints. Required before any real patient data is sent.

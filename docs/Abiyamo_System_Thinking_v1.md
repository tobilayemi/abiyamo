# ABIYAMO

**AI Companion for Safe Pregnancy and Healthy Newborns**

*System Thinking Document | Version 1.0 | March 2026*

**Core Promise:** Abiyamo turns routine ANC data and a mother's phone into an early warning system that protects both mother and baby, from pregnancy through to the first 28 days of life.

**Prepared by:** Oluwatobi, AI4SID Accelerator Programme, Cohort Capstone Project

---

## 1. Problem Statement

Nigeria accounts for roughly 20% of global maternal deaths. Most of these deaths are preventable and happen in the context of antenatal care contacts where danger signs are present but go undetected, get acted on too late, or are not communicated clearly to the mother.

Three connected failures sit behind this crisis.

**Failure 1: Clinic Side.** Considering the issue of brain drain and lack of man power within the heath sector most especially at the rural communities, Mother/child mortality sometimes happen as a result of lack of manpower available

**Failure 2: Mother Side.** Mothers leave the clinic with verbal advice they cannot recall or act on. Danger signs are not communicated in plain language or in local languages. Appointment compliance is low.

**Failure 3: Newborn Window.** The first 28 days of life carry the highest mortality risk for Nigerian newborns. Families go home from facilities with no structured watchlist or alert system for jaundice, sepsis, or feeding failure during this critical period.

---

## 2. Solution Overview: ABIYAMO

Abiyamo is a three layer AI system that works at the clinic level, the community level, and the household level at the same time. It does not require new data collection, new hardware, or major changes to existing workflows.

- **Layer 1, Clinic Risk:** Smart ANC risk scoring at the point of care.
- **Layer 2, Mother Guide:** WhatsApp engagement in English, Pidgin, or Yoruba.
- **Layer 3, Newborn Watch:** A Day 1 to 28 checklist with jaundice, sepsis, and immunization alerts.

---

## 3. System Architecture

The system has four integrated components that work together to deliver intelligent risk assessment and timely intervention.

### 3.1 Data Layer

Abiyamo draws from existing clinical data sources, so it adds no new data collection burden on healthcare workers.

- ANC registers and patient records at primary, secondary, and tertiary facilities
- EMR API integration: DHIS2, NHMIS compatible platforms, and facility specific EMRs
- A manual entry fallback interface for facilities that are not yet digitised
- WhatsApp self reported symptoms and responses from mothers

### 3.2 AI Model Architecture: Hybrid Approach

Abiyamo uses a hybrid AI model that combines rule based clinical logic with machine learning, so it stays both transparent and adaptable.

1. **Input Variables.** Blood pressure (systolic and diastolic), hemoglobin, gestational age, BMI, fundal height, urine protein, HIV status, malaria status, previous obstetric history (parity, CS, losses), and presenting symptoms (oedema, headache, reduced fetal movement, bleeding).

2. **Rule Based Layer (Clinical Guardrails).** Hard clinical thresholds taken from WHO ANC guidelines and Nigerian clinical protocols. This layer catches critical values immediately. For example, BP at or above 160/110 raises a severe pre-eclampsia flag regardless of other variables. It makes sure no dangerous case slips past the ML model.

3. **ML Model Layer (Nuanced Scoring).** A gradient boosted classifier such as XGBoost, trained on ANC outcome data. It captures interaction effects between variables that rules cannot detect, and it outputs a continuous risk probability score that the rules layer can override where thresholds are breached.

4. **ICD-10/11 Mapping Engine.** Risk outputs are mapped to relevant ICD-11 codes (Chapter 18: Pregnancy, childbirth and the puerperium). This grounds outputs in clinical language, enables documentation interoperability, and points to specific clinical guidance per condition.

5. **Output Generation.** A risk category (Low, Moderate, High, or Critical), a condition specific danger explanation, immediate clinical actions, and a referral pathway recommendation. The output uses plain language for the CHO, with the ICD code kept in the background for records.

---

## 4. ICD-11 Condition Mapping (ANC Risk Layer)

The table below maps key obstetric conditions to their ICD-11 codes, the clinical trigger criteria inside Abiyamo, and the recommended action output.

| ICD-11 Code | Condition | Abiyamo Trigger | System Action |
| --- | --- | --- | --- |
| JA24.1 | Gestational hypertension | BP at or above 140/90 on 2 readings, no proteinuria | Moderate risk flag, repeat BP in 4 hrs, monitor |
| JA24.2 | Pre-eclampsia | BP at or above 140/90 with urine protein at or above 2+ | High risk flag, urgent referral, MgSO4 protocol |
| JA24.3 | Severe pre-eclampsia | BP at or above 160/110 with symptoms (headache, oedema) | Critical flag, emergency referral, immediate action |
| JA42 | Gestational anaemia | Hb under 11 g/dL (1st and 3rd trimester), under 10.5 (2nd) | Moderate flag, iron and folate protocol, dietary advice |
| JA43 | Severe anaemia in pregnancy | Hb under 7 g/dL | High risk flag, transfusion consideration, referral |
| JA60 | Placenta praevia | Previous CS with low lying placenta history and bleeding | Critical flag, no vaginal exam, emergency referral |
| JA65 | Fetal growth restriction | Fundal height under gestational age by more than 3 cm on serial measure | High risk flag, ultrasound referral, monitoring protocol |
| 1A44.Z | Malaria in pregnancy | Confirmed malaria status flagged at intake | Moderate to high flag, treatment protocol, monitoring |
| 1C62.Z | HIV in pregnancy | HIV positive status in record | PMTCT protocol trigger, ART adherence reminder |

---

## 5. Data Input Variables

The variables below are collected as part of routine ANC practice and feed into the Abiyamo risk model. No extra data collection is needed.

| Variable | Type | Source | Clinical Relevance |
| --- | --- | --- | --- |
| Blood Pressure (SBP/DBP) | Numerical (mmHg) | Clinic measurement | Hypertension and pre-eclampsia screening |
| Hemoglobin Level | Numerical (g/dL) | Lab result or RDT | Anaemia classification and severity |
| Gestational Age | Numerical (weeks) | LMP or ultrasound | Risk calibration, growth assessment |
| Fundal Height | Numerical (cm) | Clinic measurement | Fetal growth restriction detection |
| BMI | Numerical (kg/m²) | Weight and Height | Obesity risk, GDM screening |
| Urine Protein | Categorical (neg/1+/2+/3+) | Dipstick test | Pre-eclampsia diagnosis |
| HIV Status | Binary | ANC test record | PMTCT protocol trigger |
| Malaria Status | Binary or Categorical | RDT or lab | Treatment and monitoring protocol |
| Parity | Numerical | Obstetric history | Grand multiparity risk, previous complications |
| Previous CS | Binary | Obstetric history | Placenta praevia, uterine rupture risk |
| Previous Pregnancy Loss | Binary or Count | Obstetric history | Recurrent loss risk profiling |
| Presenting Symptoms | Multi select categorical | Symptom checklist | Pre-eclampsia, APH, IUGR, infection flags |

---

## 6. System Users and Use Cases

### Nurse, Midwife, or CHO
- Opens Abiyamo at the point of ANC contact
- Enters or confirms patient data from the register
- Receives an instant risk output and action guide
- Documents the referral or management decision
- Carries no extra workload beyond normal ANC recording

### Pregnant Mother and Family
- Registered at first ANC contact through a phone number
- Receives WhatsApp messages in the preferred language
- Gets appointment reminders and danger sign alerts
- Receives personalised nutrition and newborn care tips
- Can self report symptoms through the WhatsApp chatbot

### Facility Manager
- Views an aggregate risk dashboard for the facility
- Tracks referral compliance and outcomes
- Monitors ANC quality indicators over time
- Receives alerts for high risk case clusters

### State and LGA Health Authorities
- Access aggregated, anonymised population risk data
- Track maternal health performance across facilities
- Inform resource allocation and referral pathway planning
- Support DHIS2 and NHMIS reporting integration

---

## 7. Data Flow Architecture

The steps below describe the end to end data flow for the Clinic Risk Scoring layer.

**A. Data Entry.** The nurse enters ANC variables through the Abiyamo interface, or data is pulled automatically from the facility EMR through an API (DHIS2, NHMIS compatible).

**B. Pre-processing.** Input validation and normalisation, missing value handling (imputation or flag), and data formatted for model input.

**C. Rule Engine Check.** Clinical threshold rules run first. Any critical threshold breach flags the case at the right severity level before the ML model runs.

**D. ML Model Inference.** The gradient boosted classifier scores overall obstetric risk and returns a probability vector across the risk categories (Low, Moderate, High, Critical).

**E. ICD Mapping.** The final risk output and variable profile map to relevant ICD-11 codes, and condition specific guidance loads from the protocol library.

**F. Output Display.** The clinician sees the risk category, condition name, danger explanation, immediate actions, and referral recommendation. The ICD code is stored in the record for documentation.

**G. Mother Notification.** If a phone number is registered, a WhatsApp message goes out summarising the visit outcome, the next appointment, and personalised danger sign reminders.

---

## 8. Layer 2: WhatsApp Mother Engagement

The WhatsApp layer runs independently of the clinic risk layer but stays connected to it. It runs on the WhatsApp Business API with a simple NLP chatbot, rule based at first and progressively ML enhanced.

**Message Types by Trimester and Stage**

- **First Trimester:** Nutrition basics, booking confirmation, HIV and malaria test reminders.
- **Second Trimester:** Appointment reminders, fetal movement awareness, danger signs (headache, bleeding, reduced movement).
- **Third Trimester:** Delivery preparation, facility choice, emergency contact, newborn feeding information.
- **Post-delivery:** Daily Day 1 to 7 newborn checklist, jaundice and sepsis warning signs, immunization schedule alerts.
- **All stages:** Symptom self report prompts, escalation to the clinic if danger signs are reported.

**Language Support**

- **English:** Standard clinical plain language.
- **Nigerian Pidgin:** Accessible to a broad urban and rural population.
- **Yoruba:** South-West coverage, expandable to Hausa and Igbo in future versions.

---

## 9. Layer 3: Newborn Protection (Day 1 to 28)

The perinatal window carries Nigeria's highest newborn mortality risk. Abiyamo extends the mother's engagement thread after delivery into a structured 28 day newborn watchlist delivered through WhatsApp.

| Period | Checklist Focus | Alert Triggers |
| --- | --- | --- |
| Day 1 to 3 | Breathing, cord care, first feed (breastfeeding initiation), skin colour, temperature | Yellow skin or eyes, difficulty breathing, not feeding, temperature under 36.5°C or over 37.5°C |
| Day 4 to 7 | Jaundice monitoring, cord separation, continued feeding, weight loss check | Deepening jaundice, cord redness or smell, poor feeding, excessive crying |
| Day 8 to 14 | Feeding pattern, stool and urine output, social responsiveness | No wet nappies, projectile vomiting, lethargy, persistent fever |
| Day 15 to 28 | Growth tracking, immunization reminder (BCG, HepB, OPV0 if not given), developmental checks | Missed immunizations, poor weight gain, persistent jaundice beyond 14 days |

---

## 10. Deployment Strategy

### Phase 1: Prototype (Months 1 to 3)
- Build the rule based risk scoring layer
- Develop the manual entry interface (web based)
- Prototype the WhatsApp bot for one language (English)
- Test with synthetic and de-identified ANC data
- Develop and review the ICD-11 mapping library
- Present the capstone at the AI4SID Demo Day

### Phase 2: Pilot (Months 4 to 9)
- Train the ML model on a real ANC outcome dataset
- Integrate the DHIS2 API for an automated data pull
- Expand WhatsApp to Pidgin and Yoruba
- Pilot in 3 to 5 PHCs in the FCT or North-West Nigeria
- Collect outcome data for model improvement
- Engage the state Ministry of Health as a partner

### Technical Stack (Proposed)
- **Backend:** Python (FastAPI), ML model in scikit-learn or XGBoost
- **Frontend:** React web app for the clinic interface
- **WhatsApp:** Twilio WhatsApp Business API or Meta Cloud API
- **Database:** PostgreSQL with anonymised patient records
- **EMR Integration:** DHIS2 REST API, FHIR compatible endpoints
- **Deployment:** Cloud hosted (AWS or Azure), with an offline first fallback for low connectivity facilities

---

## 11. Ethical Considerations and Responsible AI

### Data Privacy and Consent
- Patient data is anonymised in all model training
- Explicit consent is obtained for WhatsApp enrollment
- No patient identifiers are stored in the model inference layer
- Compliant with the Nigerian Data Protection Regulation (NDPR)

### Model Fairness
- Training data includes diverse geographic and ethnic representation
- Model performance is evaluated separately across population subgroups
- A bias audit happens before any clinical deployment

### Clinical Safety
- Abiyamo supports clinical decision making, it does not replace it
- Every output carries a clear disclaimer that the final decision rests with the clinician
- Critical flags always recommend human review and escalation
- Rule based guardrails stop the ML model from missing critical cases

### Transparency
- ICD-11 mapping keeps risk outputs clinically interpretable
- Rule triggers are documented and reviewable by clinical supervisors
- Model version control and an audit trail are maintained

---

## 12. Open Questions and Next Steps

The items below need further definition as the project develops through the AI4SID Accelerator Programme.

### Open Questions
- **Dataset:** Which ANC outcome dataset will train and validate the ML model (DHIS2 export, NHMIS data, research datasets)?
- **Facility Partners:** Which facilities will serve as pilot sites, and what EMR systems do they use?
- **WhatsApp Registration Flow:** How is mother enrollment triggered at ANC contact, and who captures the phone number?
- **Offline Functionality:** What is the minimum viable offline mode for facilities with intermittent connectivity?
- **Regulatory Pathway:** What approvals are needed from FMOH or NAFDAC for AI clinical decision support deployment?
- **Evaluation Framework:** Which outcomes will measure Abiyamo's impact (referral rates, maternal outcomes, ANC attendance, newborn mortality)?

### Immediate Next Steps
- Finalise the input variable list and clinical threshold rules with a clinical reviewer
- Source and clean an ANC dataset for model training (synthetic or real)
- Build the rule based scoring prototype in Python
- Set up a DHIS2 API sandbox environment for integration testing
- Draft the WhatsApp message content library in English and Pidgin
- Register Abiyamo as a capstone project with AI4SID and align it with programme milestones

---

*ABIYAMO | AI Companion for Safe Pregnancy and Healthy Newborns | AI4SID Accelerator Programme | Version 1.0*

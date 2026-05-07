# ABIYAMO — Mentor Presentation Script
**AI4SID Accelerator Programme | Week 7 of 12**
*Speak conversationally — these are talking notes, not a word-for-word read.*

---

## 1. ABOUT THE PROJECT

"The project is called **Abiyamo** — a Yoruba word that means *'mother has returned'* or *'come, be with me'*. The name is intentional: it reflects the idea of bringing clinical intelligence back to the hands of the frontline worker, right at the moment a pregnant woman walks in.

Abiyamo is a **hybrid AI clinical decision support tool** for antenatal care risk scoring. It is designed specifically for Nigerian health facilities — from primary health centres all the way to tertiary hospitals.

What it does in one sentence: a health worker enters 26 clinical variables for a pregnant woman, and Abiyamo returns a risk category — Low, Moderate, High, or Critical — along with a primary diagnosis, an ICD-11 code, an explanation of what is happening, immediate action steps, and a referral decision. All in under three seconds."

---

## 2. STATEMENT OF PROBLEM

"Nigeria accounts for nearly **12% of global maternal deaths** despite being only 2.4% of the world's population. The WHO estimates **512 maternal deaths per 100,000 live births** — one of the highest rates in the world.

The core problem is not only a lack of care. It is a lack of **structured clinical decision-making** at the point of care. Primary health centres in Nigeria are under-resourced and often staffed by Community Health Extension Workers — CHEWs — who may not have had the training to identify which of the women they see today is at serious risk.

The consequences of a missed high-risk pregnancy are severe: a woman with undetected pre-eclampsia may be sent home without magnesium sulphate, have a seizure overnight, and not survive.

What Abiyamo addresses is that gap: **no structured risk screening tool, no immediate clinical protocol, no referral guidance** — at the point where it matters most."

---

## 3. HOW I DEVELOPED IT

"I approached this in layers — thinking about it as a system before writing a single line of code.

The first thing I did was define the **problem space clearly**: what clinical variables matter for maternal risk in Nigeria, what conditions I need to cover, and what outputs a frontline worker actually needs — not just a number, but something actionable.

From there I moved into **data design**: because no labelled ANC dataset at this granularity exists publicly for Nigeria, I built a synthetic data generator calibrated to Nigerian clinical distributions — things like the prevalence of malaria, anaemia rates, typical blood pressure distributions by geopolitical zone.

I then built the **model layer** — starting with XGBoost, then layering rule-based clinical guardrails on top to make the system safe for life-critical thresholds.

Finally I built the **application layer** — a Flask web interface so the tool can actually be used in a facility, and a landing page that explains the product to any stakeholder who encounters it.

The whole architecture is what I call a **three-layer hybrid**: synthetic data → ML model → clinical rule override → structured output."

---

## 4. TOOLS USED

"The entire stack is Python-based:

- **Python 3.13** — core language
- **Pandas & NumPy** — data generation and feature engineering
- **Scikit-learn** — preprocessing, cross-validation, evaluation metrics
- **XGBoost** — the gradient boosted tree classifier at the heart of the model
- **Matplotlib & Seaborn** — confusion matrix, feature importance, risk analysis plots
- **Flask** — the web application framework serving the UI and prediction API
- **Pickle** — model and encoder serialisation for deployment
- **ICD-11** — the WHO standard used for coding all clinical outputs

The frontend is pure HTML, CSS, and JavaScript — no framework — using Poppins as the typeface, and a clinical colour palette designed around four risk levels."

---

## 5. APPLICATION OF LESSONS FROM THE PROGRAMME

"Several things I learned in the programme directly shaped how I built this.

The first is **systems thinking**. Before the programme, I might have jumped straight to training a model. Instead, I started with a 12-section system thinking document — problem statement, stakeholders, data flow, ethical considerations, deployment strategy. That thinking shaped every technical decision I made.

The second is **the distinction between accuracy and usefulness**. My XGBoost model achieves 99.5% accuracy on test data — but if it ever missed a case of severe pre-eclampsia because the numbers just barely fell below a threshold, that accuracy number means nothing. So I added **clinical rule guardrails** — hard clinical rules that override the model for life-threatening values. This is a direct application of the lesson that AI systems in high-stakes domains need human-defined constraints, not just optimised loss functions.

The third is **responsible data**. Because there is no suitable real ANC dataset I could use ethically, I built a synthetic generator from scratch. That forced me to deeply understand what the actual clinical distributions in Nigeria look like — which made the model more grounded, not less.

And finally: **explainability**. Every output from Abiyamo includes not just a risk level, but an explanation, a list of actions, and an ICD-11 code. The clinician is never left wondering why. That is a direct design principle from what we covered around responsible AI."

---

## 6. HOW I TRAINED THE DATA — STEP BY STEP

*[Reference the code in `abiyamo_model.py` if your mentor wants to see it.]*

**Step 1 — Synthetic Data Generation**
"I wrote a data generator that produces 1,000 ANC patient records. It is calibrated to Nigerian clinical parameters: mean age of 25.7 years, mean gestational age of 25.5 weeks, a malaria prevalence of 18.7%, and an anaemia rate of 61% — which reflects the real-world burden. The dataset has this risk distribution: 17.2% Low, 35.8% Moderate, 33.7% High, 13.3% Critical."

**Step 2 — Feature Engineering**
"Raw clinical variables alone are not enough. I engineered 10 additional derived features that add clinical signal:
- **Pulse pressure** (SBP minus DBP) — a hypertension indicator
- **Mean Arterial Pressure** — a better blood pressure summary than SBP or DBP alone
- **Fundal height–gestational age difference** — flags growth restriction
- **Anaemia severity score** — a 4-level ordinal (0–3) derived from haemoglobin
- **Hypertension flag** and **Severe hypertension flag** — binary clinical thresholds
- **Symptom burden** — count of all active danger signs
- **Third trimester flag**, **Grand multiparity flag**, **Obesity flag**

This took the feature set from 21 raw inputs to 31 model features."

**Step 3 — Encoding**
"Three categorical variables needed encoding:
- Urine protein: ordinal encoding in clinical order — negative, trace, 1+, 2+, 3+
- Facility level: label encoding — PHC, Secondary, Tertiary
- Geopolitical zone: label encoding — 6 zones"

**Step 4 — Train/Test Split**
"I split 80/20 with stratification on the risk category, to ensure all four classes are proportionally represented in both sets. That gave 800 training records and 200 test records."

**Step 5 — XGBoost Training**
"I used XGBoost with 200 estimators, max depth of 6, learning rate of 0.1, and subsampling of 0.8. These are fairly standard parameters for a structured tabular classification problem of this size."

**Step 6 — Clinical Rule Guardrails**
"After the model predicts, five clinical rules can override it:
- SBP ≥ 160 or DBP ≥ 110 → Critical (always)
- Haemoglobin below 7.0 → Critical (always)
- Bleeding + previous CS + GA > 24 weeks → Critical (always)
- SBP ≥ 140 and urine protein 2+ or 3+ → at least High
- Haemoglobin below 9.0 → at least High"

**Step 7 — Evaluation**
"Both the pure model and the hybrid were evaluated using accuracy, weighted F1, and 5-fold cross-validation."

---

## 7. OUTCOME

"The results were strong across both layers:

| Metric | XGBoost Only | Hybrid (Rules + ML) |
|---|---|---|
| Accuracy | **99.5%** | **97.0%** |
| F1 (weighted) | 0.9950 | 0.9707 |
| 5-Fold CV Accuracy | 97.9% ± 0.6% | — |

The hybrid model is *slightly* less accurate than raw XGBoost — and that is by design. Some cases where the model predicted Moderate, the rules correctly override to High or Critical for safety. That is not an error; that is the system working as intended.

The 5-fold cross-validation at 97.9% ± 0.6% tells me the model generalises well and is not overfitting to any one split of the data.

On the application side: the web tool is live, handles all four risk categories correctly, returns ICD-11 coded outputs, and has a landing page that introduces the product to any audience — clinical or non-clinical."

---

## 8. CONFUSION MATRIX & FEATURE IMPORTANCE

### Confusion Matrix

*[Open `abiyamo_confusion_matrix.png` on screen.]*

"This is the confusion matrix for the **hybrid model** on the 200-record test set. The axes are Actual Risk (rows) and Predicted Risk (columns). A perfect classifier would show all values only on the diagonal.

What you want to focus on here are the **off-diagonal cells**:

The most clinically dangerous error would be a **Critical case being predicted as Low or Moderate** — the model missing a life-threatening patient entirely. Looking at the matrix, you can see this is extremely rare, which is what the rule guardrails protect against. If haemoglobin is below 7 or blood pressure is above 160/110, no ML output can override that to a lower category.

The misclassifications that do exist are typically **between adjacent categories** — for example, a Moderate case predicted as High. These are clinically acceptable because they err on the side of caution.

This is a key message: in a safety-critical domain, the direction of your errors matters as much as the rate."

---

### Feature Importance

*[Open `abiyamo_feature_importance.png` on screen.]*

"This chart shows the top 20 features by importance score from the XGBoost model. A few things stand out:

**Haemoglobin and derived anaemia features dominate** — this makes clinical sense. Anaemia is the most common condition in the dataset (61% of patients), and the severity of anaemia directly determines risk level. The model has learned this correctly.

**Blood pressure features are second** — both SBP and DBP appear, along with the derived features: mean arterial pressure, pulse pressure, hypertension flag, and severe hypertension flag. The model is effectively looking at blood pressure from multiple angles simultaneously.

**Urine protein** appears meaningfully in the top features — which reflects its role in distinguishing gestational hypertension from pre-eclampsia.

**Symptom burden** — the aggregate count of danger signs — ranks higher than any individual symptom alone. This tells us the model is picking up on the co-occurrence of symptoms as a signal, not just each symptom in isolation.

What I find interesting is that **facility level and geopolitical zone** have some importance — suggesting that contextual factors about where a woman is presenting do add signal. This is consistent with the reality that risk and access to care are not uniform across Nigeria's six geopolitical zones."

---

## CLOSING

"To summarise: Abiyamo is a working, end-to-end clinical decision support tool. It has a principled data foundation, a hybrid AI architecture that puts patient safety above model accuracy, ICD-11 coded outputs, and a web interface that a health worker can use without any technical training.

What is next for the project — beyond this accelerator — is validation with real ANC data, a pilot at a PHC facility, and potentially integration with Nigeria's DHIS2 health information system.

I am happy to take questions or run a live demonstration of the tool."

---

*Script ends. Backup: open `http://localhost:5000` in browser for live demo.*
*Demo case: SBP 168, DBP 112, Hb 10.5, Protein 3+, Headache + Oedema + Epigastric Pain → should return CRITICAL / Severe Pre-eclampsia.*

# Abiyamo

**AI Companion for Safe Pregnancy and Healthy Newborns**

Abiyamo turns routine ANC data and a mother's phone into an early warning system that protects both mother and baby, from pregnancy through to the first 28 days of life. It is a capstone project for the AI4SID Accelerator Programme.

## What it does

Abiyamo works across three layers at the same time:

- **Clinic Risk:** Smart ANC risk scoring at the point of care.
- **Mother Guide:** WhatsApp engagement in English, Pidgin, or Yoruba.
- **Newborn Watch:** A Day 1 to 28 checklist with jaundice, sepsis, and immunization alerts.

It needs no new data collection, no new hardware, and no major change to existing clinic workflows.

## How it works

A hybrid model pairs rule based clinical guardrails with a gradient boosted classifier. Rules from WHO and Nigerian protocols catch critical values first, the ML model captures the nuanced interactions, and outputs map to ICD-11 codes for clear clinical guidance and documentation.

## Tech stack

- **Backend:** Python (FastAPI), scikit-learn or XGBoost
- **Frontend:** React web app for the clinic interface
- **Messaging:** WhatsApp Business API (Twilio or Meta Cloud)
- **Database:** PostgreSQL with anonymised records
- **Integration:** DHIS2 REST API, FHIR compatible endpoints

## Status

Prototype phase. Building the rule based scoring layer, the manual entry interface, and an English WhatsApp bot, tested on synthetic and de-identified ANC data.

## Responsible AI

Patient data is anonymised, consent is explicit for WhatsApp enrollment, and every output makes clear that the final decision rests with the clinician. Abiyamo supports clinical judgment, it does not replace it.

## Author

Oluwatobi, AI4SID Accelerator Programme.

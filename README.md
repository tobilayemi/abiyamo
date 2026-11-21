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

## Who it's for

- **Users:** midwives, nurses and CHEWs at primary health centres (the web app), and pregnant women and new mothers (WhatsApp, in development).
- **Customers:** state primary health care boards and ministries of health, with pilots funded by donor maternal health programmes.
- **First pilot:** a small number of PHCs; site and partner still being confirmed.

Full personas: [docs/stakeholders.md](docs/stakeholders.md).

## The ANC form

The web app (`/app`) takes the ANC form one section per screen: mother and visit, pregnancy and history, vital signs, test results, danger signs, then a review page before submission. It is built for phones. Values are checked as they are typed, entries are saved on the device after every change, and the form keeps working when the connection drops.

Each page lists what its entries are checked for, entries that can raise an alert carry an "Early warning" tag, and the risk report lists which entries raised each alert. `/early-warning` maps every form section to the alerts it can raise. The form, validation, alert rules and that page all come from one table in `anc_form.py`, which is also what the server uses to apply its clinical guardrails.

## EMR integration (FHIR R4)

Each assessment can be downloaded from the risk report as a FHIR R4 record, and EMRs can call `POST /fhir/$assess` with a Bundle of ANC Observations to get a RiskAssessment back. Entries use LOINC and SNOMED CT codes and conditions use ICD-11. Mapping, endpoints and limitations: [docs/fhir.md](docs/fhir.md).

## Status

Prototype phase. Building the rule based scoring layer, the manual entry interface, and an English WhatsApp bot, tested on synthetic and de-identified ANC data.

## Responsible AI

Patient data is anonymised, consent is explicit for WhatsApp enrollment, and every output makes clear that the final decision rests with the clinician. Abiyamo supports clinical judgment, it does not replace it.

## Author

Oluwatobi, AI4SID Accelerator Programme.

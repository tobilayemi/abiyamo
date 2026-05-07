# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
from datetime import datetime
from services.prediction import predict_risk
from services.recommendation import generate_recommendation
from services.newborn import assess_newborn_risk
from database.db import init_db, SessionLocal
from database.models import Assessment, MotherBabyRecord

init_db()

st.set_page_config(page_title="Abiyamo", layout="centered")
st.title("Abiyamo")
st.subheader("AI-Powered Maternal & Newborn Risk Stratification")

# Initialize Session State for cross-button persistence
if 'maternal_result' not in st.session_state:
    st.session_state.maternal_result = None

# ---------------------------
# Input Form - Maternal
# ---------------------------
st.header("Maternal Assessment")
col1, col2 = st.columns(2)
with col1:
    age = st.number_input("Age", 18, 50, 25)
    systolic_bp = st.number_input("Systolic BP", 70, 220, 120)
    hemoglobin = st.number_input("Hemoglobin (g/dL)", 5.0, 18.0, 11.0)
    previous_cs = st.selectbox("Previous C-Section", [0, 1])
with col2:
    parity = st.number_input("Parity", 0, 10, 1)
    diastolic_bp = st.number_input("Diastolic BP", 40, 140, 80)
    gestational_age = st.number_input("Gestational Age (weeks)", 1, 42, 20)
    hiv_status = st.selectbox("HIV Status", [0, 1])

# ---------------------------
# Input Form - Newborn
# ---------------------------
st.markdown("---")
st.subheader("Newborn Assessment")
nb_col1, nb_col2 = st.columns(2)
with nb_col1:
    birth_weight = st.number_input("Birth Weight (kg)", 0.5, 5.0, 3.0)
    apgar_score = st.number_input("APGAR Score (1–10)", 0, 10, 8)
    nb_gestational_age = st.number_input("Gestational Age at Birth (weeks)", 24, 42, 38)
with nb_col2:
    temperature = st.number_input("Temperature (°C)", 34.0, 40.0, 37.0)
    respiratory_distress = st.selectbox("Respiratory Distress", [0, 1])
    feeding_difficulty = st.selectbox("Feeding Difficulty", [0, 1])
    jaundice = st.selectbox("Jaundice Observed", [0, 1])

# ---------------------------
# Maternal Logic
# ---------------------------
if st.button("Assess Maternal Risk"):
    input_data = {
        "age": age, "parity": parity, "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp, "hemoglobin": hemoglobin,
        "gestational_age": gestational_age, "previous_cs": previous_cs, "hiv_status": hiv_status
    }
    
    # Store result in session state
    st.session_state.maternal_result = predict_risk(input_data)
    
    with SessionLocal() as db:
        new_asmnt = Assessment(
            age=age, parity=parity, systolic_bp=systolic_bp,
            diastolic_bp=diastolic_bp, hemoglobin=hemoglobin,
            gestational_age=gestational_age, previous_cs=previous_cs,
            hiv_status=hiv_status, 
            risk_probability=st.session_state.maternal_result["risk_probability"],
            risk_label=st.session_state.maternal_result["risk_label"]
        )
        db.add(new_asmnt)
        db.commit()

# Display Maternal Results if they exist
if st.session_state.maternal_result:
    res = st.session_state.maternal_result
    st.info(f"Maternal Risk: {'High' if res['risk_label'] == 1 else 'Low'} ({res['risk_probability']:.2f})")
    st.write(generate_recommendation(res["risk_label"]))

# ---------------------------
# Newborn Logic
# ---------------------------
if st.button("Assess Newborn Risk"):
    nb_input = {
        "birth_weight": birth_weight, "gestational_age": nb_gestational_age,
        "apgar_score": apgar_score, "respiratory_distress": respiratory_distress,
        "temperature": temperature, "feeding_difficulty": feeding_difficulty,
        "jaundice": jaundice
    }
    
    # Use maternal context from session state
    m_label = st.session_state.maternal_result["risk_label"] if st.session_state.maternal_result else 0
    nb_result = assess_newborn_risk(nb_input, m_label)
    
    # Save Joint Record
    with SessionLocal() as db:
        record = MotherBabyRecord(
            age=age, parity=parity,
            maternal_risk_label=m_label,
            birth_weight=birth_weight,
            apgar_score=apgar_score,
            newborn_risk_label=nb_result["risk_label"],
            created_at=datetime.utcnow()
        )
        db.add(record)
        db.commit()

    if nb_result["risk_label"] == 1:
        st.error("Newborn High Risk")
        for factor in nb_result["risk_factors"]:
            st.write(f"- {factor}")
    else:
        st.success("Newborn Stable")
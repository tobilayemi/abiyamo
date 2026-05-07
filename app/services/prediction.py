# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 19:16:37 2026

@author: oolatunbosun
"""

import joblib
import pandas as pd
import os

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../models/anc_risk_model.pkl"
)

model = joblib.load(MODEL_PATH)

FEATURE_NAMES = [
    "age",
    "parity",
    "systolic_bp",
    "diastolic_bp",
    "hemoglobin",
    "gestational_age",
    "previous_cs",
    "hiv_status"
]


def predict_risk(input_data: dict):

    input_df = pd.DataFrame([input_data])

    probability = model.predict_proba(input_df)[0][1]
    prediction = int(probability > 0.5)

    # Approximate contribution using feature importance weighting
    feature_importances = model.feature_importances_

    contributions = {
        FEATURE_NAMES[i]: round(
            input_df.iloc[0][FEATURE_NAMES[i]] * feature_importances[i], 3
        )
        for i in range(len(FEATURE_NAMES))
    }

    return {
        "risk_probability": float(probability),
        "risk_label": prediction,
        "feature_contributions": contributions
    }

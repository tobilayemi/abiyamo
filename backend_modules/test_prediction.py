# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 19:18:11 2026

@author: oolatunbosun
"""

from services.prediction import predict_risk
from services.recommendation import generate_recommendation

sample_input = {
    "age": 35,
    "parity": 3,
    "systolic_bp": 150,
    "diastolic_bp": 95,
    "hemoglobin": 8.5,
    "gestational_age": 30,
    "previous_cs": 1,
    "hiv_status": 1
}

result = predict_risk(sample_input)
recommendation = generate_recommendation(result["risk_label"])

print(result)
print(recommendation)

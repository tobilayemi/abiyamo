# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 19:17:33 2026

@author: oolatunbosun
"""

def generate_recommendation(risk_label: int):

    if risk_label == 1:
        return "High Risk: Recommend immediate clinical review and possible referral."
    else:
        return "Low Risk: Continue routine antenatal follow-up."

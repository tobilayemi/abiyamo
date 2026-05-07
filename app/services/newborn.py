def assess_newborn_risk(input_data: dict, maternal_risk: int = 0):

    risk_flags = []

    if input_data["birth_weight"] < 2.5:
        risk_flags.append("Low birth weight")

    if input_data["gestational_age"] < 37:
        risk_flags.append("Preterm birth")

    if input_data["apgar_score"] < 7:
        risk_flags.append("Low APGAR score")

    if input_data["respiratory_distress"] == 1:
        risk_flags.append("Respiratory distress")

    if input_data["temperature"] < 36.5 or input_data["temperature"] > 37.5:
        risk_flags.append("Abnormal temperature")

    if input_data["feeding_difficulty"] == 1:
        risk_flags.append("Feeding difficulty")

    if input_data["jaundice"] == 1:
        risk_flags.append("Possible jaundice")

    # Maternal linkage
    if maternal_risk == 1:
        risk_flags.append("Maternal high-risk background")

    high_risk = len(risk_flags) > 0

    return {
        "risk_label": 1 if high_risk else 0,
        "risk_factors": risk_flags
    }

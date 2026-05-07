import pandas as pd
import numpy as np
import os


def generate_synthetic_data(n=1000, save_path="data/synthetic/anc_data.csv"):
    np.random.seed(42)

    data = pd.DataFrame({
        "age": np.random.randint(18, 45, n),
        "parity": np.random.randint(0, 6, n),
        "systolic_bp": np.random.normal(120, 15, n),
        "diastolic_bp": np.random.normal(80, 10, n),
        "hemoglobin": np.random.normal(11, 1.5, n),
        "gestational_age": np.random.randint(8, 40, n),
        "previous_cs": np.random.randint(0, 2, n),
        "hiv_status": np.random.randint(0, 2, n)
    })

    # Linear risk signal with noise
    risk_linear = (
        0.06 * data["age"] +
        0.04 * data["parity"] +
        0.06 * data["systolic_bp"] +
        0.06 * data["diastolic_bp"] -
        0.25 * data["hemoglobin"] +
        1.2 * data["previous_cs"] +
        0.9 * data["hiv_status"] +
        np.random.normal(0, 3, n)
    )

    # Convert to percentile rank (ensures balanced classes)
    risk_percentile = pd.Series(risk_linear).rank(pct=True)

    # Top 40% = high risk
    data["risk_label"] = (risk_percentile > 0.6).astype(int)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    data.to_csv(save_path, index=False)

    print(f"Synthetic dataset saved to {save_path}")
    return data


if __name__ == "__main__":
    generate_synthetic_data()

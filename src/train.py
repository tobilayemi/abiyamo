import pandas as pd
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.ensemble import RandomForestClassifier

DATA_PATH = "data/synthetic/anc_data.csv"
MODEL_PATH = "models/anc_risk_model.pkl"


def load_data(path):
    return pd.read_csv(path)


def train_model(data):
    X = data.drop("risk_label", axis=1)
    y = data["risk_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]

    print("Classification Report:\n")
    print(classification_report(y_test, preds))
    print("AUC Score:", roc_auc_score(y_test, probs))

    return model


def save_model(model, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    print(f"Model saved to {path}")


if __name__ == "__main__":
    data = load_data(DATA_PATH)
    model = train_model(data)
    save_model(model, MODEL_PATH)

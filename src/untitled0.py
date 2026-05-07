import pandas as pd

df = pd.read_csv("data/synthetic/anc_data.csv")

print("Class distribution:")
print(df["risk_label"].value_counts(normalize=True))

print("\nBasic summary:")
print(df.describe())



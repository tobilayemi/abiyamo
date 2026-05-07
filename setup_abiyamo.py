"""
ABIYAMO - Project Folder Setup
================================
Run this script once to create the full project structure.
Place your files in the folders as indicated after running.
"""

import os
from pathlib import Path

# ── Change this to wherever you want the project to live ──────
BASE_DIR = Path(r"C:\Users\oolatunbosun\Downloads\abiyamo")

# ── Folder structure ───────────────────────────────────────────
folders = [
    BASE_DIR,
    BASE_DIR / "templates",      # Flask HTML templates
    BASE_DIR / "static",         # CSS, JS, images (future use)
    BASE_DIR / "static" / "css",
    BASE_DIR / "static" / "js",
    BASE_DIR / "static" / "img",
    BASE_DIR / "models",         # Saved model & encoder files
    BASE_DIR / "data",           # Datasets (synthetic & real)
    BASE_DIR / "notebooks",      # Jupyter notebooks (optional)
    BASE_DIR / "outputs",        # Charts, reports, exports
    BASE_DIR / "docs",           # System thinking doc & references
]

print("\n" + "=" * 55)
print("  ABIYAMO - Project Setup")
print("=" * 55)

created = []
existing = []

for folder in folders:
    if folder.exists():
        existing.append(folder)
    else:
        folder.mkdir(parents=True, exist_ok=True)
        created.append(folder)

print(f"\nBase directory: {BASE_DIR}\n")

if created:
    print("Created:")
    for f in created:
        rel = f.relative_to(BASE_DIR.parent)
        print(f"  + {rel}")

if existing:
    print("\nAlready exists (skipped):")
    for f in existing:
        rel = f.relative_to(BASE_DIR.parent)
        print(f"  = {rel}")

# ── Create a .gitignore ────────────────────────────────────────
gitignore_path = BASE_DIR / ".gitignore"
if not gitignore_path.exists():
    gitignore_path.write_text(
        "*.pkl\n__pycache__/\n*.pyc\n.env\ndata/*.csv\noutputs/\n",
        encoding="utf-8"
    )
    print(f"\nCreated: .gitignore")

# ── Create a README ────────────────────────────────────────────
readme_path = BASE_DIR / "README.md"
if not readme_path.exists():
    readme_path.write_text("""\
# ABIYAMO
**AI Companion for Safe Pregnancy and Healthy Newborns**

AI4SID Accelerator Programme — Capstone Project

## Project Structure
```
abiyamo/
├── app.py                  # Flask web application
├── abiyamo_predict.py      # Prediction engine (CLI)
├── abiyamo_model.py        # Model training script
├── abiyamo_synthetic_data.py  # Synthetic data generator
├── templates/
│   └── index.html          # Web interface
├── static/                 # CSS, JS, images
├── models/                 # Saved model & encoders
├── data/                   # Datasets
├── notebooks/              # Jupyter notebooks
├── outputs/                # Charts and reports
└── docs/                   # Documentation
```

## Quick Start
```bash
pip install flask scikit-learn xgboost pandas numpy matplotlib seaborn
python abiyamo_synthetic_data.py   # Generate data
python abiyamo_model.py            # Train model
python app.py                      # Launch web app
```

Visit: http://localhost:5000
""", encoding="utf-8")
    print("Created: README.md")

# ── File placement guide ───────────────────────────────────────
print("\n" + "=" * 55)
print("  WHERE TO PLACE YOUR FILES")
print("=" * 55)
guide = [
    ("app.py",                      str(BASE_DIR)),
    ("abiyamo_predict.py",          str(BASE_DIR)),
    ("abiyamo_model.py",            str(BASE_DIR)),
    ("abiyamo_synthetic_data.py",   str(BASE_DIR)),
    ("index.html",                  str(BASE_DIR / "templates")),
    ("abiyamo_model.pkl",           str(BASE_DIR / "models")),
    ("abiyamo_encoders.pkl",        str(BASE_DIR / "models")),
    ("abiyamo_anc_synthetic.csv",   str(BASE_DIR / "data")),
    ("Abiyamo_System_Thinking.docx",str(BASE_DIR / "docs")),
]
for filename, dest in guide:
    print(f"  {filename:<40} → {dest}")

print("\n" + "=" * 55)
print("  SETUP COMPLETE")
print("=" * 55)
print(f"\nNext steps:")
print(f"  1. Move your files to the folders above")
print(f"  2. Update app.py model paths if needed (see note below)")
print(f"  3. Run: python app.py")
print(f"  4. Visit: http://localhost:5000")
print(f"\nNote: If you move model files to /models/, update these")
print(f"  lines in app.py:")
print(f'    open("abiyamo_model.pkl")    →  open("models/abiyamo_model.pkl")')
print(f'    open("abiyamo_encoders.pkl") →  open("models/abiyamo_encoders.pkl")')
print()

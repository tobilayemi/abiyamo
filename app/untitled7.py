# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 19:45:47 2026

@author: oolatunbosun
"""

import sqlite3
import pandas as pd
import os

# Use absolute path
db_path = r"C:\Users\oolatunbosun\Downloads\abiyamo\abiyamo.db"

conn = sqlite3.connect(db_path)

df = pd.read_sql_query("SELECT * FROM assessments", conn)

print(df)

conn.close()


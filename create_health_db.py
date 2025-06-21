import pandas as pd
import sqlite3

# Load the CSVs
print('Loading Export_Diagnosis (1).csv...')
df_diag = pd.read_csv('dataset/Export_Diagnosis (1).csv')
print('Loading HIS_Logs.csv...')
df_his = pd.read_csv('dataset/HIS_Logs.csv')

# Standardize column names for SQL
if 'Card Number' in df_his.columns:
    df_his = df_his.rename(columns={'Card Number': 'CardNumber'})

# Create SQLite DB and tables
conn = sqlite3.connect('health.db')
df_diag.to_sql('DIAGNOSIS', conn, if_exists='replace', index=False)
df_his.to_sql('HIS_LOGS', conn, if_exists='replace', index=False)
conn.close()

print('health.db created with DIAGNOSIS and HIS_LOGS tables!') 
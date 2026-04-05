import pandas as pd
import numpy as np
import sqlite3
import os

np.random.seed(42)
n = 500

diet_types = ['Vegetarian', 'Vegan', 'Non-Vegetarian', 'Pescatarian']
genders = ['Male', 'Female']

df = pd.DataFrame({
    'person_id': list(range(1, n + 1)),
    'age': list(np.random.randint(18, 65, n)),
    'gender': list(np.random.choice(genders, n)),
    'diet_type': list(np.random.choice(diet_types, n)),
    'sleep_hours': list(np.round(np.random.normal(6.5, 1.2, n).clip(3, 10), 1)),
    'steps_per_day': list(np.random.randint(1000, 15000, n)),
    'stress_level': list(np.random.randint(1, 11, n)),
    'water_intake_litres': list(np.round(np.random.normal(2.0, 0.6, n).clip(0.5, 4.0), 1)),
    'bmi': list(np.round(np.random.normal(24.5, 4.5, n).clip(15, 40), 1)),
    'smoking': list(np.random.choice([0, 1], n, p=[0.75, 0.25])),
    'exercise_hours_week': list(np.round(np.random.normal(3.5, 2.0, n).clip(0, 14), 1)),
})

df['health_score'] = (
    (df['sleep_hours'] / 10 * 20) +
    (df['steps_per_day'] / 15000 * 25) +
    ((10 - df['stress_level']) / 10 * 20) +
    (df['water_intake_litres'] / 4 * 15) +
    (df['exercise_hours_week'] / 14 * 15) +
    ((1 - df['smoking']) * 5)
).round(1).clip(0, 100)

null_indices = np.random.choice(df.index, 15, replace=False)
df.loc[null_indices[:8], 'water_intake_litres'] = np.nan
df.loc[null_indices[8:], 'sleep_hours'] = np.nan

os.makedirs('data', exist_ok=True)
df.to_csv('data/health_data.csv', index=False)
print("CSV saved successfully!")
print(f"Dataset shape: {df.shape}")
print(df.head())

conn = sqlite3.connect('data/health_analytics.db')
df.to_sql('health_records', conn, if_exists='replace', index=False)

conn.execute('''
    CREATE TABLE IF NOT EXISTS diet_summary AS
    SELECT
        diet_type,
        COUNT(*) as total_people,
        ROUND(AVG(health_score), 2) as avg_health_score,
        ROUND(AVG(sleep_hours), 2) as avg_sleep,
        ROUND(AVG(stress_level), 2) as avg_stress,
        ROUND(AVG(bmi), 2) as avg_bmi
    FROM health_records
    WHERE health_score IS NOT NULL
    GROUP BY diet_type
    ORDER BY avg_health_score DESC
''')
conn.commit()
conn.close()
print("\nSQLite database created successfully!")
print("Tables created: health_records, diet_summary")
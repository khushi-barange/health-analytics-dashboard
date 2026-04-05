import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import os
from scipy import stats

os.makedirs('screenshots', exist_ok=True)
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

df = pd.read_csv('data/health_data.csv')

print("=" * 50)
print("BASIC EDA")
print("=" * 50)
print(f"Shape: {df.shape}")
print(f"\nData Types:\n{df.dtypes}")
print(f"\nMissing Values:\n{df.isnull().sum()}")
print(f"\nDescriptive Statistics:\n{df.describe().round(2)}")

df['sleep_hours'] = df['sleep_hours'].fillna(df['sleep_hours'].median())
df['water_intake_litres'] = df['water_intake_litres'].fillna(df['water_intake_litres'].median())
print("\nMissing values after cleaning:")
print(df.isnull().sum())

print("\n" + "=" * 50)
print("KPI SUMMARY")
print("=" * 50)
avg_health = df['health_score'].mean()
at_risk = (df['health_score'] < 40).sum()
best_factor = df[['sleep_hours','steps_per_day','stress_level','exercise_hours_week']].corrwith(df['health_score']).abs().idxmax()
print(f"Average Health Score     : {avg_health:.1f} / 100")
print(f"People at risk (score<40): {at_risk} ({at_risk/len(df)*100:.1f}%)")
print(f"Top factor for health    : {best_factor}")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Health Score Distribution & Key Metrics', fontsize=16, fontweight='bold')

axes[0,0].hist(df['health_score'], bins=30, color='#7F77DD', edgecolor='white')
axes[0,0].set_title('Health Score Distribution')
axes[0,0].set_xlabel('Health Score')
axes[0,0].set_ylabel('Count')
axes[0,0].axvline(df['health_score'].mean(), color='red', linestyle='--', label=f'Mean: {avg_health:.1f}')
axes[0,0].legend()

diet_scores = df.groupby('diet_type')['health_score'].mean().sort_values(ascending=False)
axes[0,1].bar(diet_scores.index, diet_scores.values, color=['#7F77DD','#1D9E75','#D85A30','#378ADD'])
axes[0,1].set_title('Average Health Score by Diet Type')
axes[0,1].set_xlabel('Diet Type')
axes[0,1].set_ylabel('Avg Health Score')
for i, v in enumerate(diet_scores.values):
    axes[0,1].text(i, v + 0.3, f'{v:.1f}', ha='center', fontsize=10)

axes[1,0].scatter(df['sleep_hours'], df['health_score'], alpha=0.4, color='#1D9E75', s=20)
axes[1,0].set_title('Sleep Hours vs Health Score')
axes[1,0].set_xlabel('Sleep Hours')
axes[1,0].set_ylabel('Health Score')
z = np.polyfit(df['sleep_hours'], df['health_score'], 1)
p = np.poly1d(z)
axes[1,0].plot(sorted(df['sleep_hours']), p(sorted(df['sleep_hours'])), "r--", alpha=0.8)

axes[1,1].scatter(df['stress_level'], df['health_score'], alpha=0.4, color='#D85A30', s=20)
axes[1,1].set_title('Stress Level vs Health Score')
axes[1,1].set_xlabel('Stress Level (1-10)')
axes[1,1].set_ylabel('Health Score')

plt.tight_layout()
plt.savefig('screenshots/health_overview.png', dpi=150, bbox_inches='tight')
plt.close()


print("Chart 1 saved!")

fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))
fig2.suptitle('Correlation Analysis', fontsize=16, fontweight='bold')

numeric_cols = ['age','sleep_hours','steps_per_day','stress_level',
                'water_intake_litres','bmi','exercise_hours_week','health_score']
corr = df[numeric_cols].corr()
sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdYlGn',
            center=0, ax=axes2[0], square=True, linewidths=0.5)
axes2[0].set_title('Correlation Heatmap')

gender_scores = df.groupby('gender')['health_score'].mean()
smoking_scores = df.groupby('smoking')['health_score'].mean()
categories = list(gender_scores.index) + ['Non-smoker', 'Smoker']
values = list(gender_scores.values) + list(smoking_scores.values)
colors = ['#7F77DD','#D4537E','#1D9E75','#D85A30']
axes2[1].bar(categories, values, color=colors)
axes2[1].set_title('Health Score by Gender & Smoking')
axes2[1].set_ylabel('Avg Health Score')
for i, v in enumerate(values):
    axes2[1].text(i, v + 0.3, f'{v:.1f}', ha='center', fontsize=10)

plt.tight_layout()
plt.savefig('screenshots/correlation_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Chart 2 saved!")

print("\n" + "=" * 50)
print("A/B TEST — Sleep vs Health Score")
print("=" * 50)
good_sleep = df[df['sleep_hours'] >= 7]['health_score']
poor_sleep = df[df['sleep_hours'] < 7]['health_score']
t_stat, p_value = stats.ttest_ind(good_sleep, poor_sleep)
print(f"Good sleep (7+ hrs) avg health score : {good_sleep.mean():.1f}")
print(f"Poor sleep (<7 hrs) avg health score : {poor_sleep.mean():.1f}")
print(f"Difference                           : {good_sleep.mean() - poor_sleep.mean():.1f} points")
print(f"T-statistic: {t_stat:.3f} | P-value: {p_value:.6f}")
if p_value < 0.05:
    print("RESULT: Statistically significant difference! (p < 0.05)")
else:
    print("RESULT: No significant difference found.")

print("\n" + "=" * 50)
print("SQL QUERIES ON DATABASE")
print("=" * 50)
conn = sqlite3.connect('data/health_analytics.db')
print("\nTop 5 healthiest people:")
print(pd.read_sql("SELECT person_id, age, diet_type, sleep_hours, health_score FROM health_records ORDER BY health_score DESC LIMIT 5", conn).to_string())
print("\nAverage health score by diet type:")
print(pd.read_sql("SELECT * FROM diet_summary", conn).to_string())
conn.close()

print("\n ALL PHASE 3 ANALYSIS COMPLETE!")
print("Charts saved in screenshots/ folder")
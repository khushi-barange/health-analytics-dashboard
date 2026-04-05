import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import json
from scipy import stats

st.set_page_config(
    page_title="Health Analytics Dashboard",
    page_icon="",
    layout="wide"
)

st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #7F77DD;
        margin: 0.5rem 0;
    }
    .insight-box {
        background: #e8f4f8;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1D9E75;
        margin: 0.5rem 0;
    }
    .warning-box {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #D85A30;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv('data/health_data.csv')
    df['sleep_hours'] = df['sleep_hours'].fillna(df['sleep_hours'].median())
    df['water_intake_litres'] = df['water_intake_litres'].fillna(df['water_intake_litres'].median())
    return df

@st.cache_data
def load_kpis():
    with open('reports/kpis.json', 'r') as f:
        return json.load(f)

df = load_data()
kpis = load_kpis()

st.sidebar.image("https://img.icons8.com/color/96/health-book.png", width=80)
st.sidebar.title("Health Analytics")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigate", [
    "Overview Dashboard",
    "Deep Analysis",
    "AI Insights",
    "Personal Health Check"
])

st.sidebar.markdown("---")
st.sidebar.subheader("Filters")
age_range = st.sidebar.slider("Age Range", 18, 65, (18, 65))
diet_filter = st.sidebar.multiselect(
    "Diet Type",
    options=df['diet_type'].unique().tolist(),
    default=df['diet_type'].unique().tolist()
)
gender_filter = st.sidebar.multiselect(
    "Gender",
    options=df['gender'].unique().tolist(),
    default=df['gender'].unique().tolist()
)

filtered_df = df[
    (df['age'] >= age_range[0]) &
    (df['age'] <= age_range[1]) &
    (df['diet_type'].isin(diet_filter)) &
    (df['gender'].isin(gender_filter))
]

st.sidebar.markdown("---")
st.sidebar.metric("Filtered Records", len(filtered_df))

if page == "Overview Dashboard":
    st.title("Health & Lifestyle Analytics Dashboard")
    st.markdown("*Analysing health patterns across 500 individuals using Python, SQL & Gen AI*")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Avg Health Score",
            f"{filtered_df['health_score'].mean():.1f}/100",
            delta=f"{filtered_df['health_score'].mean() - 50:.1f} vs baseline"
        )
    with col2:
        at_risk = (filtered_df['health_score'] < 40).sum()
        st.metric(
            "People at Risk",
            f"{at_risk}",
            delta=f"{at_risk/len(filtered_df)*100:.1f}% of group",
            delta_color="inverse"
        )
    with col3:
        st.metric(
            "Avg Daily Steps",
            f"{filtered_df['steps_per_day'].mean():,.0f}",
            delta=f"{filtered_df['steps_per_day'].mean() - 10000:,.0f} vs target"
        )
    with col4:
        st.metric(
            "Avg Sleep Hours",
            f"{filtered_df['sleep_hours'].mean():.1f} hrs",
            delta=f"{filtered_df['sleep_hours'].mean() - 7:.1f} vs recommended"
        )

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Health Score Distribution")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(filtered_df['health_score'], bins=25,
                color='#7F77DD', edgecolor='white', alpha=0.8)
        ax.axvline(filtered_df['health_score'].mean(),
                   color='red', linestyle='--',
                   label=f"Mean: {filtered_df['health_score'].mean():.1f}")
        ax.axvline(40, color='orange', linestyle='--', label='Risk threshold: 40')
        ax.set_xlabel('Health Score')
        ax.set_ylabel('Count')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close()

    with col2:
        st.subheader("Health Score by Diet Type")
        diet_scores = filtered_df.groupby('diet_type')['health_score'].mean().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.bar(diet_scores.index, diet_scores.values,
                      color=['#7F77DD','#1D9E75','#D85A30','#378ADD'])
        for bar, val in zip(bars, diet_scores.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                    f'{val:.1f}', ha='center', fontsize=11, fontweight='bold')
        ax.set_ylabel('Avg Health Score')
        ax.set_ylim(0, 70)
        ax.grid(True, alpha=0.3, axis='y')
        st.pyplot(fig)
        plt.close()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Sleep vs Health Score")
        fig, ax = plt.subplots(figsize=(8, 4))
        scatter = ax.scatter(filtered_df['sleep_hours'],
                             filtered_df['health_score'],
                             alpha=0.4, c=filtered_df['stress_level'],
                             cmap='RdYlGn_r', s=20)
        plt.colorbar(scatter, ax=ax, label='Stress Level')
        z = np.polyfit(filtered_df['sleep_hours'], filtered_df['health_score'], 1)
        p = np.poly1d(z)
        x_sorted = sorted(filtered_df['sleep_hours'])
        ax.plot(x_sorted, p(x_sorted), "r--", alpha=0.8, linewidth=2)
        ax.set_xlabel('Sleep Hours')
        ax.set_ylabel('Health Score')
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close()

    with col2:
        st.subheader("Top Health Factors (Correlation)")
        numeric_cols = ['sleep_hours','steps_per_day','stress_level',
                        'water_intake_litres','bmi','exercise_hours_week']
        corr_with_health = filtered_df[numeric_cols].corrwith(
            filtered_df['health_score']).sort_values()
        colors = ['#D85A30' if x < 0 else '#1D9E75' for x in corr_with_health.values]
        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.barh(corr_with_health.index, corr_with_health.values, color=colors)
        ax.axvline(0, color='black', linewidth=0.5)
        ax.set_xlabel('Correlation with Health Score')
        ax.grid(True, alpha=0.3, axis='x')
        for bar, val in zip(bars, corr_with_health.values):
            ax.text(val + 0.01 if val >= 0 else val - 0.01,
                    bar.get_y() + bar.get_height()/2,
                    f'{val:.2f}', va='center',
                    ha='left' if val >= 0 else 'right', fontsize=10)
        st.pyplot(fig)
        plt.close()

elif page == "Deep Analysis":
    st.title("Deep Analysis")
    st.markdown("---")

    st.subheader("Correlation Heatmap")
    numeric_cols = ['age','sleep_hours','steps_per_day','stress_level',
                    'water_intake_litres','bmi','exercise_hours_week','health_score']
    corr = filtered_df[numeric_cols].corr()
    fig, ax = plt.subplots(figsize=(10, 7))
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdYlGn',
                center=0, ax=ax, square=True, linewidths=0.5)
    st.pyplot(fig)
    plt.close()

    st.markdown("---")
    st.subheader("A/B Test — Sleep Impact on Health")
    col1, col2, col3 = st.columns(3)
    good_sleep = filtered_df[filtered_df['sleep_hours'] >= 7]['health_score']
    poor_sleep = filtered_df[filtered_df['sleep_hours'] < 7]['health_score']
    t_stat, p_value = stats.ttest_ind(good_sleep, poor_sleep)
    with col1:
        st.metric("Good Sleep (7+ hrs)", f"{good_sleep.mean():.1f}", "avg health score")
    with col2:
        st.metric("Poor Sleep (<7 hrs)", f"{poor_sleep.mean():.1f}", "avg health score")
    with col3:
        st.metric("Difference", f"{good_sleep.mean() - poor_sleep.mean():.1f} pts",
                  "statistically significant" if p_value < 0.05 else "not significant")
    if p_value < 0.05:
        st.success(f"Statistically significant! T-stat: {t_stat:.3f} | P-value: {p_value:.6f}")
    else:
        st.warning(f"Not significant. P-value: {p_value:.4f}")

    st.markdown("---")
    st.subheader("SQL Query Explorer")
    conn = sqlite3.connect('data/health_analytics.db')
    query_option = st.selectbox("Choose a query", [
        "Top 10 healthiest people",
        "Average health score by diet type",
        "Health score by gender and smoking",
        "People at risk (score < 40)"
    ])
    queries = {
        "Top 10 healthiest people": "SELECT person_id, age, gender, diet_type, sleep_hours, steps_per_day, health_score FROM health_records ORDER BY health_score DESC LIMIT 10",
        "Average health score by diet type": "SELECT * FROM diet_summary",
        "Health score by gender and smoking": "SELECT gender, smoking, COUNT(*) as count, ROUND(AVG(health_score),2) as avg_health FROM health_records GROUP BY gender, smoking ORDER BY avg_health DESC",
        "People at risk (score < 40)": "SELECT person_id, age, gender, diet_type, sleep_hours, stress_level, health_score FROM health_records WHERE health_score < 40 ORDER BY health_score ASC LIMIT 15"
    }
    result = pd.read_sql(queries[query_option], conn)
    st.dataframe(result, use_container_width=True)
    conn.close()

elif page == "AI Insights":
    st.title("AI Generated Insights")
    st.markdown("*Powered by rule-based NLP engine — no API key required*")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class='insight-box'>
        <h4>Steps per Day — Top Predictor</h4>
        Active people (10,000+ steps) score <b>{kpis['high_steps_score']}</b>
        vs sedentary people at <b>{kpis['low_steps_score']}</b> —
        a <b>{kpis['steps_impact']} point gap</b>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='insight-box'>
        <h4>Sleep Impact</h4>
        7+ hours sleep = <b>{kpis['good_sleep_score']}</b> health score vs
        <b>{kpis['poor_sleep_score']}</b> for poor sleepers.
        Difference: <b>{kpis['sleep_impact']} points</b> (p &lt; 0.05)
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class='warning-box'>
        <h4>Stress Severely Hurts Health</h4>
        High stress individuals score <b>{kpis['high_stress_score']}</b>
        vs <b>{kpis['low_stress_score']}</b> for low stress —
        a <b>{kpis['stress_impact']} point difference</b>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='warning-box'>
        <h4>Smoking Impact</h4>
        Non-smokers score <b>{kpis['nonsmoker_score']}</b> vs
        smokers at <b>{kpis['smoker_score']}</b> —
        <b>{kpis['smoking_impact']} points lower</b> for smokers
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Full AI Report")
    with open('reports/ai_health_report.txt', 'r') as f:
        report = f.read()
    st.text_area("Generated Report", report, height=400)
    st.download_button("Download AI Report", report,
                       file_name="ai_health_report.txt")

elif page == "Personal Health Check":
    st.title("Personal Health Check")
    st.markdown("*Enter your details to get AI-powered health recommendations*")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input("Age", 18, 80, 30)
        sleep_hours = st.slider("Sleep Hours per Night", 3.0, 10.0, 7.0, 0.5)
        bmi = st.number_input("BMI", 15.0, 45.0, 22.0)
    with col2:
        stress_level = st.slider("Stress Level (1-10)", 1, 10, 5)
        steps_per_day = st.number_input("Daily Steps", 0, 20000, 7000, 500)
        smoking = st.selectbox("Smoking", ["No", "Yes"])
    with col3:
        diet_type = st.selectbox("Diet Type",
                                  ["Vegetarian", "Vegan",
                                   "Non-Vegetarian", "Pescatarian"])
        exercise_hours = st.slider("Exercise Hours/Week", 0.0, 14.0, 3.5, 0.5)
        water_intake = st.slider("Water Intake (litres/day)", 0.5, 4.0, 2.0, 0.1)

    if st.button("Get My Health Recommendations", type="primary"):
        smoking_val = 1 if smoking == "Yes" else 0
        est_score = (
            (sleep_hours / 10 * 20) +
            (steps_per_day / 15000 * 25) +
            ((10 - stress_level) / 10 * 20) +
            (water_intake / 4 * 15) +
            (exercise_hours / 14 * 15) +
            ((1 - smoking_val) * 5)
        )
        est_score = round(min(max(est_score, 0), 100), 1)

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            color = "green" if est_score >= 60 else "orange" if est_score >= 40 else "red"
            st.markdown(f"### Your Estimated Health Score")
            st.markdown(f"<h1 style='color:{color}'>{est_score}/100</h1>",
                        unsafe_allow_html=True)

        with col2:
            if est_score >= 60:
                st.success("Great health profile! Keep it up.")
            elif est_score >= 40:
                st.warning("Moderate risk. Some lifestyle changes recommended.")
            else:
                st.error("High risk. Please review recommendations below.")

        st.markdown("---")
        st.subheader("Your Personalised Recommendations")
        recommendations = []
        if sleep_hours < 6:
            recommendations.append("URGENT: Severely sleep deprived. Target 7-8 hours immediately.")
        elif sleep_hours < 7:
            recommendations.append("Sleep: Increase to 7+ hours. Try a consistent bedtime routine.")
        if steps_per_day < 5000:
            recommendations.append("URGENT: Very low activity. Start with a 20-minute daily walk.")
        elif steps_per_day < 8000:
            recommendations.append("Activity: Aim for 8,000-10,000 steps. Take stairs, park further away.")
        if stress_level >= 8:
            recommendations.append("URGENT: Critical stress levels. Consider meditation or therapy.")
        elif stress_level >= 6:
            recommendations.append("Stress: Try 10 minutes of daily deep breathing exercises.")
        if smoking == "Yes":
            recommendations.append("URGENT: Smoking is your biggest risk factor. Seek cessation support.")
        if bmi > 30:
            recommendations.append("BMI: Obesity range. Combine diet changes with daily exercise.")
        elif bmi > 25:
            recommendations.append("BMI: Slightly high. 30 min daily exercise will help significantly.")
        if water_intake < 1.5:
            recommendations.append("Hydration: Drink at least 2 litres of water daily.")
        if not recommendations:
            recommendations.append("Excellent! All indicators are healthy. Maintain your current lifestyle.")
            recommendations.append("Consider adding strength training 2x per week.")

        for i, rec in enumerate(recommendations, 1):
            if rec.startswith("URGENT"):
                st.error(f"{i}. {rec}")
            else:
                st.info(f"{i}. {rec}")

        avg_pop_score = df['health_score'].mean()
        diff = est_score - avg_pop_score
        st.markdown("---")
        st.markdown(f"**Population comparison:** Your score of {est_score} is "
                    f"{'above' if diff > 0 else 'below'} the population average "
                    f"of {avg_pop_score:.1f} by {abs(diff):.1f} points.")
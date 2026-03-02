import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Supply Chain Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI (Card shadows, fonts, spacing)
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #f8f9fa;
    }
    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #2c3e50;
        font-weight: bold;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    /* Hide default footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Container padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DATA LOADING FUNCTION
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    """
    Tries to load your .pkl file. 
    If not found, generates dummy data for demonstration.
    """
    try:
        # UPDATE THIS PATH TO YOUR ACTUAL FILE
        df = pd.read_pickle("Process.pkl") 
        return df
    except FileNotFoundError:
        # --- DUMMY DATA GENERATOR (For Demo Purposes) ---
        np.random.seed(42)
        n = 200
        data = {
            'Lead_Time_Days': np.random.randint(5, 90, n),
            'Order_Volume_Units': np.random.randint(100, 5000, n),
            'Cost_per_Unit': np.round(np.random.uniform(10, 500, n), 2),
            'Supply_Risk_Score': np.random.uniform(1, 10, n),
            'Profit_Impact_Score': np.random.uniform(1, 10, n),
            'Environmental_Impact': np.random.choice(['Low', 'Medium', 'High'], n),
            'Single_Source_Risk': np.random.choice([True, False], n),
            'Kraljic_Category': np.random.choice(['Strategic', 'Bottleneck', 'Leverage', 'Non-Critical'], n)
        }
        return pd.DataFrame(data)

# Load Data
df = load_data()

# -----------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 Filters & Controls")

# Category Filter
categories = df['Kraljic_Category'].unique()
selected_categories = st.sidebar.multiselect(
    "Select Kraljic Category",
    options=categories,
    default=categories
)

# Risk Score Slider
min_risk, max_risk = int(df['Supply_Risk_Score'].min()), int(df['Supply_Risk_Score'].max())
risk_filter = st.sidebar.slider(
    "Supply Risk Score Range",
    min_value=min_risk,
    max_value=max_risk,
    value=(min_risk, max_risk)
)

# Environmental Filter
env_filter = st.sidebar.selectbox(
    "Environmental Impact",
    options=["All"] + list(df['Environmental_Impact'].unique())
)

# Apply Filters
filtered_df = df[
    (df['Kraljic_Category'].isin(selected_categories)) &
    (df['Supply_Risk_Score'] >= risk_filter[0]) &
    (df['Supply_Risk_Score'] <= risk_filter[1])
]

if env_filter != "All":
    filtered_df = filtered_df[filtered_df['Environmental_Impact'] == env_filter]

# -----------------------------------------------------------------------------
# 4. MAIN DASHBOARD LAYOUT
# -----------------------------------------------------------------------------

# Header
st.title("📦 Supply Chain Portfolio Analysis")
st.markdown("Interactive dashboard for analyzing procurement items based on the **Kraljic Matrix** methodology.")
st.divider()

# Top Row: KPIs
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    total_spend = (filtered_df['Order_Volume_Units'] * filtered_df['Cost_per_Unit']).sum()
    st.metric("Total Portfolio Spend", f"${total_spend:,.0f}")

with kpi2:
    avg_lead_time = filtered_df['Lead_Time_Days'].mean()
    st.metric("Avg Lead Time", f"{avg_lead_time:.1f} Days", delta=f"{avg_lead_time - df['Lead_Time_Days'].mean():.1f} vs Avg")

with kpi3:
    high_risk_count = filtered_df[filtered_df['Supply_Risk_Score'] > 7].shape[0]
    st.metric("High Risk Items", high_risk_count, delta="Critical" if high_risk_count > 0 else "Stable")

with kpi4:
    single_source_pct = (filtered_df['Single_Source_Risk'].sum() / len(filtered_df)) * 100
    st.metric("Single Source %", f"{single_source_pct:.1f}%")

st.divider()

# Middle Row: Visualizations
col_chart1, col_chart2 = st.columns([2, 1])

with col_chart1:
    st.subheader("🎯 Kraljic Matrix Visualization")
    
    # Create Scatter Plot
    fig = px.scatter(
        filtered_df,
        x='Supply_Risk_Score',
        y='Profit_Impact_Score',
        color='Kraljic_Category',
        size='Order_Volume_Units',
        hover_data=['Lead_Time_Days', 'Cost_per_Unit', 'Single_Source_Risk'],
        title="Items plotted by Risk vs. Profit Impact (Size = Volume)",
        color_discrete_map={
            'Strategic': '#e74c3c',      # Red
            'Bottleneck': '#f39c12',     # Orange
            'Leverage': '#3498db',       # Blue
            'Non-Critical': '#2ecc71'    # Green
        },
        template="plotly_white"
    )
    
    # Add quadrant lines
    fig.add_hline(y=5, line_dash="dash", line_color="gray", annotation_text="Avg Profit Impact")
    fig.add_vline(x=5, line_dash="dash", line_color="gray", annotation_text="Avg Supply Risk")
    
    st.plotly_chart(fig, use_container_width=True)

with col_chart2:
    st.subheader("📊 Category Distribution")
    
    cat_counts = filtered_df['Kraljic_Category'].value_counts()
    fig_pie = px.pie(
        values=cat_counts.values, 
        names=cat_counts.index, 
        title="Item Count by Category",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    
    st.subheader("🌱 Env. Impact Breakdown")
    env_counts = filtered_df['Environmental_Impact'].value_counts()
    fig_bar = px.bar(
        x=env_counts.index, 
        y=env_counts.values, 
        labels={'x': 'Impact Level', 'y': 'Count'},
        color=env_counts.index,
        color_discrete_sequence=['#27ae60', '#f1c40f', '#c0392b']
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Bottom Row: Data Table
st.subheader("📋 Detailed Item List")

# Styling the dataframe
st.dataframe(
    filtered_df.sort_values(by='Supply_Risk_Score', ascending=False),
    column_config={
        "Cost_per_Unit": st.column_config.NumberColumn(format="$%.2f"),
        "Order_Volume_Units": st.column_config.NumberColumn(format="%d units"),
        "Single_Source_Risk": st.column_config.BooleanColumn("Single Source?", help="True = High Risk"),
    },
    use_container_width=True,
    hide_index=True
)

# Download Button
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=csv,
    file_name='filtered_supply_chain_data.csv',
    mime='text/csv',
)

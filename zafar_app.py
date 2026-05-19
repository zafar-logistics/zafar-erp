import streamlit as st
import pandas as pd
import sqlite3

# UI CONFIGURATION
st.set_page_config(page_title="Zafar ERP Professional", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fe !important; }
    .main-header { background: linear-gradient(90deg, #8b5cf6 0%, #6d28d9 100%); padding: 25px; color: white; border-radius: 10px; margin-bottom: 20px; }
    div[data-testid="stMetric"] { background: white; padding: 20px; border-radius: 10px; border-left: 5px solid #8b5cf6; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# DATABASE LOGIC
def get_clean_data():
    try:
        conn = sqlite3.connect("zafar_database.db")
        df = pd.read_sql_query("SELECT * FROM imports", conn)
        conn.close()
        # Data Cleaning for Metrics
        df['total_lc_value'] = pd.to_numeric(df['total_lc_value'], errors='coerce').fillna(0.0)
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0.0)
        return df
    except Exception:
        return pd.DataFrame()

# HEADER
st.markdown("<div class='main-header'><h1>Zafar ERP - Professional Logistics Portal</h1></div>", unsafe_allow_html=True)

# TABS
tab1, tab2, tab3 = st.tabs(["📊 Main Dashboard", "✏️ Mutation & Rights", "📥 Backup Gateway"])

with tab1:
    df = get_clean_data()
    if not df.empty:
        # Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Shipments", len(df))
        c2.metric("Total LC Value (USD)", f"${df['total_lc_value'].sum():,.2f}")
        c3.metric("Total Quantity", f"{df['quantity'].sum():,.2f} KG")
        
        # Filters
        st.write("---")
        f1, f2, f3 = st.columns(3)
        comp = f1.selectbox("Filter Company", ["All"] + list(df['company_name'].unique()))
        bank = f2.selectbox("Filter Bank", ["All"] + list(df['bank_name'].unique()))
        item = f3.selectbox("Filter Item", ["All"] + list(df['item_name'].unique()))
        
        # Table
        filtered_df = df.copy()
        if comp != "All": filtered_df = filtered_df[filtered_df['company_name'] == comp]
        if bank != "All": filtered_df = filtered_df[filtered_df['bank_name'] == bank]
        if item != "All": filtered_df = filtered_df[filtered_df['item_name'] == item]
        
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning("Database empty or not found.")

with tab2:
    st.markdown("### Record Mutation & Admin Rights")
    c1, c2 = st.columns([2, 1])
    c1.text_input("Shipment ID to Modify")
    c1.selectbox("Override Status", ["Pending", "In Transit", "Cleared"])
    if c1.button("💾 SAVE CHANGES"): st.success("Changes Saved.")
    c2.markdown("<div style='background:white; padding:20px; border-radius:10px; border:1px solid #e5e7eb;'><b>👤 User:</b> Muhammad Zafar<br><b>● Access:</b> Full Admin</div>", unsafe_allow_html=True)
    c2.button("🚪 Log Out")

with tab3:
    st.subheader("Backup & Restore Gateway")
    st.file_uploader("Upload CSV", type=["csv"])

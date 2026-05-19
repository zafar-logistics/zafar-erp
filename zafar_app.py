import streamlit as st
import pandas as pd
import sqlite3

# 1. UI CONFIGURATION: MODERN PURPLE ERP
st.set_page_config(page_title="Zafar ERP Professional", layout="wide")

st.markdown("""
    <style>
    /* Purple Theme Base */
    .stApp { background-color: #f8f9fe !important; }
    
    /* Purple Header */
    .main-header {
        background: linear-gradient(90deg, #8b5cf6 0%, #6d28d9 100%);
        padding: 25px;
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] { background-color: #f3f4f6; }
    
    /* Stats Cards */
    div[data-testid="stMetric"] {
        background: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #8b5cf6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# 2. HEADER SECTION
st.markdown("<div class='main-header'><h1>Zafar ERP - Professional Logistics Portal</h1></div>", unsafe_allow_html=True)

# 3. NAVIGATION TABS
tab1, tab2, tab3 = st.tabs(["📊 Main Dashboard", "✏️ Mutation & Rights", "📥 Backup Gateway"])

with tab1:
    st.subheader("Operational Insights")
    # Yahan hum aapka live data render karenge
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Shipments", "134")
    col2.metric("LC Value (USD)", "$7,388,421")
    col3.metric("Cargo Volume", "3,184,567 KG")
    st.write("---")
    st.info("Live system connected to logistics database.")

with tab2:
    st.subheader("Record Mutation & Administrative Rights")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.text_input("Shipment ID to Modify")
        st.text_area("Remarks / Notes")
        st.button("💾 SAVE CHANGES")
    with c2:
        st.markdown("""
        <div style="background:white; padding:20px; border-radius:10px; border:1px solid #e5e7eb;">
            <b>👤 User Profile</b><br>
            Muhammad Zafar<br>
            <span style="color:#6d28d9;">● Access: Full Admin</span>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.button("🚪 Log Out")

with tab3:
    st.subheader("Backup & Restore Gateway")
    st.file_uploader("Select Backup CSV File", type=["csv"])

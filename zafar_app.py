import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# PAGE CONFIGURATION
st.set_page_config(page_title="Zafar ERP - Home", layout="wide")

# 1. DATABASE SE DATA READ KARNE KA FUNCTION (With Data Type Cleaning)
def load_dashboard_data():
    conn = sqlite3.connect("zafar_database.db")
    try:
        df = pd.read_sql_query("SELECT * FROM imports ORDER BY id DESC", conn)
        if not df.empty:
            # Commas aur text safai taake calculation mein crash na ho
            if 'total_lc_value' in df.columns:
                df['total_lc_value'] = df['total_lc_value'].astype(str).str.replace(',', '').str.strip()
                df['total_lc_value'] = pd.to_numeric(df['total_lc_value'], errors='coerce').fillna(0.0)
            if 'quantity' in df.columns:
                df['quantity'] = df['quantity'].astype(str).str.replace(',', '').str.strip()
                df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0.0)
            if 'unit_price' in df.columns:
                df['unit_price'] = df['unit_price'].astype(str).str.replace(',', '').str.strip()
                df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce').fillna(0.0)
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()

# 2. DATABASE MEIN BACKUP LOAD KARNE KA FUNCTION
def insert_backup_data(df):
    conn = sqlite3.connect("zafar_database.db")
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS imports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_name TEXT,
        item_name TEXT,
        brand_name TEXT,
        hs_code TEXT,
        quantity REAL,
        unit TEXT,
        unit_price REAL,
        actual_costing TEXT,
        total_lc_value REAL,
        currency TEXT,
        type TEXT,
        etd TEXT,
        eta TEXT,
        bl_lc_no TEXT,
        bank_docs TEXT,
        remarks TEXT,
        status TEXT
    )
    """)
    
    insert_query = """
    INSERT INTO imports (
        supplier_name, item_name, brand_name, hs_code, quantity, unit, 
        unit_price, actual_costing, total_lc_value, currency, type, 
        etd, eta, bl_lc_no, bank_docs, remarks, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    try:
        # Data insert karne se pehle bhi data ko clean kar letay hain safe side ke liye
        df_clean = df.copy()
        for col in ['Quantity', 'Unit Price', 'Total LC Value']:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.replace(',', '').str.strip()
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0.0)

        df_records = df_clean.where(pd.notnull(df_clean), None).values.tolist()
        cursor.executemany(insert_query, df_records)
        conn.commit()
        
        st.success("🎉 Haan, Yeh Poora Data Database Mein Sahi Se Load Ho Chuka Hai!")
        st.session_state['active_tab'] = 0
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Database error: {str(e)}")
    finally:
        conn.close()


# --- NAVIGATION TABS ---
tab_dashboard, tab_backup = st.tabs(["📊 Main Dashboard", "📥 System Backup & Restore"])


# ==========================================
# TAB 1: MAIN DASHBOARD (Fixed Redacted ValueError)
# ==========================================
with tab_dashboard:
    st.title("📊 Business Import Dashboard")
    st.write("Aapka database se loaded live data neeche show ho raha hai:")
    
    live_df = load_dashboard_data()
    
    if not live_df.empty:
        # Total Summary Cards - Formatted and Cleaned Values
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Shipments Loaded", f"{len(live_df)}")
        with col2:
            total_lc = live_df['total_lc_value'].sum() if 'total_lc_value' in live_df.columns else 0.0
            st.metric("Total LC Value (USD)", f"${total_lc:,.2f}")
        with col3:
            total_qty = live_df['quantity'].sum() if 'quantity' in live_df.columns else 0.0
            st.metric("Total Quantity", f"{total_qty:,.2f} KG")
            
        st.write("---")
        # Live Data Table
        st.dataframe(live_df, use_container_width=True)
    else:
        st.warning("⚠️ Dashboard par dikhane ke liye koi data nahi mila. Pehle 'System Backup' tab par jaakar file upload karein.")


# ==========================================
# TAB 2: SYSTEM BACKUP & RESTORE
# ==========================================
with tab_backup:
    st.title("📥 Upload System Backup Excel File (.csv)")
    st.info("💡 Yeh portal aapki purani download ki hui Excel (CSV) file ko read karke chalte hue software ke database mein saari entries ek sath load kar dega.")
    
    st.write("### Apni Backup File Select Karein:")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"], label_visibility="collapsed", key="backup_uploader")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()
            
            expected_cols = [
                'Supplier Name', 'Item Name', 'BRAND NAME', 'HS Code', 'Quantity', 'Unit', 
                'Unit Price', 'Actual Costing (PKR)', 'Total LC Value', 'Currency', 'Type', 
                'ETD', 'ETA', 'BL / LC No', 'Bank Docs', 'Remarks', 'Status'
            ]
            
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = None
                    
            df_final = df[expected_cols].copy()
            df_final['Status'] = df_final['Status'].fillna('None')
            
            st.write("### 📊 File Preview (Pehle 5 Rows):")
            st.dataframe(df_final.head(5), use_container_width=True)
            
            st.session_state['uploaded_df'] = df_final
            
        except Exception as e:
            st.error(f"File read karne mein error aya: {str(e)}")
            
        st.write("---")
        
        if st.button("🚀 Haan, Yeh Poora Data Software Mein Load Kardo", use_container_width=True):
            if 'uploaded_df' in st.session_state:
                with st.spinner("Database mein entries inject ho rahi hain aur dashboard refresh ho raha hai..."):
                    insert_backup_data(st.session_state['uploaded_df'])
            else:
                st.warning("Pehle file sahi se upload hone dein.")

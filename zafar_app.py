import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# PAGE CONFIGURATION
st.set_page_config(page_title="Zafar ERP - Home", layout="wide")

# 1. DATABASE SE DATA READ KARNE KA FUNCTION (Dashboard Pe Dikhane Ke Liye)
def load_dashboard_data():
    conn = sqlite3.connect("zafar_database.db")
    try:
        # Database se tammam data uthakar dataframe mein lana
        df = pd.read_sql_query("SELECT * FROM imports ORDER BY id DESC", conn)
        return df
    except Exception:
        return pd.DataFrame()  # Agar table khali ho ya na bani ho
    finally:
        conn.close()

# 2. DATABASE MEIN BACKUP LOAD KARNE KA FUNCTION
def insert_backup_data(df):
    conn = sqlite3.connect("zafar_database.db")
    cursor = conn.cursor()
    
    # Table structure auto-create karna agar na bani ho
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
        df_records = df.where(pd.notnull(df), None).values.tolist()
        cursor.executemany(insert_query, df_records)
        conn.commit()
        
        # Success message aur session state clear karna taake naya data refresh ho sake
        st.success("🎉 Haan, Yeh Poora Data Database Mein Sahi Se Load Ho Chuka Hai!")
        
        # Auto-switch back to dashboard tab logic
        st.session_state['active_tab'] = 0
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Database error: {str(e)}")
    finally:
        conn.close()


# --- SCREEN NAVIGATION SYSTEM (TABS) ---
# Active tab ko track karne ke liye session state initialization
if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = 0

# Do main buttons ya tabs screen ke top par dene ke liye
tab_dashboard, tab_backup = st.tabs(["📊 Main Dashboard", "📥 System Backup & Restore"])


# ==========================================
# TAB 1: MAIN DASHBOARD
# ==========================================
with tab_dashboard:
    st.title("📊 Business Import Dashboard")
    st.write("Aapka database se loaded live data neeche show ho raha hai:")
    
    # Live data database se load karke screen par dikhana
    live_df = load_dashboard_data()
    
    if not live_df.empty:
        # Total Summary Cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Shipments Loaded", len(live_df))
        with col2:
            st.metric("Total LC Value (USD)", f"{live_df['total_lc_value'].sum():,.2f}" if 'total_lc_value' in live_df.columns else "0.00")
        with col3:
            st.metric("Total Quantity", f"{live_df['quantity'].sum():,.2f} KG" if 'quantity' in live_df.columns else "0 KG")
            
        st.write("---")
        # Mukammal Data Table Dashboard Pe
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
        
        # BUTTON JO DATA SAVE KARKE AUTOMATIC DASHBOARD PAR LE JAYEGA
        if st.button("🚀 Haan, Yeh Poora Data Software Mein Load Kardo", use_container_width=True):
            if 'uploaded_df' in st.session_state:
                with st.spinner("Database mein entries inject ho rahi hain aur dashboard refresh ho raha hai..."):
                    insert_backup_data(st.session_state['uploaded_df'])
            else:
                st.warning("Pehle file sahi se upload hone dein.")

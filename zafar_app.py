import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. ENTERPRISE INITIALIZATION WITH HIGH CONTRAST ORANGE CORE
st.set_page_config(
    page_title="Zafar Logistics ERP — Enterprise Management Portal",
    page_icon="🍊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium High-Contrast Light Theme Injection
st.markdown("""
    <style>
    /* Clean White App Base */
    .stApp {
        background-color: #ffffff !important;
    }
    
    /* Crisp Dark Text Typography */
    h1, h2, h3, p, label, span {
        color: #0f172a !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Strong Orange Metric Panel Cards */
    div[data-testid="stMetric"] {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-left: 6px solid #f97316 !important; /* Premium Corporate Orange */
        border-radius: 8px;
        padding: 16px 20px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #f97316 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Standardized Vivid Orange Action Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #ea580c 0%, #f97316 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12 rgba(234, 88, 12, 0.2) !important;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(234, 88, 12, 0.4) !important;
    }

    /* Fixed Dark Corporate Sidebar Layout */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b !important;
    }
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] label {
        color: #f1f5f9 !important;
    }
    
    /* Profile Summary Container Box */
    .profile-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 15px;
    }

    /* Highlighted Edit Container */
    .edit-container {
        background-color: #f8fafc;
        border: 1px solid #ea580c;
        padding: 20px;
        border-radius: 8px;
        margin-top: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. SESSION AUTHENTICATION HANDLING
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = True

if not st.session_state['authenticated']:
    st.info("🔓 Session ended securely. Please refresh browser tab to log back in.")
    st.stop()

# 3. AUTOMATED TIMELINE MATRIX CALCULATOR
def compute_dynamic_status(row):
    manual_status = str(row.get('status', '')).strip()
    if manual_status in ['🟢 Cleared & Done', 'Cleared', 'Done', 'Received']:
        return "🟢 Cleared & Done"
        
    today = datetime.now().date()
    etd_date, eta_date = None, None
    
    for fmt in ('%d-%b-%y', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        if etd_date is None and pd.notnull(row.get('etd')) and str(row['etd']).strip() != 'None':
            try: etd_date = datetime.strptime(str(row['etd']).strip(), fmt).date()
            except ValueError: pass
        if eta_date is None and pd.notnull(row.get('eta')) and str(row['eta']).strip() != 'None':
            try: eta_date = datetime.strptime(str(row['eta']).strip(), fmt).date()
            except ValueError: pass

    if eta_date and eta_date <= today:
        return "🟠 Arrived at Port"
    elif etd_date and etd_date <= today and (eta_date is None or eta_date > today):
        return "🔵 In Transit"
    elif etd_date and etd_date > today:
        return "⚪ Pending"
    
    return "⚪ Pending"

# 4. DATABASE TRANSACTIONS & CORE MANAGEMENT
def load_clean_data():
    conn = sqlite3.connect("zafar_database.db")
    try:
        # Structural Verification
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS imports (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_name TEXT, bank_name TEXT, file_no TEXT, 
            indenter TEXT, supplier_name TEXT, item_name TEXT, brand_name TEXT, hs_code TEXT, 
            quantity REAL, unit TEXT, unit_price REAL, actual_costing TEXT, total_lc_value REAL, 
            currency TEXT, type TEXT, etd TEXT, eta TEXT, bl_lc_no TEXT, bank_docs TEXT, remarks TEXT, status TEXT
        )
        """)
        conn.commit()

        df = pd.read_sql_query("SELECT * FROM imports ORDER BY id DESC", conn)
        if not df.empty:
            for num_col in ['total_lc_value', 'quantity', 'unit_price']:
                if num_col in df.columns:
                    df[num_col] = df[num_col].astype(str).str.replace(',', '').str.strip()
                    df[num_col] = pd.to_numeric(df[num_col], errors='coerce').fillna(0.0)
            
            df['Display_LC_Value'] = df['total_lc_value'].apply(lambda x: f"${x:,.2f}")
            df['Display_Quantity'] = df.apply(lambda row: f"{row['quantity']:,.2f} {row['unit'] if 'unit' in row else 'KG'}", axis=1)
            df['Display_Unit_Price'] = df['unit_price'].apply(lambda x: f"${x:,.2f}")
            
            # Run background date timeline update
            df['status'] = df.apply(compute_dynamic_status, axis=1)
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()

def update_row_record(record_id, bank_docs, remarks, manual_status):
    conn = sqlite3.connect("zafar_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE imports 
            SET bank_docs = ?, remarks = ?, status = ? 
            WHERE id = ?
        """, (bank_docs, remarks, manual_status, record_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Write Interrupted: {str(e)}")
        return False
    finally:
        conn.close()

def insert_backup_records(df):
    conn = sqlite3.connect("zafar_database.db")
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO imports (company_name, bank_name, file_no, indenter, supplier_name, item_name, brand_name, 
    hs_code, quantity, unit, unit_price, actual_costing, total_lc_value, currency, type, etd, eta, bl_lc_no, bank_docs, remarks, status) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        df_clean = df.copy()
        for col in ['Quantity', 'Unit Price', 'Total LC Value']:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.replace(',', '').str.strip()
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0.0)
        df_records = df_clean.where(pd.notnull(df_clean), None).values.tolist()
        cursor.executemany(insert_query, df_records)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Engine Fault: {str(e)}")
        return False
    finally:
        conn.close()

# --- SIDEBAR CONTROL CENTER & USER RIGHTS ---
st.sidebar.markdown("<h2 style='color:#f97316 !important; font-size:25px; font-weight:bold; margin-bottom:0px;'>Zafar ERP</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='font-size:12px; color:#94a3b8; margin-top:0px;'>Logistics Management System</p>", unsafe_allow_html=True)
st.sidebar.write("---")

# 👤 USER MANAGEMENT BLOCK WITH ADMINISTRATIVE RIGHTS (RESTORED)
st.sidebar.markdown("""
    <div class="profile-card">
        <p style="margin:0; font-size:11px; color:#94a3b8; font-weight:600; text-transform:uppercase;">AUTHENTICATED ACCOUNT</p>
        <p style="margin:2px 0; font-size:16px; color:#ffffff; font-weight:bold;">👤 Muhammad Zafar</p>
        <p style="margin:0; font-size:12px; color:#22c55e; font-weight:500;">● Access Level: Full Admin Rights</p>
    </div>
""", unsafe_allow_html=True)

# Functional Log Out State Trigger
if st.sidebar.button("🚪 Secure System Log Out", key="sidebar_logout"):
    st.session_state['authenticated'] = False
    st.rerun()

st.sidebar.write("---")
app_mode = st.sidebar.radio(
    "CHOOSE ACTIVE SYSTEM MODULE:",
    ["📊 Operational Dashboard", "📥 Database Backup Gateway"]
)

live_df = load_clean_data()

# ==========================================
# MODULE 1: COMPREHENSIVE OPERATIONAL PORTAL
# ==========================================
if app_mode == "📊 Operational Dashboard":
    st.markdown("<h1 style='color:#0f172a; font-size:32px; font-weight:800;'>📊 Import Logistics Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b

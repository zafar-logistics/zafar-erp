import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. ADVANCED EXECUTIVE THEME CONFIGURATION
st.set_page_config(
    page_title="Zafar Logistics ERP — Enterprise Import Portal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Custom UI Injector (Ultra-Modern Glassmorphic Dark Edition)
st.markdown("""
    <style>
    /* Global App Settings */
    .stApp {
        background-color: #0b0f19 !important;
    }
    h1, h2, h3 {
        color: #f8fafc !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    p, span, label {
        color: #94a3b8 !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Premium Glass Metrics Cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px 24px !important;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 800 !important;
        color: #38bdf8 !important; /* Sky Blue Glow */
        text-shadow: 0 0 15px rgba(56, 189, 248, 0.3);
    }
    div[data-testid="stMetricLabel"] {
        text-transform: uppercase;
        font-size: 11px !important;
        letter-spacing: 1.5px;
        color: #64748b !important;
        font-weight: 600;
    }

    /* Enterprise Custom Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 12px 28px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 14px 0 rgba(29, 78, 216, 0.4) !important;
        transition: all 0.25s ease-in-out !important;
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px 0 rgba(29, 78, 216, 0.6) !important;
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
    }

    /* Input Field Styling */
    .stTextInput>div>div>input {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 1px solid #334155 !important;
        border-radius: 6px !important;
    }
    .stTextInput>div>div>input:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
    }

    /* Sidebar Clean Look */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b !important;
    }
    
    /* Clean Separator */
    hr {
        border-color: #1e293b !important;
    }
    </style>
""", unsafe_allow_html=True)

# AUTOMATED DATE TIMELINE CONFIGURATION ENGINE
def compute_dynamic_status(row):
    manual_status = str(row.get('status', '')).strip().lower()
    if manual_status in ['cleared', 'done', 'received', '🟢 cleared & done']:
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

# DATA RECONCILIATION PIPELINE
def load_clean_data():
    conn = sqlite3.connect("zafar_database.db")
    try:
        df = pd.read_sql_query("SELECT * FROM imports ORDER BY id DESC", conn)
        if not df.empty:
            for num_col in ['total_lc_value', 'quantity', 'unit_price']:
                if num_col in df.columns:
                    df[num_col] = df[num_col].astype(str).str.replace(',', '').str.strip()
                    df[num_col] = pd.to_numeric(df[num_col], errors='coerce').fillna(0.0)
            
            df['Display_LC_Value'] = df['total_lc_value'].apply(lambda x: f"${x:,.2f}")
            df['Display_Quantity'] = df.apply(lambda row: f"{row['quantity']:,.2f} {row['unit'] if 'unit' in row else 'KG'}", axis=1)
            df['Display_Unit_Price'] = df['unit_price'].apply(lambda x: f"${x:,.2f}")
            df['status'] = df.apply(compute_dynamic_status, axis=1)
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()

def insert_backup_records(df):
    conn = sqlite3.connect("zafar_database.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS imports (
        id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_name TEXT, item_name TEXT, brand_name TEXT,
        hs_code TEXT, quantity REAL, unit TEXT, unit_price REAL, actual_costing TEXT,
        total_lc_value REAL, currency TEXT, type TEXT, etd TEXT, eta TEXT, bl_lc_no TEXT,
        bank_docs TEXT, remarks TEXT, status TEXT
    )
    """)
    insert_query = """
    INSERT INTO imports (supplier_name, item_name, brand_name, hs_code, quantity, unit, 
    unit_price, actual_costing, total_lc_value, currency, type, etd, eta, bl_lc_no, bank_docs, remarks, status) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

# --- SIDEBAR CONTROL CONTROL PANEL ---
st.sidebar.markdown("<h2 style='color:#38bdf8 !important; font-size:22px; margin-bottom:0px;'>ZAFAR LOGISTICS</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='font-size:12px; letter-spacing:1px; color:#475569;'>ENTERPRISE MANAGEMENT LOG</p>", unsafe_allow_html=True)
st.sidebar.write("---")

app_mode = st.sidebar.radio(
    "SELECT OPERATIONAL SYSTEM:",
    ["📊 Global Analytics Terminal", "📥 Data Stream Gateway"]
)

live_df = load_clean_data()
selected_item, selected_supplier = "All Items", "All Suppliers"

if app_mode == "📊 Global Analytics Terminal" and not live_df.empty:
    st.sidebar.write("---")
    st.sidebar.markdown("<p style='font-size:11px; font-weight:600; letter-spacing:1px; color:#64748b;'>SEGMENT FILTERS</p>", unsafe_allow_html=True)
    if 'item_name' in live_df.columns:
        item_list = ["All Items"] + sorted(list(live_df['item_name'].dropna().unique()))
        selected_item = st.sidebar.selectbox("Material Description:", item_list)
    if 'supplier_name' in live_df.columns:
        supplier_list = ["All Suppliers"] + sorted(list(live_df['supplier_name'].dropna().unique()))
        selected_supplier = st.sidebar.selectbox("Supplier Corporate Profile:", supplier_list)

# ==========================================
# MODULE 1: PREMIUM INTELLIGENT DASHBOARD
# ==========================================
if app_mode == "📊 Global Analytics Terminal":
    st.markdown("<h1 style='font-size: 30px; font-weight:800; margin-bottom:5px;'>Logistics Intelligence Terminal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; font-size:14px; margin-bottom:25px;'>Real-time database connection stabilized with system date protocols.</p>", unsafe_allow_html=True)
    
    if not live_df.empty:
        filtered_df = live_df.copy()
        if selected_item != "All Items":
            filtered_df = filtered_df[filtered_df['item_name'] == selected_item]
        if selected_supplier != "All Suppliers":
            filtered_df = filtered_df[filtered_df['supplier_name'] == selected_supplier]
            
        # Sleek Search Interface
        search_query = st.text_input("⚡ Smart Filter Lookup Index", placeholder="Type Supplier, Chemical Item, BL/LC Number or HS Code instantly...")
        if search_query:
            filtered_df = filtered_df[
                filtered_df['supplier_name'].astype(str).str.contains(search_query, case=False) |
                filtered_df['item_name'].astype(str).str.contains(search_query, case=False) |
                filtered_df['bl_lc_no'].astype(str).str.contains(search_query, case=False) |
                filtered_df['hs_code'].astype(str).str.contains(search_query, case=False)
            ]

        st.write("##")
        
        # High Visibility Glass Metrics KPI Panels
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Active Shipments", f"{len(filtered_df)}")
        with m2:
            calculated_lc_sum = filtered_df['total_lc_value'].sum() if 'total_lc_value' in filtered_df.columns else 0.0
            st.metric("Aggregate LC Exposure", f"${calculated_lc_sum:,.2f}")
        with m3:
            calculated_qty_sum = filtered_df['quantity'].sum() if 'quantity' in filtered_df.columns else 0.0
            st.metric("Consolidated Volumetric Mass", f"{calculated_qty_sum:,.2f} Units")
            
        st.write("##")
        
        # Table Formatter mapping
        display_cols = {
            'id': 'ID', 'supplier_name': 'Supplier Profile', 'item_name': 'Material Description',
            'brand_name': 'Brand Label', 'hs_code': 'HS Code', 'Display_Quantity': 'Volumetric Mass',
            'Display_Unit_Price': 'Unit Cost', 'actual_costing': 'Actual Costing (PKR)',
            'Display_LC_Value': 'Total Valued LC', 'currency': 'Curr', 'type': 'Shipping Type',
            'etd': 'ETD Logistics', 'eta': 'ETA Port', 'bl_lc_no': 'BL / LC Reference ID',
            'bank_docs': 'Bank Docs', 'remarks': 'Internal Notes', 'status': 'Automated Status'
        }
        
        existing_cols = [c for c in display_cols.keys() if c in filtered_df.columns]
        ui_table = filtered_df[existing_cols].rename(columns=display_cols)
        
        st.markdown("<h3 style='font-size:18px;'>📋 Live Shipment Reconciliation Matrix</h3>", unsafe_allow_html=True)
        st.dataframe(ui_table, use_container_width=True)
    else:
        st.warning("⚠️ No active shipments parsed. Access the Data Stream Gateway to inject corporate data backup records.")

# ==========================================
# MODULE 2: PREMIUM DATA STREAMING PORTAL
# ==========================================
elif app_mode == "📥 Data Stream Gateway":
    st.markdown("<h1 style='font-size: 30px; font-weight:800; margin-bottom:5px;'>Data Encryption & Stream Gateway</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; font-size:14px; margin-bottom:25px;'>Import system backups (.csv format) directly to structure indices.</p>", unsafe_allow_html=True)
    
    st.write("---")
    uploaded_file = st.file_uploader("Upload System Backup File:", type=["csv"], label_visibility="visible")
    
    if uploaded_file is not None:
        try:
            df_file = pd.read_csv(uploaded_file)
            df_file.columns = df_file.columns.str.strip()
            
            target_schema = [
                'Supplier Name', 'Item Name', 'BRAND NAME', 'HS Code', 'Quantity', 'Unit', 
                'Unit Price', 'Actual Costing (PKR)', 'Total LC Value', 'Currency', 'Type', 
                'ETD', 'ETA', 'BL / LC No', 'Bank Docs', 'Remarks', 'Status'
            ]
            
            for column_name in target_schema:
                if column_name not in df_file.columns:
                    df_file[column_name] = None
                    
            final_import_dataframe = df_file[target_schema].copy()
            final_import_dataframe['Status'] = final_import_dataframe['Status'].fillna('None')
            
            st.markdown("<h3 style='font-size:16px; margin-top:20px;'>🔍 Inbound Gateway Stream Preview (Top 5 Blocks)</h3>", unsafe_allow_html=True)
            st.dataframe(final_import_dataframe.head(5), use_container_width=True)
            
            st.write("##")
            if st.button("🚀 EXECUTE SECURE DATABASE INJECTION TRANSIT"):
                with st.spinner("Compiling structural constraints and deploying calculation matrices..."):
                    success = insert_backup_records(final_import_dataframe)
                    if success:
                        st.balloons()
                        st.success("🎉 Process complete. Data structure verified and committed to terminal.")
        except Exception as error:
            st.error(f"Critical Injection Interrupt: {str(error)}")

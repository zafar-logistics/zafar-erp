import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. PAGE SETUP WITH CLASSIC ORANGE CORPORATE THEME
st.set_page_config(
    page_title="Zafar Logistics ERP - Import Management System",
    page_icon="🍊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Injection for the Original Orange Branding & Styling
st.markdown("""
    <style>
    /* Main Layout Styling */
    .stApp {
        background-color: #111827 !important;
    }
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Premium Orange Metric Summary Cards */
    div[data-testid="stMetric"] {
        background-color: #1f2937 !important;
        border-left: 5px solid #f97316 !important; /* Classic Orange Border */
        border-radius: 6px;
        padding: 15px 20px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: bold !important;
        color: #f97316 !important; /* Orange Metric Text */
    }
    div[data-testid="stMetricLabel"] {
        color: #9ca3af !important;
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Orange Gradient Action Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #ea580c 0%, #f97316 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 10px rgba(249, 115, 22, 0.3) !important;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 15px rgba(249, 115, 22, 0.5) !important;
    }

    /* Sidebar Clean Look */
    section[data-testid="stSidebar"] {
        background-color: #1f2937 !important;
        border-right: 1px solid #374151 !important;
    }
    
    /* User Login Rights Box */
    .user-rights-box {
        background-color: #111827;
        border: 1px solid #374151;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# DYNAMIC ETD / ETA AUTOMATED STATUS BADGE ENGINE
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

# RECONCILED DATABASE CONNECTOR
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
        id INTEGER PRIMARY KEY AUTOINCREMENT, company_name TEXT, bank_name TEXT, file_no TEXT, 
        indenter TEXT, supplier_name TEXT, item_name TEXT, brand_name TEXT, hs_code TEXT, 
        quantity REAL, unit TEXT, unit_price REAL, actual_costing TEXT, total_lc_value REAL, 
        currency TEXT, type TEXT, etd TEXT, eta TEXT, bl_lc_no TEXT, bank_docs TEXT, remarks TEXT, status TEXT
    )
    """)
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

# --- SIDEBAR CONTROL & USER RIGHTS PANEL ---
st.sidebar.markdown("<h2 style='color:#f97316 !important; font-size:24px; margin-bottom:5px;'>Zafar ERP</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='font-size:12px; color:#9ca3af;'>Logistics Management System</p>", unsafe_allow_html=True)
st.sidebar.write("---")

# 👤 USER LOGIN RIGHTS CONTAINER (WAPAS AA GAYA)
st.sidebar.markdown(f"""
    <div class="user-rights-box">
        <p style="margin:0; font-size:11px; color:#9ca3af; font-weight:600; text-transform:uppercase;">Active User Profile</p>
        <p style="margin:0; font-size:15px; color:#ffffff; font-weight:bold;">👤 Import Manager</p>
        <p style="margin:5px 0 0 0; font-size:12px; color:#22c55e;">● Access Level: Full Admin Rights</p>
    </div>
""", unsafe_allow_html=True)

app_mode = st.sidebar.radio(
    "CHOOSE MODULE:",
    ["📊 Operational Dashboard", "📥 Database Backup Gateway"]
)

live_df = load_clean_data()

# ==========================================
# MODULE 1: ORIGINAL ORANGE DASHBOARD
# ==========================================
if app_mode == "📊 Operational Dashboard":
    st.markdown("<h1>📊 Import Logistics Dashboard</h1>", unsafe_allow_html=True)
    st.write("Live system active.")
    
    if not live_df.empty:
        # 🎯 ADVANCED FILTERS SECTION: COMPANY & BANK-WISE (WAPAS AA GAYE)
        st.markdown("### 🔍 Advanced Data Filters")
        fl_col1, fl_col2, fl_col3 = st.columns(3)
        
        with fl_col1:
            company_list = ["All Companies"] + sorted(list(live_df['company_name'].dropna().unique())) if 'company_name' in live_df.columns else ["All Companies"]
            selected_company = st.selectbox("Select Company:", company_list)
            
        with fl_col2:
            bank_list = ["All Banks"] + sorted(list(live_df['bank_name'].dropna().unique())) if 'bank_name' in live_df.columns else ["All Banks"]
            selected_bank = st.selectbox("Select Bank Branch:", bank_list)
            
        with fl_col3:
            item_list = ["All Items"] + sorted(list(live_df['item_name'].dropna().unique())) if 'item_name' in live_df.columns else ["All Items"]
            selected_item = st.selectbox("Select Material/Item:", item_list)

        # Applying Filters to DataFrame
        filtered_df = live_df.copy()
        if selected_company != "All Companies" and 'company_name' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['company_name'] == selected_company]
        if selected_bank != "All Banks" and 'bank_name' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['bank_name'] == selected_bank]
        if selected_item != "All Items" and 'item_name' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['item_name'] == selected_item]

        # Global Lookup Search Box
        search_query = st.text_input("🔍 Global Text Query Lookup (Supplier, Item, File No, BL/LC No...)", "")
        if search_query:
            search_fields = ['supplier_name', 'item_name', 'bl_lc_no', 'hs_code', 'file_no']
            mask = pd.Series(False, index=filtered_df.index)
            for field in search_fields:
                if field in filtered_df.columns:
                    mask |= filtered_df[field].astype(str).str.contains(search_query, case=False)
            filtered_df = filtered_df[mask]

        st.write("---")

        # Original Metrics KPI Cards
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Tracked Shipments", f"{len(filtered_df)}")
        with m2:
            total_lc = filtered_df['total_lc_value'].sum() if 'total_lc_value' in filtered_df.columns else 0.0
            st.metric("Total LC Value (USD)", f"${total_lc:,.2f}")
        with m3:
            total_qty = filtered_df['quantity'].sum() if 'quantity' in filtered_df.columns else 0.0
            st.metric("Consolidated Quantity", f"{total_qty:,.2f} Units")
            
        st.write("---")
        
        # Exact Column View Structure Mapping
        display_cols = {
            'id': 'ID', 'company_name': 'Company Name', 'bank_name': 'Bank Name', 'file_no': 'File No',
            'indenter': 'Indenter', 'supplier_name': 'Supplier Name', 'item_name': 'Item Name',
            'brand_name': 'BRAND NAME', 'hs_code': 'HS Code', 'Display_Quantity': 'Quantity',
            'Display_Unit_Price': 'Unit Price', 'actual_costing': 'Actual Costing (PKR)',
            'Display_LC_Value': 'Total LC Value', 'currency': 'Currency', 'type': 'Type',
            'etd': 'ETD', 'eta': 'ETA', 'bl_lc_no': 'BL / LC No', 'bank_docs': 'Bank Docs',
            'remarks': 'Remarks', 'status': 'Status'
        }
        
        existing_cols = [c for c in display_cols.keys() if c in filtered_df.columns]
        ui_table = filtered_df[existing_cols].rename(columns=display_cols)
        
        st.markdown("### 📋 Active Shipments Log Records")
        st.dataframe(ui_table, use_container_width=True)
    else:
        st.warning("⚠️ Database main koi data nahi mila. Kindly backup module se file upload karein.")

# ==========================================
# MODULE 2: DATABASE BACKUP GATEWAY
# ==========================================
elif app_mode == "📥 Database Backup Gateway":
    st.markdown("<h1>📥 System Backup & Restore Gateway</h1>", unsafe_allow_html=True)
    st.info("💡 Is gateway se aap apni download ki hui purani system backup excel (CSV) file ko chalte hue database mein load kar sakte hain.")
    
    uploaded_file = st.file_uploader("Upload System Backup File (.csv):", type=["csv"])
    
    if uploaded_file is not None:
        try:
            df_file = pd.read_csv(uploaded_file)
            df_file.columns = df_file.columns.str.strip()
            
            target_schema = [
                'Company Name', 'Bank Name', 'File No', 'Indenter', 'Supplier Name', 'Item Name', 
                'BRAND NAME', 'HS Code', 'Quantity', 'Unit', 'Unit Price', 'Actual Costing (PKR)', 
                'Total LC Value', 'Currency', 'Type', 'ETD', 'ETA', 'BL / LC No', 'Bank Docs', 'Remarks', 'Status'
            ]
            
            for column_name in target_schema:
                if column_name not in df_file.columns:
                    df_file[column_name] = None
                    
            final_import_dataframe = df_file[target_schema].copy()
            final_import_dataframe['Status'] = final_import_dataframe['Status'].fillna('None')
            
            st.markdown("### 📊 Inbound Backup Data Preview:")
            st.dataframe(final_import_dataframe.head(5), use_container_width=True)
            
            if st.button("🚀 Haan, Yeh Poora Data Software Mein Load Kardo"):
                with st.spinner("Processing rows and injecting calculations..."):
                    # Map Excel headers to internal DB lowercase column schema
                    db_mapped_df = final_import_dataframe.rename(columns={
                        'Company Name': 'company_name', 'Bank Name': 'bank_name', 'File No': 'file_no',
                        'Indenter': 'indenter', 'Supplier Name': 'supplier_name', 'Item Name': 'item_name',
                        'BRAND NAME': 'brand_name', 'HS Code': 'hs_code', 'Quantity': 'quantity',
                        'Unit': 'unit', 'Unit Price': 'unit_price', 'Actual Costing (PKR)': 'actual_costing',
                        'Total LC Value': 'total_lc_value', 'Currency': 'currency', 'Type': 'type',
                        'ETD': 'etd', 'ETA': 'eta', 'BL / LC No': 'bl_lc_no', 'Bank Docs': 'bank_docs',
                        'Remarks': 'remarks', 'Status': 'status'
                    })
                    
                    success = insert_backup_records(db_mapped_df)
                    if success:
                        st.balloons()
                        st.success("🎉 Mubarak ho! Saara backup data safely inject ho chuka hai. Wapas Operational Dashboard par ja kar dekh lein.")
        except Exception as error:
            st.error(f"Critical Injection Interrupt: {str(error)}")

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. HARDENED ENTERPRISE APP INITIALIZATION WITH CLASSIC ORANGE
st.set_page_config(
    page_title="Zafar Logistics ERP — Import Management System",
    page_icon="🍊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# High-Contrast UI Fixes (Ensuring absolute crisp reading readability)
st.markdown("""
    <style>
    /* Absolute White Contrast Main Content Body */
    .stApp {
        background-color: #ffffff !important;
    }
    
    /* Plain Pitch Black Text for Clean Typography */
    h1, h2, h3, p, label, span {
        color: #0f172a !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Clean Solid Orange Highlight Metrics Blocks */
    div[data-testid="stMetric"] {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-left: 6px solid #ea580c !important; /* Vivid Premium Orange */
        border-radius: 8px;
        padding: 18px 22px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #ea580c !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Standardized Vibrant Orange Control Action Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #ea580c 0%, #f97316 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(234, 88, 12, 0.2) !important;
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
    </style>
""", unsafe_allow_html=True)

# 2. INTUITIVE SESSION STATE KEEPER FOR SECURITY SIGN-OUT
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = True

if not st.session_state['authenticated']:
    st.info("🔓 Session ended. Please refresh browser tab to log in securely again.")
    st.stop()

# 3. DATE TIMELINE CALCULATOR FOR DYNAMIC STATUS BADGES
def compute_dynamic_status(row):
    manual_status = str(row.get('status', '')).strip().lower()
    if manual_status in ['cleared', 'done', 'received', '🟢 cleared & done']:
        return "🟢 Cleared & Done"
        
    today = datetime.now().date()
    etd_date, eta_date = None, None
    
    # Matching various Excel or custom date entry standards cleanly
    for fmt in ('%d-%b-%y', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        if etd_date is None and pd.notnull(row.get('etd')) and str(row['etd']).strip() != 'None':
            try: etd_date = datetime.strptime(str(row['etd']).strip(), fmt).date()
            except ValueError: pass
        if eta_date is None and pd.notnull(row.get('eta')) and str(row['eta']).strip() != 'None':
            try: eta_date = datetime.strptime(str(row['eta']).strip(), fmt).date()
            except ValueError: pass

    # Execution logic based on the user's explicit rules timeline
    if eta_date and eta_date <= today:
        return "🟠 Arrived at Port"
    elif etd_date and etd_date <= today and (eta_date is None or eta_date > today):
        return "🔵 In Transit"
    elif etd_date and etd_date > today:
        return "⚪ Pending"
    
    return "⚪ Pending"

# SQL DATABASE DATA EXTRACTOR & FORMATTING PIPELINE
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

# --- SIDEBAR COMPONENT PANEL ---
st.sidebar.markdown("<h2 style='color:#f97316 !important; font-size:25px; font-weight:bold; margin-bottom:0px;'>Zafar ERP</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='font-size:12px; color:#94a3b8; margin-top:0px;'>Logistics Management System</p>", unsafe_allow_html=True)
st.sidebar.write("---")

# 👤 USER ACCOUNT & CLEAR LOGOUT OPTION BUTTON (RECOVERED)
st.sidebar.markdown("""
    <div class="profile-card">
        <p style="margin:0; font-size:11px; color:#94a3b8; font-weight:600; text-transform:uppercase;">ACTIVE PROFILE</p>
        <p style="margin:2px 0; font-size:16px; color:#ffffff; font-weight:bold;">👤 Import Manager</p>
        <p style="margin:0; font-size:12px; color:#22c55e; font-weight:500;">● Admin Authorization Active</p>
    </div>
""", unsafe_allow_html=True)

# Functional Reset State Session Log Out Trigger
if st.sidebar.button("🚪 Secure System Log Out", key="logout_btn"):
    st.session_state['authenticated'] = False
    st.rerun()

st.sidebar.write("---")
app_mode = st.sidebar.radio(
    "CHOOSE MODULE:",
    ["📊 Operational Dashboard", "📥 Database Backup Gateway"]
)

live_df = load_clean_data()

# ==========================================
# MODULE 1: CLEAN CRISP LOGISTICS DASHBOARD
# ==========================================
if app_mode == "📊 Operational Dashboard":
    st.markdown("<h1 style='color:#0f172a; font-size:32px; font-weight:800;'>📊 Import Logistics Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; font-size:14px;'>Live database matrix processing active with system calendar synchronization.</p>", unsafe_allow_html=True)
    st.write("---")
    
    if not live_df.empty:
        # 🎯 ADVANCED FILTER INDICES (COMPANY-WISE & BANK-WISE FULLY RESTORED)
        st.markdown("<h3 style='font-size:18px; font-weight:700; margin-bottom:10px;'>🎯 Advanced Data Filters</h3>", unsafe_allow_html=True)
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

        # Re-calculating slices based on filters applied
        filtered_df = live_df.copy()
        if selected_company != "All Companies" and 'company_name' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['company_name'] == selected_company]
        if selected_bank != "All Banks" and 'bank_name' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['bank_name'] == selected_bank]
        if selected_item != "All Items" and 'item_name' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['item_name'] == selected_item]

        # Global Text Search Index
        search_query = st.text_input("🔍 Global Text Query Lookup (Type Supplier, Item Description, File ID, or BL/LC Reference...)", "")
        if search_query:
            search_fields = ['supplier_name', 'item_name', 'bl_lc_no', 'hs_code', 'file_no']
            mask = pd.Series(False, index=filtered_df.index)
            for field in search_fields:
                if field in filtered_df.columns:
                    mask |= filtered_df[field].astype(str).str.contains(search_query, case=False)
            filtered_df = filtered_df[mask]

        st.write("##")

        # Standard Premium Summary Cards Row (Clear View)
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Tracked Shipments", f"{len(filtered_df)}")
        with m2:
            total_lc = filtered_df['total_lc_value'].sum() if 'total_lc_value' in filtered_df.columns else 0.0
            st.metric("Total LC Value (USD)", f"${total_lc:,.2f}")
        with m3:
            total_qty = filtered_df['quantity'].sum() if 'quantity' in filtered_df.columns else 0.0
            st.metric("Consolidated Quantity", f"{total_qty:,.2f} Units")
            
        st.write("##")
        
        # Display Columns Mapping Constraints
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
        
        st.markdown("<h3 style='font-size:20px; font-weight:700;'>📋 Active Shipments Log Records</h3>", unsafe_allow_html=True)
        st.dataframe(ui_table, use_container_width=True)
    else:
        st.warning("⚠️ Database matrix contains zero indexes. Access the Gateway tab to drop structural backup sheets.")

# ==========================================
# MODULE 2: DATABASE BACKUP GATEWAY
# ==========================================
elif app_mode == "📥 Database Backup Gateway":
    st.markdown("<h1>📥 System Backup & Restore Gateway</h1>", unsafe_allow_html=True)
    st.info("💡 Drop and upload download files (.csv format) here to write values back to active schema records instantly.")
    
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
                with st.spinner("Writing schema and indexing items row constraints..."):
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
                        st.success("🎉 Data safely restored. Switch back to Operational Dashboard to run filters.")
        except Exception as error:
            st.error(f"Critical Injection Interrupt: {str(error)}")

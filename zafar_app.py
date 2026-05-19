import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. APPLICATION INITIALIZATION & CONFIGURATION
st.set_page_config(
    page_title="Zafar Logistics ERP",
    page_icon="🍊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# High-Contrast Clean Light Theme Injection (Fixes visibility completely)
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    h1, h2, h3, p, label, span { 
        color: #0f172a !important; 
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Premium Orange Metric Panel Cards */
    div[data-testid="stMetric"] {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-left: 6px solid #f97316 !important;
        border-radius: 8px;
        padding: 16px 20px !important;
    }
    div[data-testid="stMetricValue"] { color: #f97316 !important; font-weight: 700; }
    
    /* Orange Action Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #ea580c 0%, #f97316 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
    }
    
    /* Dark Corporate Sidebar */
    section[data-testid="stSidebar"] { background-color: #0f172a !important; }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label {
        color: #f1f5f9 !important;
    }
    
    .rights-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. SESSION AUTHENTICATION
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = True

if not st.session_state['authenticated']:
    st.info("🔓 Session ended securely. Please refresh browser tab to log back in.")
    st.stop()

# 3. DATE TIMELINE CALCULATOR FOR STATUS VERIFICATION
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

# 4. CORE DATABASE OPERATIONS
def load_clean_data():
    conn = sqlite3.connect("zafar_database.db")
    try:
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
        st.error(f"Error: {str(e)}")
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
        st.error(f"Database Write Fault: {str(e)}")
        return False
    finally:
        conn.close()

# --- SIDEBAR INTERFACE ---
st.sidebar.markdown("<h2 style='color:#f97316 !important; font-size:24px; font-weight:bold;'>Zafar ERP</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='font-size:12px; color:#94a3b8;'>Logistics Management Portal</p>", unsafe_allow_html=True)
st.sidebar.write("---")

# 5. CORE INTERACTIVE TABS SYSTEM (Everything Organized clearly)
menu_tabs = st.tabs(["📊 Operational Dashboard", "✏️ Edit Data & User Rights", "📥 Database Backup Gateway"])
live_df = load_clean_data()

# ==========================================
# TAB 1: OPERATIONAL DASHBOARD
# ==========================================
with menu_tabs[0]:
    st.markdown("<h2 style='font-weight:800;'>📊 Import Logistics Dashboard</h2>", unsafe_allow_html=True)
    st.write("---")
    
    if not live_df.empty:
        # Dynamic Custom Filters Panel
        st.markdown("#### 🎯 Advanced Sourcing Filters")
        fl_col1, fl_col2, fl_col3 = st.columns(3)
        
        with fl_col1:
            company_list = ["All Companies"] + sorted(list(live_df['company_name'].dropna().unique())) if 'company_name' in live_df.columns else ["All Companies"]
            selected_company = st.selectbox("Company Division:", company_list, key="dash_co")
        with fl_col2:
            bank_list = ["All Banks"] + sorted(list(live_df['bank_name'].dropna().unique())) if 'bank_name' in live_df.columns else ["All Banks"]
            selected_bank = st.selectbox("Bank Branch Sourcing:", bank_list, key="dash_bank")
        with fl_col3:
            item_list = ["All Items"] + sorted(list(live_df['item_name'].dropna().unique())) if 'item_name' in live_df.columns else ["All Items"]
            selected_item = st.selectbox("Material / Item Type:", item_list, key="dash_item")

        # Apply Filters Sequence
        filtered_df = live_df.copy()
        if selected_company != "All Companies":
            filtered_df = filtered_df[filtered_df['company_name'] == selected_company]
        if selected_bank != "All Banks":
            filtered_df = filtered_df[filtered_df['bank_name'] == selected_bank]
        if selected_item != "All Items":
            filtered_df = filtered_df[filtered_df['item_name'] == selected_item]

        # Search Bar Lookup
        search_query = st.text_input("🔍 Global Text Lookup (Supplier, File ID, BL/LC No...)", "")
        if search_query:
            search_fields = ['supplier_name', 'item_name', 'bl_lc_no', 'file_no']
            mask = pd.Series(False, index=filtered_df.index)
            for field in search_fields:
                if field in filtered_df.columns:
                    mask |= filtered_df[field].astype(str).str.contains(search_query, case=False)
            filtered_df = filtered_df[mask]

        # Financial KPI Section
        st.write("##")
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("Total Active Shipments", f"{len(filtered_df)}")
        with m2: 
            total_lc = filtered_df['total_lc_value'].sum() if 'total_lc_value' in filtered_df.columns else 0.0
            st.metric("Aggregate LC Value (USD)", f"${total_lc:,.2f}")
        with m3:
            total_qty = filtered_df['quantity'].sum() if 'quantity' in filtered_df.columns else 0.0
            st.metric("Consolidated Quantity Mass", f"{total_qty:,.2f} Units")

        st.write("##")
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
        st.dataframe(filtered_df[existing_cols].rename(columns=display_cols), use_container_width=True)
    else:
        st.warning("⚠️ No active records found in the system database storage.")

# ==========================================
# TAB 2: EDIT DATA & USER RIGHTS MANAGEMENT (NEW)
# ==========================================
with menu_tabs[1]:
    st.markdown("<h2 style='font-weight:800;'>✏️ Record Mutation & User Rights Panel</h2>", unsafe_allow_html=True)
    st.write("---")
    
    panel_col1, panel_col2 = st.columns([2, 1])
    
    with panel_col1:
        st.markdown("### 📝 Edit Shipment Details Directly")
        if not live_df.empty:
            available_ids = sorted(list(live_df['id'].dropna().unique()))
            target_id = st.selectbox("Select Shipment Record ID to Modify:", available_ids)
            
            selected_row = live_df[live_df['id'] == target_id].iloc[0]
            
            edit_f1, edit_f2 = st.columns(2)
            with edit_f1:
                curr_docs = str(selected_row.get('bank_docs', '')) if pd.notnull(selected_row.get('bank_docs')) else 'OK'
                new_docs = st.text_input("Edit Bank Docs Status:", value=curr_docs)
                
                current_status = str(selected_row.get('status', ''))
                status_options = ["⚪ Pending", "🔵 In Transit", "🟠 Arrived at Port", "🟢 Cleared & Done"]
                default_idx = status_options.index(current_status) if current_status in status_options else 0
                new_status = st.selectbox("Override Shipment Status:", options=status_options, index=default_idx)
                
            with edit_f2:
                curr_remarks = str(selected_row.get('remarks', '')) if pd.notnull(selected_row.get('remarks')) else ''
                new_remarks = st.text_input("Modify File Remarks / Notes:", value=curr_remarks)
            
            st.write("#")
            if st.button("💾 SAVE CHANGES TO SYSTEM DATABASE"):
                if update_row_record(target_id, new_docs, new_remarks, new_status):
                    st.success(f"🎉 Shipment ID {target_id} updated successfully!")
                    st.rerun()
        else:
            st.warning("No live logs available to edit.")
            
    with panel_col2:
        st.markdown("### 👤 User Authorization Profile")
        st.markdown("""
            <div class="rights-card">
                <p style="margin:0; font-size:11px; color:#94a3b8; font-weight:600;">AUTHENTICATED IDENTITY</p>
                <p style="margin:2px 0; font-size:18px; color:#ffffff; font-weight:bold;">👤 Muhammad Zafar</p>
                <p style="margin:0; font-size:13px; color:#22c55e; font-weight:500;">● Status: Full Administrative Rights</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Securely Log Out From Session", key="tab_logout"):
            st.session_state['authenticated'] = False
            st.rerun()

# ==========================================
# TAB 3: BACKUP GATEWAY SYSTEM
# ==========================================
with menu_tabs[2]:
    st.markdown("<h2 style='font-weight:800;'>📥 System Sheet Restore Gateway</h2>", unsafe_allow_html=True)
    st.write("---")
    
    uploaded_file = st.file_uploader("Drop backup CSV spreadsheet layout file here:", type=["csv"])
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
            st.dataframe(final_import_dataframe.head(5), use_container_width=True)
            
            if st.button("🚀 Load Complete Spreadsheet Into Database Engine"):
                db_mapped_df = final_import_dataframe.rename(columns={
                    'Company Name': 'company_name', 'Bank Name': 'bank_name', 'File No': 'file_no',
                    'Indenter': 'indenter', 'Supplier Name': 'supplier_name', 'Item Name': 'item_name',
                    'BRAND NAME': 'brand_name', 'HS Code': 'hs_code', 'Quantity': 'quantity',
                    'Unit': 'unit', 'Unit Price': 'unit_price', 'Actual Costing (PKR)': 'actual_costing',
                    'Total LC Value': 'total_lc_value', 'Currency': 'currency', 'Type': 'type',
                    'ETD': 'etd', 'ETA': 'eta', 'BL / LC No': 'bl_lc_no', 'Bank Docs': 'bank_docs',
                    'Remarks': 'remarks', 'Status': 'status'
                })
                if insert_backup_records(db_mapped_df):
                    st.success("🎉 Data safely merged into active schema database.")
                    st.rerun()
        except Exception as error:
            st.error(f"Execution Error: {str(error)}")

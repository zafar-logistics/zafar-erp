import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. PAGE SETUP WITH MODERN CUSTOM GLASSMORPHIC THEME
st.set_page_config(
    page_title="Zafar Logistics ERP - Import Management",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark glassmorphic aur neon touches ka injection CSS
st.markdown("""
    <style>
    .reportview-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
        color: #38bdf8 !important;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #06b6d4 0%, #3b82f6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(6, 182, 212, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6);
    }
    </style>
""", unsafe_allow_html=True)

# DYNAMIC ETD / ETA AUTOMATED STATUS BADGE CALCULATION
def compute_dynamic_status(row):
    # Check if manually cleared or done first
    manual_status = str(row.get('status', '')).strip().lower()
    if manual_status in ['cleared', 'done', 'received', '🟢 cleared & done']:
        return "🟢 Cleared & Done"
        
    today = datetime.now().date()
    
    # Dates extraction and flexible parsing (Formats: '30-Apr-26', '2026-04-30' etc)
    etd_date = None
    eta_date = None
    
    for fmt in ('%d-%b-%y', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        if etd_date is None and pd.notnull(row.get('etd')) and str(row['etd']).strip() != 'None':
            try:
                etd_date = datetime.strptime(str(row['etd']).strip(), fmt).date()
            except ValueError:
                pass
        if eta_date is None and pd.notnull(row.get('eta')) and str(row['eta']).strip() != 'None':
            try:
                eta_date = datetime.strptime(str(row['eta']).strip(), fmt).date()
            except ValueError:
                pass

    # Logic Implementation based on exact dates timeline
    if eta_date and eta_date <= today:
        return "🟠 Arrived at Port"
    elif etd_date and etd_date <= today and (eta_date is None or eta_date > today):
        return "🔵 In Transit"
    elif etd_date and etd_date > today:
        return "⚪ Pending"
    
    # Fallback option if date format is invalid or empty
    return "⚪ Pending"

# 2. DATA PROCESSING FUNCTIONS WITH ROBUST DATATYPE CLEANSING
def load_clean_data():
    conn = sqlite3.connect("zafar_database.db")
    try:
        df = pd.read_sql_query("SELECT * FROM imports ORDER BY id DESC", conn)
        if not df.empty:
            # Calculation columns ko handle karna
            for num_col in ['total_lc_value', 'quantity', 'unit_price']:
                if num_col in df.columns:
                    df[num_col] = df[num_col].astype(str).str.replace(',', '').str.strip()
                    df[num_col] = pd.to_numeric(df[num_col], errors='coerce').fillna(0.0)
            
            # Formatting Display Columns for UI view
            df['Display_LC_Value'] = df['total_lc_value'].apply(lambda x: f"${x:,.2f}")
            df['Display_Quantity'] = df.apply(lambda row: f"{row['quantity']:,.2f} {row['unit'] if 'unit' in row else 'KG'}", axis=1)
            df['Display_Unit_Price'] = df['unit_price'].apply(lambda x: f"${x:,.2f}")
            
            # Trigger our newly built dynamic calculation logic per row
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
        df_clean = df.copy()
        for col in ['Quantity', 'Unit Price', 'Total LC Value']:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.replace(',', '').str.strip()
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0.0)

        df_records = df_clean.where(pd.notnull(df_clean), None).values.tolist()
        cursor.executemany(insert_query, df_records)
        conn.commit()
        st.success("🎉 Backup data database mein inject ho chuka hai!")
        return True
    except Exception as e:
        st.error(f"❌ Core Error: {str(e)}")
        return False
    finally:
        conn.close()

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.title("⚡ Control Center")
st.sidebar.write("Zafar Logistics ERP v2.6")
st.sidebar.write("---")

# Main Navigation Menu in Sidebar
app_mode = st.sidebar.radio(
    "Navigate Modules",
    ["📊 Live Dashboard & Search", "📥 Database Backup Restore"]
)

# Active filters setup
live_df = load_clean_data()
selected_item = "All Items"
selected_supplier = "All Suppliers"

if app_mode == "📊 Live Dashboard & Search" and not live_df.empty:
    st.sidebar.subheader("🎯 Quick Filters")
    if 'item_name' in live_df.columns:
        item_list = ["All Items"] + sorted(list(live_df['item_name'].dropna().unique()))
        selected_item = st.sidebar.selectbox("Filter by Item Material", item_list)
    if 'supplier_name' in live_df.columns:
        supplier_list = ["All Suppliers"] + sorted(list(live_df['supplier_name'].dropna().unique()))
        selected_supplier = st.sidebar.selectbox("Filter by Shipper/Supplier", supplier_list)

# ==========================================
# MODULE 1: MODERN LOOKUP & SEARCH DASHBOARD
# ==========================================
if app_mode == "📊 Live Dashboard & Search":
    st.title("📊 Business Import Analytics Dashboard")
    st.write("Live database connection active.")
    
    if not live_df.empty:
        # Applying Sidebar Filters
        filtered_df = live_df.copy()
        if selected_item != "All Items":
            filtered_df = filtered_df[filtered_df['item_name'] == selected_item]
        if selected_supplier != "All Suppliers":
            filtered_df = filtered_df[filtered_df['supplier_name'] == selected_supplier]
            
        # Top Global Search Bar
        search_query = st.text_input("🔍 Global Search (Type Supplier Name, Item, BL/LC No, or HS Code to lookup...)", "")
        if search_query:
            filtered_df = filtered_df[
                filtered_df['supplier_name'].astype(str).str.contains(search_query, case=False) |
                filtered_df['item_name'].astype(str).str.contains(search_query, case=False) |
                filtered_df['bl_lc_no'].astype(str).str.contains(search_query, case=False) |
                filtered_df['hs_code'].astype(str).str.contains(search_query, case=False)
            ]

        # Professional High-Visibility KPI Summary Blocks
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Active Shipments", f"{len(filtered_df)}")
        with c2:
            calculated_lc_sum = filtered_df['total_lc_value'].sum() if 'total_lc_value' in filtered_df.columns else 0.0
            st.metric("Aggregate LC Value (USD)", f"${calculated_lc_sum:,.2f}")
        with c3:
            calculated_qty_sum = filtered_df['quantity'].sum() if 'quantity' in filtered_df.columns else 0.0
            st.metric("Total Cargo Weight", f"{calculated_qty_sum:,.2f} Units")
            
        st.write("---")
        
        # Clean Display Table Structure
        display_cols = {
            'id': 'ID',
            'supplier_name': 'Supplier Name',
            'item_name': 'Item Description',
            'brand_name': 'Brand',
            'hs_code': 'HS Code',
            'Display_Quantity': 'Quantity (Weight)',
            'Display_Unit_Price': 'Unit Price',
            'actual_costing': 'Actual Costing (PKR)',
            'Display_LC_Value': 'Total LC Value',
            'currency': 'Currency',
            'type': 'Type',
            'etd': 'ETD',
            'eta': 'ETA',
            'bl_lc_no': 'BL / LC Number',
            'bank_docs': 'Bank Docs',
            'remarks': 'Remarks',
            'status': 'Status'
        }
        
        existing_cols = [c for c in display_cols.keys() if c in filtered_df.columns]
        ui_table = filtered_df[existing_cols].rename(columns=display_cols)
        
        st.subheader("📋 Filtered Active Shipments Record Log")
        st.dataframe(ui_table, use_container_width=True)
    else:
        st.warning("⚠️ Database structure table available, but no entries found. Use the sidebar menu to reload backup system data.")

# ==========================================
# MODULE 2: BACKUP PORTAL
# ==========================================
elif app_mode == "📥 Database Backup Restore":
    st.title("📥 System Configuration Backup & Engine Sync")
    st.info("💡 Yeh gateway Excel/CSV records backup data ko read karke local database ke metrics reset aur compile karega.")
    
    st.write("### System Architecture File Upload:")
    uploaded_file = st.file_uploader("Select architectural system file (.csv)", type=["csv"], label_visibility="collapsed")
    
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
            
            st.write("### 📊 Live Inbound Buffer Preview:")
            st.dataframe(final_import_dataframe.head(5), use_container_width=True)
            
            if st.button("🚀 Confirm Integrity & Inject Records into Database", use_container_width=True):
                with st.spinner("Processing calculations data mapping rows..."):
                    success = insert_backup_records(final_import_dataframe)
                    if success:
                        st.balloons()
                        st.success("Data compiled perfectly! Navigate to dashboard to view update.")
        except Exception as error:
            st.error(f"Inbound processing failed: {str(error)}")

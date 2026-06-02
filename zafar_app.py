import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime, timedelta

# --- DATABASE SETUP ---
db_path = 'zafar_logistics_v3.db'
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()

ALL_AVAILABLE_COLUMNS = [
    'Company Name', 'Bank Name', 'File No', 'Indenter', 'Supplier Name', 
    'Item Name', 'Brand Name', 'HS Code', 'Quantity', 'Unit', 'Unit Price', 
    'Actual Costing (PKR)', 'Total LC Value', 'Currency', 'Type', 'Status', 
    'ETD', 'ETA', 'BL / LC No', 'Bank Docs', 'Remarks'
]

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS shipments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  company_name TEXT, bank_name TEXT, indenter TEXT, file_no TEXT UNIQUE, 
                  shipper TEXT, pi_no TEXT, fc_amount TEXT, currency TEXT, 
                  shipment_type TEXT, etd TEXT, eta TEXT, bl_no TEXT, bank_docs TEXT, remarks TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS shipment_items 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  file_no TEXT, item_name TEXT, brand_name TEXT, hs_code TEXT, qty TEXT, unit TEXT, unit_price TEXT, actual_costing TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, password TEXT, role TEXT)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS user_column_rights 
                 (username TEXT PRIMARY KEY, allowed_columns TEXT)''')
    
    try:
        c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('zafar', 'zafar786', 'Admin')")
        c.execute("INSERT OR REPLACE INTO user_column_rights (username, allowed_columns) VALUES ('zafar', ?)", (json.dumps(ALL_AVAILABLE_COLUMNS),))
        conn.commit()
    except:
        pass
        
    try: c.execute('ALTER TABLE shipment_items ADD COLUMN brand_name TEXT')
    except: pass
    try: c.execute('ALTER TABLE shipment_items ADD COLUMN hs_code TEXT')
    except: pass
    try: c.execute('ALTER TABLE shipment_items ADD COLUMN actual_costing TEXT')
    except: pass
    conn.commit()

init_db()

# --- HELPER FUNCTIONS ---
def get_distinct_values(column_name, table_name="shipments"):
    try:
        c.execute(f"SELECT DISTINCT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL AND {column_name} != '' AND {column_name} != '-'")
        return [r[0] for r in c.fetchall()]
    except:
        return []

def get_hs_codes_for_item(item_name):
    try:
        c.execute("SELECT DISTINCT hs_code FROM shipment_items WHERE item_name=? AND hs_code IS NOT NULL AND hs_code != '' AND hs_code != '-'", (item_name,))
        return [r[0] for r in c.fetchall()]
    except:
        return []

def parse_date(date_str):
    if not date_str or str(date_str).strip() in ["", "-", "Pending", "None", "nan"]: return None
    for fmt in ('%d-%b-%y', '%d-%b-%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try: return datetime.strptime(str(date_str).strip(), fmt)
        except: pass
    return None

def get_safe_val(row_obj, keys_list, default=""):
    """Crash proof value retriever for mixed-case dictionary/pandas row keys"""
    if row_obj is None:
        return default
    for k in keys_list:
        if k in row_obj: 
            return row_obj[k]
        if hasattr(row_obj, 'index') and k in row_obj.index:
            return row_obj[k]
    return default

# --- INTERFACE SETUP ---
st.set_page_config(page_title="Zafar Logistics ERP", layout="wide")

if "logged_in" not in st.session_state: 
    st.session_state["logged_in"] = False
if "username" not in st.session_state: 
    st.session_state["username"] = ""
if "user_role" not in st.session_state: 
    st.session_state["user_role"] = ""

# --- GLOBAL CSS CUSTOM DESIGNS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700&display=swap');
        
        .stApp {
            background-color: #f8fafc;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        .dashboard-header {
            color: #0f172a;
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 25px;
            margin-top: -15px;
        }
        .glass-card-wrapper {
            display: flex;
            gap: 20px;
            margin-bottom: 25px;
            flex-wrap: wrap;
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.5);
            padding: 16px 24px;
            border-radius: 16px;
            min-width: 200px;
            flex: 1;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.02);
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .glass-card-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #1e293b;
            line-height: 1;
        }
        .glass-card-label {
            font-size: 0.85rem;
            color: #64748b;
            font-weight: 500;
        }
        .custom-card {
            background: #ffffff;
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0px 4px 20px rgba(0,0,0,0.01);
            border: 1px solid #f1f5f9;
            margin-bottom: 20px;
        }
        .card-title {
            font-size: 1rem;
            font-weight: 600;
            color: #334155;
            margin-bottom: 15px;
        }
        .stDownloadButton>button {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            padding: 8px 16px !important;
            box-shadow: 0px 2px 4px rgba(0,0,0,0.02);
        }
        div[data-testid="stDataFrame"] table th {
            background-color: #f8fafc !important;
            color: #475569 !important;
            font-weight: 600 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 🔑 HAAMEEM LOGIN SCREEN ---
if not st.session_state["logged_in"]:
    st.markdown("""
        <style>
            [data-testid="stHeader"], [data-testid="stSidebar"] { display: none !important; }
            .login-container { display: flex; flex-direction: row; background-color: #ffffff; border-radius: 12px; box-shadow: 0px 8px 24px rgba(0,0,0,0.12); overflow: hidden; margin-top: 5%; min-height: 480px; border: 1px solid #e2e8f0; }
            .left-banner { background: linear-gradient(135deg, #e67e22 0%, #d35400 100%); padding: 40px; color: #ffffff; flex: 1.1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }
            .left-banner h1 { color: #ffffff !important; font-family: 'Georgia', serif; font-weight: bold; font-size: 2.3rem; margin-bottom: 15px; }
            .left-banner p { font-size: 1.05rem; opacity: 0.9; max-width: 360px; }
            .right-form { flex: 1; padding: 45px; display: flex; flex-direction: column; justify-content: center; background-color: #ffffff; }
        </style>
    """, unsafe_allow_html=True)
    w1, w2, w3 = st.columns([1, 8, 1])
    with w2:
        st.markdown("""
            <div class="login-container">
                <div class="left-banner">
                    <div style="font-size: 40px;">✨📋</div>
                    <h1>HAAMEEM</h1>
                    <p>Processing Chemicals & Raw Materials System. Secure Management Portal.</p>
                </div>
                <div class="right-form">
                    <h3 style='color: #2c3e50; font-family: Georgia, serif; font-weight:700; margin-bottom: 5px;'>🔒 Secure System Entry</h3>
                    <p style='color: #7f8c8d; font-size: 0.9rem; margin-bottom: 20px;'>Please enter authorized credentials to access master files.</p>
        """, unsafe_allow_html=True)
        user_input = st.text_input("Username ID:", placeholder="Enter your username", key="login_uid")
        pass_input = st.text_input("Security Password:", type="password", placeholder="••••••••", key="login_pwd")
        if st.button("Access Dashboard 🚀", use_container_width=True):
            u_clean = user_input.strip().lower()
            c.execute("SELECT role FROM users WHERE username=? AND password=?", (u_clean, pass_input))
            result = c.fetchone()
            if result:
                st.session_state["logged_in"] = True
                st.session_state["username"] = u_clean
                st.session_state["user_role"] = result[0]
                st.rerun()
            else: 
                st.error("Invalid credentials.")
        st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.markdown(f"<h3 style='color: #e67e22; font-weight: bold; margin-bottom:0px;'>👤 {st.session_state['username'].upper()}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"**Security Profile:** `{st.session_state['user_role']}`")
st.sidebar.markdown("---")

available_options = ["📊 Dashboard", "📝 Nayi Entry (Add)", "🔄 Update / Edit"]
if st.session_state["user_role"] == "Admin": 
    available_options.append("👥 Manage Users / Accounts")
menu = st.sidebar.radio("Navigation Menu:", available_options)

# --- SIDEBAR BULK IMPORT ---
if st.session_state["user_role"] in ["Admin", "Manager"]:
    st.sidebar.markdown("---")
    st.sidebar.write("📥 **Bulk Import Data (Excel / CSV)**")
    uploaded_file = st.sidebar.file_uploader("Upload Master Sheet to Fill Dashboard:", type=["xlsx", "csv"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
            
            col_mapping = {
                'Company Name': 'company_name', 'Bank Name': 'bank_name', 'File No': 'file_no',
                'Indenter': 'indenter', 'Supplier Name': 'shipper', 'Item Name': 'item_name',
                'Brand Name': 'brand_name', 'HS Code': 'hs_code', 'Quantity': 'qty',
                'Unit': 'unit', 'Unit Price': 'unit_price', 'Actual Costing (PKR)': 'actual_costing',
                'Total LC Value': 'fc_amount', 'Currency': 'currency', 'Type': 'shipment_type',
                'ETD': 'etd', 'ETA': 'eta', 'BL / LC No': 'bl_no', 'Bank Docs': 'bank_docs', 'Remarks': 'remarks'
            }
            df_upload = df_upload.rename(columns=col_mapping).fillna("-")
            
            if 'file_no' in df_upload.columns:
                success_count = 0
                for _, row in df_upload.iterrows():
                    f_no = str(row['file_no']).strip()
                    if not f_no or f_no == "-": continue
                    
                    c.execute("SELECT 1 FROM shipments WHERE file_no=?", (f_no,))
                    if not c.fetchone():
                        c.execute('''INSERT INTO shipments (company_name, bank_name, indenter, file_no, shipper, fc_amount, currency, shipment_type, etd, eta, bl_no, bank_docs, remarks) 
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                                  (str(row.get('company_name', '-')), str(row.get('bank_name', '-')), str(row.get('indenter', '-')), f_no, 
                                   str(row.get('shipper', '-')), str(row.get('fc_amount', '0')), str(row.get('currency', 'USD')), 
                                   str(row.get('shipment_type', 'FCL')), str(row.get('etd', '-')), str(row.get('eta', '-')), 
                                   str(row.get('bl_no', '-')), str(row.get('bank_docs', 'Pending')), str(row.get('remarks', '-'))))
                    
                    if 'item_name' in df_upload.columns and str(row['item_name']) != "-":
                        c.execute("SELECT 1 FROM shipment_items WHERE file_no=? AND item_name=?", (f_no, str(row['item_name'])))
                        if not c.fetchone():
                            c.execute('''INSERT INTO shipment_items (file_no, item_name, brand_name, hs_code, qty, unit, unit_price, actual_costing) 
                                         VALUES (?,?,?,?,?,?,?,?)''', 
                                      (f_no, str(row['item_name']), str(row.get('brand_name', '-')), str(row.get('hs_code', '-')), 
                                       str(row.get('qty', '0')), str(row.get('unit', 'KG')), str(row.get('unit_price', '0')), str(row.get('actual_costing', '-'))))
                    success_count += 1
                conn.commit()
                st.sidebar.success(f"✅ Imported {success_count} rows!")
                st.rerun()
        except Exception as e:
            st.sidebar.error(f"Import failed: {e}")

# --- SIDEBAR RATE ANALYSIS GRAPH ---
st.sidebar.markdown("---")
st.sidebar.write("🔍 **Item Rate Analysis Graph**")
all_items_saved = get_distinct_values("item_name", "shipment_items")
if all_items_saved:
    selected_graph_item = st.sidebar.selectbox("Select Item for Trend:", ["-- Select Item --"] + all_items_saved)
    if selected_graph_item != "-- Select Item --":
        try:
            df_graph = pd.read_sql(f"SELECT s.file_no, i.unit_price, i.actual_costing FROM shipment_items i JOIN shipments s ON i.file_no = s.file_no WHERE i.item_name='{selected_graph_item}'", conn)
            if not df_graph.empty:
                df_graph['Unit Price'] = pd.to_numeric(df_graph['unit_price'], errors='coerce')
                df_graph['Actual Costing'] = pd.to_numeric(df_graph['actual_costing'], errors='coerce')
                st.sidebar.line_chart(df_graph.dropna(subset=['Unit Price'])[['Unit Price', 'Actual Costing']])
        except: pass

st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
if st.sidebar.button("🚪 LOGOUT SYSTEM", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()

BANKS = ["Bank Al Habib", "Habib Metro", "Meezan Bank"]
COMPANIES = ["Haa Meem Pvt Ltd", "Fine Trading Corporation", "Haa Meem AOP"]
CURRENCIES = ["USD", "CNY", "EUR", "PKR"]
UNITS = ["KG", "MT", "DRUMS", "BAGS"]
ROLES = ["Admin", "Manager", "Viewer"]

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown('<div class="dashboard-header">Good morning, Haameem Control Center</div>', unsafe_allow_html=True)
    
    if st.session_state["username"] == "zafar" or st.session_state["user_role"] == "Admin":
        allowed_display_cols = ALL_AVAILABLE_COLUMNS
    else:
        c.execute("SELECT allowed_columns FROM user_column_rights WHERE username=?", (st.session_state["username"],))
        rights_res = c.fetchone()
        allowed_display_cols = json.loads(rights_res[0]) if rights_res else ['Company Name', 'Bank Name', 'File No', 'Item Name', 'Status']
        
    try:
        query = '''
            SELECT s.company_name AS [Company Name], s.bank_name AS [Bank Name], s.file_no AS [File No],
                   s.indenter AS [Indenter], s.shipper AS [Supplier Name], i.item_name AS [Item Name],
                   i.brand_name AS [Brand Name], i.hs_code AS [HS Code], i.qty AS [Quantity],
                   i.unit AS [Unit], i.unit_price AS [Unit Price], i.actual_costing AS [Actual Costing (PKR)],
                   s.fc_amount AS [Total LC Value], s.currency AS [Currency], s.shipment_type AS [Type],
                   s.etd AS [ETD], s.eta AS [ETA], s.bl_no AS [BL / LC No], s.bank_docs AS [Bank Docs], s.remarks AS [Remarks]
            FROM shipments s LEFT JOIN shipment_items i ON s.file_no = i.file_no
        '''
        df = pd.read_sql(query, conn)
    except:
        df = pd.read_sql('SELECT * FROM shipments', conn)

    for col in ALL_AVAILABLE_COLUMNS:
        if col not in df.columns: df[col] = "-"
        
    if not df.empty:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        all_live_alerts = []
        total_count = len(df['File No'].unique())
        
        def calculated_status(row):
            f_no = str(get_safe_val(row, ['File No', 'file_no'])).strip()
            if f_no == "" or f_no == "-" or pd.isna(get_safe_val(row, ['File No', 'file_no'])): return "Query"
            etd_dt = parse_date(get_safe_val(row, ['ETD', 'etd']))
            eta_dt = parse_date(get_safe_val(row, ['ETA', 'eta', '-']))
            
            if etd_dt and etd_dt.date() == today.date(): all_live_alerts.append(f"🚢 File: {f_no} — AAJ CHALEGA!")
            if eta_dt and eta_dt <= today and (today - eta_dt).days <= 6: all_live_alerts.append(f"⚓ File: {f_no} — PORT PE HAI!")
            
            if eta_dt and (today - eta_dt).days >= 7: return "Complete"
            if eta_dt:
                if eta_dt <= today or (eta_dt > today and eta_dt <= today + timedelta(days=6)): return "Arrived"
                return "Shipment on way"
            if etd_dt:
                return "Shipped" if etd_dt <= today else "Shipment not shipped"
            return "LC Opening"
            
        df['Status'] = df.apply(calculated_status, axis=1)
        done_count = len(df[df['Status'] == 'Complete']['File No'].unique())
        arrived_count = len(df[df['Status'] == 'Arrived']['File No'].unique())
        pending_count = total_count - done_count
        
        st.markdown(f"""
            <div class="glass-card-wrapper">
                <div class="glass-card" style="border-left: 4px solid #38bdf8;"><div>📁</div><div><div class="glass-card-value">{total_count}</div><div class="glass-card-label">Total Files</div></div></div>
                <div class="glass-card" style="border-left: 4px solid #4ade80;"><div>✅</div><div><div class="glass-card-value">{done_count}</div><div class="glass-card-label">Done Projects</div></div></div>
                <div class="glass-card" style="border-left: 4px solid #fb923c;"><div>⏳</div><div><div class="glass-card-value">{pending_count}</div><div class="glass-card-label">Pending Files</div></div></div>
                <div class="glass-card" style="border-left: 4px solid #a78bfa;"><div>⚓</div><div><div class="glass-card-value">{arrived_count}</div><div class="glass-card-label">Port Arrived</div></div></div>
            </div>
        """, unsafe_allow_html=True)
        
        if all_live_alerts:
            with st.sidebar.expander("🔔 SYSTEM LIVE ALERTS", expanded=True):
                for alert_msg in set(all_live_alerts): st.info(alert_msg)
                
        c_top1, c_top2 = st.columns([2, 5])
        with c_top1:
            st.markdown('<div class="custom-card"><div class="card-title">📥 Operations</div>', unsafe_allow_html=True)
            st.download_button(label="📥 Export Master Sheet to Excel", data=df[[c for c in allowed_display_cols if c in df.columns]].to_csv(index=False).encode('utf-8'), file_name="Master_Logs.csv", mime="text/csv")
            st.markdown('</div>', unsafe_allow_html=True)
        with c_top2:
            st.markdown('<div class="custom-card"><div class="card-title">🔍 Quick Filters</div>', unsafe_allow_html=True)
            f1, f2, f3 = st.columns(3)
            sel_comp = f1.multiselect("Entity:", COMPANIES)
            sel_bank = f2.multiselect("Bank:", BANKS)
            search = f3.text_input("Search Keyword:")
            st.markdown('</div>', unsafe_allow_html=True)
            
        if sel_comp: df = df[df['Company Name'].isin(sel_comp)]
        if sel_bank: df = df[df['Bank Name'].isin(sel_bank)]
        if search: df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        
        df_display = df[[c for c in allowed_display_cols if c in df.columns]].reset_index(drop=True)
        df_display.index = df_display.index + 1
        st.dataframe(df_display, use_container_width=True)
    else: st.info("No data available.")

# --- 2. NAYI ENTRY (ADD RECORDS) ---
elif menu == "📝 Nayi Entry (Add)" and st.session_state["user_role"] in ["Admin", "Manager"]:
    st.subheader("📝 Nayi Shipment Records Entry Portal")
    past_suppliers = get_distinct_values("shipper")
    past_indenters = get_distinct_values("indenter")
    past_items = get_distinct_values("item_name", "shipment_items")
    
    with st.form("add_form", clear_on_submit=True):
        col_top1, col_top2 = st.columns(2)
        company_name = col_top1.selectbox("Company Name", COMPANIES)
        bank_name = col_top2.selectbox("Bank Name", BANKS)
        
        c1, c2, c3, c4 = st.columns(4)
        indenter = c1.selectbox("Indenter Name", [""] + past_indenters) if past_indenters else c1.text_input("Indenter")
        file_no = c2.text_input("File No (Unique)")
        shipper = c3.selectbox("Supplier Name", [""] + past_suppliers) if past_suppliers else c3.text_input("Shipper")
        pi_no = c4.text_input("P.I. No")
        
        am1, am2, am3 = st.columns([2, 1, 1])
        fc_amount = am1.text_input("Total LC Value")
        currency = am2.selectbox("Currency", CURRENCIES)
        ship_type = am3.selectbox("Type", ["FCL", "LCL"])
        
        st.markdown("---")
        st.markdown("##### 🛒 Items Breakdown")
        items_inputs = []
        for i in range(1, 4):
            st.write(f"**Item #{i}:**")
            it1, it_b, it_hs, it2, it3, it4, it5 = st.columns([3, 2, 2, 1, 1, 2, 2])
            name = it1.selectbox(f"Item Name #{i}", [""] + past_items, key=f"add_name_{i}")
            brand = it_b.text_input("Brand", key=f"add_brand_{i}")
            hs_code = it_hs.text_input("HS Code", key=f"add_hs_{i}")
            qty = it2.text_input("Qty", key=f"add_qty_{i}")
            unit = it3.selectbox("Unit", UNITS, key=f"add_unit_{i}")
            price = it4.text_input("Unit Price", key=f"add_price_{i}")
            costing = it5.text_input("Actual Costing (PKR)", key=f"add_cost_{i}")
            if name: items_inputs.append((name, brand, hs_code, qty, unit, price, costing))
            
        st.markdown("---")
        d1, d2, d3, d4 = st.columns(4)
        etd = d1.text_input("ETD (e.g. 30-May-2026)")
        eta = d2.text_input("ETA")
        bl_no = d3.text_input("BL / LC No")
        bank_docs = d4.selectbox("Bank Docs", ["Pending", "OK"])
        remarks = st.text_area("Remarks")
        
        if st.form_submit_button("Save Shipment Master"):
            if not file_no: st.error("File No missing!")
            else:
                try:
                    c.execute('''INSERT INTO shipments (company_name, bank_name, indenter, file_no, shipper, pi_no, fc_amount, currency, shipment_type, etd, eta, bl_no, bank_docs, remarks) 
                                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                              (company_name, bank_name, str(indenter), file_no, str(shipper), pi_no, fc_amount, currency, ship_type, etd, eta, bl_no, bank_docs, remarks))
                    
                    for item in items_inputs:
                        c.execute('''INSERT INTO shipment_items (file_no, item_name, brand_name, hs_code, qty, unit, unit_price, actual_costing) VALUES (?,?,?,?,?,?,?,?)''', 
                                  (file_no, item[0], item[1], str(item[2]), item[3], item[4], item[5], item[6]))
                    conn.commit()
                    st.success("✅ Shipment recorded securely!")
                    st.rerun()
                except Exception as e: st.error(f"Save Failed: {e}")

# --- 3. UPDATE / EDIT ---
elif menu == "🔄 Update / Edit" and st.session_state["user_role"] in ["Admin", "Manager"]:
    st.subheader("🔄 Update Master Logs & Costing Data")
    df_raw = pd.read_sql('SELECT * FROM shipments', conn)
    past_items = get_distinct_values("item_name", "shipment_items")
    
    if not df_raw.empty:
        file_to_update = st.selectbox("Select File No to Update:", df_raw['file_no'].tolist())
        row = df_raw[df_raw['file_no'] == file_to_update].iloc[0]
        df_ex_items = pd.read_sql(f"SELECT * FROM shipment_items WHERE file_no='{file_to_update}'", conn)
        
        with st.form(key=f"form_up_{file_to_update}"):
            u1, u2 = st.columns(2)
            
            # SAFE VALUE RETRIEVAL FROM DATABASE DICTIONARY ROW
            c_name = get_safe_val(row, ['company_name', 'COMPANY_NAME', 'Company Name'])
            b_name = get_safe_val(row, ['bank_name', 'BANK_NAME', 'Bank Name'])
            ind_val = get_safe_val(row, ['indenter', 'INDENTER', 'Indenter'])
            ship_val = get_safe_val(row, ['shipper', 'SHIPPER', 'Supplier Name'])
            fc_val = get_safe_val(row, ['fc_amount', 'FC_AMOUNT', 'Total LC Value'])
            curr_val = get_safe_val(row, ['currency', 'CURRENCY', 'Currency'])
            type_val = get_safe_val(row, ['shipment_type', 'SHIPMENT_TYPE', 'Type'])
            etd_val = get_safe_val(row, ['etd', 'ETD'])
            eta_val = get_safe_val(row, ['eta', 'ETA'])
            bl_val = get_safe_val(row, ['bl_no', 'BL_NO'])
            docs_val = get_safe_val(row, ['bank_docs', 'BANK_DOCS'])
            rem_val = get_safe_val(row, ['remarks', 'REMARKS'])

            u_comp = u1.selectbox("Company", COMPANIES, index=COMPANIES.index(c_name) if c_name in COMPANIES else 0)
            u_bank = u2.selectbox("Bank", BANKS, index=BANKS.index(b_name) if b_name in BANKS else 0)
            u_indenter = u1.text_input("Indenter", value=str(ind_val))
            u_shipper = u2.text_input("Shipper", value=str(ship_val))
            u_amount = u1.text_input("Total Value", value=str(fc_val))
            u_curr = u2.selectbox("Currency", CURRENCIES, index=CURRENCIES.index(curr_val) if curr_val in CURRENCIES else 0)
            u_type = st.selectbox("Type", ["FCL", "LCL"], index=0 if type_val == "FCL" else 1)
            
            st.markdown("---")
            updated_items = []
            for idx in range(3):
                st.write(f"**Item Row #{idx+1}:**")
                it_col1, it_col_b, it_col_hs, it_col2, it_col3, it_col4, it_col5 = st.columns([3, 2, 2, 1, 1, 1, 2])
                
                ex_name, ex_brand, ex_hs, ex_qty, ex_unit, ex_price, ex_cost = "", "", "", "", "KG", "", ""
                if idx < len(df_ex_items):
                    item_row = df_ex_items.iloc[idx]
                    ex_name = get_safe_val(item_row, ['item_name', 'ITEM_NAME', 'Item Name'])
                    ex_brand = get_safe_val(item_row, ['brand_name', 'BRAND_NAME', 'Brand Name'])
                    ex_hs = get_safe_val(item_row, ['hs_code', 'HS_CODE', 'HS Code'])
                    ex_qty = get_safe_val(item_row, ['qty', 'QTY', 'Quantity'])
                    ex_unit = get_safe_val(item_row, ['unit', 'UNIT', 'Unit'], "KG")
                    ex_price = get_safe_val(item_row, ['unit_price', 'UNIT_PRICE', 'Unit Price'])
                    ex_cost = get_safe_val(item_row, ['actual_costing', 'ACTUAL_COSTING', 'Actual Costing (PKR)'])
                    
                u_name = it_col1.selectbox("Item Name", [""] + past_items, index=past_items.index(ex_name)+1 if ex_name in past_items else 0, key=f"u_name_{idx}")
                u_brand = it_col_b.text_input("Brand", value=str(ex_brand), key=f"u_brand_{idx}")
                u_hs = it_col_hs.text_input("HS Code", value=str(ex_hs), key=f"u_hs_{idx}")
                u_qty = it_col2.text_input("Qty", value=str(ex_qty), key=f"u_qty_{idx}")
                u_unit = it_col3.selectbox("Unit", UNITS, index=UNITS.index(ex_unit) if ex_unit in UNITS else 0, key=f"u_unit_{idx}")
                u_price = it_col4.text_input("Price", value=str(ex_price), key=f"u_price_{idx}")
                u_cost = it_col5.text_input("Actual Costing (PKR)", value=str(ex_cost), key=f"u_cost_{idx}")
                
                if u_name: updated_items.append((u_name, u_brand, u_hs, u_qty, u_unit, u_price, u_cost))
                
            st.markdown("---")
            u_etd = u1.text_input("ETD", value=str(etd_val))
            u_eta = u2.text_input("ETA", value=str(eta_val))
            u_bl = u1.text_input("BL No", value=str(bl_val))
            u_docs = u2.selectbox("Docs", ["Pending", "OK"], index=0 if docs_val == "Pending" else 1)
            u_remarks = st.text_area("Remarks", value=str(rem_val))
            
            if st.form_submit_button("💾 Update Master Records"):
                c.execute('''UPDATE shipments SET company_name=?, bank_name=?, indenter=?, shipper=?, fc_amount=?, currency=?, shipment_type=?, etd=?, eta=?, bl_no=?, bank_docs=?, remarks=? WHERE file_no=?''', 
                          (u_comp, u_bank, u_indenter, u_shipper, u_amount, u_curr, u_type, u_etd, u_eta, u_bl, u_docs, u_remarks, file_to_update))
                c.execute(f"DELETE FROM shipment_items WHERE file_no='{file_to_update}'")
                for item in updated_items:
                    c.execute('''INSERT INTO shipment_items (file_no, item_name, brand_name, hs_code, qty, unit, unit_price, actual_costing) VALUES (?,?,?,?,?,?,?,?)''', 
                              (file_to_update, item[0], item[1], str(item[2]), item[3], item[4], item[5], item[6]))
                conn.commit()
                st.success("✅ Records updated successfully!")
                st.rerun()

# --- 4. MANAGE ACCOUNTS PANEL ---
elif menu == "👥 Manage Users / Accounts" and st.session_state["user_role"] == "Admin":
    st.subheader("👥 System Accounts Security Profile Settings")
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.write("##### 👤 Naya Account Banayein")
        selected_role = st.selectbox("Rights Level:", ROLES)
        with st.form("create_user_form"):
            new_user = st.text_input("Username:")
            new_pass = st.text_input("Password:", type="password")
            if st.form_submit_button("Create Account"):
                if new_user and new_pass:
                    try:
                        u_clean = new_user.strip().lower()
                        c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", (u_clean, new_pass, selected_role))
                        c.execute("INSERT OR REPLACE INTO user_column_rights (username, allowed_columns) VALUES (?,?)", (u_clean, json.dumps(ALL_AVAILABLE_COLUMNS)))
                        conn.commit()
                        st.success(f"✅ User '{u_clean}' registered!")
                        st.rerun()
                    except: st.error("User already exists.")
    with m_col2:
        st.write("##### 🔄 Manage Passwords & Deletions")
        df_users_list = pd.read_sql("SELECT username FROM users WHERE username != 'zafar'", conn)
        if not df_users_list.empty:
            target_user = st.selectbox("Account List:", df_users_list['username'].tolist())
            with st.form("update_password_form"):
                new_password_val = st.text_input("Naya Password:", type="password")
                if st.form_submit_button("🔒 Save Password"):
                    c.execute("UPDATE users SET password=? WHERE username=?", (new_password_val, target_user))
                    conn.commit()
                    st.success("Password updated!")
            if st.button("❌ Delete This Account"):
                c.execute("DELETE FROM users WHERE username=?", (target_user,))
                c.execute("DELETE FROM user_column_rights WHERE username=?", (target_user,))
                conn.commit()
                st.rerun()
                
    st.markdown("---")
    st.write("##### 🎛️ Column-Level Visibility Control Rights")
    df_all_users_raw = pd.read_sql("SELECT username FROM users", conn)
    user_to_configure = st.selectbox("Configure rights for user:", df_all_users_raw['username'].tolist())
    
    c.execute("SELECT allowed_columns FROM user_column_rights WHERE username=?", (user_to_configure,))
    current_rights_res = c.fetchone()
    current_allowed = json.loads(current_rights_res[0]) if current_rights_res else ALL_AVAILABLE_COLUMNS
    
    chk_cols = st.columns(4)
    chosen_columns = []
    for idx, col_name in enumerate(ALL_AVAILABLE_COLUMNS):
        with chk_cols[idx % 4]:
            if st.checkbox(col_name, value=(col_name in current_allowed), key=f"col_chk_{col_name}"):
                chosen_columns.append(col_name)
                
    if st.button("🔒 Save Column Layout Configuration", use_container_width=True):
        if not chosen_columns: st.error("Select at least one column!")
        else:
            c.execute("INSERT OR REPLACE INTO user_column_rights (username, allowed_columns) VALUES (?,?)", (user_to_configure, json.dumps(chosen_columns)))
            conn.commit()
            st.success("Column permissions saved!")

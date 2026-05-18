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

# --- INTERFACE SETUP ---
st.set_page_config(page_title="Zafar Logistics ERP", layout="wide")

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "username" not in st.session_state: st.session_state["username"] = ""
if "user_role" not in st.session_state: st.session_state["user_role"] = ""

# --- GLOBAL STYLING INJECTOR ---
st.markdown("""
    <style>
        .stApp { background-color: #fafafa; }
        .dashboard-header {
            font-family: 'Helvetica Neue', Arial, sans-serif; color: #1a252f; font-size: 1.6rem; font-weight: 700;
            border-bottom: 2px solid #e67e22; padding-bottom: 6px; margin-bottom: 20px; margin-top: -10px;
        }
        .custom-card {
            background-color: #ffffff; padding: 16px 20px; border-radius: 8px;
            box-shadow: 0px 2px 8px rgba(0,0,0,0.03); border: 1px solid #e2e8f0; margin-bottom: 15px;
        }
        .card-title {
            font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 1rem; font-weight: bold;
            color: #2c3e50; margin-bottom: 10px; display: flex; align-items: center; gap: 6px;
        }
        .stDownloadButton>button { background-color: #e67e22 !important; color: white !important; border-radius: 4px !important; border: none !important; font-weight: bold !important; padding: 6px 14px !important; font-size: 0.9rem !important; }
        .stSidebar .stButton>button { background-color: #c0392b !important; color: #ffffff !important; font-weight: bold !important; border: 1px solid #962d22 !important; border-radius: 6px !important; padding: 8px 12px !important; transition: all 0.2s ease !important; }
    </style>
""", unsafe_allow_html=True)

# --- 🔑 HAAMEEM BRANDED LOGIN SCREEN ---
if not st.session_state["logged_in"]:
    st.markdown("""
        <style>
            [data-testid="stHeader"], [data-testid="stSidebar"] { display: none !important; }
            .login-container { display: flex; flex-direction: row; background-color: #ffffff; border-radius: 12px; box-shadow: 0px 8px 24px rgba(0,0,0,0.12); overflow: hidden; margin-top: 5%; min-height: 480px; border: 1px solid #e2e8f0; }
            .left-banner { background: linear-gradient(135deg, #e67e22 0%, #d35400 100%); padding: 40px; color: #ffffff; flex: 1.1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; position: relative; }
            .left-banner h1 { color: #ffffff !important; font-family: 'Georgia', serif; font-weight: bold; font-size: 2.3rem; margin-bottom: 15px; letter-spacing: 1px; }
            .left-banner p { font-size: 1.05rem; opacity: 0.9; max-width: 360px; line-height: 1.5; }
            .right-form { flex: 1; padding: 45px; display: flex; flex-direction: column; justify-content: center; background-color: #ffffff; }
        </style>
    """, unsafe_allow_html=True)
    
    w1, w2, w3 = st.columns([1, 8, 1])
    with w2:
        st.markdown("""
            <div class="login-container">
                <div class="left-banner">
                    <div class="brand-logo-icon">✨📋</div>
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
            else: st.error("Invalid credentials.")
        st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()

# --- 📊 MASTER APP SECTION (AFTER LOGGED IN) ---
st.sidebar.markdown(f"<h3 style='color: #e67e22; font-weight: bold; margin-bottom:0px;'>👤 {st.session_state['username'].upper()}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"**Security Profile:** `{st.session_state['user_role']}`")
st.sidebar.markdown("---")

available_options = ["📊 Dashboard", "📝 Nayi Entry (Add)", "🔄 Update / Edit"]
if st.session_state["user_role"] == "Admin": available_options.append("👥 Manage Users / Accounts")
menu = st.sidebar.radio("Navigation Menu:", available_options)

# --- 📈 SIDEBAR GRAPH HISTORY FEATURE ---
st.sidebar.markdown("---")
st.sidebar.write("🔍 **Item Rate Analysis History Graph**")
all_items_saved = get_distinct_values("item_name", "shipment_items")
if all_items_saved:
    selected_graph_item = st.sidebar.selectbox("Select Item for Trend Line:", ["-- Select Item --"] + all_items_saved)
    if selected_graph_item != "-- Select Item --":
        graph_query = f"""
            SELECT s.file_no, i.unit_price, i.actual_costing 
            FROM shipment_items i 
            JOIN shipments s ON i.file_no = s.file_no 
            WHERE i.item_name='{selected_graph_item}'
        """
        try:
            df_graph = pd.read_sql(graph_query, conn)
            if not df_graph.empty:
                df_graph['Unit Price'] = pd.to_numeric(df_graph['unit_price'], errors='coerce')
                df_graph['Actual Costing (PKR)'] = pd.to_numeric(df_graph['actual_costing'], errors='coerce')
                df_graph = df_graph.dropna(subset=['Unit Price']).reset_index(drop=True)
                if not df_graph.empty:
                    st.sidebar.line_chart(df_graph[['Unit Price', 'Actual Costing (PKR)']])
        except: pass

st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
if st.sidebar.button("🚪 LOGOUT SYSTEM", use_container_width=True):
    st.session_state["logged_in"] = False; st.rerun()

BANKS = ["Bank Al Habib", "Habib Metro", "Meezan Bank"]
COMPANIES = ["Haa Meem Pvt Ltd", "Fine Trading Corporation", "Haa Meem AOP"]
CURRENCIES = ["USD", "CNY", "EUR", "PKR"]
UNITS = ["KG", "MT", "DRUMS", "BAGS"]
ROLES = ["Admin", "Manager", "Viewer"]

def parse_date(date_str):
    if not date_str or str(date_str).strip() in ["", "-", "Pending", "None", "nan"]: return None
    for fmt in ('%d-%b-%y', '%d-%b-%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try: return datetime.strptime(str(date_str).strip(), fmt)
        except: pass
    return None

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown('<div class="dashboard-header">📋 HAAMEEM - Logistics Master Dashboard</div>', unsafe_allow_html=True)
    
    if st.session_state["username"] == "zafar" or st.session_state["user_role"] == "Admin":
        allowed_display_cols = ALL_AVAILABLE_COLUMNS
    else:
        c.execute("SELECT allowed_columns FROM user_column_rights WHERE username=?", (st.session_state["username"],))
        rights_res = c.fetchone()
        allowed_display_cols = json.loads(rights_res[0]) if rights_res else ['Company Name', 'Bank Name', 'File No', 'Item Name', 'Status']

    try:
        query = '''
            SELECT 
                s.company_name AS [Company Name], s.bank_name AS [Bank Name], s.file_no AS [File No],
                s.indenter AS [Indenter], s.shipper AS [Supplier Name], i.item_name AS [Item Name],
                i.brand_name AS [Brand Name], i.hs_code AS [HS Code], i.qty AS [Quantity],
                i.unit AS [Unit], i.unit_price AS [Unit Price], i.actual_costing AS [Actual Costing (PKR)],
                s.fc_amount AS [Total LC Value], s.currency AS [Currency], s.shipment_type AS [Type],
                s.etd AS [ETD], s.eta AS [ETA], s.bl_no AS [BL / LC No], s.bank_docs AS [Bank Docs], s.remarks AS [Remarks]
            FROM shipments s
            LEFT JOIN shipment_items i ON s.file_no = i.file_no
        '''
        df = pd.read_sql(query, conn)
    except:
        df = pd.read_sql('SELECT * FROM shipments', conn)

    if not df.empty and 'Company Name' not in df.columns:
        cols_map = {'company_name': 'Company Name', 'bank_name': 'Bank Name', 'file_no': 'File No', 'indenter': 'Indenter', 'shipper': 'Supplier Name', 'items': 'Item Name', 'fc_amount': 'Total LC Value', 'currency': 'Currency', 'shipment_type': 'Type', 'etd': 'ETD', 'eta': 'ETA', 'bl_no': 'BL / LC No', 'bank_docs': 'Bank Docs', 'remarks': 'Remarks'}
        df.rename(columns={k: v for k, v in cols_map.items() if k in df.columns}, inplace=True)

    for col in ALL_AVAILABLE_COLUMNS:
        if col not in df.columns: df[col] = "-"

    if not df.empty:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Lists for side alert notifications
        all_live_alerts = []

        def calculated_status(row):
            f_no = str(row['File No']).strip()
            if f_no == "" or f_no == "-" or pd.isna(row['File No']) or f_no == "None": return "Query"
            
            etd_dt = parse_date(row['ETD'])
            text_eta = row.get('ETA', '-') if 'ETA' in row else '-'
            eta_dt = parse_date(text_eta)
            
            if etd_dt and etd_dt.year == today.year and etd_dt.month == today.month and etd_dt.day == today.day:
                all_live_alerts.append(f"🚢 File No: {f_no} — AAJ CHALEGA!")
            if eta_dt and eta_dt <= today and (today - eta_dt).days <= 6:
                all_live_alerts.append(f"⚓ File No: {f_no} — MAL PORT PE LAG GAYA HAI!")

            if eta_dt and (today - eta_dt).days >= 7: return "Complete"
            if eta_dt:
                if eta_dt <= today or (eta_dt > today and eta_dt <= today + timedelta(days=6)): return "Arrived"
                if eta_dt > today + timedelta(days=6): return "Shipment on way"
            if etd_dt:
                if etd_dt > today: return "Shipment not shipped"
                if etd_dt <= today: return "Shipped"
                
            return "LC Opening"

        df['Status'] = df.apply(calculated_status, axis=1)

        # 🌟 2. LEFT SIDE SIDEBAR ALERT CONFIGURATION (CLICK TO EXPAND)
        if all_live_alerts:
            with st.sidebar.expander("🔔 LIVE NOTIFICATIONS", expanded=True):
                for alert_msg in set(all_live_alerts):
                    st.warning(alert_msg)

        c_top1, c_top2 = st.columns([2, 5])
        with c_top1:
            st.markdown('<div class="custom-card"><div class="card-title">📥 System Backup</div>', unsafe_allow_html=True)
            safe_display_cols_clean = [c for c in allowed_display_cols if c in df.columns]
            safe_download_df = df[safe_display_cols_clean]
            # 🌟 NAME FIX: Arguments correct order mapped to resolve Python positional syntax error
            st.download_button(label="🟢 Download Excel Sheet", data=safe_download_df.to_csv(index=False).encode('utf-8'), file_name=f"Haameem_Master_{datetime.now().strftime('%Y-%m-%d')}.csv", mime="text/csv")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_top2:
            st.markdown('<div class="custom-card"><div class="card-title">🔍 Quick Filters Control</div>', unsafe_allow_html=True)
            f1, f2, f3 = st.columns(3)
            sel_comp = f1.multiselect("Import Entity:", COMPANIES)
            sel_bank = f2.multiselect("Opening Bank:", BANKS)
            search = f3.text_input("Global Search Keywords:", placeholder="Type to filter data...")
            st.markdown('</div>', unsafe_allow_html=True)

        if 'Company Name' in df.columns and sel_comp: df = df[df['Company Name'].isin(sel_comp)]
        if 'Bank Name' in df.columns and sel_bank: df = df[df['Bank Name'].isin(sel_bank)]
        if search: df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        display_cols = [c for c in allowed_display_cols if c in df.columns]
        df_display = df[display_cols]
        df_display.reset_index(drop=True, inplace=True)
        df_display.index = df_display.index + 1
        df_display.index.name = "S.No"

        # 🌟 5. RE-DESIGNED SOPHISTICATED MODERN PROFESSIONAL TABLE COLOR PALETTE
        def style_rows(row):
            color = ''
            if 'Status' in row.index:
                if row['Status'] == 'Arrived': color = 'background-color: #d1e7dd; color: #0f5132; font-weight: bold;' # Perfect Executive Soft Green
                elif row['Status'] == 'Complete': color = 'background-color: #f8f9fa; color: #6c757d; opacity: 0.8;' # Soft Muted Archive Gray
                elif row['Status'] == 'Query': color = 'background-color: #f8d7da; color: #842029; font-weight: bold;' # Warning Soft Red
                elif row['Status'] == 'Shipment on way': color = 'background-color: #fff3cd; color: #664d03;' # Attention Soft Gold/Yellow
                elif row['Status'] == 'Shipped': color = 'background-color: #cff4fc; color: #055160;' # Blue Transit
            return [color] * len(row)

        try:
            styled_df = df_display.style.apply(style_rows, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=False)
        except:
            st.dataframe(df_display, use_container_width=True, hide_index=False)
    else: st.info("System mein koi data majood nahi hai.")

# --- 2. NAYI ENTRY ---
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
        indenter = c1.selectbox("Indenter Name", [""] + past_indenters if past_indenters else [""]) if past_indenters else c1.text_input("Indenter")
        file_no = c2.text_input("File No (Unique)")
        shipper = c3.selectbox("Supplier Name (Shipper)", [""] + past_suppliers if past_suppliers else [""]) if past_suppliers else c3.text_input("Shipper")
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
            
            name = it1.selectbox(f"Item Name #{i}", [""] + past_items, key=f"add_item_name_drop_{i}")
            brand = it_b.text_input("Brand Name", key=f"add_brand_{i}")
            
            hs_suggestions = get_hs_codes_for_item(name) if name else []
            if hs_suggestions:
                hs_code = it_hs.selectbox("HS Code (Historic)", hs_suggestions, key=f"add_hs_drop_{i}")
            else:
                hs_code = it_hs.text_input("HS Code", key=f"add_hs_text_{i}")
                
            qty = it2.text_input("Qty", key=f"add_qty_{i}")
            unit = it3.selectbox("Unit", UNITS, key=f"add_unit_{i}")
            price = it4.text_input("Unit Price", key=f"add_price_{i}")
            costing = it5.text_input("Actual Costing", key=f"add_cost_{i}")
            
            if name: items_inputs.append((name, brand, hs_code, qty, unit, price, costing))
                
        st.markdown("---")
        d1, d2, d3, d4 = st.columns(4)
        etd = d1.text_input("ETD (e.g. 30-May-2026)")
        eta = d2.text_input("ETA")
        bl_no = d3.text_input("BL / LC No")
        bank_docs = d4.selectbox("Bank Docs", ["Pending", "OK"])
        remarks = st.text_area("Remarks")
        
        if st.form_submit_button("Save Shipment Master"):
            if not file_no: st.error("File No likhna zaroori hai!")
            else:
                try:
                    c.execute('''INSERT INTO shipments (company_name, bank_name, indenter, file_no, shipper, pi_no, fc_amount, currency, shipment_type, etd, eta, bl_no, bank_docs, remarks) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (company_name, bank_name, str(indenter), file_no, str(shipper), pi_no, fc_amount, currency, ship_type, etd, eta, bl_no, bank_docs, remarks))
                    for item in items_inputs:
                        c.execute('''INSERT INTO shipment_items (file_no, item_name, brand_name, hs_code, qty, unit, unit_price, actual_costing) VALUES (?,?,?,?,?,?,?,?)''', (file_no, item[0], item[1], str(item[2]), item[3], item[4], item[5], item[6]))
                    conn.commit()
                    st.success("✅ Shipment recorded securely!")
                    st.rerun()
                except Exception as e: st.error(f"Error: Save nahi ho saka. Details: {e}")

# --- 3. UPDATE / EDIT ---
elif menu == "🔄 Update / Edit" and st.session_state["user_role"] in ["Admin", "Manager"]:
    st.subheader("🔄 Update Master Logs & Costing Data")
    df_raw = pd.read_sql('SELECT * FROM shipments', conn)
    past_items = get_distinct_values("item_name", "shipment_items")
    
    if not df_raw.empty:
        file_to_update = st.selectbox("Select File No to Update:", df_raw['file_no'].tolist())
        row = df_raw[df_raw['file_no'] == file_to_update].iloc[0]
        df_ex_items = pd.read_sql(f"SELECT * FROM shipment_items WHERE file_no='{file_to_update}'", conn)
        
        with st.form(key=f"form_update_{file_to_update}"):
            u1, u2 = st.columns(2)
            def get_val(row_obj, keys_list, default=""):
                for k in keys_list:
                    if k in row_obj: return row_obj[k]
                return default

            comp_val = get_val(row, ['company_name', 'COMPANY_NAME'])
            bank_val = get_val(row, ['bank_name', 'BANK_NAME'])
            ind_val = get_val(row, ['indenter', 'INDENTER'])
            ship_val = get_val(row, ['shipper', 'SHIPPER'])
            amt_val = get_val(row, ['fc_amount', 'FC_AMOUNT'])
            curr_val = get_val(row, ['currency', 'CURRENCY'])
            type_val = get_val(row, ['shipment_type', 'SHIPMENT_TYPE'])
            etd_val = get_val(row, ['etd', 'ETD'])
            eta_val = get_val(row, ['eta', 'ETA'])
            bl_val = get_val(row, ['bl_no', 'BL__LC_NO', 'bl_no'])
            docs_val = get_val(row, ['bank_docs', 'BANK_DOCS'])
            rem_val = get_val(row, ['remarks', 'REMARKS'])

            u_comp = u1.selectbox("Company", COMPANIES, index=COMPANIES.index(comp_val) if comp_val in COMPANIES else 0)
            u_bank = u2.selectbox("Bank", BANKS, index=BANKS.index(bank_val) if bank_val in BANKS else 0)
            u_indenter = u1.text_input("Indenter", value=str(ind_val))
            u_shipper = u2.text_input("Shipper", value=str(ship_val))
            u_amount = u1.text_input("Total LC Amount", value=str(amt_val))
            u_curr = u2.selectbox("Currency", CURRENCIES, index=CURRENCIES.index(curr_val) if curr_val in CURRENCIES else 0)
            u_type = st.selectbox("Shipment Type", ["FCL", "LCL"], index=0 if type_val == "FCL" else 1)
            
            st.markdown("---")
            st.markdown("##### 🛒 Edit Items, Brand & Add Actual Costing Here")
            updated_items = []
            
            for idx in range(3):
                st.write(f"**Item Row #{idx+1}:**")
                it_col1, it_col_b, it_col_hs, it_col2, it_col3, it_col4, it_col5

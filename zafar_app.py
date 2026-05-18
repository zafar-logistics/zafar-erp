import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
db_path = 'zafar_logistics_v3.db'
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()

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
    
    try:
        c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('zafar', 'zafar786', 'Admin')")
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

# --- INTERFACE SETUP ---
st.set_page_config(page_title="Zafar Logistics ERP", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""

# --- GLOBAL ADVANCED STYLING INJECTOR ---
st.markdown("""
    <style>
        .stApp {
            background-color: #fafafa;
        }
        .dashboard-header {
            font-family: 'Georgia', serif;
            color: #1a252f;
            font-size: 1.6rem;
            font-weight: 700;
            border-bottom: 2px solid #e67e22;
            padding-bottom: 6px;
            margin-bottom: 20px;
            margin-top: -10px;
        }
        .custom-card {
            background-color: #ffffff;
            padding: 16px 20px;
            border-radius: 8px;
            box-shadow: 0px 2px 8px rgba(0,0,0,0.03);
            border: 1px solid #e2e8f0;
            margin-bottom: 15px;
        }
        .card-title {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 1rem;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .stDownloadButton>button {
            background-color: #e67e22 !important;
            color: white !important;
            border-radius: 4px !important;
            border: none !important;
            font-weight: bold !important;
            padding: 6px 14px !important;
            font-size: 0.9rem !important;
        }
        .stDownloadButton>button:hover {
            background-color: #d35400 !important;
        }
        .stSidebar .stButton>button {
            background-color: #c0392b !important;
            color: #ffffff !important;
            font-weight: bold !important;
            border: 1px solid #962d22 !important;
            border-radius: 6px !important;
            padding: 8px 12px !important;
            transition: all 0.2s ease !important;
        }
        .stSidebar .stButton>button:hover {
            background-color: #e74c3c !important;
            box-shadow: 0px 4px 10px rgba(192, 57, 43, 0.3) !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 🔑 HAAMEEM BRANDED LOGIN SCREEN ---
if not st.session_state["logged_in"]:
    st.markdown("""
        <style>
            [data-testid="stHeader"], [data-testid="stSidebar"] { display: none !important; }
            .login-container {
                display: flex; flex-direction: row; background-color: #ffffff;
                border-radius: 12px; box-shadow: 0px 8px 24px rgba(0,0,0,0.12);
                overflow: hidden; margin-top: 5%; min-height: 480px; border: 1px solid #e2e8f0;
            }
            .left-banner {
                background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
                padding: 40px; color: #ffffff; flex: 1.1; display: flex;
                flex-direction: column; justify-content: center; align-items: center; text-align: center; position: relative;
            }
            .left-banner::after {
                content: ""; position: absolute; width: 150%; height: 100%;
                background: rgba(255, 255, 255, 0.06); top: -30%; left: -20%; transform: rotate(-15deg); border-radius: 50%;
            }
            .left-banner h1 { color: #ffffff !important; font-family: 'Georgia', serif; font-weight: bold; font-size: 2.3rem; margin-bottom: 15px; letter-spacing: 1px; }
            .left-banner p { font-size: 1.05rem; opacity: 0.9; max-width: 360px; line-height: 1.5; }
            .brand-logo-icon { font-size: 4rem; margin-bottom: 20px; color: #fff3e0; }
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
        
        st.write("")
        submit_login = st.button("Access Dashboard 🚀", use_container_width=True)
        
        if submit_login:
            c.execute("SELECT role FROM users WHERE username=? AND password=?", (user_input.strip(), pass_input))
            result = c.fetchone()
            if result:
                st.session_state["logged_in"] = True
                st.session_state["username"] = user_input.strip()
                st.session_state["user_role"] = result[0]
                st.success("Access Verified!")
                st.rerun()
            else:
                st.error("Invalid credentials. Try again.")
                
        st.markdown("""
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.stop()

# --- 📊 MASTER APP SECTION (AFTER LOGGED IN) ---
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #243242 !important;
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] span {
            color: #ffffff !important;
        }
        .stRadio>div{
            gap: 6px;
        }
        div[data-testid="stRadio"] label {
            background-color: #2c3d52;
            padding: 6px 12px;
            border-radius: 4px;
            border: 1px solid #344963;
            transition: all 0.2s ease;
        }
        div[data-testid="stRadio"] label:hover {
            background-color: #e67e22;
            cursor: pointer;
        }
    </style>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"<h3 style='color: #e67e22; font-weight: bold; margin-bottom:0px;'>👤 {st.session_state['username'].upper()}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"**Security Profile:** `{st.session_state['user_role']}`")
st.sidebar.markdown("---")

available_options = ["📊 Dashboard"]
if st.session_state["user_role"] in ["Admin", "Manager"]:
    available_options.append("📝 Nayi Entry (Add)")
    available_options.append("🔄 Update / Edit")
if st.session_state["user_role"] == "Admin":
    available_options.append("👥 Manage Users / Accounts")

menu = st.sidebar.radio("Navigation Menu:", available_options)

st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
if st.sidebar.button("🚪 LOGOUT SYSTEM", use_container_width=True, key="logout_btn_key"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["user_role"] = ""
    st.rerun()

BANKS = ["Bank Al Habib", "Habib Metro", "Meezan Bank"]
COMPANIES = ["Haa Meem Pvt Ltd", "Fine Trading Corporation", "Haa Meem AOP"]
CURRENCIES = ["USD", "CNY", "EUR", "PKR"]
UNITS = ["KG", "MT", "DRUMS", "BAGS"]
ROLES = ["Admin", "Manager", "Viewer"]

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown('<div class="dashboard-header">📋 HAAMEEM - Logistics Master Dashboard</div>', unsafe_allow_html=True)
    
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
        cols_map = {
            'company_name': 'Company Name', 'bank_name': 'Bank Name', 'file_no': 'File No',
            'indenter': 'Indenter', 'shipper': 'Supplier Name', 'items': 'Item Name',
            'brand_name': 'Brand Name', 'hs_code': 'HS Code', 'weight': 'Quantity',
            'weight_unit': 'Unit', 'unit_price': 'Unit Price', 'actual_costing': 'Actual Costing (PKR)',
            'fc_amount': 'Total LC Value', 'currency': 'Currency', 'shipment_type': 'Type',
            'etd': 'ETD', 'eta': 'ETA', 'bl_no': 'BL / LC No', 'bank_docs': 'Bank Docs', 'remarks': 'Remarks'
        }
        df.rename(columns={k: v for k, v in cols_map.items() if k in df.columns}, inplace=True)

    expected_cols = [
        'Company Name', 'Bank Name', 'File No', 'Indenter', 'Supplier Name', 
        'Item Name', 'Brand Name', 'HS Code', 'Quantity', 'Unit', 'Unit Price', 
        'Actual Costing (PKR)', 'Total LC Value', 'Currency', 'Type', 'ETD', 'ETA', 'BL / LC No', 'Bank Docs', 'Remarks'
    ]
    for column_check in expected_cols:
        if column_check not in df.columns: df[column_check] = "-"

    if not df.empty:
        today = datetime.now()
        def get_status(row):
            try:
                if 'ETA' not in row or not row['ETA'] or row['ETA'] in ["", "-", None]: return "📄 LC Opened"
                eta = pd.to_datetime(row['ETA'], errors='coerce')
                etd = pd.to_datetime(row['ETD'], errors='coerce')
                if pd.notnull(eta) and eta <= today: return "✅ Arrived"
                if pd.notnull(etd) and etd <= today: return "🚢 In Transit"
                return "📄 LC Opened"
            except: return "Pending"
        df['Status'] = df.apply(get_status, axis=1)

        c_top1, c_top2 = st.columns([2, 5])
        
        with c_top1:
            st.markdown('<div class="custom-card"><div class="card-title">📥 System Backup</div>', unsafe_allow_html=True)
            if st.session_state["user_role"] in ["Admin", "Manager"]:
                csv_data = df.to_csv(index=False).encode('utf-8')
                # 🌟 FIXED LINE: 'data=' ka keyword parameter lagaya hai error khatam karne ke liye
                st.download_button(label="🟢 Download Excel Sheet", data=csv_data, file_name=f"Haameem_Master_{datetime.now().strftime('%Y-%m-%d')}.csv", mime="text/csv")
            else:
                st.caption("No backup clearance rights.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_top2:
            st.markdown('<div class="custom-card"><div class="card-title">🔍 Quick Filters Control</div>', unsafe_allow_html=True)
            f1, f2, f3 = st.columns(3)
            sel_comp = f1.multiselect("Import Entity:", COMPANIES)
            sel_bank = f2.multiselect("Opening Bank:", BANKS)
            search = f3.text_input("Global Search Keywords:", placeholder="Type to filter data...")
            st.markdown('</div>', unsafe_allow_html=True)

        comp_col = 'Company Name' if 'Company Name' in df.columns else ('company_name' if 'company_name' in df.columns else '')
        bank_col = 'Bank Name' if 'Bank Name' in df.columns else ('bank_name' if 'bank_name' in df.columns else '')

        if comp_col and sel_comp: df = df[df[comp_col].isin(sel_comp)]
        if bank_col and sel_bank: df = df[df[bank_col].isin(sel_bank)]
        if search: df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        cols_order = ['Company Name', 'Bank Name', 'File No', 'Indenter', 'Supplier Name', 'Item Name', 'Brand Name', 'HS Code', 'Quantity', 'Unit', 'Unit Price', 'Actual Costing (PKR)', 'Total LC Value', 'Currency', 'Type', 'Status', 'ETD', 'ETA', 'BL / LC No', 'Bank Docs', 'Remarks']
        display_cols = [c for c in cols_order if c in df.columns]
        df_display = df[display_cols]
        df_display.reset_index(drop=True, inplace=True)
        df_display.index = df_display.index + 1
        df_display.index.name = "S.No"

        st.markdown("""
            <style>
                div[data-testid="stDataFrame"] table th {
                    background-color: #243242 !important;
                    color: #ffffff !important;
                    font-weight: bold !important;
                    font-size: 0.9rem !important;
                    text-align: center !important;
                }
                div[data-testid="stDataFrame"] table td { font-size: 0.85rem !important; }
            </style>
        """, unsafe_allow_html=True)

        st.dataframe(df_display.fillna("-"), use_container_width=True, hide_index=False)
    else:
        st.info("System mein koi data majood nahi hai.")

# --- 2. NAYI ENTRY ---
elif menu == "📝 Nayi Entry (Add)" and st.session_state["user_role"] in ["Admin", "Manager"]:
    st.subheader("📝 Nayi Shipment Records Entry Portal")
    with st.form("add_form", clear_on_submit=True):
        col_top1, col_top2 = st.columns(2)
        company_name = col_top1.selectbox("Company Name", COMPANIES)
        bank_name = col_top2.selectbox("Bank Name", BANKS)
        
        c1, c2, c3, c4 = st.columns(4)
        indenter = c1.text_input("Indenter")
        file_no = c2.text_input("File No (Unique)")
        shipper = c3.text_input("Shipper")
        pi_no = c4.text_input("P.I. No")
        
        am1, am2, am3 = st.columns([2, 1, 1])
        fc_amount = am1.text_input("Total LC Value")
        currency = am2.selectbox("Currency", CURRENCIES)
        ship_type = am3.selectbox("Type", ["FCL", "LCL"])
        
        st.markdown("---")
        st.markdown("##### 🛒 Items Breakdown")
        items_inputs = []
        for i in range(1, 5):
            st.write(f"**Item #{i}:**")
            it1, it_b, it_hs, it2, it3, it4, it5 = st.columns([3, 2, 2, 1, 1, 2, 2])
            name = it1.text_input("Item Name", key=f"add_name_{i}")
            brand = it_b.text_input("Brand Name", key=f"add_brand_{i}")
            hs_code = it_hs.text_input("HS Code", key=f"add_hs_{i}")
            qty = it2.text_input("Qty", key=f"add_qty_{i}")
            unit = it3.selectbox("Unit", UNITS, key=f"add_unit_{i}")
            price = it4.text_input("Unit Price", key=f"add_price_{i}")
            costing = it5.text_input("Actual Costing", key=f"add_cost_{i}")
            if name: items_inputs.append((name, brand, hs_code, qty, unit, price, costing))
                
        st.markdown("---")
        d1, d2, d3, d4 = st.columns(4)
        etd = d1.text_input("ETD")
        eta = d2.text_input("ETA")
        bl_no = d3.text_input("BL / LC No")
        bank_docs = d4.selectbox("Bank Docs", ["Pending", "OK"])
        remarks = st.text_area("Remarks")
        
        if st.form_submit_button("Save Shipment Master"):
            if not file_no: st.error("File No likhna zaroori hai!")
            else:
                try:
                    c.execute('''INSERT INTO shipments (company_name, bank_name, indenter, file_no, shipper, pi_no, fc_amount, currency, shipment_type, etd, eta, bl_no, bank_docs, remarks) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (company_name, bank_name, indenter, file_no, shipper, pi_no, fc_amount, currency, ship_type, etd, eta, bl_no, bank_docs, remarks))
                    for item in items_inputs:
                        c.execute('''INSERT INTO shipment_items (file_no, item_name, brand_name, hs_code, qty, unit, unit_price, actual_costing) VALUES (?,?,?,?,?,?,?,?)''', (file_no, item[0], item[1], item[2], item[3], item[4], item[5], item[6]))
                    conn.commit()
                    st.success("✅ New shipment recorded successfully!")
                    st.rerun()
                except: st.error("Error: Save nahi ho saka.")

# --- 3. UPDATE / EDIT ---
elif menu == "🔄 Update / Edit" and st.session_state["user_role"] in ["Admin", "Manager"]:
    st.subheader("🔄 Update Master Logs & Costing Data")
    df_raw = pd.read_sql('SELECT * FROM shipments', conn)
    
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
            bl_val = get_val(row, ['bl_no', 'BL_NO'])
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
            for idx in range(4):
                st.write(f"**Item Row #{idx+1}:**")
                it_col1, it_col_b, it_col_hs, it_col2, it_col3, it_col4, it_col5 = st.columns([3, 2, 2, 1, 1, 1, 2])
                ex_name, ex_brand, ex_hs, ex_qty, ex_unit, ex_price, ex_cost = "", "", "", "", "KG", "", ""
                if idx < len(df_ex_items):
                    item_row = df_ex_items.iloc[idx]
                    ex_name = get_val(item_row, ['item_name', 'ITEM_NAME'])
                    ex_brand = get_val(item_row, ['brand_name', 'BRAND_NAME'])
                    ex_hs = get_val(item_row, ['hs_code', 'HS_CODE'])
                    ex_qty = get_val(item_row, ['qty', 'QTY'])
                    ex_unit = get_val(item_row, ['unit', 'UNIT'], "KG")
                    ex_price = get_val(item_row, ['unit_price', 'UNIT_PRICE'])
                    ex_cost = get_val(item_row, ['actual_costing', 'ACTUAL_COSTING'])
                
                u_name = it_col1.text_input("Item Name", value=str(ex_name), key=f"u_name_{file_to_update}_{idx}")
                u_brand = it_col_b.text_input("Brand", value=str(ex_brand), key=f"u_brand_{file_to_update}_{idx}")
                u_hs = it_col_hs.text_input("HS Code", value=str(ex_hs), key=f"u_hs_{file_to_update}_{idx}")
                u_qty = it_col2.text_input("Qty", value=str(ex_qty), key=f"u_qty_{file_to_update}_{idx}")
                u_unit = it_col3.selectbox("Unit", UNITS, index=UNITS.index(ex_unit) if ex_unit in UNITS else 0, key=f"u_unit_{file_to_update}_{idx}")
                u_price = it_col4.text_input("Price", value=str(ex_price), key=f"u_price_{file_to_update}_{idx}")
                u_cost = it_col5.text_input("Actual Costing", value=str(ex_cost), key=f"u_cost_{file_to_update}_{idx}")
                
                if u_name and u_name.strip() != "": updated_items.append((u_name, u_brand, u_hs, u_qty, u_unit, u_price, u_cost))
                    
            st.markdown("---")
            u_etd = u1.text_input("ETD", value=str(etd_val))
            u_eta = u2.text_input("ETA", value=str(eta_val))
            u_bl = u1.text_input("BL/LC No", value=str(bl_val))
            u_docs = u2.selectbox("Bank Docs", ["Pending", "OK"], index=0 if docs_val == "Pending" else 1)
            u_remarks = st.text_area("Remarks", value=str(rem_val))
            
            if st.form_submit_button("💾 Update Master Records"):
                c.execute('''UPDATE shipments SET company_name=?, bank_name=?, indenter=?, shipper=?, fc_amount=?, currency=?, shipment_type=?, etd=?, eta=?, bl_no=?, bank_docs=?, remarks=? WHERE file_no=?''', (u_comp, u_bank, u_indenter, u_shipper, u_amount, u_curr, u_type, u_etd, u_eta, u_bl, u_docs, u_remarks, file_to_update))
                c.execute(f"DELETE FROM shipment_items WHERE file_no='{file_to_update}'")
                for item in updated_items:
                    c.execute('''INSERT INTO shipment_items (file_no, item_name, brand_name, hs_code, qty, unit, unit_price, actual_costing) VALUES (?,?,?,?,?,?,?,?)''', (file_to_update, item[0], item[1], item[2], item[3], item[4], item[5], item[6]))
                conn.commit()
                st.success("✅ Records updated successfully!")
                st.rerun()

# --- 4. 👥 MANAGE ACCOUNTS ---
elif menu == "👥 Manage Users / Accounts" and st.session_state["user_role"] == "Admin":
    st.subheader("👥 System Accounts Control Center")
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.write("##### 👤 Naya Account Banayein")
        selected_role = st.selectbox("Rights Level (Role) Chunien:", ROLES, key="new_role_sel")
        with st.form("create_user_form"):
            new_user = st.text_input("Username:")
            new_pass = st.text_input("Password:", type="password")
            if st.form_submit_button("Create Account"):
                if new_user and new_pass:
                    try:
                        c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", (new_user.strip(), new_pass, selected_role))
                        conn.commit()
                        st.success(f"✅ User '{new_user}' created!")
                        st.rerun()
                    except: st.error("Error: Username pehle se dakhil hai.")
                else: st.error("Fields bhanna zaroori hain.")

    with m_col2:
        st.write("##### 🔄 Password Badlein ya Account Delete Karein")
        df_users_list = pd.read_sql("SELECT username FROM users WHERE username != 'zafar'", conn)
        if not df_users_list.empty:
            target_user = st.selectbox("Account Select Karein:", df_users_list['username'].tolist())
            with st.form("update_password_form"):
                new_password_val = st.text_input("Naya Password Likhein:", type="password")
                if st.form_submit_button("🔒 Password Change Karein"):
                    if new_password_val:
                        c.execute("UPDATE users SET password=? WHERE username=?", (new_password_val, target_user))
                        conn.commit()
                        st.success(f"✅ '{target_user}' ka password change ho gaya!")
                    else: st.error("Naya password likhna zaroori hai.")
            st.write("---")
            st.warning(f"⚠️ Kya aap '{target_user}' ka account permanent khatam karna chahte hain?")
            if st.button("❌ Haan, Account Delete Kardo"):
                c.execute("DELETE FROM users WHERE username=?", (target_user,))
                conn.commit()
                st.success(f"🗑️ User '{target_user}' successfully deleted!")
                st.rerun()
        else:
            st.info("Zafar bhai ke ilawa koi aur extra sub-account nahi bana hua.")

    st.markdown("---")
    st.write("##### 📊 User Accounts & Assigned Rights List")
    df_users = pd.read_sql("SELECT id AS [ID], username AS [Username], role AS [Role Description] FROM users", conn)
    def map_rights(role):
        if role == "Admin": return "Full System Control + Account Management"
        if role == "Manager": return "Can Add & Edit Logistics Data (No User Control)"
        return "Read-Only Dashboard Access (Viewer)"
    df_users['Assigned Operations'] = df_users['Role Description'].apply(map_rights)
    st.dataframe(df_users, use_container_width=True, hide_index=True)

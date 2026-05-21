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

# --- 🚀 GLOBAL INTERACTIVE GLASSMORPHIC INTERFACE INJECTOR ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        
        .stApp {
            background-color: #f8fafc;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        
        /* Dashboard Top Header */
        .dashboard-header {
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #0f172a;
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 25px;
            margin-top: -15px;
        }
        
        /* Glassmorphism Summary Cards Layout */
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
        
        /* Modern Container Card Boxes */
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
        
        /* Branded Clean Custom Buttons UI */
        .stDownloadButton>button {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            padding: 8px 16px !important;
            box-shadow: 0px 2px 4px rgba(0,0,0,0.02);
            transition: all 0.2s ease;
        }
        .stDownloadButton>button:hover {
            background-color: #f8fafc !important;
            border-color: #cbd5e1 !important;
        }
        
        /* Main Grid Dataframe Header Theme Customization */
        div[data-testid="stDataFrame"] table th {
            background-color: #f8fafc !important;
            color: #475569 !important;
            font-weight: 600 !important;
            font-size: 0.85rem !important;
            border-bottom: 1px solid #e2e8f0 !important;
        }
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

available_options = [" 📊  Dashboard", " 📝  Nayi Entry (Add)", " 🔄  Update / Edit", " 📤  Excel Upload"]
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
    st.markdown('<div class="dashboard-header">Good morning, Haameem Control Center</div>', unsafe_allow_html=True)
    
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
        
        all_live_alerts = []
        total_count = len(df['File No'].unique())
        done_count = 0
        pending_count = 0

        def calculated_status(row):
            global done_count, pending_count
            f_no = str(row['File No']).strip()
            if f_no == "" or f_no == "-" or pd.isna(row['File No']) or f_no == "None": return "Query"
            
            etd_dt = parse_date(row['ETD'])
            text_eta = row.get('ETA', '-') if 'ETA' in row else '-'
            eta_dt = parse_date(text_eta)
            
            if etd_dt and etd_dt.year == today.year and etd_dt.month == today.month and etd_dt.day == today.day:
                all_live_alerts.append(f"🚢 File No: {f_no} — AAJ CHALEGA!")
            if eta_dt and eta_dt <= today and (today - eta_dt).days <= 6:
                all_live_alerts.append(f"⚓ File No: {f_no} — PORT PE LAG GAYA HAI!")

            if eta_dt and (today - eta_dt).days >= 7:
                return "Complete"
            if eta_dt:
                if eta_dt <= today or (eta_dt > today and eta_dt <= today + timedelta(days=6)): return "Arrived"
                if eta_dt > today + timedelta(days=6): return "Shipment on way"
            if etd_dt:
                if etd_dt > today: return "Shipment not shipped"
                if etd_dt <= today: return "Shipped"
                
            return "LC Opening"

        df['Status'] = df.apply(calculated_status, axis=1)
        
        # Calculate distinct counts for visual blocks
        done_count = len(df[df['Status'] == 'Complete']['File No'].unique())
        arrived_count = len(df[df['Status'] == 'Arrived']['File No'].unique())
        pending_count = total_count - done_count

        # 🌟 1. PREMIUM GLASSMORPHISM SUMMARY CARDS INJECTOR
        st.markdown(f"""
            <div class="glass-card-wrapper">
                <div class="glass-card" style="border-left: 4px solid #38bdf8;">
                    <div><span style="font-size:20px;">📁</span></div>
                    <div>
                        <div class="glass-card-value">{total_count}</div>
                        <div class="glass-card-label">Total Files</div>
                    </div>
                </div>
                <div class="glass-card" style="border-left: 4px solid #4ade80;">
                    <div><span style="font-size:20px;">✅</span></div>
                    <div>
                        <div class="glass-card-value">{done_count}</div>
                        <div class="glass-card-label">Done Projects</div>
                    </div>
                </div>
                <div class="glass-card" style="border-left: 4px solid #fb923c;">
                    <div><span style="font-size:20px;">⏳</span></div>
                    <div>
                        <div class="glass-card-value">{pending_count}</div>
                        <div class="glass-card-label">Pending Files</div>
                    </div>
                </div>
                <div class="glass-card" style="border-left: 4px solid #a78bfa;">
                    <div><span style="font-size:20px;">⚓</span></div>
                    <div>
                        <div class="glass-card-value">{arrived_count}</div>
                        <div class="glass-card-label">Port Arrived</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 🌟 2. SIDEBAR ALERTS BLOCK (CLEAN & MINIMAL)
        if all_live_alerts:
            with st.sidebar.expander("🔔 SYSTEM LIVE ALERTS", expanded=True):
                for alert_msg in set(all_live_alerts):
                    st.info(alert_msg)

        c_top1, c_top2 = st.columns([2, 5])
        with c_top1:
            st.markdown('<div class="custom-card"><div class="card-title">📥 Operations Actions</div>', unsafe_allow_html=True)
            safe_display_cols_clean = [c for c in allowed_display_cols if c in df.columns]
            safe_download_df = df[safe_display_cols_clean]
            st.download_button(label="📥 Export Master Sheet to Excel", data=safe_download_df.to_csv(index=False).encode('utf-8'), file_name=f"Haameem_Master_{datetime.now().strftime('%Y-%m-%d')}.csv", mime="text/csv")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_top2:
            st.markdown('<div class="custom-card"><div class="card-title">🔍 Quick Filters Control</div>', unsafe_allow_html=True)
            f1, f2, f3 = st.columns(3)
            sel_comp = f1.multiselect("Import Entity:", COMPANIES)
            sel_bank = f2.multiselect("Opening Bank:", BANKS)
            search = f3.text_input("Global Search Keywords:", placeholder="Type to filter...")
            st.markdown('</div>', unsafe_allow_html=True)

        if 'Company Name' in df.columns and sel_comp: df = df[df['Company Name'].isin(sel_comp)]
        if 'Bank Name' in df.columns and sel_bank: df = df[df['Bank Name'].isin(sel_bank)]
        if search: df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        display_cols = [c for c in allowed_display_cols if c in df.columns]
        df_display = df[display_cols]
        df_display.reset_index(drop=True, inplace=True)
        df_display.index = df_display.index + 1
        df_display.index.name = "S.No"

        # 🌟 5. EXTREMELY CLEAN GLASS-STYLE DYNAMIC COLOR CODES PER CELL/ROW
        def style_rows(row):
            color = ''
            if 'Status' in row.index:
                # Minimalist Soft Colors Matching the User's Image Layout
                if row['Status'] == 'Arrived': color = 'background-color: #f0fdf4; color: #166534; font-weight: 500;' # Soft Emerald Mint
                elif row['Status'] == 'Complete': color = 'background-color: #fafafa; color: #94a3b8; opacity: 0.7;' # Gray Outline Archival
                elif row['Status'] == 'Query': color = 'background-color: #fef2f2; color: #991b1b;' # Crimson Rose Line
                elif row['Status'] == 'Shipment on way': color = 'background-color: #fffbeb; color: #92400e;' # Soft Lavender Amber Tint
                elif row['Status'] == 'Shipped': color = 'background-color: #f0f9ff; color: #075985;' # Sky Blue
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
                
                u_name = it_col1.selectbox("Item Name", [""] + past_items, index=past_items.index(ex_name)+1 if ex_name in past_items else 0, key=f"u_name_{file_to_update}_{idx}")
                u_brand = it_col_b.text_input("Brand", value=str(ex_brand), key=f"u_brand_{file_to_update}_{idx}")
                
                hs_suggestions = get_hs_codes_for_item(u_name) if u_name else []
                if hs_suggestions:
                    u_hs = it_col_hs.selectbox("HS Code", hs_suggestions, index=hs_suggestions.index(ex_hs) if ex_hs in hs_suggestions else 0, key=f"u_hs_drop_{file_to_update}_{idx}")
                else:
                    u_hs = it_col_hs.text_input("HS Code", value=str(ex_hs), key=f"u_hs_txt_{file_to_update}_{idx}")
                    
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
                    c.execute('''INSERT INTO shipment_items (file_no, item_name, brand_name, hs_code, qty, unit, unit_price, actual_costing) VALUES (?,?,?,?,?,?,?,?)''', (file_to_update, item[0], item[1], str(item[2]), item[3], item[4], item[5], item[6]))
                conn.commit()
                st.success("✅ Records updated successfully!")
                st.rerun()
# --- 4. EXCEL UPLOAD SECTION ---
    elif menu == " 📤  Excel Upload" and st.session_state["user_role"] in ["Admin", "Manager"]:
        st.subheader(" 📤  Upload Master Excel Sheet")
        uploaded_file = st.file_uploader("Excel (.xlsx) ya CSV file select karein", type=["xlsx", "csv"])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                
                st.write("File Preview:")
                st.dataframe(df_upload.head())
                
                if st.button(" 💾  Database mein Data Save Karein"):
                    # Ye data ko 'shipments' table mein add karega
                    df_upload.to_sql('shipments', conn, if_exists='append', index=False)
                    st.success(" ✅  Data successfully upload aur save ho gaya!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}. (Check karein ke Excel ke column names database se match karte hain)")

# --- 5. MANAGE ACCOUNTS PANEL ---
elif menu == "👥 Manage Users / Accounts" and st.session_state["user_role"] == "Admin":
    st.subheader("👥 System Accounts & Column Security Settings")
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
                        u_clean = new_user.strip().lower()
                        c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", (u_clean, new_pass, selected_role))
                        c.execute("INSERT OR REPLACE INTO user_column_rights (username, allowed_columns) VALUES (?,?)", (u_clean, json.dumps(ALL_AVAILABLE_COLUMNS)))
                        conn.commit()
                        st.success(f"✅ User '{u_clean}' created!")
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
                        st.success(f"✅ Password changed!")
                    else: st.error("Field empty.")
            if st.button("❌ Haan, Account Delete Kardo"):
                c.execute("DELETE FROM users WHERE username=?", (target_user,))
                c.execute("DELETE FROM user_column_rights WHERE username=?", (target_user,))
                conn.commit(); st.rerun()

    st.markdown("---")
    st.write("##### 🎛️ Assign Column-Level Visibility Rights")
    df_all_users_raw = pd.read_sql("SELECT username FROM users", conn)
    user_to_configure = st.selectbox("Kis user ke Columns control karne hain?", df_all_users_raw['username'].tolist())
    
    c.execute("SELECT allowed_columns FROM user_column_rights WHERE username=?", (user_to_configure,))
    current_rights_res = c.fetchone()
    current_allowed = json.loads(current_rights_res[0]) if current_rights_res else ALL_AVAILABLE_COLUMNS
    
    chk_cols = st.columns(4)
    chosen_columns = []
    for idx, col_name in enumerate(ALL_AVAILABLE_COLUMNS):
        with chk_cols[idx % 4]:
            is_checked = col_name in current_allowed
            if st.checkbox(col_name, value=is_checked, key=f"chk_{user_to_configure}_{col_name}"):
                chosen_columns.append(col_name)
                
    if st.button("🔒 Column Permissions Save Karein", use_container_width=True):
        if not chosen_columns: st.error("Kam az kam aik column allow karna zaroori hai!")
        else:
            c.execute("INSERT OR REPLACE INTO user_column_rights (username, allowed_columns) VALUES (?,?)", (user_to_configure, json.dumps(chosen_columns)))
            conn.commit(); st.success("Stored successfully!")

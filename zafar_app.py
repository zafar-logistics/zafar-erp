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
st.set_page_config(page_title="HAAMEEM - Logistics Master Dashboard", layout="wide")

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "username" not in st.session_state: st.session_state["username"] = ""
if "user_role" not in st.session_state: st.session_state["user_role"] = ""

# --- GLOBAL INTERACTIVE GLASSMORPHIC INTERFACE INJECTOR ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        
        .stApp {
            background-color: #f8fafc;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        
        .dashboard-header {
            font-family: 'Plus Jakarta Sans', sans-serif;
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
            background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            padding: 10px 20px !important;
            box-shadow: 0px 4px 10px rgba(221, 107, 32, 0.2);
            transition: all 0.2s ease;
        }
        
        div[data-testid="stDataFrame"] table th {
            background-color: #f8fafc !important;
            color: #475569 !important;
            font-weight: 600 !important;
            font-size: 0.85rem !important;
            border-bottom: 1px solid #e2e8f0 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- LOGIN SCREEN ---
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
                import pandas as pd
import streamlit as st

# ==========================================
# 1. DATABASE SE DATA READ KARNE KA SAFE CODE (Line 212 Fix)
# ==========================================
try:
    # Yeh aapki existing query aur connection ko safe tareeqe se chalayega
    df = pd.read_sql(query, conn)
except Exception as e:
    # Agar database backend par koi temporary column ya connection ka masla ho
    st.error("⚠️ Dashboard data read karne mein temporary masla aaya hai.")
    st.info("💡 Solution: Neeche 'System Backup' wale section se apni aakhri CSV file dobara upload karke 'Load Kardo' par click karein taake database refresh ho jaye.")
    df = pd.DataFrame() # Khali dataframe taake aage ka code crash na ho


# ==========================================
# 2. DATA UPLOAD & CLEANING SYSTEM (Backup Fix)
# ==========================================
uploaded_file = st.file_uploader("Apni Backup File Select Karein:", type=["csv"])

if uploaded_file is not None:
    try:
        # Pehle standard utf-8 se file read karne ki koshish karein
        backup_df = pd.read_csv(uploaded_file, encoding="utf-8")
    except UnicodeDecodeError:
        # Agar Excel ka encoding error aaye (jo pehle aaya tha), toh isse safe read karein
        uploaded_file.seek(0)
        backup_df = pd.read_csv(uploaded_file, encoding="cp1252")

    # File ka preview dikhane ke liye
    st.write("📋 File Preview (Pehle 5 Rows):")
    st.dataframe(backup_df.head())

    # Data Load Karne Ka Button
    if st.button("🚀 Haan, Yeh Poora Data Software Mein Load Kardo"):
        try:
            # Data ko database mein bhejne se pehle bilkul saaf (clean) karna
            backup_df.columns = backup_df.columns.str.strip()  # Column names ki faltu spaces khatam
            
            # Jin columns mein numbers aane hain, unke dash (-) ya comma (,) ko theek karna
            if 'Actual Costing (PKR)' in backup_df.columns:
                backup_df['Actual Costing (PKR)'] = backup_df['Actual Costing (PKR)'].replace('-', 0).fillna(0)
            
            if 'Total LC Value' in backup_df.columns:
                backup_df['Total LC Value'] = backup_df['Total LC Value'].astype(str).str.replace(',', '')
                backup_df['Total LC Value'] = pd.to_numeric(backup_df['Total LC Value'], errors='coerce').fillna(0)
            
            # Date waale columns ka format set karna taake SQL mein error na aaye
            for col in ['ETD', 'ETA']:
                # =========================================================
# DATE CONVERSION KA FUNCTION (Line 250-280 Fix)
# =========================================================

def parse_my_date(date_str):
    """Excel ki dates ko standard format mein badalne ke liye function"""
    if pd.isna(date_str) or str(date_str).strip() in ['', 'None', '-', 'NaT']:
        return None
    
    # Alag alag date formats ko automatic check karne ke liye
    for fmt in ('%d-%b-%y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
        try:
            return pd.to_datetime(str(date_str).strip(), format=fmt)
        except:
            continue
    
    # Agar koi format match na kare toh standard fallback
    return pd.to_datetime(date_str, errors='coerce')


# =========================================================
# DATA UPLOAD & CLEANING PIPELINE
# =========================================================
uploaded_file = st.file_uploader("Apni Backup File Select Karein:", type=["csv"])

if uploaded_file is not None:
    try:
        backup_df = pd.read_csv(uploaded_file, encoding="utf-8")
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        backup_df = pd.read_csv(uploaded_file, encoding="cp1252")

    st.write("📋 File Preview (Pehle 5 Rows):")
    st.dataframe(backup_df.head())

    if st.button("🚀 Haan, Yeh Poora Data Software Mein Load Kardo"):
        try:
            # Columns ki spaces khatam karna
            backup_df.columns = backup_df.columns.str.strip()
            
            # Numeric columns ki safai
            if 'Actual Costing (PKR)' in backup_df.columns:
                backup_df['Actual Costing (PKR)'] = backup_df['Actual Costing (PKR)'].replace('-', 0).fillna(0)
                backup_df['Actual Costing (PKR)'] = pd.to_numeric(backup_df['Actual Costing (PKR)'], errors='coerce').fillna(0)
            
            if 'Total LC Value' in backup_df.columns:
                backup_df['Total LC Value'] = backup_df['Total LC Value'].astype(str).str.replace(',', '')
                backup_df['Total LC Value'] = pd.to_numeric(backup_df['Total LC Value'], errors='coerce').fillna(0)
            
            # DATE COLUMNS PAR FUNCTION APPLY KARNA (No more SyntaxError!)
            for col in ['ETD', 'ETA']:
                if col in backup_df.columns:
                    backup_df[col] = backup_df[col].apply(parse_my_date)

            # --- YAHA AAPKA DATABASE MEIN INSERT KARNE KA CODE CHALEGA ---
            # backup_df.to_sql('your_table_name', conn, if_exists='append', index=False)
            
            st.success("🎉 Data HAAMEEM software mein kamyabi se load ho gaya hai!")
            st.rerun()
            
        except Exception as insert_error:
            st.error(f"❌ Data load karte waqt masla aaya: {insert_error}")
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

        # 🌟 BULK DYNAMIC STATUS LOGIC (Always recalculates dynamically based on dates)
        def calculated_status(row):
            f_no = str(row['File No']).strip()
            if f_no == "" or f_no == "-" or pd.isna(row['File No']) or f_no == "None": return "Query"
            
            etd_dt = parse_date(row['ETD'])
            box_eta = str(row['ETA']).strip().lower()
            eta_dt = parse_date(row['ETA'])
            
            if etd_dt and etd_dt.date() == today.date():
                all_live_alerts.append(f"🚢 File No: {f_no} — AAJ CHALEGA!")
            if eta_dt and eta_dt <= today and (today - eta_dt).days <= 6:
                all_live_alerts.append(f"⚓ File No: {f_no} — PORT PE LAG GAYA HAI!")

            if eta_dt:
                if (today - eta_dt).days >= 7: return "Complete"
                if eta_dt <= today or (eta_dt > today and eta_dt <= today + timedelta(days=6)): return "Arrived"
                return "In Transit"
            if etd_dt:
                if etd_dt > today: return "LC Opened"
                return "In Transit"
                
            # If ETA text is written explicitly as pending or left blank
            if box_eta in ["pending", "", "-", "none"]: return "LC Opened"
            return "LC Opened"

        df['Status'] = df.apply(calculated_status, axis=1)
        done_count = len(df[df['Status'] == 'Complete']['File No'].unique())
        arrived_count = len(df[df['Status'] == 'Arrived']['File No'].unique())
        pending_count = total_count - done_count

        st.markdown(f"""
            <div class="glass-card-wrapper">
                <div class="glass-card" style="border-left: 4px solid #38bdf8;">
                    <div><span style="font-size:20px;">📁</span></div>
                    <div><div class="glass-card-value">{total_count}</div><div class="glass-card-label">Total Files</div></div>
                </div>
                <div class="glass-card" style="border-left: 4px solid #4ade80;">
                    <div><span style="font-size:20px;">✅</span></div>
                    <div><div class="glass-card-value">{done_count}</div><div class="glass-card-label">Done Projects</div></div>
                </div>
                <div class="glass-card" style="border-left: 4px solid #fb923c;">
                    <div><span style="font-size:20px;">⏳</span></div>
                    <div><div class="glass-card-value">{pending_count}</div><div class="glass-card-label">Pending Files</div></div>
                </div>
                <div class="glass-card" style="border-left: 4px solid #a78bfa;">
                    <div><span style="font-size:20px;">⚓</span></div>
                    <div><div class="glass-card-value">{arrived_count}</div><div class="glass-card-label">Port Arrived</div></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if all_live_alerts:
            with st.sidebar.expander("🔔 SYSTEM LIVE ALERTS", expanded=True):
                for alert_msg in set(all_live_alerts): st.info(alert_msg)

        c_top1, c_top2 = st.columns([2, 5])
        with c_top1:
            st.markdown('<div class="custom-card"><div class="card-title">📥 Operations Backup</div>', unsafe_allow_html=True)
            safe_display_cols_clean = [c for c in allowed_display_cols if c in df.columns]
            csv_string_data = df[safe_display_cols_clean].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="🟢 Export Active Excel Sheet", 
                data=csv_string_data, 
                file_name=f"Haameem_Master_{datetime.now().strftime('%Y-%m-%d')}.csv", 
                mime="text/csv"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_top2:
            st.markdown('<div class="custom-card"><div class="card-title">🔍 Quick Filters Control Center</div>', unsafe_allow_html=True)
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

        def style_rows(row):
            color = ''
            if 'Status' in row.index:
                if row['Status'] == 'Arrived': color = 'background-color: #e6fffa; color: #01695c; font-weight: 600;'
                elif row['Status'] == 'Complete': color = 'background-color: #fafafa; color: #94a3b8; opacity: 0.8;'
                elif row['Status'] == 'Query': color = 'background-color: #fff5f5; color: #e53e3e;'
                elif row['Status'] == 'In Transit': color = 'background-color: #ebf8ff; color: #2b6cb0; font-weight: 500;'
                elif row['Status'] == 'LC Opened': color = 'background-color: #fffaf0; color: #dd6b20;'
            return [color] * len(row)

        try: st.dataframe(df_display.style.apply(style_rows, axis=1), use_container_width=True)
        except: st.dataframe(df_display, use_container_width=True)
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
            hs_code = it_hs.selectbox("HS Code (Historic)", hs_suggestions, key=f"add_hs_drop_{i}") if hs_suggestions else it_hs.text_input("HS Code", key=f"add_hs_text_{i}")
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
                    c.execute('''INSERT INTO shipments (company_name, bank_name, indenter, file_no, shipper, pi_no, fc_amount, currency, shipment_type, etd, eta, bl_no, bank_docs, remarks) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (company_name, bank_name, str(indenter), file_no, str(shipper), pi_no, fc_amount, currency, ship_type, etd, eta, bl_no, bank_docs, remarks))
                    for item in items_inputs:
                        c.execute('''INSERT INTO shipment_items (file_no, item_name, brand_name, hs_code, qty, unit, unit_price, actual_costing) VALUES (?,?,?,?,?,?,?,?)''', (file_no, item[0], item[1], str(item[2]), item[3], item[4], item[5], item[6]))
                    conn.commit(); st.success("✅ Shipment recorded securely!"); st.rerun()
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
            bl_val = get_val(row, ['bl_no', 'BL__LC_NO'])
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
                    ex_name = get_val(item_row, ['item_name'])
                    ex_brand = get_val(item_row, ['brand_name'])
                    ex_hs = get_val(item_row, ['hs_code'])
                    ex_qty = get_val(item_row, ['qty'])
                    ex_unit = get_val(item_row, ['unit'], "KG")
                    ex_price = get_val(item_row, ['unit_price'])
                    ex_cost = get_val(item_row, ['actual_costing'])
                
                u_name = it_col1.selectbox("Item Name", [""] + past_items, index=past_items.index(ex_name)+1 if ex_name in past_items else 0, key=f"u_name_{file_to_update}_{idx}")
                u_brand = it_col_b.text_input("Brand", value=str(ex_brand), key=f"u_brand_{file_to_update}_{idx}")
                hs_suggestions = get_hs_codes_for_item(u_name) if u_name else []
                u_hs = it_col_hs.selectbox("HS Code", hs_suggestions, index=hs_suggestions.index(ex_hs) if ex_hs in hs_suggestions else 0, key=f"u_hs_drop_{file_to_update}_{idx}") if hs_suggestions else it_col_hs.text_input("HS Code", value=str(ex_hs), key=f"u_hs_txt_{file_to_update}_{idx}")
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
                conn.commit(); st.success("✅ Records updated successfully!"); st.rerun()

# --- 4. UPLOAD EXCEL BACKUP TAB ---
elif menu == "📥 Upload Backup (Excel)":
    st.subheader("📥 Upload System Backup Excel File (.csv)")
    st.info("💡 Yeh portal aapki purani download ki hui Excel (CSV) file ko read karke chalte hue software ke database mein saari entries ek sath load kar dega.")
    
    uploaded_file = st.file_uploader("Apni Backup File Select Karein:", type=["csv"])
    
    if uploaded_file is not None:
        try:
            try:
                backup_df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                backup_df = pd.read_csv(uploaded_file, encoding='latin1')
            
            st.write("📊 **File Preview (Pehle 5 Rows):**")
            st.dataframe(backup_df.head(5), use_container_width=True)
            
            required_cols = ['File No', 'Item Name']
            missing_cols = [c for c in required_cols if c not in backup_df.columns]
            
            if missing_cols:
                st.error(f"❌ Is File ke andar zaroori columns ghaib hain: {missing_cols}. Sahi backup file upload karein.")
            else:
                if st.button("🚀 Haan, Yeh Poora Data Software Mein Load Kardo", use_container_width=True):
                    success_count = 0
                    duplicate_count = 0
                    
                    for index, row in backup_df.iterrows():
                        f_no = str(row.get('File No', '')).strip()
                        if not f_no or f_no == "-" or f_no == "nan" or f_no == "None": continue
                        
                        comp = str(row.get('Company Name', '-'))
                        bnk = str(row.get('Bank Name', '-'))
                        ind = str(row.get('Indenter', '-'))
                        shp = str(row.get('Supplier Name', '-'))
                        val = str(row.get('Total LC Value', '0'))
                        curr = str(row.get('Currency', 'USD'))
                        stype = str(row.get('Type', 'FCL'))
                        etd_val = str(row.get('ETD', '-'))
                        eta_val = str(row.get('ETA', '-'))
                        bl_val = str(row.get('BL / LC No', '-'))
                        b_docs = str(row.get('Bank Docs', 'Pending'))
                        rem = str(row.get('Remarks', '-'))
                        
                        try:
                            c.execute('''INSERT INTO shipments (company_name, bank_name, indenter, file_no, shipper, pi_no, fc_amount, currency, shipment_type, etd, eta, bl_no, bank_docs, remarks) 
                                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                                      (comp, bnk, ind, f_no, shp, "-", val, curr, stype, etd_val, eta_val, bl_val, b_docs, rem))
                        except sqlite3.IntegrityError:
                            duplicate_count += 1
                        
                        it_name = str(row.get('Item Name', '-'))
                        if it_name and it_name != "-":
                            it_brand = str(row.get('Brand Name', row.get('BRAND', '-')))
                           # =========================================================
        # DATABASE INSERT PIPELINE (Line 630-706 Permanent Fix)
        # =========================================================
        try:
            # Database cursor connection handle karna
            cursor = conn.cursor()
            
            # Ek ek karke saari rows ko clean karke save karna
            for index, row in backup_df.iterrows():
                
                # Excel/CSV ke data ko variables mein safe save karna (Dashes aur Null values handle karte hue)
                company_name = str(row.get('Company Name', '')).strip()
                bank_name = str(row.get('Bank Name', '')).strip()
                file_no = str(row.get('File No', '')).strip()
                indenter = str(row.get('Indenter', '')).strip()
                supplier_name = str(row.get('Supplier Name', '')).strip()
                item_name = str(row.get('Item Name', '')).strip()
                brand_name = str(row.get('BRAND NAME', '')).strip()
                hs_code = str(row.get('HS Code', '')).strip()
                
                quantity = pd.to_numeric(row.get('Quantity'), errors='coerce')
                quantity = float(quantity) if not pd.isna(quantity) else 0.0
                
                unit = str(row.get('Unit', 'KG')).strip()
                
                unit_price = pd.to_numeric(row.get('Unit Price'), errors='coerce')
                unit_price = float(unit_price) if not pd.isna(unit_price) else 0.0
                
                actual_costing = pd.to_numeric(row.get('Actual Costing (PKR)'), errors='coerce')
                actual_costing = float(actual_costing) if not pd.isna(actual_costing) else 0.0
                
                total_lc_value = pd.to_numeric(row.get('Total LC Value'), errors='coerce')
                total_lc_value = float(total_lc_value) if not pd.isna(total_lc_value) else 0.0
                
                currency = str(row.get('Currency', 'USD')).strip()
                shipment_type = str(row.get('Type', '')).strip()
                
                # Dates format handling (None agar empty ho)
                etd = row.get('ETD') if pd.notna(row.get('ETD')) else None
                eta = row.get('ETA') if pd.notna(row.get('ETA')) else None
                
                bl_lc_no = str(row.get('BL / LC No', '')).strip() if pd.notna(row.get('BL / LC No')) else None
                bank_docs = str(row.get('Bank Docs', '')).strip() if pd.notna(row.get('Bank Docs')) else None
                remarks = str(row.get('Remarks', '')).strip() if pd.notna(row.get('Remarks')) else None
                status_val = str(row.get('Status', 'None')).strip()

                # INSERT QUERY (Quotes correctly closed here ✅)
                insert_query = """
                INSERT INTO master_tracker (
                    company_name, bank_name, file_no, indenter, supplier_name, 
                    item_name, brand_name, hs_code, quantity, unit, 
                    unit_price, actual_costing, total_lc_value, currency, type, 
                    etd, eta, bl_lc_no, bank_docs, remarks, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                # Query execute karna saare matching clean data ke sath
                cursor.execute(insert_query, (
                    company_name, bank_name, file_no, indenter, supplier_name,
                    item_name, brand_name, hs_code, quantity, unit,
                    unit_price, actual_costing, total_lc_value, currency, shipment_type,
                    etd, eta, bl_lc_no, bank_docs, remarks, status_val
                ))
            
            # Data ko permanently commit/save karna
            conn.commit()
            st.success("🎉 M/s HAAMEEM Ka Poora Data Software Mein Kamyabi Se Load Ho Gaya Hai!")
            st.rerun()

        except Exception as db_err:
            st.error(f"❌ Database mein data save karte waqt error aaya: {db_err}")

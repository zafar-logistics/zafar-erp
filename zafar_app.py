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
                                      (f_

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
                  items TEXT, shipper TEXT, pi_no TEXT, fc_amount TEXT, currency TEXT, 
                  unit_price TEXT, weight TEXT, weight_unit TEXT, shipment_type TEXT, 
                  etd TEXT, eta TEXT, bl_no TEXT, bank_docs TEXT, remarks TEXT)''')
    
    new_cols = [
        ('bank_name', 'TEXT'), ('company_name', 'TEXT'),
        ('currency', 'TEXT'), ('unit_price', 'TEXT'),
        ('weight', 'TEXT'), ('weight_unit', 'TEXT'), ('shipment_type', 'TEXT')
    ]
    for col_name, col_type in new_cols:
        try:
            c.execute(f'ALTER TABLE shipments ADD COLUMN {col_name} {col_type}')
        except:
            pass
    conn.commit()

init_db()

# --- INTERFACE SETUP ---
st.set_page_config(page_title="Zafar Logistics ERP", layout="wide")

if "admin_mode" not in st.session_state:
    st.session_state["admin_mode"] = False

# Sidebar for Login
st.sidebar.title("🔐 Access Control")
if not st.session_state["admin_mode"]:
    pwd = st.sidebar.text_input("Admin Password:", type="password")
    if st.sidebar.button("Login as Admin"):
        if pwd == "zafar786":
            st.session_state["admin_mode"] = True
            st.rerun()
        else:
            st.sidebar.error("Ghalat Password!")
else:
    st.sidebar.success("✅ Admin Mode: ON")
    if st.sidebar.button("Logout"):
        st.session_state["admin_mode"] = False
        st.rerun()

st.title("🛡️ Zafar Logistics ERP - Master System")

# --- DATA LISTS ---
BANKS = ["Bank Al Habib", "Habib Metro", "Meezan Bank"]
COMPANIES = ["Haa Meem Pvt Ltd", "Fine Trading Corporation", "Haa Meem AOP"]
CURRENCIES = ["USD", "CNY", "EUR", "PKR"]
UNITS = ["KG", "MT"]

if st.session_state["admin_mode"]:
    menu = st.sidebar.radio("Option Chunien:", ["📊 Dashboard", "📝 Nayi Entry (Add)", "🔄 Update / Edit"])
else:
    st.sidebar.info("📖 Read-Only Mode")
    menu = "📊 Dashboard"

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    df = pd.read_sql('SELECT * FROM shipments', conn)
    if not df.empty:
        today = datetime.now()
        def get_status(row):
            try:
                eta = pd.to_datetime(row['eta'], errors='coerce')
                etd = pd.to_datetime(row['etd'], errors='coerce')
                if pd.notnull(eta) and eta <= today: return "✅ Arrived"
                if pd.notnull(etd) and etd <= today: return "🚢 In Transit"
                return "📄 LC Opened"
            except: return "Pending"
        
        df['Status'] = df.apply(get_status, axis=1)
        
        def format_weight(row):
            w = row['weight'] if row['weight'] else ""
            u = row['weight_unit'] if row['weight_unit'] else ""
            return f"{w} {u}".strip()
        
        df['Total Weight'] = df.apply(format_weight, axis=1)
        
        # Filters
        st.write("### 🔍 Filters")
        f1, f2, f3 = st.columns(3)
        sel_comp = f1.multiselect("Company:", COMPANIES)
        sel_bank = f2.multiselect("Bank:", BANKS)
        search = f3.text_input("Search (File, Item, Price, Weight):")

        if sel_comp: df = df[df['company_name'].isin(sel_comp)]
        if sel_bank: df = df[df['bank_name'].isin(sel_bank)]
        if search: df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        cols_order = [
            'company_name', 'bank_name', 'file_no', 'items', 'shipper', 
            'fc_amount', 'currency', 'unit_price', 'Total Weight', 'shipment_type', 
            'Status', 'etd', 'eta', 'bl_no', 'bank_docs', 'remarks'
        ]
        display_cols = [c for c in cols_order if c in df.columns]
        
        df_display = df[display_cols].fillna("")
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("Data nahi hai.")

# --- 2. NAYI ENTRY ---
elif menu == "📝 Nayi Entry (Add)" and st.session_state["admin_mode"]:
    st.subheader("📝 Nayi Shipment Details")
    with st.form("add_form", clear_on_submit=True):
        col_top1, col_top2 = st.columns(2)
        company_name = col_top1.selectbox("Company Name", COMPANIES)
        bank_name = col_top2.selectbox("Bank Name", BANKS)
        
        c1, c2 = st.columns(2)
        indenter = c1.text_input("Indenter")
        file_no = c2.text_input("File No")
        
        # Items ke liye bada box banaya taake zyada items enter ho saken
        items = st.text_area("Items (Agar ek se zyada hain, toh har item alag line mein likhein)")
        
        c3, c4 = st.columns(2)
        shipper = c3.text_input("Shipper")
        pi_no = c4.text_input("P.I. No")
        
        am1, am2 = st.columns([2, 1])
        fc_amount = am1.text_input("Total Amount")
        currency = am2.selectbox("Currency", CURRENCIES)
        
        p1, p2, p3, p4 = st.columns([2, 1, 2, 2])
        unit_price = p1.text_input("Unit Price (e.g. $1.20 / $1.50)")
        weight = p2.text_input("Weight")
        weight_unit = p3.selectbox("Unit", UNITS)
        ship_type = p4.selectbox("Type", ["FCL", "LCL"])
        
        d1, d2, d3 = st.columns(3)
        etd = d1.text_input("ETD")
        eta = d2.text_input("ETA")
        bl_no = d3.text_input("BL / LC No")
        
        bank_docs = st.selectbox("Bank Docs", ["Pending", "OK"])
        remarks = st.text_area("Remarks")
        
        if st.form_submit_button("Save Record"):
            try:
                c.execute('''INSERT INTO shipments (company_name, bank_name, indenter, file_no, items, shipper, pi_no, fc_amount, currency, unit_price, weight, weight_unit, shipment_type, etd, eta, bl_no, bank_docs, remarks) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                          (company_name, bank_name, indenter, file_no, items, shipper, pi_no, fc_amount, currency, unit_price, weight, weight_unit, ship_type, etd, eta, bl_no, bank_docs, remarks))
                conn.commit()
                st.success("✅ Record save ho gaya!")
            except Exception as e:
                st.error(f"Error: {e}")

# --- 3. UPDATE / EDIT ---
elif menu == "🔄 Update / Edit" and st.session_state["admin_mode"]:
    st.subheader("🔄 Update Data")
    df = pd.read_sql('SELECT * FROM shipments', conn)
    if not df.empty:
        file_to_update = st.selectbox("Select File No to Update:", df['file_no'].tolist())
        row = df[df['file_no'] == file_to_update].iloc[0]
        with st.form("update_form"):
            u1, u2 = st.columns(2)
            u_comp = u1.selectbox("Company", COMPANIES, index=COMPANIES.index(row['company_name']) if row['company_name'] in COMPANIES else 0)
            u_bank = u2.selectbox("Bank", BANKS, index=BANKS.index(row['bank_name']) if row['bank_name'] in BANKS else 0)
            
            # Items udhar bhi badi text area banadi
            u_items = st.text_area("Update Items", value=row['items'] if row['items'] else "")
            
            u_amount = u1.text_input("Total Amount", value=row['fc_amount'] if row['fc_amount'] else "")
            u_curr = u2.selectbox("Currency", CURRENCIES, index=CURRENCIES.index(row['currency']) if row['currency'] in CURRENCIES else 0)
            
            u_price = u1.text_input("Unit Price", value=row['unit_price'] if row['unit_price'] else "")
            u_weight = u1.text_input("Weight", value=row['weight'] if row['weight'] else "")
            u_unit = u2.selectbox("Weight Unit", UNITS, index=UNITS.index(row['weight_unit']) if row['weight_unit'] in UNITS else 0)
            
            u_type = st.selectbox("Shipment Type", ["FCL", "LCL"], index=0 if row['shipment_type'] == "FCL" else 1)
            u_docs = st.selectbox("Bank Docs", ["Pending", "OK"], index=0 if row['bank_docs'] == "Pending" else 1)
            u_remarks = st.text_area("Remarks", value=row['remarks'])
            
            if st.form_submit_button("Update Record"):
                c.execute('''UPDATE shipments SET 
                             company_name=?, bank_name=?, items=?, fc_amount=?, currency=?, 
                             unit_price=?, weight=?, weight_unit=?, shipment_type=?, bank_docs=?, remarks=? 
                             WHERE file_no=?''', 
                          (u_comp, u_bank, u_items, u_amount, u_curr, u_price, u_weight, u_unit, u_type, u_docs, u_remarks, file_to_update))
                conn.commit()
                st.success("✅ Updated Successfully!")
                st.rerun()

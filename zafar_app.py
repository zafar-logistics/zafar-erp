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
        
        # Filters
        st.write("### 🔍 Filters")
        f1, f2, f3 = st.columns(3)
        sel_comp = f1.multiselect("Company:", COMPANIES)
        sel_bank = f2.multiselect("Bank:", BANKS)
        search = f3.text_input("Search (File, Item, Price, Shipping Terms):")

        if sel_comp: df = df[df['company_name'].isin(sel_comp)]
        if sel_bank: df = df[df['bank_name'].isin(sel_bank)]
        if search: df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        # Sequence Columns ka (Clean Dashboard view)
        cols_order = [
            'company_name', 'bank_name', 'file_no', 'items', 'shipper', 
            'fc_amount', 'currency', 'shipment_type', 'Status', 'etd', 'eta', 'bl_no', 'bank_docs', 'remarks'
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
        
        # Bada Breakdown Box jahan har cheez alag likhi ja sakti hai
        st.info("💡 Tip: Agar 1 se zyada items hain, toh har line mein Item | Qty | Rate alag alag likhein.")
        items = st.text_area("Item Details (e.g., TBHQ - 7500 KG - $7.1985)", height=150)
        
        c3, c4 = st.columns(2)
        shipper = c3.text_input("Shipper")
        pi_no = c4.text_input("P.I. No")
        
        am1, am2, am3 = st.columns([2, 1, 1])
        fc_amount = am1.text_input("LC / PI Total Amount (Gross)")
        currency = am2.selectbox("Currency", CURRENCIES)
        ship_type = am3.selectbox("Type", ["FCL", "LCL"])
        
        d1, d2, d3 = st.columns(3)
        etd = d1.text_input("ETD (DD-Mon-YY)")
        eta = d2.text_input("ETA (DD-Mon-YY)")
        bl_no = d3.text_input("BL / LC No")
        
        bank_docs = st.selectbox("Bank Docs", ["Pending", "OK"])
        remarks = st.text_area("Remarks")
        
        if st.form_submit_button("Save Record"):
            try:
                c.execute('''INSERT INTO shipments (company_name, bank_name, indenter, file_no, items, shipper, pi_no, fc_amount, currency, shipment_type, etd, eta, bl_no, bank_docs, remarks) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                          (company_name, bank_name, indenter, file_no, items, shipper, pi_no, fc_amount, currency, ship_type, etd, eta, bl_no, bank_docs, remarks))
                conn.commit()
                st.success("✅ New shipment record saved successfully!")
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
            
            # Pure breakdown ko edit karne ka box
            st.info("💡 Yahan har item ka weight aur unit price enter daba kar alag alag barha/theek kar sakte hain.")
            u_items = st.text_area("Update Items Breakdown (Item | Qty | Price)", value=row['items'] if row['items'] else "", height=150)
            
            u_amount = u1.text_input("Total LC Amount", value=row['fc_amount'] if row['fc_amount'] else "")
            u_curr = u2.selectbox("Currency", CURRENCIES, index=CURRENCIES.index(row['currency']) if row['currency'] in CURRENCIES else 0)
            u_type = st.selectbox("Shipment Type", ["FCL", "LCL"], index=0 if row['shipment_type'] == "FCL" else 1)
            
            u_etd = u1.text_input("ETD", value=row['etd'] if row['etd'] else "")
            u_eta = u2.text_input("ETA", value=row['eta'] if row['eta'] else "")
            u_bl = u1.text_input("BL/LC No", value=row['bl_no'] if row['bl_no'] else "")
            u_docs = u2.selectbox("Bank Docs", ["Pending", "OK"], index=0 if row['bank_docs'] == "Pending" else 1)
            
            u_remarks = st.text_area("Remarks", value=row['remarks'])
            
            if st.form_submit_button("Update Record"):
                c.execute('''UPDATE shipments SET 
                             company_name=?, bank_name=?, items=?, fc_amount=?, currency=?, 
                             shipment_type=?, etd=?, eta=?, bl_no=?, bank_docs=?, remarks=? 
                             WHERE file_no=?''', 
                          (u_comp, u_bank, u_items, u_amount, u_curr, u_type, u_etd, u_eta, u_bl, u_docs, u_remarks, file_to_update))
                conn.commit()
                st.success("✅ Record updated successfully!")
                st.rerun()

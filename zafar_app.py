import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
db_path = 'zafar_logistics_v3.db'
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()

def init_db():
    # 1. Main Table (Sirf LC aur Shipping Details ke liye)
    c.execute('''CREATE TABLE IF NOT EXISTS shipments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  company_name TEXT, bank_name TEXT, indenter TEXT, file_no TEXT UNIQUE, 
                  shipper TEXT, pi_no TEXT, fc_amount TEXT, currency TEXT, 
                  shipment_type TEXT, etd TEXT, eta TEXT, bl_no TEXT, bank_docs TEXT, remarks TEXT)''')
    
    # 2. Items Table (Har Item ki Qty aur Rate alag rakhne ke liye)
    c.execute('''CREATE TABLE IF NOT EXISTS shipment_items 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  file_no TEXT, item_name TEXT, qty TEXT, unit TEXT, unit_price TEXT)''')
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

st.title("🛡️ Zafar Logistics ERP - Professional Master System")

BANKS = ["Bank Al Habib", "Habib Metro", "Meezan Bank"]
COMPANIES = ["Haa Meem Pvt Ltd", "Fine Trading Corporation", "Haa Meem AOP"]
CURRENCIES = ["USD", "CNY", "EUR", "PKR"]
UNITS = ["KG", "MT", "DRUMS", "BAGS"]

if st.session_state["admin_mode"]:
    menu = st.sidebar.radio("Option Chunien:", ["📊 Dashboard", "📝 Nayi Entry (Add)", "🔄 Update / Edit"])
else:
    st.sidebar.info("📖 Read-Only Mode")
    menu = "📊 Dashboard"

# --- 1. DASHBOARD (WORLD STANDARD TABLE VIEW) ---
if menu == "📊 Dashboard":
    # SQL Query jo dono tables ko jor kar single excel table banati hai
    query = '''
        SELECT 
            s.company_name, s.bank_name, s.file_no,
            i.item_name, i.qty, i.unit, i.unit_price,
            s.fc_amount, s.currency, s.shipment_type,
            s.etd, s.eta, s.bl_no, s.bank_docs, s.remarks
        FROM shipments s
        LEFT JOIN shipment_items i ON s.file_no = i.file_no
    '''
    df = pd.read_sql(query, conn)
    
    if not df.empty:
        # Filters
        st.write("### 🔍 Filters")
        f1, f2, f3 = st.columns(3)
        sel_comp = f1.multiselect("Company:", COMPANIES)
        sel_bank = f2.multiselect("Bank:", BANKS)
        search = f3.text_input("Search (File, Item, Shipper):")

        if sel_comp: df = df[df['company_name'].isin(sel_comp)]
        if sel_bank: df = df[df['bank_name'].isin(sel_bank)]
        if search: df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        # Formatting columns for clean display
        df_display = df.fillna("")
        df_display.columns = [c.replace('_', ' ').title() for c in df_display.columns]
        
        # Displaying the complete grid
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Data nahi hai.")

# --- 2. NAYI ENTRY (WITH SEPARATE ITEM FIELDS) ---
elif menu == "📝 Nayi Entry (Add)" and st.session_state["admin_mode"]:
    st.subheader("📝 Nayi Shipment & Multiple Items Entry")
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
        st.markdown("##### 🛒 Items Breakdown (Har Item ki details alag likhein)")
        
        # Form mein 4 items ke alag alag saaf khane
        items_inputs = []
        for i in range(1, 5):
            st.write(f"**Item #{i}:**")
            it1, it2, it3, it4 = st.columns([4, 2, 2, 3])
            name = it1.text_input("Item Name", key=f"add_name_{i}", placeholder="e.g. TBHQ")
            qty = it2.text_input("Qty", key=f"add_qty_{i}", placeholder="e.g. 5000")
            unit = it3.selectbox("Unit", UNITS, key=f"add_unit_{i}")
            price = it4.text_input("Unit Price", key=f"add_price_{i}", placeholder="e.g. 6.920")
            if name:
                items_inputs.append((name, qty, unit, price))
                
        st.markdown("---")
        d1, d2, d3, d4 = st.columns(4)
        etd = d1.text_input("ETD")
        eta = d2.text_input("ETA")
        bl_no = d3.text_input("BL / LC No")
        bank_docs = d4.selectbox("Bank Docs", ["Pending", "OK"])
        remarks = st.text_area("Remarks")
        
        if st.form_submit_button("Save Record"):
            if not file_no:
                st.error("File No likhna zaroori hai!")
            else:
                try:
                    # 1. Master shipment save karein
                    c.execute('''INSERT INTO shipments (company_name, bank_name, indenter, file_no, shipper, pi_no, fc_amount, currency, shipment_type, etd, eta, bl_no, bank_docs, remarks) 
                                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                              (company_name, bank_name, indenter, file_no, shipper, pi_no, fc_amount, currency, ship_type, etd, eta, bl_no, bank_docs, remarks))
                    
                    # 2. Saare items ko looping se unki table mein save karein
                    for item in items_inputs:
                        c.execute('''INSERT INTO shipment_items (file_no, item_name, qty, unit, unit_price) 
                                     VALUES (?,?,?,?,?)''', (file_no, item[0], item[1], item[2], item[3]))
                    conn.commit()
                    st.success("✅ Shipment aur saare items international standard par save ho gaye!")
                except Exception as e:
                    st.error(f"Error: File No pehle se majood hai ya data ghalat hai. ({e})")

# --- 3. UPDATE / EDIT (WITH SEPARATE ITEM FIELDS) ---
elif menu == "🔄 Update / Edit" and st.session_state["admin_mode"]:
    st.subheader("🔄 Update Master & Items Data")

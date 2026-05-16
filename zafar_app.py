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

# --- 1. DASHBOARD (FIXED MULTI-ROW & SERIAL NO) ---
if menu == "📊 Dashboard":
    # 🌟 Perfect Query: Agar items table mein data mil jaye toh usko priority de
    query = '''
        SELECT 
            s.company_name AS [Company Name], 
            s.bank_name AS [Bank Name], 
            s.file_no AS [File No],
            CASE WHEN i.item_name IS NOT NULL AND i.item_name != "" THEN i.item_name ELSE s.items END AS [Item Name],
            CASE WHEN i.qty IS NOT NULL AND i.qty != "" THEN i.qty ELSE s.weight END AS [Quantity],
            CASE WHEN i.unit IS NOT NULL AND i.unit != "" THEN i.unit ELSE s.weight_unit END AS [Unit],
            CASE WHEN i.unit_price IS NOT NULL AND i.unit_price != "" THEN i.unit_price ELSE s.unit_price END AS [Unit Price],
            s.fc_amount AS [Total LC Value], 
            s.currency AS [Currency], 
            s.shipment_type AS [Type],
            s.etd AS [ETD], 
            s.eta AS [ETA], 
            s.bl_no AS [BL / LC No], 
            s.bank_docs AS [Bank Docs], 
            s.remarks AS [Remarks]
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

        if sel_comp: df = df[df['Company Name'].isin(sel_comp)]
        if sel_bank: df = df[df['Bank Name'].isin(sel_bank)]
        if search: df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        # 🌟 SERIAL NUMBER LOGIC (Hamesha 1 se shuru hoga aur continuous chalega)
        df.reset_index(drop=True, inplace=True)
        df.index = df.index + 1
        df.index.name = "S.No"

        # Table Display
        st.dataframe(df.fillna(""), use_container_width=True, hide_index=False)
    else:
        st.info("System mein koi data majood nahi hai.")

# --- 2. NAYI ENTRY ---
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
        st.markdown("##### 🛒 Items Breakdown")
        
        items_inputs = []
        for i in range(1, 5):
            st.write(f"**Item #{i}:**")
            it1, it2, it3, it4 = st.columns([4, 2, 2, 3])
            name = it1.text_input("Item Name", key=f"add_name_{i}")
            qty = it2.text_input("Qty", key=f"add_qty_{i}")
            unit = it3.selectbox("Unit", UNITS, key=f"add_unit_{i}")
            price = it4.text_input("Unit Price", key=f"add_price_{i}")
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
                    c.execute('''INSERT INTO shipments (company_name, bank_name, indenter, file_no, shipper, pi_no, fc_amount, currency, shipment_type, etd, eta, bl_no, bank_docs, remarks) 
                                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                              (company_name, bank_name, indenter, file_no, shipper, pi_no, fc_amount, currency, ship_type, etd, eta, bl_no, bank_docs, remarks))
                    
                    for item in items_inputs:
                        c.execute('''INSERT INTO shipment_items (file_no, item_name, qty, unit, unit_price) 
                                     VALUES (?,?,?,?,?)''', (file_no, item[0], item[1], item[2], item[3]))
                    conn.commit()
                    st.success("✅ Shipment aur saare items kamyabi se save ho gaye!")
                    st.rerun()
                except Exception as e:
                    st.error("Error: File No pehle se majood hai.")

# --- 3. UPDATE / EDIT ---
elif menu == "🔄 Update / Edit" and st.session_state["admin_mode"]:
    st.subheader("🔄 Update Master & Items Data")
    df_ship = pd.read_sql('SELECT * FROM shipments', conn)
    if not df_ship.empty:
        file_to_update = st.selectbox("Select File No to Update:", df_ship['file_no'].tolist())
        row = df_ship[df_ship['file_no'] == file_to_update].iloc[0]
        
        df_ex_items = pd.read_sql(f"SELECT * FROM shipment_items WHERE file_no='{file_to_update}'", conn)
        
        with st.form("update_form"):
            u1, u2 = st.columns(2)
            u_comp = u1.selectbox("Company", COMPANIES, index=COMPANIES.index(row['company_name']) if 'company_name' in row and row['company_name'] in COMPANIES else 0)
            u_bank = u2.selectbox("Bank", BANKS, index=BANKS.index(row['bank_name']) if 'bank_name' in row and row['bank_name'] in BANKS else 0)
            
            u_amount = u1.text_input("Total LC Amount", value=row['fc_amount'] if row['fc_amount'] else "")
            u_curr = u2.selectbox("Currency", CURRENCIES, index=CURRENCIES.index(row['currency']) if row['currency'] in CURRENCIES else 0)
            u_type = st.selectbox("Shipment Type", ["FCL", "LCL"], index=0 if row['shipment_type'] == "FCL" else 1)
            
            st.markdown("---")
            st.markdown("##### 🛒 Edit Items Breakdown")
            
            updated_items = []
            for idx in range(4):
                st.write(f"**Item Row #{idx+1}:**")
                it_col1, it_col2, it_col3, it_col4 = st.columns([4, 2, 2, 3])
                
                ex_name, ex_qty, ex_unit, ex_price = "", "", "KG", ""
                if idx < len(df_ex_items):
                    ex_name = df_ex_items.iloc[idx]['item_name']
                    ex_qty = df_ex_items.iloc[idx]['qty']
                    ex_unit = df_ex_items.iloc[idx]['unit']
                    ex_price = df_ex_items.iloc[idx]['unit_price']
                
                u_name = it_col1.text_input("Item Name", value=ex_name, key=f"u_name_{idx}")
                u_qty = it_col2.text_input("Qty", value=ex_qty, key=f"u_qty_{idx}")
                u_unit = it_col3.selectbox("Unit", UNITS, index=UNITS.index(ex_unit) if ex_unit in UNITS else 0, key=f"u_unit_{idx}")
                u_price = it_col4.text_input("Unit Price", value=ex_price, key=f"u_price_{idx}")
                
                if u_name:
                    updated_items.append((u_name, u_qty, u_unit, u_price))
                    
            st.markdown("---")
            u_etd = u1.text_input("ETD", value=row['etd'] if row['etd'] else "")
            u_eta = u2.text_input("ETA", value=row['eta'] if row['eta'] else "")
            u_bl = u1.text_input("BL/LC No", value=row['bl_no'] if row['bl_no'] else "")
            u_docs = u2.selectbox("Bank Docs", ["Pending", "OK"], index=0 if row['bank_docs'] == "Pending" else 1)
            u_remarks = st.text_area("Remarks", value=row['remarks'])
            
            if st.form_submit_button("Update Master & Items"):
                c.execute('''UPDATE shipments SET 
                             company_name=?, bank_name=?, fc_amount=?, currency=?, 
                             shipment_type=?, etd=?, eta=?, bl_no=?, bank_docs=?, remarks=? 
                             WHERE file_no=?''', 
                          (u_comp, u_bank, u_amount, u_curr, u_type, u_etd, u_eta, u_bl, u_docs, u_remarks, file_to_update))
                
                c.execute(f"DELETE FROM shipment_items WHERE file_no='{file_to_update}'")
                for item in updated_items:
                    c.execute('''INSERT INTO shipment_items (file_no, item_name, qty, unit, unit_price) 
                                 VALUES (?,?,?,?,?)''', (file_to_update, item[0], item[1], item[2], item[3]))
                conn.commit()
                st.success("✅ Data kamyabi se update ho gaya!")
                st.rerun()

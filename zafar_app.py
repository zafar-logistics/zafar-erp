import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import json

# --- DATABASE SETUP ---
db_path = 'zafar_logistics_v3.db'
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()

def init_db():
    # Main Shipments Table
    c.execute('''CREATE TABLE IF NOT EXISTS shipments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  company_name TEXT, bank_name TEXT, indenter TEXT, file_no TEXT UNIQUE, 
                  shipper TEXT, pi_no TEXT, fc_amount TEXT, currency TEXT, 
                  shipment_type TEXT, etd TEXT, eta TEXT, bl_no TEXT, bank_docs TEXT, remarks TEXT)''')
    
    # Professional Items Table (Jo multiple items ko alag alag handle karegi)
    c.execute('''CREATE TABLE IF NOT EXISTS shipment_items 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  file_no TEXT, item_name TEXT, hs_code TEXT, qty TEXT, unit TEXT, unit_price TEXT, total_amount TEXT)''')
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

# --- DATA LISTS ---
BANKS = ["Bank Al Habib", "Habib Metro", "Meezan Bank"]
COMPANIES = ["Haa Meem Pvt Ltd", "Fine Trading Corporation", "Haa Meem AOP"]
CURRENCIES = ["USD", "CNY", "EUR", "PKR"]
UNITS = ["KG", "MT", "DRUMS", "BAGS"]

if st.session_state["admin_mode"]:
    menu = st.sidebar.radio("Option Chunien:", ["📊 Dashboard", "📝 Nayi Entry (Add)", "🔄 Update / Edit"])
else:
    st.sidebar.info("📖 Read-Only Mode")
    menu = "📊 Dashboard"

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    df_ship = pd.read_sql('SELECT * FROM shipments', conn)
    
    if not df_ship.empty:
        today = datetime.now()
        def get_status(row):
            try:
                eta = pd.to_datetime(row['eta'], errors='coerce')
                etd = pd.to_datetime(row['etd'], errors='coerce')
                if pd.notnull(eta) and eta <= today: return "✅ Arrived"
                if pd.notnull(etd) and etd <= today: return "🚢 In Transit"
                return "📄 LC Opened"
            except: return "Pending"
        
        df_ship['Status'] = df_ship.apply(get_status, axis=1)
        
        # Filters
        st.write("### 🔍 Filters")
        f1, f2, f3 = st.columns(3)
        sel_comp = f1.multiselect("Company:", COMPANIES)
        sel_bank = f2.multiselect("Bank:", BANKS)
        search = f3.text_input("Search (File No, Shipper, BL):")

        if sel_comp: df_ship = df_ship[df_ship['company_name'].isin(sel_comp)]
        if sel_bank: df_ship = df_ship[df_ship['bank_name'].isin(sel_bank)]
        if search: df_ship = df_ship[df_ship.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        # Har shipment ko screen par professional andaz mein dikhana
        for index, row in df_ship.iterrows():
            with st.container():
                st.markdown(f"#### 📁 File No: **{row['file_no']}** | {row['company_name']} | {row['bank_name']} | Status: **{row['Status']}**")
                
                # Main info cards
                c_info1, c_info2, c_info3, c_info4 = st.columns(4)
                c_info1.write(f"**Shipper:** {row['shipper']}")
                c_info2.write(f"**Total LC Value:** {row['fc_amount']} {row['currency']}")
                c_info3.write(f"**ETD:** {row['etd']} | **ETA:** {row['eta']}")
                c_info4.write(f"**BL/LC No:** {row['bl_no']} | **Docs:** {row['bank_docs']}")
                
                # Is file ke items alag saaf table mein dikhana
                df_items = pd.read_sql(f"SELECT item_name, hs_code, qty, unit, unit_price, total_amount FROM shipment_items WHERE file_no='{row['file_no']}'", conn)
                if not df_items.empty:
                    df_items.columns = ['Item Name', 'HS Code', 'Quantity', 'Unit', 'Unit Price', 'Total Item Value']
                    st.dataframe(df_items, use_container_width=True, hide_index=True)
                else:
                    # Agar purana data ho jo naye format mein nahi hai
                    st.caption("No item breakdown found for this file. Please update using 'Update / Edit' menu.")
                
                if row['remarks']:
                    st.caption(f"**Remarks:** {row['remarks']}")
                st.markdown("---")
    else:
        st.info("System mein koi data nahi hai.")

# --- 2. NAYI ENTRY (With Multiple Item Grid) ---
elif menu == "📝 Nayi Entry (Add)" and st.session_state["admin_mode"]:
    st.subheader("📝 Nayi Shipment & Items Ki Form Entry")
    
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
        fc_amount = am1.text_input("Total LC / Invoice Value")
        currency = am2.selectbox("Currency", CURRENCIES)
        ship_type = am3.selectbox("Type", ["FCL", "LCL"])
        
        st.markdown("##### 🛒 Item Breakdown (Safarish: Max 4 Items ek sath enter karein)")
        
        # Grid for up to 4 items dynamically in the form
        item_data_list = []
        for i in range(1, 5):
            with st.expander(f"Item #{i} ki Tafseelat (Agar hai to bharein)"):
                it1, it2, it3, it4, it5 = st.columns([3, 2, 2, 2, 3])
                i_name = it1.text_input(f"Item Name #{i}", key=f"name_{i}")
                i_hs = it2.text_input(f"HS Code #{i}", key=f"hs_{i}")
                i_qty = it3.text_input(f"Quantity #{i}", key=f"qty_{i}")
                i_unit = it4.selectbox(f"Unit #{i}", UNITS, key=f"unit_{i}")
                i_price = it5.text_input(f"Unit Price #{i}", key=f"price_{i}")
                i_total = "" # Auto calc framework handles display
                if i_name:
                    item_data_list.append((i_name, i_hs, i_qty, i_unit, i_price))
        
        st.markdown("##### 📅 Dates & Tracking")
        d1, d2, d3, d4 = st.columns(4)
        etd = d1.text_input("ETD (DD-Mon-YY)")
        eta = d2.text_input("ETA (DD-Mon-YY)")
        bl_no = d3.text_input("BL / LC No")
        bank_docs = d4.selectbox("Bank Docs", ["Pending", "OK"])
        remarks = st.text_area("Remarks")
        
        if st.form_submit_button("Save Master Record"):
            if not file_no:
                st.error("File No dena zaroori hai!")
            else:
                try:
                    # Master Entry
                    c.execute('''INSERT INTO shipments (company_name, bank_name, indenter, file_no, shipper, pi_no, fc_amount, currency, shipment_type, etd, eta, bl_no, bank_docs, remarks) 
                                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                              (company_name, bank_name, indenter, file_no, shipper, pi_no, fc_amount, currency, ship_type, etd, eta, bl_no, bank_docs, remarks))
                    
                    # Items Entry
                    for item in item_data_list:
                        # Simple multiplication text generation or estimation if possible
                        try:
                            t_calc = str(float(item[2]) * float(item[4].replace('$','').strip()))
                        except:
                            t_calc = "-"
                        c.execute('''INSERT INTO shipment_items (file_no, item_name, hs_code, qty, unit, unit_price, total_amount) 
                                     VALUES (?,?,?,?,?,?,?)''', (file_no, item[0], item[1], item[2], item[3], item[4], t_calc))
                    
                    conn.commit()
                    st.success(f"✅ File {file_no} aur uske saare items professional treekay se save ho gaye!")
                except Exception as e:
                    st.error(f"Error: File No ya data mein masla hai. ({e})")

# --- 3. UPDATE / EDIT ---
elif menu == "🔄 Update / Edit" and st.session_state["admin_mode"]:
    st.subheader("🔄 Master & Items Data Update")
    df_ship = pd.read_sql('SELECT * FROM shipments', conn)
    if not df_ship.empty:
        file_to_update = st.selectbox("Select File No to Update:", df_ship['file_no'].tolist())
        row = df_ship[df_ship['file_no'] == file_to_update].iloc[0]
        
        with st.form("update_form"):
            u1, u2 = st.columns(2)
            u_comp = u1.selectbox("Company", COMPANIES, index=COMPANIES.index(row['company_name']) if row['company_name'] in COMPANIES else 0)
            u_bank = u2.selectbox("Bank", BANKS, index=BANKS.index(row['bank_name']) if row['bank_name'] in BANKS else 0)
            
            u_amount = u1.text_input("Total LC Amount", value=row['fc_amount'] if row['fc_amount'] else "")
            u_curr = u2.selectbox("Currency", CURRENCIES, index=CURRENCIES.index(row['currency']) if row['currency'] in CURRENCIES else 0)
            u_type = st.selectbox("Shipment Type", ["FCL", "LCL"], index=0 if row['shipment_type'] == "FCL" else 1)
            
            st.markdown("##### 🛠️ Edit / Add Items Breakdown for this File")
            
            # Pehle se majood items load karein edit ke liye
            df_existing_items = pd.read_sql(f"SELECT * FROM shipment_items WHERE file_no='{file_to_update}'", conn)
            
            updated_items = []
            for idx in range(4):
                st.write(f"**Item Row #{idx+1}**")
                it_col1, it_col2, it_col3, it_col4, it_col5 = st.columns([3, 2, 2, 2, 3])
                
                # Check if item data exists for this index
                ex_name, ex_hs, ex_qty, ex_unit, ex_price = "", "", "", "KG", ""
                if idx < len(df_existing_items):
                    ex_name = df_existing_items.iloc[idx]['item_name']
                    ex_hs = df_existing_items.iloc[idx]['hs_code']
                    ex_qty = df_existing_items.iloc[idx]['qty']
                    ex_unit = df_existing_items.iloc[idx]['unit']
                    ex_price = df_existing_items.iloc[idx]['unit_price']
                
                u_i_name = it_col1.text_input(f"Item Name", value=ex_name, key=f"u_name_{idx}")
                u_i_hs = it_col2.text_input(f"HS Code", value=ex_hs, key=f"u_hs_{idx}")
                u_i_qty = it_col3.text_input(f"Qty", value=ex_qty, key=f"u_qty_{idx}")
                u_i_unit = it_col4.selectbox(f"Unit", UNITS, index=UNITS.index(ex_unit) if ex_unit in UNITS else 0, key=f"u_unit_{idx}")
                u_i_price = it_col5.text_input(f"Price", value=ex_price, key=f"u_price_{idx}")
                
                if u_i_name:
                    updated_items.append((u_i_name, u_i_hs, u_i_qty, u_i_unit, u_i_price))

            st.markdown("---")
            u_etd = u1.text_input("ETD", value=row['etd'] if row['etd'] else "")
            u_eta = u2.text_input("ETA", value=row['eta'] if row['eta'] else "")
            u_bl = u1.text_input("BL/LC No", value=row['bl_no'] if row['bl_no'] else "")
            u_docs = u2.selectbox("Bank Docs", ["Pending", "OK"], index=0 if row['bank_docs'] == "Pending" else 1)
            u_remarks = st.text_area("Remarks", value=row['remarks'])
            
            if st.form_submit_button("Update Master & Items Data"):
                # 1. Update Master Shipment
                c.execute('''UPDATE shipments SET 
                             company_name=?, bank_name=?, fc_amount=?, currency=?, 
                             shipment_type=?, etd=?, eta=?, bl_no=?, bank_docs=?, remarks=? 
                             WHERE file_no=?''', 
                          (u_comp, u_bank, u_amount, u_curr, u_type, u_etd, u_eta, u_bl, u_docs, u_remarks, file_to_update))
                
                # 2. Refresh Items for this file (Purane saaf karke naye table data save)
                c.execute(f"DELETE FROM shipment_items WHERE file_no='{file_to_update}'")
                for item in updated_items:
                    try: t_calc = str(float(item[2]) * float(item[4].replace('$','').strip()))
                    except: t_calc = "-"
                    c.execute('''INSERT INTO shipment_items (file_no, item_name, hs_code, qty, unit, unit_price, total_amount) 
                                 VALUES (?,?,?,?,?,?,?)''', (file_to_update, item[0], item[1], item[2], item[3], item[4], t_calc))
                
                conn.commit()
                st.success("✅ Master Data aur Items Grid kamyabi se professional design mein update ho gaye!")
                st.rerun()

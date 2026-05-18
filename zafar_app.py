import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
db_path = 'zafar_logistics_v3.db'
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()

def init_db():
    # 1. Main Shipments Table
    c.execute('''CREATE TABLE IF NOT EXISTS shipments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  company_name TEXT, bank_name TEXT, indenter TEXT, file_no TEXT UNIQUE, 
                  shipper TEXT, pi_no TEXT, fc_amount TEXT, currency TEXT, 
                  shipment_type TEXT, etd TEXT, eta TEXT, bl_no TEXT, bank_docs TEXT, remarks TEXT)''')
    
    # 2. Items Table
    c.execute('''CREATE TABLE IF NOT EXISTS shipment_items 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  file_no TEXT, item_name TEXT, brand_name TEXT, hs_code TEXT, qty TEXT, unit TEXT, unit_price TEXT, actual_costing TEXT)''')
    
    # 3. Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, password TEXT, role TEXT)''')
    
    # Auto-create Master Admin Account
    try:
        c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('zafar', 'zafar786', 'Admin')")
        conn.commit()
    except:
        pass

    # 🌟 PHYSICAL COLUMN INJECTION: Back-end par forcefully check aur column create karne ke liye
    columns_to_ensure = [
        ('brand_name', 'TEXT'),
        ('hs_code', 'TEXT'),
        ('actual_costing', 'TEXT')
    ]
    for col_name, col_type in columns_to_ensure:
        try:
            c.execute(f'ALTER TABLE shipment_items ADD COLUMN {col_name} {col_type}')
        except:
            pass # Agar column pehle se bana hua hai toh bina chere agay barho

    # Main shipments fallback protection columns
    fallback_cols = [
        ('bank_name', 'TEXT'), ('company_name', 'TEXT'), ('currency', 'TEXT'), 
        ('shipment_type', 'TEXT'), ('items', 'TEXT'), ('weight', 'TEXT'), ('weight_unit', 'TEXT'), ('unit_price', 'TEXT'),
        ('indenter', 'TEXT'), ('shipper', 'TEXT')
    ]
    for col_name, col_type in fallback_cols:
        try:
            c.execute(f'ALTER TABLE shipments ADD COLUMN {col_name} {col_type}')
        except:
            pass
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

# --- 🔑 LOGIN SCREEN ---
if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🔒 Zafar Logistics ERP - Secure Login</h2>", unsafe_allow_html=True)
    st.write("")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login_form"):
            user_input = st.text_input("Username:")
            pass_input = st.text_input("Password:", type="password")
            submit_login = st.form_submit_button("Sign In / Login")
            
            if submit_login:
                c.execute("SELECT role FROM users WHERE username=? AND password=?", (user_input, pass_input))
                result = c.fetchone()
                if result:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = user_input
                    st.session_state["user_role"] = result[0]
                    st.success("Logging in...")
                    st.rerun()
                else:
                    st.error("Ghalat Username ya Password!")
    st.stop()

# --- 📊 MASTER APP SECTION ---
st.sidebar.title(f"👤 User: {st.session_state['username']}")
st.sidebar.info(f"🛡️ Rights: {st.session_state['user_role']}")

available_options = ["📊 Dashboard"]
if st.session_state["user_role"] in ["Admin", "Manager"]:
    available_options.append("📝 Nayi Entry (Add)")
    available_options.append("🔄 Update / Edit")
if st.session_state["user_role"] == "Admin":
    available_options.append("👥 Manage Users / Accounts")

menu = st.sidebar.radio("Navigation Menu:", available_options)

if st.sidebar.button("🚪 Logout System"):
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
    query = '''
        SELECT 
            IFNULL(s.company_name, "-") AS [Company Name], 
            IFNULL(s.bank_name, "-") AS [Bank Name], 
            IFNULL(s.file_no, "-") AS [File No],
            IFNULL(s.indenter, "-") AS [Indenter], 
            IFNULL(s.shipper, "-") AS [Supplier Name],
            CASE WHEN i.item_name IS NOT NULL AND i.item_name != "" THEN i.item_name ELSE IFNULL(s.items, "-") END AS [Item Name],
            IFNULL(i.brand_name, "-") AS [Brand Name], 
            IFNULL(i.hs_code, "-") AS [HS Code],
            CASE WHEN i.qty IS NOT NULL AND i.qty != "" THEN i.qty ELSE IFNULL(s.weight, "-") END AS [Quantity],
            CASE WHEN i.unit IS NOT NULL AND i.unit != "" THEN i.unit ELSE IFNULL(s.weight_unit, "-") END AS [Unit],
            CASE WHEN i.unit_price IS NOT NULL AND i.unit_price != "" THEN i.unit_price ELSE IFNULL(s.unit_price, "-") END AS [Unit Price],
            IFNULL(i.actual_costing, "-") AS [Actual Costing (PKR)],
            IFNULL(s.fc_amount, "-") AS [Total LC Value], 
            IFNULL(s.currency, "-") AS [Currency], 
            IFNULL(s.shipment_type, "-") AS [Type],
            IFNULL(s.etd, "") AS [ETD], 
            IFNULL(s.eta, "") AS [ETA], 
            IFNULL(s.bl_no, "-") AS [BL / LC No], 
            IFNULL(s.bank_docs, "-") AS [Bank Docs], 
            IFNULL(s.remarks, "") AS [Remarks]
        FROM shipments s
        LEFT JOIN shipment_items i ON s.file_no = i.file_no
    '''
    try:
        df = pd.read_sql(query, conn)
    except:
        # Ultimate fallback to make sure screen never goes red
        df = pd.read_sql('SELECT * FROM shipments', conn)

    if not df.empty:
        # Auto Status
        today = datetime.now()
        def get_status(row):
            try:
                if 'ETA' not in row or not row['ETA'] or row['ETA'] == "": return "📄 LC Opened"
                eta = pd.to_datetime(row['ETA'], errors='coerce')
                etd = pd.to_datetime(row['ETD'], errors='coerce')
                if pd.notnull(eta) and eta <= today: return "✅ Arrived"
                if pd.notnull(etd) and etd <= today: return "🚢 In Transit"
                return "📄 LC Opened"
            except: return "Pending"
        df['Status'] = df.apply(get_status, axis=1)

        # Excel Backup
        if st.session_state["user_role"] in ["Admin", "Manager"]:
            st.write("### 📥 System Backup")
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(label="🟢 Download Data for Excel", data=csv_data, file_name=f"Zafar_Backup_{datetime.now().strftime('%Y-%m-%d')}.csv", mime="text/csv")
            st.markdown("---")
        
        st.write("### 🔍 Filters")
        f1, f2, f3 = st.columns(3)
        sel_comp = f1.multiselect("Company:", COMPANIES)
        sel_bank = f2.multiselect("Bank:", BANKS)
        search = f3.text_input("Search (File, Item, Supplier, Brand):")

        if 'Company Name' in df.columns and sel_comp: 
            df = df[df['Company Name'].isin(sel_comp)]
        if 'Bank Name' in df.columns and sel_bank: 
            df = df[df['Bank Name'].isin(sel_bank)]
        if search: 
            df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        # Sequence Columns mapping
        cols_order = [
            'Company Name', 'Bank Name', 'File No', 'Indenter', 'Supplier Name', 
            'Item Name', 'Brand Name', 'HS Code', 'Quantity', 'Unit', 'Unit Price', 
            'Actual Costing (PKR)', 'Total LC Value', 'Currency', 'Type', 'Status', 
            'ETD', 'ETA', 'BL / LC No', 'Bank Docs', 'Remarks'
        ]
        
        display_cols = [c for c in cols_order if c in df.columns]
        df_display = df[display_cols]
        
        df_display.reset_index(drop=True, inplace=True)
        df_display.index = df_display.index + 1
        df_display.index.name = "S.No"

        st.dataframe(df_display.fillna("-"), use_container_width=True, hide_index=False)
    else:
        st.info("System mein koi data majood nahi hai.")

# --- 2. NAYI ENTRY ---
elif menu == "📝 Nayi Entry (Add)" and st.session_state["user_role"] in ["Admin", "Manager"]:
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
        
        if st.form_submit_button("Save Record"):
            if not file_no: st.error("File No likhna zaroori hai!")
            else:
                try:
                    c.execute('''INSERT INTO shipments (company_name, bank_name, indenter, file_no, shipper, pi_no, fc_amount, currency, shipment_type, etd, eta, bl_no, bank_docs, remarks) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (company_name, bank_name, indenter, file_no, shipper, pi_no, fc_amount, currency, ship_type, etd, eta, bl_no, bank_docs, remarks))
                    for item in items_inputs:
                        c.execute('''INSERT INTO shipment_items (file_no, item_name, brand_name, hs_code, qty, unit, unit_price, actual_costing) VALUES (?,?,?,?,?,?,?,?)''', (file_no, item[0], item[1], item[2], item[3], item[4], item[5], item[6]))
                    conn.commit()
                    st.success("✅ Save ho gaya!")
                    st.rerun()
                except: st.error("Error: Save nahi ho saka.")

# --- 3. UPDATE / EDIT ---
elif menu == "🔄 Update / Edit" and st.session_state["user_role"] in ["Admin", "Manager"]:
    st.subheader("🔄 Update Master, Items & Actual Costing Data")
    df_ship = pd.read_sql('SELECT * FROM shipments', conn)
    if not df_ship.empty:
        file_to_update = st.selectbox("Select File No to Update:", df_ship['file_no'].tolist())
        row = df_ship[df_ship['file_no'] == file_to_update].iloc[0]
        df_ex_items = pd.read_sql(f"SELECT * FROM shipment_items WHERE file_no='{file_to_update}'", conn)
        
        with st.form(key=f"form_{file_to_update}"):
            u1, u2 = st.columns(2)
            u_comp = u1.selectbox("Company", COMPANIES, index=COMPANIES.index(row['company_name']) if 'company_name' in row and row['company_name'] in COMPANIES else 0)
            u_bank = u2.selectbox("Bank", BANKS, index=BANKS.index(row['bank_name']) if 'bank_name' in row and row['bank_name'] in BANKS else 0)
            u_indenter = u1.text_input("Indenter", value=row['indenter'] if row['indenter'] else "")
            u_shipper = u2.text_input("Shipper", value=row['shipper'] if row['shipper'] else "")
            u_amount = u1.text_input("Total LC Amount", value=row['fc_amount'] if row['fc_amount'] else "")
            u_curr = u2.selectbox("Currency", CURRENCIES, index=CURRENCIES.index(row['currency']) if row['currency'] in CURRENCIES else 0)
            u_type = st.selectbox("Shipment Type", ["FCL", "LCL"], index=0 if row['shipment_type'] == "FCL" else 1)
            
            st.markdown("---")
            updated_items = []
            for idx in range(4):
                st.write(f"**Item Row #{idx+1}:**")
                it_col1, it_col_b, it_col_hs, it_col2, it_col3, it_col4, it_col5 = st.columns([3, 2, 2, 1, 1, 1, 2])
                ex_name, ex_brand, ex_hs, ex_qty, ex_unit, ex_price, ex_cost = "", "", "", "", "KG", "", ""
                if idx < len(df_ex_items):
                    ex_name = df_ex_items.iloc[idx]['item_name'] if df_ex_items.iloc[idx]['item_name'] else ""
                    ex_brand = df_ex_items.iloc[idx]['brand_name'] if 'brand_name' in df_ex_items.columns and df_ex_items.iloc[idx]['brand_name'] else ""
                    ex_hs = df_ex_items.iloc[idx]['hs_code'] if 'hs_code' in df_ex_items.columns and df_ex_items.iloc[idx]['hs_code'] else ""
                    ex_qty = df_ex_items.iloc[idx]['qty'] if df_ex_items.iloc[idx]['qty'] else ""
                    ex_unit = df_ex_items.iloc[idx]['unit'] if df_ex_items.iloc[idx]['unit'] else "KG"
                    ex_price = df_ex_items.iloc[idx]['unit_price'] if df_ex_items.iloc[idx]['unit_price'] else ""
                    ex_cost = df_ex_items.iloc[idx]['actual_costing'] if 'actual_costing' in df_ex_items.columns and df_ex_items.iloc[idx]['actual_costing'] else ""
                
                u_name = it_col1.text_input("Item Name", value=ex_name, key=f"u_name_{file_to_update}_{idx}")
                u_brand = it_col_b.text_input("Brand", value=ex_brand, key=f"u_brand_{file_to_update}_{idx}")
                u_hs = it_col_hs.text_input("HS Code", value=ex_hs, key=f"u_hs_{file_to_update}_{idx}")
                u_qty = it_col2.text_input("Qty", value=ex_qty, key=f"u_qty_{file_to_update}_{idx}")
                u_unit = it_col3.selectbox("Unit", UNITS, index=UNITS.index(ex_unit) if ex_unit in UNITS else 0, key=f"u_unit_{file_to_update}_{idx}")
                u_price = it_col4.text_input("Price", value=ex_price, key=f"u_price_{file_to_update}_{idx}")
                u_cost = it_col5.text_input("Actual Costing", value=ex_cost, key=f"u_cost_{file_to_update}_{idx}")
                if u_name: updated_items.append((u_name, u_brand, u_hs, u_qty, u_unit, u_price, u_cost))
                    
            st.markdown("---")
            u_etd = u1.text_input("ETD", value=row['etd'] if row['etd'] else "")
            u_eta = u2.text_input("ETA", value=row['eta'] if row['eta'] else "")
            u_bl = u1.text_input("BL/LC No", value=row['bl_no'] if row['bl_no'] else "")
            u_docs = u2.selectbox("Bank Docs", ["Pending", "OK"], index=0 if row['bank_docs'] == "Pending" else 1)
            u_remarks = st.text_area("Remarks", value=row['remarks'])
            
            if st.form_submit_button("Update Master & Items"):
                c.execute('''UPDATE shipments SET company_name=?, bank_name=?, indenter=?, shipper=?, fc_amount=?, currency=?, shipment_type=?, etd=?, eta=?, bl_no=?, bank_docs=?, remarks=? WHERE file_no=?''', (u_comp, u_bank, u_indenter, u_shipper, u_amount, u_curr, u_type, u_etd, u_eta, u_bl, u_docs, u_remarks, file_to_update))
                c.execute(f"DELETE FROM shipment_items WHERE file_no='{file_to_update}'")
                for item in updated_items:
                    c.execute('''INSERT INTO shipment_items (file_no, item_name, brand_name, hs_code, qty, unit, unit_price, actual_costing) VALUES (?,?,?,?,?,?,?,?)''', (file_to_update, item[0], item[1], item[2], item[3], item[4], item[5], item[6]))
                conn.commit()
                st.success("✅ Updated!")
                st.rerun()

# --- 4. 👥 MANAGE ACCOUNTS ---
elif menu == "👥 Manage Users / Accounts" and st.session_state["user_role"] == "Admin":
    st.subheader("👥 Accounts Control Center")
    with st.form("create_user_form"):
        new_user = st.text_input("Username:")
        new_pass = st.text_input("Password:", type="password")
        new_role = st.selectbox("Role:", ROLES)
        if st.form_submit_button("Create Account"):
            if new_user and new_pass:
                try:
                    c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", (new_user, new_pass, new_role))
                    conn.commit()
                    st.success(f"✅ User '{new_user}' created!")
                except: st.error("Username already exists.")
    st.markdown("---")
    df_users = pd.read_sql("SELECT id, username, role FROM users", conn)
    st.dataframe(df_users, use_container_width=True)

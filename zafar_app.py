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
                  indenter TEXT, file_no TEXT UNIQUE, items TEXT, shipper TEXT, 
                  pi_no TEXT, fc_amount TEXT, eif_expiry TEXT, 
                  etd TEXT, eta TEXT, bl_no TEXT, 
                  bank_docs TEXT, doc_retire TEXT, remarks TEXT)''')
    conn.commit()

init_db()

# --- INTERFACE SETUP ---
st.set_page_config(page_title="Zafar Logistics ERP", layout="wide")

# --- LOGIN LOGIC (Admin vs Guest) ---
if "admin_mode" not in st.session_state:
    st.session_state["admin_mode"] = False

# Sidebar for Login
st.sidebar.title("🔐 Access Control")
if not st.session_state["admin_mode"]:
    pwd = st.sidebar.text_input("Admin Password dalo (Edit ke liye):", type="password")
    if st.sidebar.button("Login as Admin"):
        if pwd == "zafar786": # Yahan apna password badal sakte hain
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

# --- MENU OPTIONS (Restricted based on Login) ---
if st.session_state["admin_mode"]:
    menu = st.sidebar.radio("Option Chunien:", ["📊 Dashboard", "📝 Nayi Entry (Add)", "🔄 Update / Edit"])
else:
    st.sidebar.info("📖 Aap 'Read-Only' mode mein hain.")
    menu = "📊 Dashboard" # Guest sirf Dashboard dekh sakta hai

# --- 1. DASHBOARD (Sab ke liye) ---
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
        search = st.text_input("🔍 Search Anything (Item, File, Shipper):")
        if search:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        st.dataframe(df.drop(columns=['id']), use_container_width=True)
    else:
        st.info("Dashboard khali hai.")

# --- 2. NAYI ENTRY (Sirf Admin) ---
elif menu == "📝 Nayi Entry (Add)" and st.session_state["admin_mode"]:
    st.subheader("📝 Nayi Shipment ki Tafseelat")
    with st.form("add_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        indenter = col1.text_input("Indenter")
        file_no = col2.text_input("File No")
        items = col3.text_input("Items")
        shipper = col1.text_input("Shipper")
        pi_no = col2.text_input("P.I. No")
        fc_amount = col3.text_input("Amount")
        etd = col1.text_input("ETD (DD-Mon-YY)", value=datetime.now().strftime("%d-%b-%y"))
        eta = col2.text_input("ETA (DD-Mon-YY)", value="-")
        eif_exp = col3.text_input("EIF Expiry", value="-")
        bl_no = col1.text_input("BL / LC No")
        bank_docs = col2.selectbox("Bank Docs", ["Pending", "OK"])
        doc_retire = col3.text_input("Retire Date", value="-")
        remarks = st.text_area("Remarks / DHL Tracking")
        
        if st.form_submit_button("Save Record"):
            try:
                c.execute('INSERT INTO shipments (indenter, file_no, items, shipper, pi_no, fc_amount, eif_expiry, etd, eta, bl_no, bank_docs, doc_retire, remarks) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', 
                          (indenter, file_no, items, shipper, pi_no, fc_amount, eif_exp, etd, eta, bl_no, bank_docs, doc_retire, remarks))
                conn.commit()
                st.success(f"✅ File {file_no} save ho gayi!")
            except Exception as e:
                st.error(f"Error: {e}")

# --- 3. UPDATE / EDIT (Sirf Admin) ---
elif menu == "🔄 Update / Edit" and st.session_state["admin_mode"]:
    st.subheader("🔄 Shipment Update Karein")
    df = pd.read_sql('SELECT * FROM shipments', conn)
    if not df.empty:
        file_to_update = st.selectbox("Update ke liye File No chunein:", df['file_no'].tolist())
        row = df[df['file_no'] == file_to_update].iloc[0]
        with st.form("update_form"):
            u_col1, u_col2 = st.columns(2)
            u_bank = u_col1.selectbox("Bank Docs Status", ["Pending", "OK"], index=0 if row['bank_docs'] == "Pending" else 1)
            u_retire = u_col2.text_input("Document Retire Date", value=row['doc_retire'])
            u_remarks = st.text_area("Update Remarks", value=row['remarks'])
            if st.form_submit_button("Update Data"):
                c.execute('UPDATE shipments SET bank_docs=?, doc_retire=?, remarks=? WHERE file_no=?', 
                          (u_bank, u_retire, u_remarks, file_to_update))
                conn.commit()
                st.success(f"✅ Update Done!")
                st.rerun()

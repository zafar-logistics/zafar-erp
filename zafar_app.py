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

# --- INTERFACE ---
st.set_page_config(page_title="Zafar Logistics ERP", layout="wide")
st.title("🛡️ Zafar Logistics ERP - Master System")

# Sidebar Menu
menu = st.sidebar.radio("Option Chunien:", ["📊 Dashboard", "📝 Nayi Entry (Add)", "🔄 Update / Edit"])

# --- RESTORE BUTTON ---
if st.sidebar.button("🚀 Restore All Excel Data"):
    zafar_data = [
        ('SELF', 'LC63480', 'TBHQ', 'L & P', '2026032401', '50390.0', '28-Sep-26', '23-Apr-26', '11-May-26', 'KMTCSHKA607976', 'OK', '-', 'DHL # 1753348634'),
        ('Jiangsu', 'CONT37280', 'SODIUM DIACETATE', 'Qisong', 'GFP-QS-202501', '3562.5', '20-May-26', '13-Apr-26', '12-May-26', 'QDWH260328766', 'OK', '-', 'DHL # 8409933685'),
        ('TRI BROTHER', 'CONT37620', 'CMC', 'CHONGQING', '26-085-521 (084)', '427700.0', '29-May-26', '15-Apr-26', '14-May-26', 'CKGCB26000464', 'OK', '-', '50 bags empty DHL # 3351232964'),
        ('SEAWALL', 'IFDBC35091', 'TRI SODIUM', 'TTCA', 'S262Y103205', '44010.0', '05-Jun-26', '17-Apr-26', '16-May-26', '799610185374', 'OK', '-', 'DHL # 9510703532'),
        ('COSMO', 'LC8372', 'LAURIC, PALMITIC, MYR', 'EDENOR', 'CCI/786/01856', '53600.0', '31-Mar-26', '29-Apr-26', '17-May-26', 'MLNPKGKHI260435', 'OK', '279.35', 'DHL # 1978629240'),
        ('LIHUA', 'LC60727', 'MALTODEXTRIN', 'QINHUANGDAO', 'LH261663', '16520.0', '29-Jul-26', '05-Apr-26', '20-May-26', 'KMTCXGG2994069', 'OK', '-', '20 empty bags DHL 4755652996'),
        ('SELF', 'CONT38475', 'TRI SODIUM', 'TTCA', 'FS0260305V039P', '21870.0', '-', '25-Apr-26', '21-May-26', 'MEDUWZ115025', 'OK', '279.2', 'DHL # 7787179923'),
        ('SELF', 'LC8424', 'ASCORBYL PALMITATE', 'GEEN', '2026032401', '25000.0', '31-May-26', '11-May-26', '25-May-26', 'ECJPLCL260400203', 'OK', '7052500', 'NOMAN GOODS READY 26-APR'),
        ('MANSOOR', 'LC61736', 'GLYCERIN', 'I.CONT', 'SC/26/GLY/0221', '27000.0', '19-Aug-26', '23-Apr-26', '23-May-26', 'SSLBWKHICAD0687', 'OK', '7616700', 'DHL # 1978554233'),
        ('WENGFU', 'LC63493', 'PHOSPHORIC ACID', 'WENGFU', '260401', '115311.0', '19-Aug-26', '21-Apr-26', '24-May-26', 'COAU7268344300', 'OK', '-', 'DHL # 9188384553'),
        ('HITECH', 'LC62516', 'TBHQ', 'Jiangxi Hitech', '20260318', '51255.0', '03-Jun-26', '10-May-26', '05-Jun-26', '-', 'OK', '14459036', 'DRAFT JUST BL WAIT'),
        ('MAJ INT.', 'LC60581', 'NORIT D10', 'NORIT', '7047188 SX', '30264.0', '06-Sep-26', '27-Apr-26', '08-Jun-26', 'MEDUWO151718', 'OK', '8537474', 'FEDEX 871463716329'),
        ('MUSA', 'LC8330', 'RADIAMULS POLY 2251K', 'OLEON', '99126510', '11312.6', '31-Jan-26', '24-Mar-26', '-', 'HPKGSINKHI2600086-07', 'OK', '3191296', 'DHL # 2527225212'),
        ('DSM', 'LC8391', 'VITAMIN AD3', 'DSM', '2814245047', '270000.0', '21-Jul-26', '25-May-26', '-', '-', 'OK', '76167000', 'REQ ARRIVAL 25-5-26'),
        ('DSM', 'LC8392', 'VITAMIN AD3', 'DSM', '2814245050', '270000.0', '21-Jul-26', '26-Jun-26', '-', '-', 'OK', '76167000', 'REQ ARRIVAL 26-6-26'),
        ('WENGFU', 'LC66751', 'PHOSPHORIC ACID', 'WENGFU', '260508', '121695.0', '-', '24-May-26', '09-Jun-26', '-', 'Pending', '34330160', '-'),
        ('VYBE', 'LC', 'PHOSPHORIC ACID', 'Chengdu', 'CCUP26050728', '118902.0', '-', '-', '-', '-', 'Pending', '33542254', '-'),
        ('DSM', 'LC60717.', 'VITAMIN AD3', 'DSM', '2814245045', '172800.0', '19-Aug-26', '-', '-', '-', 'Pending', '48746880', '-')
    ]
    try:
        c.executemany('INSERT OR IGNORE INTO shipments (indenter, file_no, items, shipper, pi_no, fc_amount, eif_expiry, etd, eta, bl_no, bank_docs, doc_retire, remarks) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', zafar_data)
        conn.commit()
        st.sidebar.success("✅ Data Restore Done!")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

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
        search = st.text_input("🔍 Search Anything (Item, File, Shipper):")
        if search:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        st.dataframe(df.drop(columns=['id']), use_container_width=True)
    else:
        st.info("Dashboard khali hai. Sidebar se Restore karein ya Nayi Entry dalein.")

# --- 2. NAYI ENTRY (ADD) ---
elif menu == "📝 Nayi Entry (Add)":
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
            except sqlite3.IntegrityError:
                st.error("❌ Yeh File No pehle se majood hai!")

# --- 3. UPDATE / EDIT ---
elif menu == "🔄 Update / Edit":
    st.subheader("🔄 Shipment Update Karein")
    df = pd.read_sql('SELECT * FROM shipments', conn)
    if not df.empty:
        file_to_update = st.selectbox("Update ke liye File No chunein:", df['file_no'].tolist())
        row = df[df['file_no'] == file_to_update].iloc[0]
        
        with st.form("update_form"):
            u_col1, u_col2 = st.columns(2)
            u_bank = u_col1.selectbox("Bank Docs Status", ["Pending", "OK"], index=0 if row['bank_docs'] == "Pending" else 1)
            u_retire = u_col2.text_input("Document Retire Date", value=row['doc_retire'])
            u_eta = u_col1.text_input("Update ETA", value=row['eta'])
            u_bl = u_col2.text_input("Update BL/LC No", value=row['bl_no'])
            u_remarks = st.text_area("Update Remarks", value=row['remarks'])
            
            if st.form_submit_button("Update Data"):
                c.execute('UPDATE shipments SET bank_docs=?, doc_retire=?, eta=?, bl_no=?, remarks=? WHERE file_no=?', 
                          (u_bank, u_retire, u_eta, u_bl, u_remarks, file_to_update))
                conn.commit()
                st.success(f"✅ File {file_to_update} update ho gayi!")
                st.rerun()
    else:
        st.info("Pehle Dashboard mein data dalein.")
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

    # Safe Schema Alterations
    alter_cols = [
        ('shipment_items', 'brand_name', 'TEXT'),
        ('shipment_items', 'hs_code', 'TEXT'),
        ('shipment_items', 'actual_costing', 'TEXT')
    ]
    for table, col, col_type in alter_cols:
        try:
            c.execute(f'ALTER TABLE {table} ADD COLUMN {col} {col_type}')
        except:
            pass
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
    if not date_str or str(date_str).strip() in ["", "-", "Pending", "None", "nan"]: 
        return None
    for fmt in ('%d-%b-%y', '%d-%b-%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try: 
            return datetime.strptime(str(date_str).strip(), fmt)
        except: 
            pass
    return None

# --- INTERFACE SETUP ---
st.set_page_config(page_title="Zafar Logistics ERP", layout="wide")

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "username" not in st.session_state: st.session_state["username"] = ""
if "user_role" not in st.session_state: st.session_state["user_role"] = ""

# --- GLOBAL INTERACTIVE GLASSMORPHIC INTERFACE INJECTOR ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
.stApp { background-color: #f8fafc; font-family: 'Plus Jakarta Sans', sans-serif; }
.dashboard-header { font-family: 'Plus Jakarta Sans', sans-serif; color: #0f172a; font-size: 1.8rem; font-weight: 700; margin-bottom: 25px; margin-top: -15px; }
.glass-card-wrapper { display: flex; gap: 20px; margin-bottom: 25px; flex-wrap: wrap; }
.glass-card { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.5); padding: 16px 24px; border-radius: 16px; min-width: 200px; flex: 1; box-shadow: 0 4px 30px rgba(0, 0, 0, 0.02); display: flex; align-items: center; gap: 15px; }
.glass-card-value { font-size: 1.8rem; font-weight: 700; color: #1e293b; line-height: 1; }
.glass-card-label { font-size: 0.85rem; color: #64748b; font-weight: 500; }
.custom-card { background: #ffffff; padding: 20px; border-radius: 16px; box-shadow: 0px 4px 20px rgba(0,0,0,0.01); border: 1px solid #f1f5f9; margin-bottom: 20px; }
.card-title { font-size: 1rem; font-weight: 600; color: #334155; margin-bottom: 15px; }
.stDownloadButton>button { background-color: #ffffff !important; color: #1e293b !important; border: 1px solid #e2e8f0 !important; border-radius: 10px !important; font-weight: 600 !important; padding: 8px 16px !important; box-shadow: 0px 2px 4px rgba(0,0,0,0.02); transition: all 0.2s ease; }
.stDownloadButton>button:hover { background-color: #f8fafc !important; border-color: #cbd5e1 !important; }
div[data-testid="stDataFrame"] table th { background-color: #f8fafc !important; color: #475569 !important; font-weight: 600 !important; font-size: 0.85rem !important; border-bottom: 1px solid #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

# --- LOGIN SCREEN ---
if not st.session_state["logged_in"]:
    st.markdown("""
    <style>
    [data-testid="stHeader"], [data-testid="stSidebar"] { display: none !important; }
    .login-container { display: flex; flex-direction: row; background-color: #ffffff; border-radius: 12px; box-shadow: 0px 8px 24px rgba(0,0,0,0.12); overflow: hidden; margin-top: 5%; min-height: 480px; border: 1px solid #e2e8f0; }
    .left-banner { background

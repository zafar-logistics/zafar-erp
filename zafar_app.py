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

# --- INTERFACE SETUP ---
st.set_page_config(page_title="Zafar Logistics ERP", layout="wide")

if "logged_in" not in st.session_state: 
    st.session_state["logged_in"] = False
if "username" not in st.session_state: 
    st.session_state["username"] = ""
if "user_role" not in st.session_state: 
    st.session_state["user_role"] = ""

# --- 🚀 GLOBAL INTERACTIVE GLASSMORPHIC INTERFACE INJECTOR ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        
        .stApp {
            background-color: #f8fafc;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        
        /* Dashboard Top Header */
        .dashboard-header {
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #0f172a;
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 25px;
            margin-top: -15px;
        }
        
        /* Glassmorphism Summary Cards Layout */
        .glass-card-wrapper {
            display: flex;
            gap: 20px;
            margin-bottom: 25px;
            flex-wrap

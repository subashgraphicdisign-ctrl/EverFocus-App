import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- 🔐 CLOUD CONNECTION ---
# ඔයාගේ Supabase විස්තර මෙතන තියෙනවා
URL = "https://euwkypgzqmbqtigoluza.supabase.co"
KEY = "sb_publishable_v4ePATXMmbnE4aRxwjsIhA_9CsjORUJ"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Ever Focus Technologies", page_icon="🚀", layout="wide")

# --- UI STYLE (TECHNOLOGY THEME) ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #0a192f, #020c1b); color: #e6f1ff; }
    .company-header {
        text-align: center !important; 
        background: -webkit-linear-gradient(#00d4ff, #0072ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-family: 'Segoe UI', sans-serif; font-size: 3rem !important;
        font-weight: 800; margin-top: -40px; letter-spacing: 2px; text-transform: uppercase;
    }
    .developer-tag { text-align: center !important; color: #64ffda; font-family: 'Courier New', monospace; font-size: 1rem; margin-bottom: 40px; opacity: 0.8; }
    div[data-testid="stMetric"] { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); padding: 20px; border-radius: 15px; backdrop-filter: blur(10px); }
    .stApp label, .stWidgetLabel p { color: #00d4ff !important; font-weight: 600 !important; }
    .stButton>button { width: 100%; border-radius: 8px; border: 1px solid #64ffda; color: #64ffda; background: rgba(100, 255, 218, 0.05); font-weight: bold; height: 3em; }
    .stButton>button:hover { background: #64ffda; color: #020c1b; box-shadow: 0 0 20px rgba(100, 255, 218, 0.4); }
    [data-testid="stSidebar"] { background-color: #0a192f; border-right: 1px solid rgba(100, 255, 218, 0.1); }
    </style>
    """, unsafe_allow_html=True)

# Session States
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'allowed_tabs' not in st.session_state: st.session_state.allowed_tabs = []

st.markdown("<div class='company-header'>EVER FOCUS TECHNOLOGIES</div>", unsafe_allow_html=True)
st.markdown("<div class='developer-tag'>POWERED BY : PESHALA SUBHASH</div>", unsafe_allow_html=True)

# --- 📊 FUNCTIONS ---
def fetch_inventory_summary(table_name):
    try:
        res = supabase.table(table_name).select("item_name, quantity").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            summary = df.groupby('item_name')['quantity'].sum().reset_index()
            return summary[summary['quantity'] != 0]
    except: pass
    return pd.DataFrame(columns=['item_name', 'quantity'])

def log_to_archive(site, loc, item_name, qty_val, type_label, serial="None"):
    supabase.table('transactions').insert({"site_name": site, "location": loc, "item": item_name, "qty": qty_val, "type": type_label, "serial_no": serial}).execute()

# --- LOGIN SYSTEM ---
if not st.session_state.auth:
    with st.columns([1,1.5,1])[1]:
        st.markdown("<h3 style='text-align:center; color:#64ffda;'>SECURE ACCESS</h3>", unsafe_allow_html=True)
        u = st.text_input("USER ID")
        p = st.text_input("PASSWORD", type="password")
        if st.button("AUTHENTICATE"):
            res = supabase.table('users').select("*").eq('username', u).eq('password', p).execute()
            if res.data and len(res.data) > 0:
                user = res.data[0]
                st.session_state.auth = True
                st.session_state.user_name = user['username']
                # Permissions ලෝඩ් කිරීම
                raw_menus = user.get('allowed_menus', "📊 DASHBOARD")
                st.session_state.allowed_tabs = [i.strip() for i in raw_menus.split(',')]
                st.rerun()
            else:
                st.error("Invalid Credentials")
else:
    # Sidebar Navigation based on Database Permissions
    choice = st.sidebar.selectbox("PROTOCOL CONTROL", st.session_state.allowed_tabs)
    st.sidebar.write(f"Logged in as: **{st.session_state.user_name}**")

    # 1. DASHBOARD
    if choice == "📊 DASHBOARD":
        m_df = fetch_inventory_summary('inventory')
        t_df = fetch_inventory_summary('truck_stock')
        c1, c2 = st.columns(2)
        c1.metric("MAIN STORE", f"{int(m_df['quantity'].sum()) if not m_df.empty else 0} PKTS")
        c2.metric("TRUCK PAYLOAD", f"{int(t_df['quantity'].sum()) if not t_df.empty else 0} PKTS")
        st.divider()
        st.subheader("Inventory Status")
        st.dataframe(m_df, use_container_width=True, hide_index=True)

    # 2. ADD RESOURCE
    elif choice == "📥 ADD RESOURCE":
        st.subheader("Stock Entry")
        item = st.text_input("New Item Name")
        qty = st.number_input("Quantity", min_value=1)
        if st.button("Update Cloud"):
            supabase.table('inventory').insert({"item_name": item, "quantity": qty}).execute()
            log_to_archive("MAIN STORE", "ENTRY", item, qty, "STOCK IN")
            st.success("Synchronized with Cloud")

    # 3. TRUCK LOGISTICS
    elif choice == "🚛 TRUCK LOGISTICS":
        st.subheader("Truck Transfer")
        m_df = fetch_inventory_summary('inventory')
        item = st.selectbox("Select Resource", m_df['item_name'].unique() if not m_df.empty else [])
        qty = st.number_input("Transfer Qty", min_value=1)
        if st.button("Authorize Transfer"):
            supabase.table('inventory').insert({"item_name": item, "quantity": -qty}).execute()
            supabase.table('truck_stock').insert({"item_name": item, "quantity": qty}).execute()
            log_to_archive("TRUCK", "LOAD", item, qty, "TRANSFER")
            st.success("Transfer Completed")

    # 4. SITE DEPLOYMENT
    elif choice == "🏗️ SITE DEPLOYMENT":
        st.subheader("Field Deployment")
        site = st.text_input("Site ID")
        loc = st.text_input("Location")
        t_df = fetch_inventory_summary('truck_stock')
        item = st.selectbox("Item from Truck", t_df['item_name'].unique() if not t_df.empty else [])
        qty = st.number_input("Qty", min_value=1)
        if st.button("Confirm Deployment"):
            supabase.table('truck_stock').insert({"item_name": item, "quantity": -qty}).execute()
            log_to_archive(site, loc, item, qty, "SITE ISSUE")
            st.success("Deployed Successfully")

    # 5. DATA ARCHIVE
    elif choice == "📜 DATA ARCHIVE":
        st.subheader("History Log")
        res = supabase.table('transactions').select("*").order('created_at', desc=True).execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data), use_container_width=True)

    # 6. MANAGE USERS (ඔයාට විතරයි පේන්නේ)
    elif choice == "MANAGE USERS":
        st.subheader("👥 User Management")
        with st.expander("Add New Employee"):
            new_u = st.text_input("New Username")
            new_p = st.text_input("New Password")
            options = ["📊 DASHBOARD", "📥 ADD RESOURCE", "🚛 TRUCK LOGISTICS", "🏗️ SITE DEPLOYMENT", "📜 DATA ARCHIVE"]
            selected_tabs = st.multiselect("Assign Access", options)
            if st.button("Create"):
                perms = ",".join(selected_tabs)
                supabase.table('users').insert({"username": new_u, "password": new_p, "role": "EMPLOYEE", "allowed_menus": perms}).execute()
                st.success(f"User {new_u} created!")

    if st.sidebar.button("Logout"):
        st.session_state.auth = False
        st.rerun()
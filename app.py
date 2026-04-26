import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- 🔐 CLOUD CONNECTION ---
URL = "https://euwkypgzqmbqtigoluza.supabase.co"
KEY = "sb_publishable_v4ePATXMmbnE4aRxwjsIhA_9CsjORUJ"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Ever Focus Technologies", page_icon="🚀", layout="wide")

# --- UI STYLE (HIGH-TECH TECHNOLOGY THEME) ---
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
    .stApp label, .stWidgetLabel p { color: #00d4ff !important; font-weight: 600 !important; letter-spacing: 0.5px; }
    .stButton>button { width: 100%; border-radius: 8px; border: 1px solid #64ffda; color: #64ffda; background: rgba(100, 255, 218, 0.05); font-weight: bold; transition: all 0.3s ease; height: 3em; }
    .stButton>button:hover { background: #64ffda; color: #020c1b; box-shadow: 0 0 20px rgba(100, 255, 218, 0.4); }
    [data-testid="stSidebar"] { background-color: #0a192f; border-right: 1px solid rgba(100, 255, 218, 0.1); }
    .stDataFrame { border: 1px solid rgba(0, 212, 255, 0.2); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Session States for Auth & User Info
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'allowed_tabs' not in st.session_state: st.session_state.allowed_tabs = []
if 'user_name' not in st.session_state: st.session_state.user_name = ""

st.markdown("<div class='company-header'>EVER FOCUS TECHNOLOGIES</div>", unsafe_allow_html=True)
st.markdown("<div class='developer-tag'>POWERED BY : PESHALA SUBHASH</div>", unsafe_allow_html=True)

# --- 📊 SMART DATA FETCHING ---
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
    try:
        supabase.table('transactions').insert({
            "site_name": site, "location": loc, "item": item_name, 
            "qty": qty_val, "type": type_label, "serial_no": serial
        }).execute()
    except Exception as e:
        st.error(f"Archive Write Error: {e}")

# --- LOGIN SYSTEM ---
if not st.session_state.auth:
    with st.columns([1,1.5,1])[1]:
        st.markdown("<h3 style='text-align:center; color:#64ffda;'>SECURE ACCESS</h3>", unsafe_allow_html=True)
        u = st.text_input("USER ID")
        p = st.text_input("PASSWORD", type="password")
        if st.button("AUTHENTICATE"):
            # Check users table in Supabase
            res = supabase.table('users').select("*").eq('username', u).eq('password', p).execute()
            if res.data:
                user = res.data[0]
                st.session_state.auth = True
                st.session_state.user_name = user['username']
                st.session_state.user_role = user['role']
                # මෙතනින් තමයි අවසර දීපු ටැබ්ස් ටික ලෝඩ් කරන්නේ
                st.session_state.allowed_tabs = user['allowed_menus'].split(',')
                st.rerun()
            else:
                st.error("Invalid Credentials or Access Denied")
else:
    # Navigation based on DB permissions
    menu = st.session_state.allowed_tabs
    choice = st.sidebar.selectbox("PROTOCOL CONTROL", menu)
    st.sidebar.markdown(f"**Current User:** {st.session_state.user_name}")
    st.sidebar.markdown(f"**Access:** {st.session_state.user_role}")

    # 1. DASHBOARD
    if choice == "📊 DASHBOARD":
        m_df = fetch_inventory_summary('inventory')
        t_df = fetch_inventory_summary('truck_stock')
        c1, c2 = st.columns(2)
        c1.metric("MAIN STORE", f"{int(m_df['quantity'].sum()) if not m_df.empty else 0} PKTS")
        c2.metric("TRUCK PAYLOAD", f"{int(t_df['quantity'].sum()) if not t_df.empty else 0} PKTS")
        st.divider()
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("📦 Main Inventory")
            st.dataframe(m_df, use_container_width=True, hide_index=True)
        with col_right:
            st.subheader("🚛 Truck Payload")
            st.dataframe(t_df, use_container_width=True, hide_index=True)

    # 2. ADD RESOURCE
    elif choice == "📥 ADD RESOURCE":
        st.subheader("Stock Entry Protocol")
        item = st.text_input("New Item Name")
        qty = st.number_input("Quantity", min_value=1)
        if st.button("Update Cloud Database"):
            supabase.table('inventory').insert({"item_name": item, "quantity": qty}).execute()
            log_to_archive("MAIN STORE", "ENTRY", item, qty, "STOCK IN")
            st.success("Cloud Synchronization Complete")

    # 3. TRUCK LOGISTICS
    elif choice == "🚛 TRUCK LOGISTICS":
        st.subheader("Logistics Transfer")
        m_df = fetch_inventory_summary('inventory')
        item_list = m_df['item_name'].unique() if not m_df.empty else []
        item = st.selectbox("Select Resource", item_list)
        qty = st.number_input("Transfer Quantity", min_value=1)
        if st.button("Authorize Transfer"):
            supabase.table('inventory').insert({"item_name": item, "quantity": -qty}).execute()
            supabase.table('truck_stock').insert({"item_name": item, "quantity": qty}).execute()
            log_to_archive("TRUCK", "LOAD", item, qty, "TRANSFER")
            st.success("Logistics Route Verified")

    # 4. SITE DEPLOYMENT
    elif choice == "🏗️ SITE DEPLOYMENT":
        st.subheader("Field Deployment")
        site = st.text_input("Client/Site ID")
        loc = st.text_input("Geo Location")
        serial_no = st.text_input("Asset Serial Number")
        t_df = fetch_inventory_summary('truck_stock')
        item_list = t_df['item_name'].unique() if not t_df.empty else []
        item = st.selectbox("Resource from Truck", item_list)
        qty = st.number_input("Deployment Qty", min_value=1)
        if st.button("Confirm Deployment"):
            supabase.table('truck_stock').insert({"item_name": item, "quantity": -qty}).execute()
            log_to_archive(site, loc, item, qty, "SITE ISSUE", serial_no)
            st.success(f"Deployed to {site}")

    # 5. DATA ARCHIVE
    elif choice == "📜 DATA ARCHIVE":
        st.subheader("Transaction Intelligence")
        search = st.text_input("🔍 Query Database (Site, Item, Serial)")
        res = supabase.table('transactions').select("*").order('created_at', desc=True).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            if search:
                df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            df = df.rename(columns={'created_at':'TIMESTAMP','site_name':'CLIENT','location':'LOCATION','item':'RESOURCE','qty':'QTY','type':'STATUS','serial_no':'SERIAL_ID'})
            cols = ['TIMESTAMP', 'CLIENT', 'LOCATION', 'RESOURCE', 'SERIAL_ID', 'QTY', 'STATUS']
            st.dataframe(df[cols], use_container_width=True, hide_index=True)

    # 6. --- 🛠️ MANAGE USERS (ඔයාට විතරයි) ---
    elif choice == "MANAGE USERS":
        st.subheader("👥 System User Management")
        with st.expander("➕ Add New Employee Profile"):
            new_u = st.text_input("Employee Username")
            new_p = st.text_input("Employee Password")
            # මෙතනින් ඔයාට ඕන ටැබ්ස් ටික සේවකයා අනුව තෝරන්න පුළුවන්
            options = ["📊 DASHBOARD", "📥 ADD RESOURCE", "🚛 TRUCK LOGISTICS", "🏗️ SITE DEPLOYMENT", "📜 DATA ARCHIVE"]
            selected_tabs = st.multiselect("Select Access Permissions", options)
            
            if st.button("Create Account"):
                if new_u and new_p and selected_tabs:
                    perms = ",".join(selected_tabs)
                    supabase.table('users').insert({
                        "username": new_u, "password": new_p, 
                        "role": "EMPLOYEE", "allowed_menus": perms
                    }).execute()
                    st.success(f"User {new_u} created successfully!")
                else:
                    st.warning("Please fill all details and select at least one permission.")

        st.divider()
        st.write("Current Access Ledger:")
        u_res = supabase.table('users').select("username, role, allowed_menus").execute()
        if u_res.data:
            st.table(pd.DataFrame(u_res.data))

    if st.sidebar.button("System Logout"):
        st.session_state.auth = False
        st.rerun()

# --- FOOTER ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #64ffda; font-size: 0.8rem; font-family: monospace;'>EVER FOCUS CLOUD NETWORK v6.0 | POWERED BY: PESHALA SUBHASH</div>", unsafe_allow_html=True)
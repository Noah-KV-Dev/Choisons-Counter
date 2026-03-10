import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Choisons Counter", layout="wide")
st.title("⛽ Choisons Petroleum Counter")
st.markdown("<p style='text-align:right; font-size:12px; color:gray;'>Created by Nazeeh</p>", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("counter.db", check_same_thread=False)
cursor = conn.cursor()

# Transactions table
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions(
id INTEGER PRIMARY KEY AUTOINCREMENT,
date TEXT,
cashier TEXT,
type TEXT,
amount REAL,
note TEXT
)
""")

# Staff advance table
cursor.execute("""
CREATE TABLE IF NOT EXISTS staff_advance(
id INTEGER PRIMARY KEY AUTOINCREMENT,
date TEXT,
staff TEXT,
type TEXT,
amount REAL,
note TEXT
)
""")

conn.commit()

# ---------------- SESSION ----------------
if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.role = ""
    st.session_state.user = ""

if "openings" not in st.session_state:
    st.session_state.openings = {}

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# ---------------- LOGIN ----------------
if not st.session_state.login:

    st.header("Login")

    role = st.selectbox("Login as", ["Cashier","Admin"])
    user = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if role == "Admin":
            if user == ADMIN_USER and password == ADMIN_PASS:
                st.session_state.login = True
                st.session_state.role = "Admin"
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Wrong Admin Login")

        else:
            st.session_state.login = True
            st.session_state.role = "Cashier"
            st.session_state.user = user
            st.rerun()

# ---------------- MAIN SYSTEM ----------------
else:

    st.success(f"Logged in as {st.session_state.user}")

    # ---------------- OPENING BALANCE ----------------
    st.header("Opening Balance")

    opening = st.number_input(
        f"{st.session_state.user} Opening Cash ₹",
        min_value=0.0
    )

    st.session_state.openings[st.session_state.user] = opening

    # ---------------- TRANSACTION ENTRY ----------------
    st.header("Transaction Entry")

    col1,col2,col3 = st.columns(3)

    with col1:
        t_type = st.selectbox(
            "Transaction Type",
            [
                "Sales",
                "Receipt",
                "Credit Receipt",
                "Bank Withdrawal",
                "Paytm Receipt",
                "Payment",
                "Bank Deposit",
                "Paytm Payment",
                "SBI",
                "KDC"
            ]
        )

    with col2:
        amount = st.number_input("Amount ₹", min_value=0.0)

    with col3:
        t_date = st.date_input("Date", date.today())

    note = st.text_input("Note")

    if st.button("Save Transaction"):

        cursor.execute(
            "INSERT INTO transactions (date,cashier,type,amount,note) VALUES (?,?,?,?,?)",
            (str(t_date),st.session_state.user,t_type,amount,note)
        )

        conn.commit()

        st.success("Transaction Saved")

    # ---------------- STAFF ADVANCE ENTRY ----------------
    st.header("Staff Advance")

    col1,col2,col3,col4 = st.columns(4)

    with col1:
        staff_name = st.text_input("Staff Name")

    with col2:
        adv_type = st.selectbox(
            "Advance Type",
            ["Advance Paid","Advance Received"]
        )

    with col3:
        adv_amount = st.number_input("Advance Amount ₹",min_value=0.0)

    with col4:
        adv_date = st.date_input("Advance Date")

    adv_note = st.text_input("Advance Note")

    if st.button("Save Advance"):

        cursor.execute(
            "INSERT INTO staff_advance (date,staff,type,amount,note) VALUES (?,?,?,?,?)",
            (str(adv_date),staff_name,adv_type,adv_amount,adv_note)
        )

        conn.commit()
        st.success("Staff Advance Saved")

    # ---------------- LOAD DATA ----------------
    cash_df = pd.read_sql("SELECT * FROM transactions",conn)
    advance_df = pd.read_sql("SELECT * FROM staff_advance",conn)

    if not cash_df.empty:
        cash_df["date"] = pd.to_datetime(cash_df["date"])

    if not advance_df.empty:
        advance_df["date"] = pd.to_datetime(advance_df["date"])

    # ---------------- BALANCE TYPES ----------------

    cash_in_types = ["Sales","Receipt","Credit Receipt","Bank Withdrawal"]
    cash_out_types = ["Payment","Bank Deposit"]

    paytm_in_types = ["Paytm Receipt"]
    paytm_out_types = ["Paytm Payment"]

    sbi_types = ["SBI"]
    kdc_types = ["KDC"]

    if not cash_df.empty:

        cash_in = cash_df[cash_df["type"].isin(cash_in_types)]["amount"].sum()
        cash_out = cash_df[cash_df["type"].isin(cash_out_types)]["amount"].sum()

        paytm_in = cash_df[cash_df["type"].isin(paytm_in_types)]["amount"].sum()
        paytm_out = cash_df[cash_df["type"].isin(paytm_out_types)]["amount"].sum()

        sbi_total = cash_df[cash_df["type"].isin(sbi_types)]["amount"].sum()
        kdc_total = cash_df[cash_df["type"].isin(kdc_types)]["amount"].sum()

    else:

        cash_in=cash_out=paytm_in=paytm_out=sbi_total=kdc_total=0

    total_opening = sum(st.session_state.openings.values())

    cash_balance = total_opening + cash_in - cash_out
    paytm_balance = paytm_in - paytm_out
    sbi_balance = -sbi_total
    kdc_balance = -kdc_total

    # ---------------- BALANCE DASHBOARD ----------------
    st.header("Balances")

    b1,b2,b3,b4 = st.columns(4)

    b1.metric("Cash Balance",f"₹{cash_balance:,.2f}")
    b2.metric("Paytm Balance",f"₹{paytm_balance:,.2f}")
    b3.metric("SBI Balance",f"₹{sbi_balance:,.2f}")
    b4.metric("KDC Balance",f"₹{kdc_balance:,.2f}")

    # ---------------- COLLECTION DASHBOARD ----------------
    st.header("Collection Dashboard")

    total_sales = cash_df[cash_df["type"]=="Sales"]["amount"].sum() if not cash_df.empty else 0

    d1,d2 = st.columns(2)

    d1.metric("Total Sales",f"₹{total_sales:,.2f}")
    d2.metric("Total Collection",f"₹{cash_in:,.2f}")

    # ---------------- TRANSACTION HISTORY ----------------
    st.header("Transaction History")

    opening_rows=[]

    for cashier,value in st.session_state.openings.items():

        opening_rows.append({
            "id":"-",
            "date":str(date.today()),
            "cashier":cashier,
            "type":"Opening Balance",
            "amount":value,
            "note":"Opening Cash"
        })

    opening_df=pd.DataFrame(opening_rows)

    if not cash_df.empty:
        history_df=pd.concat([opening_df,cash_df],ignore_index=True)
    else:
        history_df=opening_df

    st.dataframe(history_df)

    # ---------------- STAFF ADVANCE SUMMARY ----------------
    st.header("Staff Advance Summary")

    if not advance_df.empty:

        paid_df = advance_df[advance_df["type"]=="Advance Paid"]
        received_df = advance_df[advance_df["type"]=="Advance Received"]

        paid_summary = paid_df.groupby("staff")["amount"].sum()
        received_summary = received_df.groupby("staff")["amount"].sum()

        staff_summary = pd.DataFrame({
            "Advance Paid": paid_summary,
            "Advance Received": received_summary
        }).fillna(0)

        st.dataframe(staff_summary)

    else:

        st.info("No staff advance records")

    # ---------------- STAFF ADVANCE HISTORY ----------------
    st.header("Staff Advance History")

    if not advance_df.empty:
        st.dataframe(advance_df)

    # ---------------- ADMIN DELETE ----------------
    if st.session_state.role=="Admin" and not cash_df.empty:

        st.header("Delete Transaction")

        delete_id=st.selectbox("Select Transaction ID",cash_df["id"])

        if st.button("Delete Transaction"):

            cursor.execute("DELETE FROM transactions WHERE id=?",(delete_id,))
            conn.commit()

            st.success("Transaction Deleted")
            st.rerun()

    # ---------------- DAILY BALANCE ----------------
    if not cash_df.empty:

        st.header("Daily Balance")

        daily=cash_df.groupby(cash_df["date"].dt.date)["amount"].sum().reset_index()

        st.dataframe(daily)

    # ---------------- MONTHLY BALANCE ----------------
    if not cash_df.empty:

        st.header("Monthly Balance")

        cash_df["month"]=cash_df["date"].dt.to_period("M")

        monthly=cash_df.groupby("month")["amount"].sum().reset_index()

        monthly["month"]=monthly["month"].astype(str)

        st.dataframe(monthly)

    # ---------------- LOGOUT ----------------
    if st.button("Logout"):

        st.session_state.login=False
        st.rerun()

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("<p style='text-align:right; font-size:12px; color:gray;'>Created by Nazeeh</p>", unsafe_allow_html=True)

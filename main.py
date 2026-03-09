import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

st.set_page_config(page_title="Cash Counter System", layout="wide")

st.title("⛽ Petrol Pump Cash Counter")

# ---------------- DATABASE ----------------

conn = sqlite3.connect("cash_counter.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS cashiers(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS cash_transactions(
id INTEGER PRIMARY KEY AUTOINCREMENT,
date TEXT,
cashier TEXT,
type TEXT,
amount REAL,
note TEXT
)
""")

conn.commit()

# ---------------- ADMIN LOGIN ----------------

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.role = ""
    st.session_state.user = ""

# ---------------- LOGIN SCREEN ----------------

if not st.session_state.login:

    st.header("Login")

    role = st.selectbox("Login As",["Cashier","Admin"])

    username = st.text_input("Username")
    password = st.text_input("Password",type="password")

    if st.button("Login"):

        if role == "Admin":

            if username == ADMIN_USER and password == ADMIN_PASS:

                st.session_state.login = True
                st.session_state.role = "Admin"
                st.session_state.user = username

                st.rerun()

            else:
                st.error("Wrong Admin Login")

        else:

            df = pd.read_sql("SELECT * FROM cashiers",conn)

            user = df[(df["name"]==username) & (df["password"]==password)]

            if not user.empty:

                st.session_state.login = True
                st.session_state.role = "Cashier"
                st.session_state.user = username

                st.rerun()

            else:
                st.error("Invalid Cashier Login")

# ---------------- MAIN SYSTEM ----------------

else:

    st.success(f"Logged in as {st.session_state.user} ({st.session_state.role})")

    # ---------------- ADMIN PANEL ----------------

    if st.session_state.role == "Admin":

        st.header("Admin Controls")

        new_name = st.text_input("New Cashier Name")
        new_pass = st.text_input("Cashier Password")

        if st.button("Add Cashier"):

            cursor.execute(
            "INSERT INTO cashiers (name,password) VALUES (?,?)",
            (new_name,new_pass)
            )

            conn.commit()

            st.success("Cashier Added")

        st.subheader("Cashier List")

        cashiers = pd.read_sql("SELECT * FROM cashiers",conn)

        st.dataframe(cashiers)

    # ---------------- OPENING BALANCE ----------------

    st.header("Opening Balance")

    opening_balance = st.number_input("Opening Cash ₹",min_value=0.0)

    # ---------------- TRANSACTION ENTRY ----------------

    st.header("Cash Transaction")

    c1,c2,c3 = st.columns(3)

    with c1:
        transaction_type = st.selectbox(
        "Transaction Type",
        ["Receipt","Payment","Bank Transfer","Bank Deposit"]
        )

    with c2:
        amount = st.number_input("Amount ₹",min_value=0.0)

    with c3:
        trans_date = st.date_input("Date",date.today())

    note = st.text_input("Note")

    if st.button("Save Transaction"):

        cursor.execute(
        "INSERT INTO cash_transactions (date,cashier,type,amount,note) VALUES (?,?,?,?,?)",
        (str(trans_date),st.session_state.user,transaction_type,amount,note)
        )

        conn.commit()

        st.success("Transaction Saved")

    # ---------------- LOAD DATA ----------------

    df = pd.read_sql("SELECT * FROM cash_transactions",conn)

    if not df.empty:

        df["date"] = pd.to_datetime(df["date"])

        receipts = df[df["type"]=="Receipt"]["amount"].sum()
        payments = df[df["type"]=="Payment"]["amount"].sum()
        transfers = df[df["type"]=="Bank Transfer"]["amount"].sum()
        deposits = df[df["type"]=="Bank Deposit"]["amount"].sum()

        closing = opening_balance + receipts - payments - transfers - deposits

        st.header("Cash Summary")

        a,b,c,d,e = st.columns(5)

        a.metric("Opening Balance",opening_balance)
        b.metric("Receipts",receipts)
        c.metric("Payments",payments)
        d.metric("Bank Transfers",transfers)
        e.metric("Bank Deposits",deposits)

        st.metric("Closing Balance",closing)

    # ---------------- TRANSACTION HISTORY ----------------

    st.header("Transaction History")

    st.dataframe(df,use_container_width=True)

    # ---------------- DAILY BALANCE ----------------

    if not df.empty:

        st.header("Daily Balance")

        daily = df.groupby(df["date"].dt.date).apply(
        lambda x:
        opening_balance
        + x[x["type"]=="Receipt"]["amount"].sum()
        - x[x["type"]=="Payment"]["amount"].sum()
        - x[x["type"]=="Bank Transfer"]["amount"].sum()
        - x[x["type"]=="Bank Deposit"]["amount"].sum()
        ).reset_index(name="Daily Balance")

        st.dataframe(daily)

    # ---------------- MONTHLY BALANCE ----------------

        st.header("Monthly Balance")

        df["month"] = df["date"].dt.to_period("M")

        monthly = df.groupby("month").apply(
        lambda x:
        opening_balance
        + x[x["type"]=="Receipt"]["amount"].sum()
        - x[x["type"]=="Payment"]["amount"].sum()
        - x[x["type"]=="Bank Transfer"]["amount"].sum()
        - x[x["type"]=="Bank Deposit"]["amount"].sum()
        ).reset_index(name="Monthly Balance")

        monthly["month"] = monthly["month"].astype(str)

        st.dataframe(monthly)

    # ---------------- LOGOUT ----------------

    if st.button("Logout"):

        st.session_state.login = False
        st.rerun()

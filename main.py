import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

st.set_page_config(page_title="Petrol Pump Cash System", layout="wide")
st.title("⛽ Petrol Pump Cash Counter")
st.list("                  Created by naseeh")
# ---------------- DATABASE ----------------

conn = sqlite3.connect("petrol_cash.db", check_same_thread=False)
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

# ---------------- LOGIN SESSION ----------------

if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.role = ""
    st.session_state.user = ""

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# ---------------- LOGIN PAGE ----------------

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
                st.error("Wrong admin login")

        else:

            df = pd.read_sql("SELECT * FROM cashiers", conn)

            check = df[(df["name"]==user) & (df["password"]==password)]

            if not check.empty:

                st.session_state.login = True
                st.session_state.role = "Cashier"
                st.session_state.user = user
                st.rerun()

            else:
                st.error("Invalid cashier")

# ---------------- SYSTEM ----------------

else:

    st.success(f"Logged in as {st.session_state.user}")

    # ---------------- ADMIN PANEL ----------------

    if st.session_state.role == "Admin":

        st.header("Admin Panel")

        new_name = st.text_input("Cashier Name")
        new_pass = st.text_input("Cashier Password")

        if st.button("Add Cashier"):

            cursor.execute(
            "INSERT INTO cashiers (name,password) VALUES (?,?)",
            (new_name,new_pass)
            )

            conn.commit()

            st.success("Cashier added")

        st.subheader("Cashiers")

        st.dataframe(pd.read_sql("SELECT * FROM cashiers",conn))

    # ---------------- OPENING BALANCE ----------------

    st.header("Opening Balance")

    opening = st.number_input("Opening Cash ₹", min_value=0.0)

    # ---------------- CASH TRANSACTION ----------------

    st.header("Cash Transactions")

    col1,col2,col3 = st.columns(3)

    with col1:
        t_type = st.selectbox(
        "Transaction Type",
        ["Receipt","Payment","Bank Transfer","Bank Deposit"]
        )

    with col2:
        amount = st.number_input("Amount ₹", min_value=0.0)

    with col3:
        t_date = st.date_input("Date",date.today())

    note = st.text_input("Note")

    if st.button("Save Transaction"):

        cursor.execute(
        "INSERT INTO cash_transactions (date,cashier,type,amount,note) VALUES (?,?,?,?,?)",
        (str(t_date),st.session_state.user,t_type,amount,note)
        )

        conn.commit()

        st.success("Transaction saved")

    # ---------------- STAFF ADVANCE ----------------

    st.header("Staff Advance")

    a1,a2,a3,a4 = st.columns(4)

    with a1:
        staff = st.text_input("Staff Name")

    with a2:
        adv_type = st.selectbox(
        "Type",
        ["Advance Payment","Advance Received"]
        )

    with a3:
        adv_amt = st.number_input("Advance Amount ₹",min_value=0.0)

    with a4:
        adv_date = st.date_input("Advance Date",date.today())

    adv_note = st.text_input("Advance Note")

    if st.button("Save Advance"):

        cursor.execute(
        "INSERT INTO staff_advance (date,staff,type,amount,note) VALUES (?,?,?,?,?)",
        (str(adv_date),staff,adv_type,adv_amt,adv_note)
        )

        conn.commit()

        st.success("Advance saved")

    # ---------------- LOAD DATA ----------------

    cash_df = pd.read_sql("SELECT * FROM cash_transactions",conn)

    if not cash_df.empty:

        cash_df["date"] = pd.to_datetime(cash_df["date"])

        receipts = cash_df[cash_df["type"]=="Receipt"]["amount"].sum()
        payments = cash_df[cash_df["type"]=="Payment"]["amount"].sum()
        transfers = cash_df[cash_df["type"]=="Bank Transfer"]["amount"].sum()
        deposits = cash_df[cash_df["type"]=="Bank Deposit"]["amount"].sum()

        closing = opening + receipts - payments - transfers - deposits

        st.header("Cash Balance")

        c1,c2,c3,c4,c5 = st.columns(5)

        c1.metric("Opening",opening)
        c2.metric("Receipts",receipts)
        c3.metric("Payments",payments)
        c4.metric("Transfers",transfers)
        c5.metric("Deposits",deposits)

        st.metric("Closing Cash Balance",closing)

    # ---------------- STAFF ADVANCE BALANCE ----------------

    st.header("Staff Advance Balance")

    adv_df = pd.read_sql("SELECT * FROM staff_advance",conn)

    if not adv_df.empty:

        paid = adv_df[adv_df["type"]=="Advance Payment"]
        received = adv_df[adv_df["type"]=="Advance Received"]

        paid_sum = paid.groupby("staff")["amount"].sum()
        rec_sum = received.groupby("staff")["amount"].sum()

        balance = (paid_sum - rec_sum).fillna(0)

        staff_balance = balance.reset_index()
        staff_balance.columns = ["Staff","Advance Balance"]

        st.dataframe(staff_balance)

    # ---------------- TRANSACTION HISTORY ----------------

    st.header("Transaction History")

    st.dataframe(cash_df)

    # ---------------- ADMIN EDIT ----------------

    if st.session_state.role == "Admin" and not cash_df.empty:

        st.header("Edit Transaction")

        tid = st.selectbox("Transaction ID",cash_df["id"])

        row = cash_df[cash_df["id"]==tid].iloc[0]

        new_amt = st.number_input("Edit Amount",value=float(row["amount"]))
        new_note = st.text_input("Edit Note",value=row["note"])

        if st.button("Update"):

            cursor.execute(
            "UPDATE cash_transactions SET amount=?,note=? WHERE id=?",
            (new_amt,new_note,tid)
            )

            conn.commit()

            st.success("Updated")

    # ---------------- DAILY BALANCE ----------------

    if not cash_df.empty:

        st.header("Daily Balance")

        daily = cash_df.groupby(cash_df["date"].dt.date).apply(
        lambda x:
        opening
        + x[x["type"]=="Receipt"]["amount"].sum()
        - x[x["type"]=="Payment"]["amount"].sum()
        - x[x["type"]=="Bank Transfer"]["amount"].sum()
        - x[x["type"]=="Bank Deposit"]["amount"].sum()
        ).reset_index(name="Balance")

        st.dataframe(daily)

        # ---------------- MONTHLY BALANCE ----------------

        st.header("Monthly Balance")

        cash_df["month"] = cash_df["date"].dt.to_period("M")

        monthly = cash_df.groupby("month").apply(
        lambda x:
        opening
        + x[x["type"]=="Receipt"]["amount"].sum()
        - x[x["type"]=="Payment"]["amount"].sum()
        - x[x["type"]=="Bank Transfer"]["amount"].sum()
        - x[x["type"]=="Bank Deposit"]["amount"].sum()
        ).reset_index(name="Balance")

        monthly["month"] = monthly["month"].astype(str)

        st.dataframe(monthly)

    # ---------------- LOGOUT ----------------

    if st.button("Logout"):

        st.session_state.login = False
        st.rerun()



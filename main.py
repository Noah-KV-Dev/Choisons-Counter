import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

st.set_page_config(page_title="Petrol Pump Cash Counter", layout="wide")

st.title("⛽ Petrol Pump Cash Counter")

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

# ---------------- MAIN SYSTEM ----------------

else:

    st.success(f"Logged in as {st.session_state.user}")

    if st.button("Logout"):
        st.session_state.login = False
        st.rerun()

    st.divider()

# ---------------- ADMIN PANEL ----------------

    if st.session_state.role == "Admin":

        st.subheader("Admin Panel")

        new_name = st.text_input("Cashier Name")
        new_pass = st.text_input("Cashier Password")

        if st.button("Add Cashier"):

            cursor.execute(
            "INSERT INTO cashiers (name,password) VALUES (?,?)",
            (new_name,new_pass)
            )

            conn.commit()
            st.success("Cashier added")

        st.dataframe(pd.read_sql("SELECT * FROM cashiers",conn))

# ---------------- OPENING CASH ----------------

    st.subheader("Opening Cash")

    opening = st.number_input("Opening Cash ₹", min_value=0.0)

# ---------------- TRANSACTION ENTRY ----------------

    st.subheader("Add Transaction")

    col1,col2,col3 = st.columns(3)

    transaction_types = [
        "Receipt",
        "Credit Receipt",
        "Bank Withdrawal",
        "Payment",
        "Bank Deposit",
        "Paytm",
        "SBI",
        "KDC"
    ]

    with col1:
        t_type = st.selectbox("Transaction Type", transaction_types)

    with col2:
        amount = st.number_input("Amount ₹", min_value=0.0)

    with col3:
        t_date = st.date_input("Date", date.today())

    note = st.text_input("Note")

    if st.button("Save Transaction"):

        cursor.execute(
        "INSERT INTO cash_transactions (date,cashier,type,amount,note) VALUES (?,?,?,?,?)",
        (str(t_date),st.session_state.user,t_type,amount,note)
        )

        conn.commit()
        st.success("Transaction saved")

# ---------------- LOAD DATA ----------------

    cash_df = pd.read_sql("SELECT * FROM cash_transactions",conn)

    if not cash_df.empty:
        cash_df["date"] = pd.to_datetime(cash_df["date"])

# ---------------- CASH EQUATIONS ----------------

    incoming_types = ["Receipt","Credit Receipt","Bank Withdrawal"]

    outgoing_types = ["Payment","Bank Deposit","Paytm","SBI","KDC"]

    incoming = 0
    outgoing = 0

    if not cash_df.empty:

        incoming = cash_df[cash_df["type"].isin(incoming_types)]["amount"].sum()

        outgoing = cash_df[cash_df["type"].isin(outgoing_types)]["amount"].sum()

    closing = opening + incoming - outgoing

# ---------------- DASHBOARD ----------------

    st.subheader("Cash Summary")

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Opening Cash", opening)
    c2.metric("Incoming", incoming)
    c3.metric("Outgoing", outgoing)
    c4.metric("System Cash", closing)

# ---------------- TRANSACTION HISTORY ----------------

    st.subheader("Transaction History")

    if not cash_df.empty:

        total_amount = cash_df["amount"].sum()

        st.write(f"Total Transaction Amount: ₹ {total_amount}")

        st.dataframe(cash_df)

# ---------------- ADMIN EDIT ----------------

        if st.session_state.role == "Admin":

            st.subheader("Edit Transaction")

            tid = st.selectbox("Transaction ID", cash_df["id"])

            row = cash_df[cash_df["id"]==tid].iloc[0]

            new_amt = st.number_input("Edit Amount", value=float(row["amount"]))
            new_note = st.text_input("Edit Note", value=row["note"])

            if st.button("Update Transaction"):

                cursor.execute(
                "UPDATE cash_transactions SET amount=?,note=? WHERE id=?",
                (new_amt,new_note,tid)
                )

                conn.commit()
                st.success("Transaction updated")

# ---------------- DAILY REPORT ----------------

    st.subheader("Daily Cash Report")

    if st.button("Generate Today Report"):

        if not cash_df.empty:

            today = pd.to_datetime(date.today())

            today_data = cash_df[cash_df["date"].dt.date == today.date()]

            incoming_today = today_data[today_data["type"].isin(incoming_types)]["amount"].sum()
            outgoing_today = today_data[today_data["type"].isin(outgoing_types)]["amount"].sum()

            balance_today = opening + incoming_today - outgoing_today

            report = pd.DataFrame({
                "Opening":[opening],
                "Incoming":[incoming_today],
                "Outgoing":[outgoing_today],
                "System Balance":[balance_today]
            })

            st.dataframe(report)

# ---------------- MONTHLY ACCOUNT ----------------

    st.subheader("Monthly Cash Account")

    if not cash_df.empty:

        cash_df["month"] = cash_df["date"].dt.to_period("M")

        monthly = cash_df.groupby(["month","type"])["amount"].sum().unstack(fill_value=0)

        monthly["Incoming"] = monthly[incoming_types].sum(axis=1)

        monthly["Outgoing"] = monthly[outgoing_types].sum(axi# ---------------- MONTHLY ACCOUNT ----------------

st.subheader("Monthly Cash Account")

if not cash_df.empty:

    cash_df["month"] = cash_df["date"].dt.to_period("M")

    monthly = cash_df.groupby(["month","type"])["amount"].sum().unstack(fill_value=0)

    # SAFE incoming calculation
    monthly["Incoming"] = (
        monthly.get("Receipt",0)
        + monthly.get("Credit Receipt",0)
        + monthly.get("Bank Withdrawal",0)
    )

    # SAFE outgoing calculation
    monthly["Outgoing"] = (
        monthly.get("Payment",0)
        + monthly.get("Bank Deposit",0)
        + monthly.get("Paytm",0)
        + monthly.get("SBI",0)
        + monthly.get("KDC",0)
    )

    monthly["Closing"] = opening + monthly["Incoming"] - monthly["Outgoing"]

    monthly = monthly.reset_index()
    monthly["month"] = monthly["month"].astype(str)

    st.dataframe(monthly)s=1)

        monthly["Closing"] = opening + monthly["Incoming"] - monthly["Outgoing"]

        monthly = monthly.reset_index()
        monthly["month"] = monthly["month"].astype(str)

        st.dataframe(monthly)


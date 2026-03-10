import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# ---------------- PAGE ----------------
st.set_page_config(page_title="Petrol Pump Cash Counter", layout="wide")
st.title("⛽ Petrol Pump Cash Counter")
st.text("Created by Nazeeh,")align="right")

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

    role = st.selectbox("Login as", ["Cashier", "Admin"])
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
            check = df[(df["name"] == user) & (df["password"] == password)]

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

    # ---------------- OPENING BALANCE ----------------
    st.header("Opening Balance")

    opening = st.number_input(
        f"{st.session_state.user} Opening Cash ₹",
        min_value=0.0
    )

    st.session_state.openings[st.session_state.user] = opening

    # ---------------- TRANSACTION ENTRY ----------------
    st.header("Cash Transactions")

    col1, col2, col3 = st.columns(3)

    with col1:
        t_type = st.selectbox(
            "Transaction Type",
            [
                "Receipt",
                "Credit Receipt",
                "Bank Withdrawal",
                "Payment",
                "Bank Deposit",
                "Paytm",
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
            "INSERT INTO cash_transactions (date,cashier,type,amount,note) VALUES (?,?,?,?,?)",
            (str(t_date), st.session_state.user, t_type, amount, note)
        )

        conn.commit()
        st.success("Transaction saved")

    # ---------------- LOAD DATA ----------------
    cash_df = pd.read_sql("SELECT * FROM cash_transactions", conn)

    if not cash_df.empty:
        cash_df["date"] = pd.to_datetime(cash_df["date"])

    # ---------------- CASH BALANCE ----------------
    st.header("Cash Balance")

    total_opening = sum(st.session_state.openings.values())

    incoming_types = ["Receipt", "Credit Receipt", "Bank Withdrawal"]
    outgoing_types = ["Payment", "Bank Deposit", "Paytm", "SBI", "KDC"]

    if not cash_df.empty:

        incoming = cash_df[cash_df["type"].isin(incoming_types)]["amount"].sum()
        outgoing = cash_df[cash_df["type"].isin(outgoing_types)]["amount"].sum()

    else:

        incoming = 0
        outgoing = 0

    closing = total_opening + incoming - outgoing

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Opening", total_opening)
    c2.metric("Incoming", incoming)
    c3.metric("Outgoing", outgoing)
    c4.metric("Closing Cash", closing)

    # ---------------- TRANSACTION HISTORY ----------------
    st.header("Transaction History")

    opening_rows = []

    for cashier, value in st.session_state.openings.items():

        opening_rows.append({
            "id": "-",
            "date": str(date.today()),
            "cashier": cashier,
            "type": "Opening Balance",
            "amount": value,
            "note": "Opening Cash"
        })

    opening_df = pd.DataFrame(opening_rows)

    if not cash_df.empty:
        history_df = pd.concat([opening_df, cash_df], ignore_index=True)
    else:
        history_df = opening_df

    st.dataframe(history_df)

    st.write("Total Transaction Amount ₹", history_df["amount"].sum())

    # ---------------- ADMIN DELETE ----------------
    if st.session_state.role == "Admin" and not cash_df.empty:

        st.header("Delete Transaction")

        delete_id = st.selectbox("Select Transaction ID", cash_df["id"])

        if st.button("Delete Transaction"):

            cursor.execute(
                "DELETE FROM cash_transactions WHERE id=?",
                (delete_id,)
            )

            conn.commit()

            st.success("Transaction Deleted")
            st.rerun()

    # ---------------- DAILY BALANCE ----------------
    if not cash_df.empty:

        st.header("Daily Balance")

        daily = cash_df.groupby(cash_df["date"].dt.date)["amount"].sum().reset_index()

        st.dataframe(daily)

    # ---------------- MONTHLY BALANCE ----------------
    if not cash_df.empty:

        st.header("Monthly Balance")

        cash_df["month"] = cash_df["date"].dt.to_period("M")

        monthly = cash_df.groupby("month")["amount"].sum().reset_index()

        monthly["month"] = monthly["month"].astype(str)

        st.dataframe(monthly)

    # ---------------- TODAY REPORT ----------------
    st.header("Daily Cash Report")

    if st.button("Generate Today Report"):

        today = pd.to_datetime(date.today())

        today_data = cash_df[cash_df["date"].dt.date == today.date()]

        if not today_data.empty:

            total = today_data["amount"].sum()

            report = pd.DataFrame({
                "Opening": [total_opening],
                "Today Total": [total],
                "Closing": [closing]
            })

            st.dataframe(report)

        else:
            st.info("No transactions today")

    # ---------------- LOGOUT ----------------
    if st.button("Logout"):

        st.session_state.login = False
        st.rerun()










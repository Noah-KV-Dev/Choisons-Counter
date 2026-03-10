import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Petrol Pump Cash Counter", layout="wide")
st.title("⛽ Petrol Pump Cash Counter")
st.markdown("<p style='text-align:right; font-size:12px; color:gray;'>Created by Nazeeh</p>", unsafe_allow_html=True)


# ---------------- DATABASE ----------------
conn = sqlite3.connect("petrol_cash.db", check_same_thread=False)
cursor = conn.cursor()

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

# ---------------- LOGIN PAGE ----------------
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
            st.session_state.login = True
            st.session_state.role = "Cashier"
            st.session_state.user = user
            st.rerun()

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
            "INSERT INTO cash_transactions (date,cashier,type,amount,note) VALUES (?,?,?,?,?)",
            (str(t_date), st.session_state.user, t_type, amount, note)
        )

        conn.commit()
        st.success("Transaction saved")

    # ---------------- LOAD DATA ----------------
    cash_df = pd.read_sql("SELECT * FROM cash_transactions", conn)

    if not cash_df.empty:
        cash_df["date"] = pd.to_datetime(cash_df["date"])

    # ---------------- TOTAL OPENING ----------------
    total_opening = sum(st.session_state.openings.values())

    # ---------------- BALANCE TYPES ----------------
    cash_in_types = ["Receipt", "Credit Receipt", "Bank Withdrawal"]
    cash_out_types = ["Payment", "Bank Deposit"]

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

        cash_in = cash_out = paytm_in = paytm_out = sbi_total = kdc_total = 0

    cash_balance = total_opening + cash_in - cash_out
    paytm_balance = paytm_in - paytm_out
    sbi_balance = -sbi_total
    kdc_balance = -kdc_total

    # ---------------- BALANCES ----------------
    st.header("Balances")

    b1, b2, b3, b4 = st.columns(4)

    b1.metric("Cash Balance", cash_balance)
    b2.metric("Paytm Balance", paytm_balance)
    b3.metric("SBI Balance", sbi_balance)
    b4.metric("KDC Balance", kdc_balance)

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

            total_today = today_data["amount"].sum()

            report = pd.DataFrame({
                "Total Opening":[total_opening],
                "Today's Transactions":[total_today],
                "Cash Balance":[cash_balance]
            })

            st.dataframe(report)

        else:
            st.info("No transactions today")

    # ---------------- LOGOUT ----------------
    if st.button("Logout"):

        st.session_state.login = False
        st.rerun()

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("<p style='text-align:right; font-size:12px; color:gray;'>Created by Nazeeh</p>", unsafe_allow_html=True)






import streamlit as st
import pandas as pd
import pyrebase
from datetime import date

# ---------------- PAGE SETTINGS ----------------

st.set_page_config(page_title="Petrol Pump System", layout="wide")

st.title("⛽ Petrol Pump Cash Counter")

# ---------------- FIREBASE CONFIG (FIX FOR ERROR) ----------------

firebase_config = {
    "apiKey": "YOUR_API_KEY",
    "authDomain": "YOUR_PROJECT.firebaseapp.com",
    "databaseURL": "YOUR_DATABASE_URL",
    "projectId": "YOUR_PROJECT_ID",
    "storageBucket": "YOUR_PROJECT.appspot.com",
    "messagingSenderId": "XXXX",
    "appId": "XXXX"
}

firebase = pyrebase.initialize_app(firebase_config)

db = firebase.database()

# ---------------- CASH COUNTER ----------------

st.header("💰 Cash Counter")

col1, col2, col3 = st.columns(3)

with col1:
    transaction_type = st.selectbox(
        "Transaction Type",
        ["Receipt", "Payment", "Bank Transfer", "Bank Deposit"]
    )

with col2:
    amount = st.number_input(
        "Amount (₹)",
        min_value=0.0,
        step=1.0
    )

with col3:
    cash_date = st.date_input(
        "Date",
        date.today()
    )

note = st.text_input("Description / Note")

# ---------- SAVE TRANSACTION ----------

if st.button("Save Transaction"):

    new_transaction = {
        "type": transaction_type,
        "amount": amount,
        "date": str(cash_date),
        "note": note
    }

    db.child("cash_transactions").push(new_transaction)

    st.success("Transaction Saved")

# ---------- LOAD DATA ----------

cash_data = db.child("cash_transactions").get()

records = []

if cash_data.each():

    for item in cash_data.each():

        data = item.val()
        data["id"] = item.key()

        records.append(data)

df_cash = pd.DataFrame(records)

# ---------- IF DATA EXISTS ----------

if not df_cash.empty:

    df_cash["date"] = pd.to_datetime(df_cash["date"])

    # ---------- SUMMARY ----------

    receipts = df_cash[df_cash["type"]=="Receipt"]["amount"].sum()
    payments = df_cash[df_cash["type"]=="Payment"]["amount"].sum()
    transfers = df_cash[df_cash["type"]=="Bank Transfer"]["amount"].sum()
    deposits = df_cash[df_cash["type"]=="Bank Deposit"]["amount"].sum()

    cash_balance = receipts - payments - transfers - deposits

    st.subheader("📊 Cash Summary")

    c1,c2,c3,c4,c5 = st.columns(5)

    c1.metric("Receipts", f"₹{receipts}")
    c2.metric("Payments", f"₹{payments}")
    c3.metric("Transfers", f"₹{transfers}")
    c4.metric("Deposits", f"₹{deposits}")
    c5.metric("Cash Balance", f"₹{cash_balance}")

    # ---------- TRANSACTION HISTORY ----------

    st.subheader("📋 Transaction History")

    st.dataframe(df_cash)

    # ---------- DAILY BALANCE ----------

    st.subheader("📅 Daily Balance")

    daily_balance = df_cash.groupby(df_cash["date"].dt.date).apply(
        lambda x:
        x[x["type"]=="Receipt"]["amount"].sum()
        - x[x["type"]=="Payment"]["amount"].sum()
        - x[x["type"]=="Bank Transfer"]["amount"].sum()
        - x[x["type"]=="Bank Deposit"]["amount"].sum()
    ).reset_index(name="Daily Balance")

    st.dataframe(daily_balance)

    # ---------- MONTHLY BALANCE ----------

    st.subheader("📆 Monthly Balance")

    df_cash["month"] = df_cash["date"].dt.to_period("M")

    monthly_balance = df_cash.groupby("month").apply(
        lambda x:
        x[x["type"]=="Receipt"]["amount"].sum()
        - x[x["type"]=="Payment"]["amount"].sum()
        - x[x["type"]=="Bank Transfer"]["amount"].sum()
        - x[x["type"]=="Bank Deposit"]["amount"].sum()
    ).reset_index(name="Monthly Balance")

    monthly_balance["month"] = monthly_balance["month"].astype(str)

    st.dataframe(monthly_balance)

import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

st.set_page_config(page_title="Cash Counter", layout="wide")

st.title("💰 Petrol Pump Cash Counter")

# ---------------- DATABASE ----------------

conn = sqlite3.connect("cash_counter.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS cash_transactions(
id INTEGER PRIMARY KEY AUTOINCREMENT,
date TEXT,
type TEXT,
amount REAL,
note TEXT
)
""")

conn.commit()

# ---------------- OPENING BALANCE ----------------

st.header("Opening Balance")

opening_balance = st.number_input("Opening Cash Balance ₹", min_value=0.0)

# ---------------- CASH TRANSACTION ENTRY ----------------

st.header("Cash Entry")

col1,col2,col3 = st.columns(3)

with col1:
    transaction_type = st.selectbox(
        "Transaction Type",
        ["Receipt","Payment","Bank Transfer","Bank Deposit"]
    )

with col2:
    amount = st.number_input("Amount ₹", min_value=0.0)

with col3:
    trans_date = st.date_input("Date", date.today())

note = st.text_input("Note")

if st.button("Save Transaction"):

    cursor.execute(
    "INSERT INTO cash_transactions (date,type,amount,note) VALUES (?,?,?,?)",
    (str(trans_date),transaction_type,amount,note)
    )

    conn.commit()

    st.success("Transaction Saved")

# ---------------- LOAD DATA ----------------

df = pd.read_sql("SELECT * FROM cash_transactions", conn)

if not df.empty:

    df["date"] = pd.to_datetime(df["date"])

    receipts = df[df["type"]=="Receipt"]["amount"].sum()
    payments = df[df["type"]=="Payment"]["amount"].sum()
    transfers = df[df["type"]=="Bank Transfer"]["amount"].sum()
    deposits = df[df["type"]=="Bank Deposit"]["amount"].sum()

    closing_balance = opening_balance + receipts - payments - transfers - deposits

    st.header("Cash Summary")

    a,b,c,d,e = st.columns(5)

    a.metric("Opening Balance", opening_balance)
    b.metric("Receipts", receipts)
    c.metric("Payments", payments)
    d.metric("Bank Transfers", transfers)
    e.metric("Bank Deposits", deposits)

    st.metric("Closing Cash Balance", closing_balance)

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

    st.dataframe(daily,use_container_width=True)

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

    st.dataframe(monthly,use_container_width=True)

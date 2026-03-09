import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

st.set_page_config(page_title="Petrol Pump System", layout="wide")

st.title("⛽ Petrol Pump Management System")

# ---------------- DATABASE ----------------

conn = sqlite3.connect("petrol_pump.db", check_same_thread=False)
cursor = conn.cursor()

# Fuel sales table
cursor.execute("""
CREATE TABLE IF NOT EXISTS fuel_sales(
id INTEGER PRIMARY KEY AUTOINCREMENT,
date TEXT,
staff TEXT,
fuel TEXT,
opening REAL,
closing REAL,
litres REAL,
price REAL,
total REAL
)
""")

# Cash counter table
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

# ---------------- FUEL SALES ----------------

st.header("⛽ Fuel Sales Entry")

col1,col2,col3 = st.columns(3)

with col1:
    sale_date = st.date_input("Date",date.today())
    staff = st.text_input("Staff Name")

with col2:
    fuel = st.selectbox("Fuel Type",["Petrol","Diesel","Power Petrol"])
    price = st.number_input("Price per Litre",min_value=0.0)

with col3:
    opening = st.number_input("Opening Meter",min_value=0.0)
    closing = st.number_input("Closing Meter",min_value=0.0)

litres = closing - opening

if litres < 0:
    litres = 0

total = litres * price

st.write("Litres Sold:", litres)
st.write("Total Sale: ₹", total)

if st.button("Save Fuel Sale"):

    cursor.execute(
    "INSERT INTO fuel_sales (date,staff,fuel,opening,closing,litres,price,total) VALUES (?,?,?,?,?,?,?,?)",
    (str(sale_date),staff,fuel,opening,closing,litres,price,total)
    )

    conn.commit()

    st.success("Fuel Sale Saved")

# ---------------- SALES HISTORY ----------------

st.subheader("Fuel Sales Records")

sales_df = pd.read_sql("SELECT * FROM fuel_sales",conn)

st.dataframe(sales_df,use_container_width=True)

# ---------------- CASH COUNTER ----------------

st.header("💰 Cash Counter")

c1,c2,c3 = st.columns(3)

with c1:
    transaction_type = st.selectbox(
    "Transaction Type",
    ["Receipt","Payment","Bank Transfer","Bank Deposit"]
    )

with c2:
    amount = st.number_input("Amount ₹",min_value=0.0)

with c3:
    cash_date = st.date_input("Cash Date",date.today())

note = st.text_input("Note")

if st.button("Save Transaction"):

    cursor.execute(
    "INSERT INTO cash_transactions (date,type,amount,note) VALUES (?,?,?,?)",
    (str(cash_date),transaction_type,amount,note)
    )

    conn.commit()

    st.success("Transaction Saved")

# ---------------- CASH DATA ----------------

cash_df = pd.read_sql("SELECT * FROM cash_transactions",conn)

if not cash_df.empty:

    cash_df["date"] = pd.to_datetime(cash_df["date"])

    receipts = cash_df[cash_df["type"]=="Receipt"]["amount"].sum()
    payments = cash_df[cash_df["type"]=="Payment"]["amount"].sum()
    transfers = cash_df[cash_df["type"]=="Bank Transfer"]["amount"].sum()
    deposits = cash_df[cash_df["type"]=="Bank Deposit"]["amount"].sum()

    balance = receipts - payments - transfers - deposits

    st.subheader("Cash Summary")

    a,b,c,d,e = st.columns(5)

    a.metric("Receipts",receipts)
    b.metric("Payments",payments)
    c.metric("Transfers",transfers)
    d.metric("Deposits",deposits)
    e.metric("Cash Balance",balance)

# ---------------- TRANSACTION HISTORY ----------------

st.subheader("Cash Transactions")

st.dataframe(cash_df,use_container_width=True)

# ---------------- DAILY BALANCE ----------------

if not cash_df.empty:

    st.subheader("📅 Daily Balance")

    daily = cash_df.groupby(cash_df["date"].dt.date).apply(
    lambda x:
    x[x["type"]=="Receipt"]["amount"].sum()
    - x[x["type"]=="Payment"]["amount"].sum()
    - x[x["type"]=="Bank Transfer"]["amount"].sum()
    - x[x["type"]=="Bank Deposit"]["amount"].sum()
    ).reset_index(name="Daily Balance")

    st.dataframe(daily,use_container_width=True)

# ---------------- MONTHLY BALANCE ----------------

    st.subheader("📆 Monthly Balance")

    cash_df["month"] = cash_df["date"].dt.to_period("M")

    monthly = cash_df.groupby("month").apply(
    lambda x:
    x[x["type"]=="Receipt"]["amount"].sum()
    - x[x["type"]=="Payment"]["amount"].sum()
    - x[x["type"]=="Bank Transfer"]["amount"].sum()
    - x[x["type"]=="Bank Deposit"]["amount"].sum()
    ).reset_index(name="Monthly Balance")

    monthly["month"] = monthly["month"].astype(str)

    st.dataframe(monthly,use_container_width=True)

import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# ---------------- TOTAL CASH ACCOUNT ----------------

st.header("Final Cash Account Summary")

# CASH DATA
if not cash_df.empty:

    total_receipts = cash_df[cash_df["type"]=="Receipt"]["amount"].sum()
    total_payments = cash_df[cash_df["type"]=="Payment"]["amount"].sum()
    total_transfer = cash_df[cash_df["type"]=="Bank Transfer"]["amount"].sum()
    total_deposit = cash_df[cash_df["type"]=="Bank Deposit"]["amount"].sum()

else:
    total_receipts = 0
    total_payments = 0
    total_transfer = 0
    total_deposit = 0


# STAFF ADVANCE DATA
if not adv_df.empty:

    total_adv_paid = adv_df[adv_df["type"]=="Advance Payment"]["amount"].sum()
    total_adv_received = adv_df[adv_df["type"]=="Advance Received"]["amount"].sum()

else:
    total_adv_paid = 0
    total_adv_received = 0


# FINAL CASH BALANCE
final_balance = (
    opening
    + total_receipts
    - total_payments
    - total_transfer
    - total_deposit
    - total_adv_paid
    + total_adv_received
)

st.subheader("Total Cash Balance")

col1,col2,col3,col4 = st.columns(4)

col1.metric("Total Receipts", total_receipts)
col2.metric("Total Payments", total_payments)
col3.metric("Advance Given", total_adv_paid)
col4.metric("Advance Received", total_adv_received)

st.metric("FINAL CASH IN HAND", final_balance)


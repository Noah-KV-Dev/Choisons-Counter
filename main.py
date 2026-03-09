import streamlit as st
import pandas as pd


# ---------------- CASH BALANCE ACCOUNT ----------------

st.header("💰 Cash Balance Account")

# transaction types
transaction_type = st.selectbox(
    "Transaction Type",
    ["Receipt", "Payment", "Bank Transfer", "Bank Deposit"]
)

amount = st.number_input("Amount (₹)", min_value=0.0, step=0.01)

note = st.text_input("Note / Description")

cash_date = st.date_input("Date")

if st.button("Save Cash Transaction"):

    new_cash = {
        "date": str(cash_date),
        "type": transaction_type,
        "amount": amount,
        "note": note
    }

    cash_ref = db.child("cash_transactions").push(new_cash)

    st.success("Transaction Saved Successfully")

# ---------- LOAD DATA ----------

cash_data = db.child("cash_transactions").get()

records = []

if cash_data.each():
    for item in cash_data.each():
        data = item.val()
        data["id"] = item.key()
        records.append(data)

df_cash = pd.DataFrame(records)

if not df_cash.empty:

    # calculate balances
    receipts = df_cash[df_cash["type"]=="Receipt"]["amount"].sum()
    payments = df_cash[df_cash["type"]=="Payment"]["amount"].sum()
    transfers = df_cash[df_cash["type"]=="Bank Transfer"]["amount"].sum()
    deposits = df_cash[df_cash["type"]=="Bank Deposit"]["amount"].sum()

    cash_balance = receipts - payments - transfers - deposits

    st.subheader("📊 Cash Summary")

    col1,col2,col3,col4,col5 = st.columns(5)

    col1.metric("Receipts", f"₹{receipts}")
    col2.metric("Payments", f"₹{payments}")
    col3.metric("Transfers", f"₹{transfers}")
    col4.metric("Deposits", f"₹{deposits}")
    col5.metric("Cash Balance", f"₹{cash_balance}")

    st.subheader("📋 Transaction History")

    st.dataframe(df_cash)

# -------- ADMIN EDIT / DELETE --------

if role == "Admin":

    st.subheader("Admin Edit/Delete")

    if not df_cash.empty:

        selected_id = st.selectbox(
            "Select Transaction",
            df_cash["id"]
        )

        selected_row = df_cash[df_cash["id"]==selected_id].iloc[0]

        edit_amount = st.number_input(
            "Edit Amount",
            value=float(selected_row["amount"])
        )

        edit_note = st.text_input(
            "Edit Note",
            value=selected_row["note"]
        )

        if st.button("Update Transaction"):

            db.child("cash_transactions").child(selected_id).update({
                "amount": edit_amount,
                "note": edit_note
            })

            st.success("Transaction Updated")

        if st.button("Delete Transaction"):

            db.child("cash_transactions").child(selected_id).remove()

            st.warning("Transaction Deleted")


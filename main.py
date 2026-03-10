import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Choisons Counter", layout="wide")
st.title("⛽ Choisons Petroleum Counter")
st.markdown("<p style='text-align:right;font-size:12px;color:gray;'>Created by Nazeeh</p>", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("counter.db", check_same_thread=False)
cursor = conn.cursor()

# Transactions table
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions(
id INTEGER PRIMARY KEY AUTOINCREMENT,
date TEXT,
cashier TEXT,
type TEXT,
amount REAL,
note TEXT
)
""")

# Staff advance table
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

# Staff list table
cursor.execute("""
CREATE TABLE IF NOT EXISTS staff(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT UNIQUE
)
""")

conn.commit()

# ---------------- SESSION ----------------
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
                st.session_state.login=True
                st.session_state.role="Admin"
                st.session_state.user=user
                st.rerun()
            else:
                st.error("Wrong Admin Login")

        else:
            st.session_state.login=True
            st.session_state.role="Cashier"
            st.session_state.user=user
            st.rerun()

# ---------------- MAIN SYSTEM ----------------
else:

    st.sidebar.success(f"User : {st.session_state.user}")
    st.sidebar.header("Menu")

    # ---------------- SIDEBAR BUTTONS ----------------
    menu = st.session_state.get("menu","Opening Balance")  # Default menu

    if st.sidebar.button("Opening Balance"):
        st.session_state.menu = "Opening Balance"
    if st.sidebar.button("Transaction Entry"):
        st.session_state.menu = "Transaction Entry"
    if st.sidebar.button("Staff Advance"):
        st.session_state.menu = "Staff Advance"
    if st.sidebar.button("Add Staff"):
        st.session_state.menu = "Add Staff"
    if st.sidebar.button("Balances"):
        st.session_state.menu = "Balances"
    if st.sidebar.button("Collection Dashboard"):
        st.session_state.menu = "Collection Dashboard"
    if st.sidebar.button("Transaction History"):
        st.session_state.menu = "Transaction History"
    if st.sidebar.button("Staff Advance Summary"):
        st.session_state.menu = "Staff Advance Summary"
    if st.sidebar.button("Daily Balance"):
        st.session_state.menu = "Daily Balance"
    if st.sidebar.button("Monthly Balance"):
        st.session_state.menu = "Monthly Balance"
    if st.sidebar.button("Logout"):
        st.session_state.login=False
        st.rerun()

    menu = st.session_state.get("menu","Opening Balance")  # fetch selected menu

    # ---------------- LOAD DATA ----------------
    cash_df = pd.read_sql("SELECT * FROM transactions",conn)
    advance_df = pd.read_sql("SELECT * FROM staff_advance",conn)
    staff_df = pd.read_sql("SELECT * FROM staff",conn)

    if not cash_df.empty:
        cash_df["date"] = pd.to_datetime(cash_df["date"])

    if not advance_df.empty:
        advance_df["date"] = pd.to_datetime(advance_df["date"])

    today = date.today()

# ---------------- OPENING BALANCE ----------------
    if menu == "Opening Balance":

        st.header("Opening Balance")

        check = pd.read_sql(
            f"SELECT * FROM transactions WHERE type='Opening Balance' AND date='{today}'",
            conn
        )

        if check.empty:

            opening = st.number_input("Opening Cash ₹", min_value=0.0)

            if st.button("Save Opening"):

                cursor.execute(
                    "INSERT INTO transactions (date,cashier,type,amount,note) VALUES (?,?,?,?,?)",
                    (str(today),st.session_state.user,"Opening Balance",opening,"Day Opening")
                )

                conn.commit()

                st.success("Opening Balance Saved")

        else:

            st.success("Opening already saved today")
            st.dataframe(check)

# ---------------- TRANSACTION ENTRY ----------------
    if menu == "Transaction Entry":

        st.header("Transaction Entry")

        col1,col2,col3 = st.columns(3)

        with col1:
            t_type = st.selectbox(
                "Transaction Type",
                [
                    "Sales",
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
            amount = st.number_input("Amount ₹",min_value=0.0)

        with col3:
            t_date = st.date_input("Date",today)

        note = st.text_input("Note")

        if st.button("Save Transaction"):

            cursor.execute(
                "INSERT INTO transactions (date,cashier,type,amount,note) VALUES (?,?,?,?,?)",
                (str(t_date),st.session_state.user,t_type,amount,note)
            )

            conn.commit()

            st.success("Transaction Saved")

# ---------------- ADD STAFF ----------------
    if menu == "Add Staff":

        st.header("Add Staff")

        staff_name = st.text_input("Staff Name")

        if st.button("Add Staff"):

            try:

                cursor.execute(
                    "INSERT INTO staff (name) VALUES (?)",
                    (staff_name,)
                )

                conn.commit()

                st.success("Staff Added")

            except:
                st.warning("Staff already exists")

        st.subheader("Staff List")
        st.dataframe(staff_df)

# ---------------- STAFF ADVANCE ----------------
    if menu == "Staff Advance":

        st.header("Staff Advance")

        staff_names = staff_df["name"].tolist()
        if not staff_names:
            st.info("No staff available. Add staff first.")
        else:
            col1,col2,col3 = st.columns(3)

            with col1:
                staff = st.selectbox("Select Staff",staff_names)

            with col2:
                adv_type = st.selectbox(
                    "Advance Type",
                    ["Advance Paid","Advance Received"]
                )

            with col3:
                amount = st.number_input("Amount ₹",min_value=0.0)

            adv_date = st.date_input("Date",today)

            note = st.text_input("Note")

            if st.button("Save Advance"):

                cursor.execute(
                    "INSERT INTO staff_advance (date,staff,type,amount,note) VALUES (?,?,?,?,?)",
                    (str(adv_date),staff,adv_type,amount,note)
                )

                conn.commit()

                st.success("Advance Saved")

# ---------------- BALANCE CALCULATIONS ----------------

    cash_in_types = [
        "Opening Balance",
        "Sales",
        "Receipt",
        "Credit Receipt",
        "Bank Withdrawal"
    ]

    cash_out_types = ["Payment","Bank Deposit"]

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

        cash_in=cash_out=paytm_in=paytm_out=sbi_total=kdc_total=0

    cash_balance = cash_in - cash_out
    paytm_balance = paytm_in - paytm_out
    sbi_balance = -sbi_total
    kdc_balance = -kdc_total

# ---------------- BALANCES ----------------
    if menu == "Balances":

        st.header("Balances")

        c1,c2,c3,c4 = st.columns(4)

        c1.metric("Cash Balance",f"₹{cash_balance:,.2f}")
        c2.metric("Paytm Balance",f"₹{paytm_balance:,.2f}")
        c3.metric("SBI Balance",f"₹{sbi_balance:,.2f}")
        c4.metric("KDC Balance",f"₹{kdc_balance:,.2f}")

# ---------------- COLLECTION DASHBOARD ----------------
    if menu == "Collection Dashboard":

        st.header("Collection Dashboard")

        total_sales = cash_df[cash_df["type"]=="Sales"]["amount"].sum() if not cash_df.empty else 0

        d1,d2 = st.columns(2)

        d1.metric("Total Sales",f"₹{total_sales:,.2f}")
        d2.metric("Total Collection",f"₹{cash_in:,.2f}")

# ---------------- TRANSACTION HISTORY WITH ADMIN DELETE ----------------
if menu == "Transaction History":

    st.header("Today Transactions")

    if not cash_df.empty:

        today_df = cash_df[cash_df["date"].dt.date == today]

        if today_df.empty:
            st.info("No transactions today")
        else:

            st.dataframe(today_df)

            if st.session_state.role == "Admin":
                st.subheader("Delete Transactions (Admin Only)")

                # Select transaction to delete
                trans_id = st.selectbox(
                    "Select Transaction ID to Delete",
                    today_df["id"].tolist()
                )

                if st.button("Delete Transaction"):
                    # Delete from DB
                    cursor.execute(
                        "DELETE FROM transactions WHERE id=?",
                        (trans_id,)
                    )
                    conn.commit()
                    st.success(f"Transaction ID {trans_id} deleted")
                    st.experimental_rerun()
    else:
        st.info("No transactions today")

# ---------------- STAFF ADVANCE SUMMARY ----------------
if menu == "Staff Advance Summary":

    st.header("Staff Advance Summary")

    if staff_df.empty:
        st.info("No staff available. Add staff first.")
    else:

        # Initialize empty summary with all staff
        summary = pd.DataFrame(staff_df["name"])
        summary.columns = ["Staff"]

        if not advance_df.empty:
            # Paid
            paid_sum = (
                advance_df[advance_df["type"]=="Advance Paid"]
                .groupby("staff")["amount"]
                .sum()
                .reset_index()
            )
            paid_sum.columns = ["Staff","Advance Paid"]

            # Received
            received_sum = (
                advance_df[advance_df["type"]=="Advance Received"]
                .groupby("staff")["amount"]
                .sum()
                .reset_index()
            )
            received_sum.columns = ["Staff","Advance Received"]

            # Merge both with all staff
            summary = summary.merge(paid_sum, on="Staff", how="left")
            summary = summary.merge(received_sum, on="Staff", how="left")
            summary = summary.fillna(0)

            # Add Net Balance column
            summary["Balance"] = summary["Advance Paid"] - summary["Advance Received"]

        else:
            summary["Advance Paid"] = 0
            summary["Advance Received"] = 0
            summary["Balance"] = 0

        st.dataframe(summary)
        else:
            summary["Advance Paid"] = 0
            summary["Advance Received"] = 0

        st.dataframe(summary)
# ---------------- DAILY BALANCE ----------------
    if menu == "Daily Balance":

        st.header("Daily Balance")

        if not cash_df.empty:

            daily = cash_df.groupby(cash_df["date"].dt.date)["amount"].sum().reset_index()

            st.dataframe(daily)

# ---------------- MONTHLY BALANCE ----------------
    if menu == "Monthly Balance":

        st.header("Monthly Balance")

        if not cash_df.empty:

            cash_df["month"] = cash_df["date"].dt.to_period("M")

            monthly = cash_df.groupby("month")["amount"].sum().reset_index()

            monthly["month"] = monthly["month"].astype(str)

            st.dataframe(monthly)

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("<p style='text-align:right;font-size:12px;color:gray;'>Created by Nazeeh</p>", unsafe_allow_html=True)





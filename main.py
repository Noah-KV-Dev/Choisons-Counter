import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ------------------------------
# PAGE SETTINGS
# ------------------------------

st.set_page_config(page_title="Petrol Pump Cash Counter", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #ff6f00;
}
h1,h2,h3 {
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# DATABASE
# ------------------------------

conn = sqlite3.connect("petrol_counter.db", check_same_thread=False)
c = conn.cursor()

# USERS
c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT,
password TEXT,
role TEXT
)
""")

# CASH TRANSACTIONS
c.execute("""
CREATE TABLE IF NOT EXISTS cash_transactions(
id INTEGER PRIMARY KEY AUTOINCREMENT,
date TEXT,
cashier TEXT,
type TEXT,
amount REAL,
note TEXT
)
""")

# STAFF ADVANCE
c.execute("""
CREATE TABLE IF NOT EXISTS staff_advance(
id INTEGER PRIMARY KEY AUTOINCREMENT,
staff TEXT,
advance REAL,
received REAL
)
""")

# CENTRAL CASH BALANCE
c.execute("""
CREATE TABLE IF NOT EXISTS cash_balance(
id INTEGER PRIMARY KEY AUTOINCREMENT,
date TEXT,
opening REAL,
closing REAL
)
""")

conn.commit()

# default admin
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES ('admin','admin123','admin')")
    conn.commit()

# ------------------------------
# LOGIN
# ------------------------------

if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.user = ""
    st.session_state.role = ""

if not st.session_state.login:

    st.title("Cash Counter Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):

        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        data = c.fetchone()

        if data:
            st.session_state.login=True
            st.session_state.user=data[0]
            st.session_state.role=data[2]
            st.rerun()
        else:
            st.error("Wrong login")

    st.stop()

# ------------------------------
# SIDEBAR
# ------------------------------

st.sidebar.title("Menu")

menu = st.sidebar.selectbox("Select",[
"Cash Balance",
"Cash Transaction",
"Staff Advance",
"Reports"
])

if st.session_state.role == "admin":
    menu = st.sidebar.selectbox("Admin Menu",[
    "Cash Balance",
    "Cash Transaction",
    "Staff Advance",
    "Reports",
    "Admin Panel"
    ])

# ------------------------------
# CASH BALANCE ACCOUNT
# ------------------------------

if menu == "Cash Balance":

    st.title("Central Cash Balance")

    opening = st.number_input("Opening Cash",0.0)
    closing = st.number_input("Closing Cash",0.0)

    if st.button("Save Balance"):
        c.execute("INSERT INTO cash_balance(date,opening,closing) VALUES (?,?,?)",
        (datetime.today().date(),opening,closing))
        conn.commit()
        st.success("Saved")

    df = pd.read_sql("SELECT * FROM cash_balance", conn)

    st.dataframe(df)

# ------------------------------
# CASH TRANSACTION
# ------------------------------

if menu == "Cash Transaction":

    st.title("Cash Transactions")

    ttype = st.selectbox("Type",
    ["Receipt","Payment","Bank Deposit","Bank Transfer"])

    amount = st.number_input("Amount",0.0)
    note = st.text_input("Note")

    if st.button("Save Transaction"):

        c.execute("""
        INSERT INTO cash_transactions(date,cashier,type,amount,note)
        VALUES(?,?,?,?,?)
        """,(datetime.today().date(),st.session_state.user,ttype,amount,note))

        conn.commit()

        st.success("Transaction saved")

    df = pd.read_sql("SELECT * FROM cash_transactions", conn)

    st.dataframe(df)

# ------------------------------
# STAFF ADVANCE
# ------------------------------

if menu == "Staff Advance":

    st.title("Staff Advance Balance")

    staff = st.text_input("Staff Name")
    advance = st.number_input("Advance Given",0.0)
    received = st.number_input("Advance Received",0.0)

    if st.button("Save Advance"):
        c.execute("""
        INSERT INTO staff_advance(staff,advance,received)
        VALUES(?,?,?)
        """,(staff,advance,received))
        conn.commit()
        st.success("Saved")

    df = pd.read_sql("SELECT * FROM staff_advance", conn)

    if len(df)>0:

        df["Balance"] = df["advance"] - df["received"]

    st.dataframe(df)

# ------------------------------
# REPORTS
# ------------------------------

if menu == "Reports":

    st.title("Daily & Monthly Reports")

    trans = pd.read_sql("SELECT * FROM cash_transactions", conn)

    if len(trans)>0:

        total_receipt = trans[trans["type"]=="Receipt"]["amount"].sum()
        total_payment = trans[trans["type"]=="Payment"]["amount"].sum()

        st.metric("Total Receipt", total_receipt)
        st.metric("Total Payment", total_payment)

        st.dataframe(trans)

# ------------------------------
# ADMIN PANEL
# ------------------------------

if menu == "Admin Panel":

    st.title("Admin Controls")

    st.subheader("Create Cashier")

    u = st.text_input("New Username")
    p = st.text_input("New Password")

    if st.button("Create Cashier"):
        c.execute("INSERT INTO users VALUES (?,?,?)",(u,p,"cashier"))
        conn.commit()
        st.success("Cashier created")

    st.subheader("Edit Transaction")

    df = pd.read_sql("SELECT * FROM cash_transactions", conn)

    st.dataframe(df)

    tid = st.number_input("Transaction ID")

    new_amt = st.number_input("New Amount")

    if st.button("Update Transaction"):
        c.execute("UPDATE cash_transactions SET amount=? WHERE id=?",(new_amt,tid))
        conn.commit()
        st.success("Updated")

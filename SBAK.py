import streamlit as st
import pandas as pd
import re
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="SMS Expense Tracker", layout="wide")

# ---------- Users for Login ----------
users = {"admin": "1234", "user": "pass"}

def login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if users.get(username) == password:
        return True
    elif username and password:
        st.sidebar.error("Invalid credentials")
    return False

# ---------- Helper Functions ----------
def extract_amount(msg):
    match = re.search(r'₹\s?([\d,]+\.?\d*)', str(msg))
    return float(match.group(1).replace(',', '')) if match else 0

def fallback_categorize(msg):
    msg = str(msg).lower()
    if "amazon" in msg: return "Shopping"
    if "swiggy" in msg or "zomato" in msg: return "Food"
    if "petrol" in msg or "fuel" in msg: return "Fuel"
    if "bill" in msg or "electricity" in msg: return "Utilities"
    return "Others"

def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

# ---------- Main App ----------
def app():
    st.title("📊 SMS Expense Tracker")
    st.markdown("Upload your exported SMS or expense CSV to view and analyze your spending.")

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(r"C:\Users\kirti\Desktop\sms_expenses_tracker\Dataset.csv")
        df.columns = df.columns.str.strip().str.lower()

        if 'date' not in df.columns and 'Date' in df.columns:
            df.rename(columns={'Date': 'date'}, inplace=True)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

        if 'amount' not in df.columns and 'message' in df.columns:
            df['amount'] = df['message'].apply(extract_amount)

        if 'category' not in df.columns and 'message' in df.columns:
            df['category'] = df['message'].apply(fallback_categorize)

        # Sidebar filters
        st.sidebar.header("Filter Options")
        start = st.sidebar.date_input("Start Date", df['date'].min().date())
        end = st.sidebar.date_input("End Date", df['date'].max().date())
        filtered = df[(df['date'] >= pd.to_datetime(start)) & (df['date'] <= pd.to_datetime(end))]

        if 'category' in df.columns:
            categories = df['category'].dropna().unique()
            selected_cat = st.sidebar.multiselect("Category", categories)
            if selected_cat:
                filtered = filtered[filtered['category'].isin(selected_cat)]

        if 'location' in df.columns:
            locations = df['location'].dropna().unique()
            selected_loc = st.sidebar.multiselect("Location", locations)
            if selected_loc:
                filtered = filtered[filtered['location'].isin(selected_loc)]

        if 'payment' in df.columns:
            payments = df['payment'].dropna().unique()
            selected_pay = st.sidebar.multiselect("Payment Mode", payments)
            if selected_pay:
                filtered = filtered[filtered['payment'].isin(selected_pay)]

        if not filtered.empty:
            st.subheader("Summary")
            col1, col2 = st.columns(2)
            col1.metric("Total Spent", f"₹{filtered['amount'].sum():,.2f}")
            col2.metric("Transactions", len(filtered))

            st.subheader("Category Breakdown")
            if 'category' in filtered.columns:
                pie_data = filtered.groupby("category")["amount"].sum().reset_index()
                st.plotly_chart(px.pie(pie_data, names='category', values='amount'))

            st.subheader("Spending Over Time")
            time_series = filtered.groupby(filtered['date'].dt.date)['amount'].sum()
            st.line_chart(time_series)

            st.subheader("Transactions")
            st.dataframe(filtered)

            st.download_button("Download Filtered CSV", convert_df(filtered), "filtered_expenses.csv", "text/csv")
        else:
            st.warning("No records match your filters.")
    else:
        st.info("Upload a CSV file to begin.")

# ---------- Run ----------
if login():
    app()
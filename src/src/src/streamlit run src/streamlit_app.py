# src/streamlit_app.py
import streamlit as st
import pandas as pd
from pathlib import Path
import sqlite3
from datetime import datetime

BASE = Path(__file__).resolve().parents[1]
CSV_FILE = BASE / "attendance.csv"
DB_FILE = BASE / "attendance.sqlite3"

st.set_page_config(page_title="Face Attendance", layout="wide")

st.title("Face Recognition Attendance Dashboard")

st.sidebar.header("Data Source")
source = st.sidebar.selectbox("Load from", ["SQLite DB", "CSV file"])
if source == "CSV file":
    if CSV_FILE.exists():
        df = pd.read_csv(CSV_FILE)
    else:
        df = pd.DataFrame(columns=["name","date","time","status"])
else:
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT name,date,time,status FROM attendance ORDER BY date DESC, time DESC", conn)
    conn.close()

st.subheader("Attendance Records")
st.dataframe(df)

# summary
st.subheader("Summary")
if not df.empty:
    counts = df.groupby(["date","status"]).size().unstack(fill_value=0)
    st.write("Daily counts")
    st.dataframe(counts)
else:
    st.info("No attendance records yet.")

# mark absent send email sample
st.subheader("Actions")
date_filter = st.date_input("Select date", datetime.today())
selected_date = date_filter.strftime("%Y-%m-%d")
if st.button("Show absentees for selected date"):
    if df.empty:
        st.warning("No data.")
    else:
        absentees = df[df["date"]==selected_date]
        present_names = set(absentees[absentees["status"]=="Present"]["name"].tolist())
        # simplified: read dataset folder names to get total students
        import os
        dataset_dir = BASE.parent / "dataset"
        all_students = [d.name for d in dataset_dir.iterdir() if d.is_dir()]
        missing = [s for s in all_students if s not in present_names]
        st.write("Absentees:", missing)

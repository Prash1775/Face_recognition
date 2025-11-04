import streamlit as st
import cv2
import os
import numpy as np
import pandas as pd
import sqlite3
from datetime import datetime

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect("attendance.sqlite3")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            roll_no TEXT,
            class TEXT,
            image_path TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT,
            date TEXT,
            time TEXT,
            status TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- HELPER FUNCTIONS ----------------
def export_attendance_to_excel():
    conn = sqlite3.connect("attendance.sqlite3")
    query = """
        SELECT 
            s.name AS Student_Name,
            s.roll_no AS Roll_No,
            s.class AS Class,
            a.subject AS Subject,
            a.date AS Date,
            a.time AS Time,
            a.status AS Status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC, a.time DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    if not df.empty:
        df.to_excel("attendance_records.xlsx", index=False)
        st.toast("✅ Attendance exported automatically to 'attendance_records.xlsx'")

def get_students():
    conn = sqlite3.connect("attendance.sqlite3")
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    data = c.fetchall()
    conn.close()
    return data

def mark_attendance(student_id, subject):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    conn = sqlite3.connect("attendance.sqlite3")
    c = conn.cursor()
    c.execute("""
        SELECT * FROM attendance 
        WHERE student_id = ? AND date = ? AND subject = ?
    """, (student_id, date, subject))
    already_marked = c.fetchone()

    if already_marked:
        st.warning(f"⚠️ Attendance for this student already marked for {subject} today.")
    else:
        c.execute("""
            INSERT INTO attendance (student_id, subject, date, time, status)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, subject, date, time, "Present"))
        conn.commit()
        st.success(f"✅ Attendance marked for student ID {student_id} ({subject})")
        export_attendance_to_excel()
    conn.close()

# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="Smart Face Attendance", page_icon="🎓", layout="wide")
st.title("🎓 Smart Face Attendance System")

menu = ["Register Student", "Mark Attendance", "Attendance Records"]
choice = st.sidebar.selectbox("📚 Select Option", menu)

# ---------------- REGISTER STUDENT ----------------
if choice == "Register Student":
    st.header("🧍 Register New Student")
    name = st.text_input("Enter Student Name")
    roll_no = st.text_input("Enter Roll Number")
    class_name = st.text_input("Enter Class Name")

    if st.button("📸 Capture & Register"):
        if name and roll_no and class_name:
            cap = cv2.VideoCapture(0)
            st.info("Camera started — please look at the camera.")
            if not os.path.exists("dataset"):
                os.makedirs("dataset")

            img_path = f"dataset/{roll_no}_{name}.jpg"
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(img_path, frame)
                st.image(frame, channels="BGR", caption="Captured Image")
                conn = sqlite3.connect("attendance.sqlite3")
                c = conn.cursor()
                c.execute("INSERT INTO students (name, roll_no, class, image_path) VALUES (?, ?, ?, ?)",
                          (name, roll_no, class_name, img_path))
                conn.commit()
                conn.close()
                st.success("✅ Student registered successfully!")
            cap.release()
        else:
            st.warning("⚠️ Please fill all details before registering.")

# ---------------- MARK ATTENDANCE ----------------
elif choice == "Mark Attendance":
    st.header("📷 Mark Attendance by Face Recognition")
    subject = st.text_input("Enter Subject Name")

    if st.button("Start Attendance"):
        if not subject:
            st.warning("⚠️ Please enter subject name before starting attendance.")
        else:
            st.info("Starting camera... Press 'Stop Attendance' button to stop.")
            students = get_students()

            # Simulated attendance marking (face recognition can be added later)
            for student in students:
                student_id = student[0]
                mark_attendance(student_id, subject)

            st.success("✅ Attendance marking completed.")

# ---------------- ATTENDANCE RECORDS ----------------
elif choice == "Attendance Records":
    st.header("📅 Attendance Records")

    conn = sqlite3.connect("attendance.sqlite3")
    df = pd.read_sql_query("""
        SELECT 
            s.name AS Student_Name, 
            s.roll_no AS Roll_No, 
            s.class AS Class, 
            a.subject AS Subject,
            a.date AS Date, 
            a.time AS Time, 
            a.status AS Status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC
    """, conn)
    conn.close()

    if not df.empty:
        st.dataframe(df)
        st.success("📤 Automatically exported attendance to Excel file: 'attendance_records.xlsx'")
    else:
        st.warning("⚠️ No attendance records found.")

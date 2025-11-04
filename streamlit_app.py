import streamlit as st
import cv2
import os
import numpy as np
import pandas as pd
import sqlite3
from datetime import datetime, date

# ---------------- DATABASE PATH ----------------
DB_PATH = "attendance.sqlite3"

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
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

# ---------------- APP UI ----------------
st.title("🎓 Smart Face Attendance System")

menu = ["Home", "Register Student", "Mark Attendance", "View Attendance"]
choice = st.sidebar.selectbox("Menu", menu)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# ---------------- REGISTER STUDENT ----------------
if choice == "Register Student":
    st.header("🧑‍💼 Register New Student")

    name = st.text_input("Full Name")
    roll_no = st.text_input("Roll Number")
    student_class = st.text_input("Class")

    if st.button("📸 Capture Face and Save"):
        if name and roll_no:
            dataset_dir = "dataset"
            os.makedirs(dataset_dir, exist_ok=True)

            cap = cv2.VideoCapture(0)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

            count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in faces:
                    count += 1
                    face = frame[y:y + h, x:x + w]
                    img_path = f"{dataset_dir}/{roll_no}_{count}.jpg"
                    cv2.imwrite(img_path, face)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                cv2.imshow("Capturing Faces (Press 'Enter' to stop)", frame)
                if cv2.waitKey(1) == 13 or count >= 20:
                    break

            cap.release()
            cv2.destroyAllWindows()

            image_path = f"{dataset_dir}/{roll_no}_1.jpg"
            c.execute("INSERT INTO students (name, roll_no, class, image_path) VALUES (?, ?, ?, ?)",
                      (name, roll_no, student_class, image_path))
            conn.commit()
            st.success(f"✅ Student {name} registered successfully!")
        else:
            st.warning("Please fill all fields before capturing.")

# ---------------- MARK ATTENDANCE ----------------
elif choice == "Mark Attendance":
    st.header("📷 Mark Attendance by Face Recognition")

    subject = st.text_input("Enter Subject Name")

    if not subject:
        st.warning("Please enter the subject name to continue.")
    else:
        c.execute("SELECT * FROM students")
        students = c.fetchall()

        if not students:
            st.warning("⚠️ No students registered yet.")
        else:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            faces, labels = [], []

            for s in students:
                path = s[4]
                if os.path.exists(path):
                    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        faces.append(img)
                        labels.append(s[0])

            if faces:
                recognizer.train(faces, np.array(labels))

                st.info("Click 'Start Camera' to begin marking attendance.")
                if st.button("🎥 Start Camera"):
                    cap = cv2.VideoCapture(0)
                    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    marked_today = set()

                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        faces_detected = face_cascade.detectMultiScale(gray, 1.3, 5)

                        for (x, y, w, h) in faces_detected:
                            face_roi = gray[y:y + h, x:x + w]
                            id_, conf = recognizer.predict(face_roi)
                            if conf < 70:
                                student = [s for s in students if s[0] == id_][0]
                                name, roll_no = student[1], student[2]

                                now = datetime.now()
                                date_str, time_str = now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")

                                # Prevent duplicate marking for the same day & subject
                                if (id_, subject, date_str) not in marked_today:
                                    c.execute("""SELECT * FROM attendance 
                                                 WHERE student_id=? AND subject=? AND date=?""",
                                              (id_, subject, date_str))
                                    if not c.fetchone():
                                        c.execute("""INSERT INTO attendance 
                                                     (student_id, subject, date, time, status) 
                                                     VALUES (?, ?, ?, ?, ?)""",
                                                  (id_, subject, date_str, time_str, "Present"))
                                        conn.commit()
                                        marked_today.add((id_, subject, date_str))
                                        st.success(f"✅ Attendance marked for {name} ({subject})")

                                cv2.putText(frame, f"{name}", (x, y - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                            else:
                                cv2.putText(frame, "Unknown", (x, y - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                        cv2.imshow("Mark Attendance (Press 'q' to stop)", frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break

                    cap.release()
                    cv2.destroyAllWindows()
            else:
                st.error("No valid face images found for training!")

# ---------------- VIEW ATTENDANCE ----------------
elif choice == "View Attendance":
    st.header("📋 Attendance Records")

    roll_filter = st.text_input("🔍 Enter Roll Number to Filter (optional)")
    class_filter = st.text_input("🏫 Enter Class to Filter (optional)")
    date_filter = st.date_input("📅 Select Date (optional)", value=None)

    query = """
        SELECT students.name, students.roll_no, students.class, 
               attendance.subject, attendance.date, attendance.time, attendance.status
        FROM attendance
        JOIN students ON attendance.student_id = students.id
    """
    filters = []
    params = []

    if roll_filter:
        filters.append("students.roll_no = ?")
        params.append(roll_filter)
    if class_filter:
        filters.append("students.class = ?")
        params.append(class_filter)
    if date_filter:
        filters.append("attendance.date = ?")
        params.append(date_filter.strftime("%Y-%m-%d"))

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY attendance.date DESC, attendance.time DESC"

    df = pd.read_sql_query(query, conn, params=params)

    st.dataframe(df)

    if not df.empty:
        excel_path = "attendance_records.xlsx"
        df.to_excel(excel_path, index=False)
        st.success(f"✅ Attendance exported to {excel_path}")
    else:
        st.info("No records found for the selected filters.")

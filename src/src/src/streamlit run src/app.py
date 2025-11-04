import streamlit as st
import sqlite3
import cv2
import os
import numpy as np
import pandas as pd
from datetime import datetime

# ============ DATABASE SETUP ============
DB_PATH = "attendance.sqlite3"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute('''CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                roll_no TEXT,
                class TEXT,
                image_path TEXT
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                date TEXT,
                time TEXT,
                status TEXT,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )''')
conn.commit()

# ============ STREAMLIT APP ============
st.set_page_config(page_title="Smart Face Attendance", layout="centered")
st.title("🎓 Smart Face Attendance System")

menu = ["🏠 Home", "🧑‍💼 Register Student", "📷 Mark Attendance", "📋 View Attendance"]
choice = st.sidebar.selectbox("Navigation", menu)

# ============ HOME ============
if choice == "🏠 Home":
    st.write("""
    Welcome to the **Smart Face Attendance System** 👋  
    - Register student faces  
    - Mark attendance automatically using face recognition  
    - View attendance records anytime
    """)

# ============ REGISTER STUDENT ============
elif choice == "🧑‍💼 Register Student":
    st.header("Register New Student")

    name = st.text_input("Full Name")
    roll_no = st.text_input("Roll Number")
    student_class = st.text_input("Class")

    if st.button("📸 Capture Face and Save"):
        if not name or not roll_no or not student_class:
            st.warning("Please fill all fields!")
        else:
            dataset_dir = "dataset"
            os.makedirs(dataset_dir, exist_ok=True)

            cap = cv2.VideoCapture(0)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

            count = 0
            st.info("Capturing face images... Press 'Enter' in window to stop early.")
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in faces:
                    count += 1
                    face = gray[y:y + h, x:x + w]
                    file_path = f"{dataset_dir}/{roll_no}_{count}.jpg"
                    cv2.imwrite(file_path, face)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                cv2.imshow("Capturing Faces", frame)
                if cv2.waitKey(1) == 13 or count >= 20:  # Enter key or 20 faces
                    break

            cap.release()
            cv2.destroyAllWindows()

            first_image = f"{dataset_dir}/{roll_no}_1.jpg"
            c.execute("INSERT INTO students (name, roll_no, class, image_path) VALUES (?, ?, ?, ?)",
                      (name, roll_no, student_class, first_image))
            conn.commit()

            st.success(f"✅ Student {name} registered successfully!")

# ============ MARK ATTENDANCE ============
elif choice == "📷 Mark Attendance":
    st.header("Mark Attendance by Face Recognition")

    c.execute("SELECT * FROM students")
    students = c.fetchall()

    if not students:
        st.warning("⚠️ No students found. Please register students first.")
    else:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        faces, labels = [], []

        for s in students:
            student_id, name, roll_no, cls, img_path = s
            for file in os.listdir("dataset"):
                if file.startswith(roll_no):
                    path = os.path.join("dataset", file)
                    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        faces.append(img)
                        labels.append(student_id)

        if len(faces) == 0:
            st.error("No face data found to train recognizer!")
        else:
            recognizer.train(faces, np.array(labels))

            cap = cv2.VideoCapture(0)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

            st.info("Press 'q' to quit marking attendance.")

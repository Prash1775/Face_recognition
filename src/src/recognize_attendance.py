# src/recognize_attendance.py
import cv2
import face_recognition
import pickle
import os
from datetime import datetime
import pandas as pd
from pathlib import Path
import sqlite3

BASE = Path(__file__).resolve().parents[1]
ENCODINGS_FILE = BASE / "encodings" / "encodings.pickle"
CSV_FILE = BASE / "attendance.csv"
DB_FILE = BASE / "attendance.sqlite3"

# load encodings
with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.load(f)
known_encodings = data["encodings"]
known_names = data["names"]

# initialize DB if not exists
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    date TEXT,
    time TEXT,
    status TEXT
)
""")
conn.commit()

# helper: mark attendance (only once per person per day)
def mark_attendance(name, status="Present"):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    # check DB if already present today
    cur.execute("SELECT * FROM attendance WHERE name=? AND date=?", (name, date_str))
    if cur.fetchone():
        # already present today
        return
    cur.execute("INSERT INTO attendance (name,date,time,status) VALUES (?,?,?,?)",
                (name, date_str, time_str, status))
    conn.commit()
    # also add to CSV
    df = pd.DataFrame([[name, date_str, time_str, status]], columns=["name","date","time","status"])
    if CSV_FILE.exists():
        df.to_csv(CSV_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(CSV_FILE, index=False)

# start webcam
video_capture = cv2.VideoCapture(0)  # change index if multiple cams

process_frame = True
while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    # downscale for speed
    small_frame = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
    rgb_small_frame = small_frame[:, :, ::-1]

    if process_frame:
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")  # or 'cnn' for accuracy (slower)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.45)
            name = "Unknown"
            # use the shortest distance
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            if len(face_distances) > 0:
                best_idx = face_distances.argmin()
                if matches[best_idx]:
                    name = known_names[best_idx]
            face_names.append(name)

            if name != "Unknown":
                mark_attendance(name)

    process_frame = not process_frame

    # display
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # scale back up since we used 1/4 size
        top *= 4; right *= 4; bottom *= 4; left *= 4
        cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)
        cv2.rectangle(frame, (left, bottom-35), (right, bottom), (0,255,0), cv2.FILLED)
        cv2.putText(frame, name, (left+6, bottom-6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255,255,255), 1)

    cv2.imshow('Attendance (q to quit)', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# cleanup
video_capture.release()
cv2.destroyAllWindows()
conn.close()

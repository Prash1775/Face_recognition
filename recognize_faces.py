import cv2
import numpy as np
import face_recognition
import pickle
import csv
from datetime import datetime

MODEL_PATH = "trained_faces.pkl"
ATTENDANCE_FILE = "attendance.csv"

# Load trained model
print("📂 Loading trained model...")
with open(MODEL_PATH, "rb") as f:
    data = pickle.load(f)

known_encodings = data["encodings"]
known_names = data["names"]

# Initialize webcam
print("📸 Starting camera...")
cam = cv2.VideoCapture(0)
if not cam.isOpened():
    print("❌ Unable to access camera.")
    exit()

# Helper function to mark attendance
def mark_attendance(name):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    # Check if already marked today
    with open(ATTENDANCE_FILE, "r+") as f:
        existing = f.readlines()
        names_today = [line.split(",")[0] for line in existing if date in line]

        if name not in names_today:
            f.writelines(f"{name},{date},{time}\n")
            print(f"✅ Attendance marked for {name} at {time}")

print("➡ Press ESC to quit.")
while True:
    ret, frame = cam.read()
    if not ret:
        print("⚠️ Unable to read frame.")
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        name = "Unknown"

        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_names[best_match_index]

        # Draw box and label
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Mark attendance
        if name != "Unknown":
            mark_attendance(name)

    cv2.imshow("Face Recognition Attendance", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC key
        break

cam.release()
cv2.destroyAllWindows()

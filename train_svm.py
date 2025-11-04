import os
import cv2
import face_recognition
import pickle

DATASET_DIR = "dataset"
MODEL_PATH = "trained_faces.pkl"

known_encodings = []
known_names = []

print("🔍 Scanning dataset folder...")
for person_name in os.listdir(DATASET_DIR):
    person_folder = os.path.join(DATASET_DIR, person_name)
    if not os.path.isdir(person_folder):
        continue

    print(f"📂 Processing {person_name}...")
    for filename in os.listdir(person_folder):
        if not filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            continue
        path = os.path.join(person_folder, filename)
        image = face_recognition.load_image_file(path)
        encodings = face_recognition.face_encodings(image)
        if len(encodings) > 0:
            known_encodings.append(encodings[0])
            known_names.append(person_name)

print("✅ Training model...")
data = {"encodings": known_encodings, "names": known_names}

with open(MODEL_PATH, "wb") as f:
    pickle.dump(data, f)

print(f"🎓 Model trained and saved as '{MODEL_PATH}'")

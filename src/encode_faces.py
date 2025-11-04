# src/encode_faces.py
import os
import face_recognition
import pickle
from pathlib import Path
import numpy as np

DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"
ENCODINGS_FILE = Path(__file__).resolve().parents[1] / "encodings" / "encodings.pickle"
ENCODINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

known_encodings = []
known_names = []

def encode_dataset():
    for person_dir in DATASET_DIR.iterdir():
        if not person_dir.is_dir():
            continue
        name = person_dir.name
        print(f"Processing {name}")
        for img_path in person_dir.glob("*"):
            try:
                image = face_recognition.load_image_file(str(img_path))
                # Convert to face_locations and encodings
                boxes = face_recognition.face_locations(image, model="hog")
                encs = face_recognition.face_encodings(image, boxes)
                if len(encs) == 0:
                    print(f"  no faces found in {img_path.name}")
                    continue
                # store first face encoding found in file
                known_encodings.append(encs[0])
                known_names.append(name)
            except Exception as e:
                print(f"  error processing {img_path}: {e}")

    # Save
    data = {"encodings": known_encodings, "names": known_names}
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(data, f)
    print(f"Saved encodings to {ENCODINGS_FILE}")

if __name__ == "__main__":
    encode_dataset()

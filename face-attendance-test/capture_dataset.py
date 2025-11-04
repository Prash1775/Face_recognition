import cv2
import os

# Ask user for their name
name = input("Enter your name: ").strip()
dataset_path = "dataset"

# Create folder for user
user_path = os.path.join(dataset_path, name)
os.makedirs(user_path, exist_ok=True)

# Start webcam (force use of DirectShow)
cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cam.isOpened():
    print("❌ Error: Could not access the webcam.")
    exit()

print("✅ Camera opened successfully.")
print("Press SPACE to capture an image or ESC to exit.")

count = 0
while True:
    ret, frame = cam.read()
    if not ret:
        print("⚠️ Unable to grab frame. Retrying...")
        continue

    cv2.imshow("Capture Dataset", frame)
    key = cv2.waitKey(1)

    if key == 27:  # ESC to exit
        print("👋 Exiting capture.")
        break
    elif key == 32:  # SPACE to capture
        img_name = os.path.join(user_path, f"{name}_{count}.jpg")
        cv2.imwrite(img_name, frame)
        print(f"📸 Saved: {img_name}")
        count += 1

cam.release()
cv2.destroyAllWindows()

import sqlite3

# Connect to (or create) the database
conn = sqlite3.connect("attendance.sqlite3")
c = conn.cursor()

# Create the students table if it doesn't exist
c.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_no TEXT UNIQUE NOT NULL,
    class TEXT,
    image_path TEXT
)
""")

# Create attendance table (optional but useful)
c.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    date TEXT,
    time TEXT,
    status TEXT,
    FOREIGN KEY(student_id) REFERENCES students(id)
)
""")

conn.commit()
conn.close()

print("✅ Database initialized successfully! Tables created.")

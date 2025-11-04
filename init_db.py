import sqlite3

conn = sqlite3.connect("attendance.sqlite3")
c = conn.cursor()

# Create students table
c.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_no TEXT UNIQUE NOT NULL,
    class TEXT,
    image_path TEXT
)
''')

# Create attendance table (if not already)
c.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    date TEXT,
    time TEXT,
    status TEXT
)
''')

conn.commit()
conn.close()
print("✅ Database initialized with 'students' and 'attendance' tables.")

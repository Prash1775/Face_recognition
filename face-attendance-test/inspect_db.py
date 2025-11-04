import sqlite3

conn = sqlite3.connect("attendance.sqlite3")
c = conn.cursor()

c.execute("PRAGMA table_info(students);")
rows = c.fetchall()

print("students table schema (cid, name, type, notnull, dflt_value, pk):")
for r in rows:
    print(r)

conn.close()

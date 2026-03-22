import sqlite3
import os

db_path = r"c:\Users\LENOVO\OneDrive\Desktop\DS.web\instance\app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE user ADD COLUMN name VARCHAR(150) DEFAULT 'User'")
    print("Column added successfully.")
except sqlite3.OperationalError as e:
    print("Notice: ", e)

# Update the specific user
cursor.execute("UPDATE user SET name = 'Pushpendra' WHERE email = 'this.pushpendra@gmail.com'")
conn.commit()
print("Updated user Name successfully.")

conn.close()

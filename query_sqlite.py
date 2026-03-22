import sqlite3

db_path = r"c:\Users\LENOVO\OneDrive\Desktop\DS.web\instance\app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id FROM user WHERE email = ?", ("this.pushpendra@gmail.com",))
user = cursor.fetchone()

if user:
    user_id = user[0]
    cursor.execute("SELECT job_id, status FROM reel WHERE user_id = ?", (user_id,))
    reels = cursor.fetchall()
    if not reels:
        print("No reels found for this user.")
    for reel in reels:
        print(f"Reel ID: {reel[0]}, Status: {reel[1]}")
else:
    print("User not found")

conn.close()

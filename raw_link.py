import sqlite3
import os

db_path = r"c:\Users\LENOVO\OneDrive\Desktop\DS.web\instance\app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get user ID
cursor.execute("SELECT id FROM user WHERE email = ?", ("this.pushpendra@gmail.com",))
user = cursor.fetchone()

if user:
    user_id = user[0]
    reels_dir = os.path.join(r"c:\Users\LENOVO\OneDrive\Desktop\DS.web\static", "reels")
    
    count = 0
    for f in os.listdir(reels_dir):
        if f.endswith(".mp4"):
            job_id = f[:-4]
            # Check if it already exists in the database
            cursor.execute("SELECT id FROM reel WHERE job_id = ?", (job_id,))
            existing_reel = cursor.fetchone()
            if not existing_reel:
                cursor.execute("INSERT INTO reel (job_id, user_id, status) VALUES (?, ?, ?)", (job_id, user_id, 'completed'))
                count += 1
            else:
                cursor.execute("UPDATE reel SET user_id = ? WHERE job_id = ?", (user_id, job_id))
                count += 1
                
    conn.commit()
    print(f"Successfully linked {count} legacy reels to {user_id}.")
else:
    print("User not found in db.")
conn.close()

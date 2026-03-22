import sys
import os
sys.path.append(r'c:\Users\LENOVO\OneDrive\Desktop\DS.web')
from main import app, db, User, Reel

with app.app_context():
    user = User.query.filter_by(email="this.pushpendra@gmai.com").first()
    if user:
        print(f"User ID: {user.id}")
        reels = Reel.query.filter_by(user_id=user.id).all()
        if not reels:
            print("No reels found for this user.")
        for reel in reels:
            print(f"Reel ID: {reel.job_id}, Status: {reel.status}")
    else:
        print("User not found")

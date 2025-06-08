import sqlite3
from datetime import datetime, timedelta
import random

# Categories to randomly assign
categories = ["Groceries", "Transport", "Entertainment", "Bills", "Eating Out", "Shopping", "Health"]

# Replace this with an actual user_id from your 'users' table
user_id = 4  # Make sure this user exists!

# Connect to the zamani database
conn = sqlite3.connect('data/zamani.db')
c = conn.cursor()

# Generate expenses for the past 14 days
for i in range(14):
    day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
    for _ in range(random.randint(1, 4)):  # Add 1 to 4 expenses per day
        amount = round(random.uniform(100, 2500), 2)  # Random amount between 100 and 2500
        category = random.choice(categories)
        note = f"Auto-generated {category} expense"
        c.execute("INSERT INTO expenses (amount, category, note, date, user_id) VALUES (?, ?, ?, ?, ?)",
                  (amount, category, note, day, user_id))

conn.commit()
conn.close()
print("✅ Fake data added for the past 14 days!")

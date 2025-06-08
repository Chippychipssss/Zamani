import sqlite3

# Connect to (or create) the database
conn = sqlite3.connect('data/zamani.db')
c = conn.cursor()

# Create a table for expenses
c.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount INTEGER NOT NULL,
    category TEXT NOT NULL,
    note TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()

print("✅ Database initialized")

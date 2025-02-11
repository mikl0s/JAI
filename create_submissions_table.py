import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('judges.db')
cursor = conn.cursor()

# Create submissions table
cursor.execute('''
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    position TEXT NOT NULL,
    ruling TEXT NOT NULL,
    link TEXT NOT NULL,
    x_link TEXT,
    status TEXT DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Commit and close
conn.commit()
conn.close()
print("Submissions table created successfully!")
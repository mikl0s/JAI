import sqlite3
from datetime import datetime

# Connect to SQLite database
conn = sqlite3.connect('judges.db')
cursor = conn.cursor()

# Create submissions table with IP tracking
cursor.execute('''
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    position TEXT NOT NULL,
    ruling TEXT NOT NULL,
    link TEXT NOT NULL,
    x_link TEXT,
    status TEXT DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT NOT NULL
)
''')

# Create admin_logs table
cursor.execute('''
CREATE TABLE IF NOT EXISTS admin_logs (
    id INTEGER PRIMARY KEY,
    admin_username TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    ip_address TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Create ip_whitelist table
cursor.execute('''
CREATE TABLE IF NOT EXISTS ip_whitelist (
    id INTEGER PRIMARY KEY,
    ip_address TEXT NOT NULL,
    reason TEXT NOT NULL,
    expiry TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ip_address)
)
''')

# Create ip_locations table
cursor.execute('''
CREATE TABLE IF NOT EXISTS ip_locations (
    id INTEGER PRIMARY KEY,
    ip_address TEXT NOT NULL,
    country TEXT NOT NULL,
    country_code TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ip_address)
)
''')

# Insert localhost into whitelist with no expiry (far future date)
far_future = datetime(2099, 12, 31).isoformat()
cursor.execute('''
INSERT OR IGNORE INTO ip_whitelist (ip_address, reason, expiry)
VALUES ('127.0.0.1', 'localhost', ?)
''', (far_future,))

# Commit and close
conn.commit()
conn.close()
print("Tables created successfully!")
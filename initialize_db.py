import sqlite3
from datetime import datetime, timedelta

# Connect to SQLite database
conn = sqlite3.connect('judges.db')
cursor = conn.cursor()

# Create judges table
cursor.execute('''
CREATE TABLE IF NOT EXISTS judges (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    job_position TEXT NOT NULL,
    ruling TEXT NOT NULL,
    link TEXT NOT NULL,
    x_link TEXT,
    confirmed INTEGER DEFAULT 0,
    displayed INTEGER DEFAULT 1
)
''')

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

# Sample data for judges
sample_judges = [
    ('Judge John Smith', 'District Court Judge', 'Ruled in favor of constitutional rights', 'https://example.com/ruling1', 'https://x.com/post1', 1),
    ('Judge Sarah Johnson', 'Supreme Court Justice', 'Upheld First Amendment protections', 'https://example.com/ruling2', 'https://x.com/post2', 1),
    ('Judge Michael Brown', 'Federal Judge', 'Protected civil liberties', 'https://example.com/ruling3', 'https://x.com/post3', 0),
    ('Judge Emily Davis', 'Circuit Court Judge', 'Defended constitutional principles', 'https://example.com/ruling4', 'https://x.com/post4', 0),
    ('Judge Robert Wilson', 'Appeals Court Judge', 'Preserved individual rights', 'https://example.com/ruling5', 'https://x.com/post5', 1)
]

cursor.executemany('''
INSERT INTO judges (name, job_position, ruling, link, x_link, confirmed)
VALUES (?, ?, ?, ?, ?, ?)
''', sample_judges)

# Sample data for submissions
sample_submissions = [
    ('Judge Maria Garcia', 'State Court Judge', 'Landmark privacy rights decision', 'https://example.com/sub1', 'https://x.com/sub1', 'pending', '192.168.1.1'),
    ('Judge David Lee', 'District Judge', 'Protected freedom of speech', 'https://example.com/sub2', 'https://x.com/sub2', 'approved', '192.168.1.2'),
    ('Judge Lisa Chen', 'Federal Judge', 'Upheld due process rights', 'https://example.com/sub3', 'https://x.com/sub3', 'pending', '192.168.1.3'),
    ('Judge James Wilson', 'Circuit Judge', 'Constitutional interpretation ruling', 'https://example.com/sub4', 'https://x.com/sub4', 'rejected', '192.168.1.4'),
    ('Judge Anna Martinez', 'Supreme Court Justice', 'Protected religious freedom', 'https://example.com/sub5', 'https://x.com/sub5', 'pending', '192.168.1.5')
]

cursor.executemany('''
INSERT INTO submissions (name, position, ruling, link, x_link, status, ip_address)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', sample_submissions)

# Insert localhost into whitelist with no expiry (far future date)
far_future = (datetime.now() + timedelta(days=36500)).isoformat()
cursor.execute('''
INSERT OR IGNORE INTO ip_whitelist (ip_address, reason, expiry)
VALUES ('127.0.0.1', 'localhost', ?)
''', (far_future,))

# Commit and close
conn.commit()
conn.close()
print("Database initialized successfully with sample data!")
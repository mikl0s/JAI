import sqlite3
from datetime import datetime

# Connect to SQLite database
conn = sqlite3.connect('judges.db')
cursor = conn.cursor()

# Create ip_geolocation table with detailed information
cursor.execute('''
CREATE TABLE IF NOT EXISTS ip_geolocation (
    id INTEGER PRIMARY KEY,
    ip_address TEXT NOT NULL UNIQUE,
    hostname TEXT,
    continent_code TEXT,
    continent_name TEXT,
    country_code2 TEXT,
    country_code3 TEXT,
    country_name TEXT,
    country_capital TEXT,
    state_prov TEXT,
    state_code TEXT,
    city TEXT,
    zipcode TEXT,
    latitude TEXT,
    longitude TEXT,
    is_eu BOOLEAN,
    country_flag TEXT,
    country_emoji TEXT,
    isp TEXT,
    organization TEXT,
    timezone_name TEXT,
    timezone_offset INTEGER,
    currency_code TEXT,
    currency_symbol TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Create index on ip_address for faster lookups
cursor.execute('''
CREATE INDEX IF NOT EXISTS idx_ip_geolocation_ip
ON ip_geolocation(ip_address)
''')

# Commit and close
conn.commit()
conn.close()
print("IP Geolocation table created successfully!")
import psycopg2
import psycopg2.extras
from psycopg2.extras import RealDictCursor
import os
from ip_geolocation import get_ip_geolocation
from time import sleep
from dotenv import load_dotenv

# Load environment variables
def load_env_vars():
    # Try to load from admin_app/.env first, then from .env.local
    if os.path.exists('admin_app/.env'):
        load_dotenv('admin_app/.env')
    elif os.path.exists('.env.local'):
        load_dotenv('.env.local')
    else:
        print("Error: No .env file found. Please create one with PostgreSQL credentials.")
        sys.exit(1)

# Load environment variables
load_env_vars()

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', '5432'),
        dbname=os.environ.get('DB_NAME', 'jai_db'),
        user=os.environ.get('DB_USER', 'jai'),
        password=os.environ.get('DB_PASSWORD', '')
    )
    conn.autocommit = True
    return conn

def query_db(query, args=(), one=False, commit=True):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor if one else None)
    cur.execute(query, args)
    if commit:
        conn.commit()
    rv = cur.fetchall()
    cur.close()
    conn.close()
    return (dict(rv[0]) if rv else None) if one else rv

def populate_missing_geolocation_data():
    print("Fetching unique IP addresses from submissions...")
    # Get all unique IP addresses from submissions
    submissions_ips = query_db('''
        SELECT DISTINCT ip_address 
        FROM submissions 
        WHERE ip_address NOT IN (
            SELECT ip_address 
            FROM ip_geolocation
        )
    ''')

    total_ips = len(submissions_ips)
    print(f"Found {total_ips} IP addresses without geolocation data")

    # Process each IP address
    for i, row in enumerate(submissions_ips, 1):
        ip_address = row['ip_address'] if isinstance(row, dict) else row[0]
        print(f"Processing IP {i}/{total_ips}: {ip_address}")
        try:
            geo_data = get_ip_geolocation(ip_address)
            if geo_data:
                print(f"✓ Successfully cached geolocation data for {ip_address}")
            else:
                print(f"✗ Failed to get geolocation data for {ip_address}")
            # Add a small delay to avoid hitting API rate limits
            sleep(1)
        except Exception as e:
            print(f"✗ Error processing {ip_address}: {str(e)}")

    print("\nGeolocation data population complete!")

if __name__ == '__main__':
    populate_missing_geolocation_data()
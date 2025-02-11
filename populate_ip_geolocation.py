import sqlite3
from ip_geolocation import get_ip_geolocation
from time import sleep

def get_db_connection():
    return sqlite3.connect('judges.db')

def query_db(query, args=(), one=False, commit=True):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    if commit:
        conn.commit()
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

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
    for i, (ip_address,) in enumerate(submissions_ips, 1):
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
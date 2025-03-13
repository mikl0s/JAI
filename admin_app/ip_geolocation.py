import os
import requests
from datetime import datetime
import psycopg2
import psycopg2.extras
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import subprocess

# Load environment variables from .env.local
load_dotenv('.env.local')

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

def get_external_ip():
    """
    Get the external IP address using OpenDNS
    """
    try:
        result = subprocess.run(['dig', '@resolver4.opendns.com', 'myip.opendns.com', '+short'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            ip = result.stdout.strip()
            # Skip if IPv6
            if ':' in ip:
                return None
            return ip
    except Exception as e:
        print(f"Error fetching external IP: {str(e)}")
        return None

def is_ipv4(ip):
    """
    Check if an IP address is IPv4
    """
    return ':' not in ip

def get_ip_geolocation(ip_address):
    """
    Get geolocation data for an IP address, using cached data if available
    or fetching from the API if not.
    """
    # Skip IPv6 addresses
    if not is_ipv4(ip_address):
        return None

    # Easter egg: Make localhost/127.0.0.1 show up as Antarctica
    if ip_address in ['127.0.0.1', 'localhost']:
        # Insert Antarctica data into the database if it doesn't exist
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if entry exists
        cur.execute('SELECT id FROM ip_geolocation WHERE ip_address = %s', (ip_address,))
        exists = cur.fetchone()
        
        if exists is None:
            # Insert Antarctica data - let PostgreSQL handle the ID auto-increment
            cur.execute('''
                INSERT INTO ip_geolocation (
                    ip_address, hostname, continent_code, continent_name,
                    country_code2, country_code3, country_name, country_capital,
                    state_prov, state_code, city, zipcode, latitude, longitude,
                    is_eu, country_flag, country_emoji,
                    isp, organization, timezone_name, timezone_offset,
                    currency_code, currency_symbol
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                ip_address, 'penguin.antarctica.local', 'AN', 'Antarctica',
                'AQ', 'ATA', 'Antarctica', 'Amundsen-Scott Station',
                'South Pole', 'SP', 'Penguin Colony', '00000', '-90.0000', '0.0000',
                False, '/static/antarctica.png', '🇦🇶',
                'Antarctic Network Services', 'Penguin Research Institute', 'Antarctica/South_Pole', '0',
                'USD', '$'
            ))
            conn.commit()
        
        cur.close()
        conn.close()
        
        # Return the data from the database
        result = query_db('SELECT * FROM ip_geolocation WHERE ip_address = %s', 
                       (ip_address,), one=True)
        
        # Ensure we return a proper dictionary
        if result is not None:
            # Convert to a standard dictionary if it's not already
            return dict(result) if hasattr(result, 'keys') else result
        return None

    # Check cache first
    cached = query_db('''
        SELECT * FROM ip_geolocation 
        WHERE ip_address = %s
    ''', (ip_address,), one=True)
    
    if cached:
        return cached

    # If not in cache, fetch from API
    api_key = os.getenv('IPGEOLOCATION_API_KEY')
    if not api_key:
        raise ValueError("IPGEOLOCATION_API_KEY not found in environment variables")

    url = f"https://api.ipgeolocation.io/ipgeo"
    params = {
        "apiKey": api_key,
        "ip": ip_address
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for non-200 status codes
        data = response.json()

        # Insert into database
        query_db('''
            INSERT INTO ip_geolocation (
                ip_address, hostname, continent_code, continent_name,
                country_code2, country_code3, country_name, country_capital,
                state_prov, state_code, city, zipcode, latitude, longitude,
                is_eu, country_flag, country_emoji,
                isp, organization, timezone_name, timezone_offset,
                currency_code, currency_symbol
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            data.get('ip'),
            data.get('hostname'),
            data.get('continent_code'),
            data.get('continent_name'),
            data.get('country_code2'),
            data.get('country_code3'),
            data.get('country_name'),
            data.get('country_capital'),
            data.get('state_prov'),
            data.get('state_code'),
            data.get('city'),
            data.get('zipcode'),
            data.get('latitude'),
            data.get('longitude'),
            data.get('is_eu'),
            data.get('country_flag'),
            data.get('country_emoji'),
            data.get('isp'),
            data.get('organization'),
            data.get('time_zone', {}).get('name'),
            data.get('time_zone', {}).get('offset'),
            data.get('currency', {}).get('code'),
            data.get('currency', {}).get('symbol')
        ))

        # Return the geolocation data
        result = query_db('SELECT * FROM ip_geolocation WHERE ip_address = %s', 
                       (ip_address,), one=True)
        
        # Ensure we return a proper dictionary
        if result is not None:
            # Convert to a standard dictionary if it's not already
            return dict(result) if hasattr(result, 'keys') else result
        return None
    
    except Exception as e:
        print(f"Error fetching geolocation data for IP {ip_address}: {str(e)}")
        return None

def format_geolocation_data(geo_data):
    """
    Format geolocation data into a human-readable string
    """
    if not geo_data:
        return "Location data unavailable"
    
    # Unpack the data (matches order of columns in table)
    (id, ip, hostname, continent_code, continent_name, country_code2,
     country_code3, country_name, country_capital, state_prov, state_code,
     city, zipcode, latitude, longitude, is_eu, country_flag, country_emoji,
     isp, organization, timezone_name, timezone_offset, currency_code,
     currency_symbol, last_updated) = geo_data

    # Build location string with emoji flag if available
    location_parts = []
    if city:
        location_parts.append(city)
    if state_prov:
        location_parts.append(state_prov)
    if country_name and country_emoji:
        location_parts.append(f"{country_emoji} {country_name}")
    elif country_name:
        location_parts.append(country_name)
    
    location = ", ".join(location_parts)
    
    # Add additional details
    details = []
    if isp:
        details.append(f"ISP: {isp}")
    if organization:
        details.append(f"Org: {organization}")
    if timezone_name:
        # Convert timezone_offset to int if it's a string, or handle it safely
        if timezone_offset is not None:
            try:
                offset_int = int(timezone_offset) if isinstance(timezone_offset, str) else timezone_offset
                offset_str = f"{offset_int:+d}"
            except (ValueError, TypeError):
                offset_str = str(timezone_offset)
        else:
            offset_str = ""
        details.append(f"TZ: {timezone_name} (UTC{offset_str})")
    if is_eu:
        details.append("🇪🇺 EU")

    return f"{location} ({', '.join(details)})" if details else location
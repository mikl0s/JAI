import os
import requests
from datetime import datetime
import sqlite3
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

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

def get_ip_geolocation(ip_address):
    """
    Get geolocation data for an IP address, using cached data if available
    or fetching from the API if not.
    """
    # Check cache first
    cached = query_db('''
        SELECT * FROM ip_geolocation 
        WHERE ip_address = ?
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
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

        return query_db('SELECT * FROM ip_geolocation WHERE ip_address = ?', 
                       (ip_address,), one=True)
    
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
        offset_str = f"{timezone_offset:+d}" if timezone_offset is not None else ""
        details.append(f"TZ: {timezone_name} (UTC{offset_str})")
    if is_eu:
        details.append("🇪🇺 EU")

    return f"{location} ({', '.join(details)})" if details else location
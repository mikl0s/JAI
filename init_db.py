#!/usr/bin/env python3
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Database connection parameters from environment variables
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

def get_db_connection():
    """Create a database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        sys.exit(1)

def initialize_database():
    """Initialize the database schema with hardcoded users table content"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("Starting database initialization...")
        
        # Drop all existing tables
        print("Dropping existing tables...")
        cursor.execute("""
        DO $$ 
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END $$;
        """)
        
        # Create tables
        print("Creating tables...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS judges (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            title VARCHAR(255) NOT NULL,
            court VARCHAR(255) NOT NULL,
            state VARCHAR(50) NOT NULL,
            corrupt_votes INTEGER DEFAULT 0,
            not_corrupt_votes INTEGER DEFAULT 0,
            us_corrupt_votes INTEGER DEFAULT 0,
            us_not_corrupt_votes INTEGER DEFAULT 0,
            status VARCHAR(50) DEFAULT 'confirmed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS judge_submissions (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            title VARCHAR(255) NOT NULL,
            court VARCHAR(255) NOT NULL,
            state VARCHAR(50) NOT NULL,
            ip_address VARCHAR(50) NOT NULL,
            browser_fingerprint VARCHAR(255),
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            country VARCHAR(50),
            city VARCHAR(100),
            region VARCHAR(100),
            latitude FLOAT,
            longitude FLOAT
        );
        
        CREATE TABLE IF NOT EXISTS votes (
            id SERIAL PRIMARY KEY,
            judge_id INTEGER REFERENCES judges(id),
            ip_address VARCHAR(50) NOT NULL,
            browser_fingerprint VARCHAR(255),
            vote_type VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            country VARCHAR(50),
            city VARCHAR(100),
            region VARCHAR(100),
            latitude FLOAT,
            longitude FLOAT
        );
        
        CREATE TABLE IF NOT EXISTS ip_geolocation (
            ip_address VARCHAR(50) PRIMARY KEY,
            country VARCHAR(50),
            city VARCHAR(100),
            region VARCHAR(100),
            latitude FLOAT,
            longitude FLOAT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS whitelisted_ips (
            id SERIAL PRIMARY KEY,
            ip_address VARCHAR(50) UNIQUE NOT NULL,
            description VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Insert the exact current users data
        print("Inserting users data...")
        cursor.execute("""
        INSERT INTO users (id, username, password_hash, is_admin, created_at, last_login) VALUES
        (1, 'mikkel', '$2b$12$tVN1BhHXEJPzVpkp8Jh.1.32VIJDxbA9tNEkyB619N.o4lZKCuaXe', TRUE, '2023-11-01 12:00:00', '2025-03-13 14:25:10');
        """)
        
        # Reset the sequence for the id column to continue after the highest id
        cursor.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));")
        
        print("Users data inserted successfully.")
        print("Database initialization completed successfully.")
        
    except psycopg2.Error as e:
        print(f"Error during database initialization: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    initialize_database()

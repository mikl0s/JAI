import sqlite3
import psycopg2
import os
from dotenv import load_dotenv
import sys

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

# SQLite connection
def get_sqlite_connection():
    return sqlite3.connect('judges.db')

# PostgreSQL connection
def get_postgres_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', '5432'),
        dbname=os.environ.get('DB_NAME', 'jai_db'),
        user=os.environ.get('DB_USER', 'jai'),
        password=os.environ.get('DB_PASSWORD', '')
    )

# Get SQLite tables and their schema
def get_sqlite_tables():
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    table_schemas = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        table_schemas[table_name] = columns
    
    conn.close()
    return table_schemas

# Drop existing PostgreSQL tables
def drop_postgres_tables(table_schemas):
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    print("Dropping existing tables...")
    for table_name in table_schemas.keys():
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            print(f"Dropped table {table_name}")
        except Exception as e:
            print(f"Error dropping table {table_name}: {str(e)}")
    
    conn.commit()
    conn.close()

# Create PostgreSQL tables based on SQLite schema
def create_postgres_tables(table_schemas):
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    # SQLite to PostgreSQL type mapping
    type_mapping = {
        'INTEGER': 'INTEGER',
        'REAL': 'REAL',
        'TEXT': 'TEXT',
        'BLOB': 'BYTEA',
        'BOOLEAN': 'BOOLEAN',
        'DATETIME': 'TIMESTAMP',
        'TIMESTAMP': 'TIMESTAMP',
        'DATE': 'DATE',
        'TIME': 'TIME',
    }
    
    for table_name, columns in table_schemas.items():
        # Start building the CREATE TABLE statement
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
        
        # Add columns
        column_defs = []
        primary_key_columns = []
        
        for column in columns:
            # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
            col_id, col_name, col_type, not_null, default_val, is_pk = column
            
            # Map SQLite type to PostgreSQL type
            pg_type = type_mapping.get(col_type.upper(), 'TEXT')
            
            # Special case for displayed column in judges table
            if table_name == 'judges' and col_name == 'displayed':
                pg_type = 'INTEGER'  # Keep as INTEGER instead of converting to BOOLEAN
            
            # Build column definition
            col_def = f"{col_name} {pg_type}"
            
            # Add NOT NULL constraint if needed
            if not_null:
                col_def += " NOT NULL"
            
            # Add default value if exists
            if default_val is not None:
                if default_val.lower() == 'current_timestamp':
                    col_def += " DEFAULT CURRENT_TIMESTAMP"
                else:
                    col_def += f" DEFAULT {default_val}"
            
            # Track primary key columns
            if is_pk:
                primary_key_columns.append(col_name)
            
            column_defs.append(col_def)
        
        # Add primary key constraint if exists
        if primary_key_columns:
            pk_constraint = f"PRIMARY KEY ({', '.join(primary_key_columns)})"
            column_defs.append(pk_constraint)
        
        # Finalize the CREATE TABLE statement
        create_table_sql += ",\n".join(column_defs)
        create_table_sql += "\n);"
        
        # Execute the CREATE TABLE statement
        print(f"Creating table {table_name}...")
        print(create_table_sql)
        cursor.execute(create_table_sql)
    
    conn.commit()
    conn.close()

# Convert SQLite data types to PostgreSQL compatible types
def convert_data_types(row, columns, table_name):
    converted_row = list(row)
    
    for i, column in enumerate(columns):
        # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
        col_name = column[1]
        col_type = column[2].upper()
        
        # Convert SQLite INTEGER to PostgreSQL BOOLEAN for boolean columns
        # But keep 'displayed' as INTEGER for the judges table
        if col_type == 'BOOLEAN' or col_name == 'is_eu':
            if converted_row[i] is not None:
                # Convert 0/1 to False/True
                converted_row[i] = bool(converted_row[i])
        
        # Special case: don't convert 'displayed' column in judges table
        if table_name == 'judges' and col_name == 'displayed':
            # Ensure it remains as an integer
            if converted_row[i] is not None:
                converted_row[i] = int(converted_row[i])
    
    return tuple(converted_row)

# Migrate data from SQLite to PostgreSQL
def migrate_data(table_schemas):
    sqlite_conn = get_sqlite_connection()
    sqlite_cursor = sqlite_conn.cursor()
    
    postgres_conn = get_postgres_connection()
    postgres_cursor = postgres_conn.cursor()
    
    for table_name, columns in table_schemas.items():
        print(f"Migrating data for table {table_name}...")
        
        # Get all data from SQLite table
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"No data to migrate for table {table_name}")
            continue
        
        # Get column names
        column_names = [column[1] for column in columns]
        
        # Prepare INSERT statement for PostgreSQL
        placeholders = ", ".join("%s" for _ in range(len(column_names)))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
        
        # Insert data in batches
        batch_size = 1000
        total_rows = len(rows)
        
        for i in range(0, total_rows, batch_size):
            batch = rows[i:i+batch_size]
            # Convert data types for each row
            converted_batch = [convert_data_types(row, columns, table_name) for row in batch]
            postgres_cursor.executemany(insert_sql, converted_batch)
            postgres_conn.commit()
            print(f"Migrated {min(i+batch_size, total_rows)}/{total_rows} rows for table {table_name}")
    
    sqlite_conn.close()
    postgres_conn.commit()
    postgres_conn.close()

# Main migration function
def migrate_to_postgres():
    print("Starting migration from SQLite to PostgreSQL...")
    
    # Load environment variables
    load_env_vars()
    
    # Get SQLite table schemas
    print("Extracting SQLite schema...")
    table_schemas = get_sqlite_tables()
    
    # Drop existing tables in PostgreSQL
    drop_postgres_tables(table_schemas)
    
    # Create tables in PostgreSQL
    print("Creating tables in PostgreSQL...")
    create_postgres_tables(table_schemas)
    
    # Migrate data
    print("Migrating data from SQLite to PostgreSQL...")
    migrate_data(table_schemas)
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate_to_postgres()

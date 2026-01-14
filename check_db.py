import sqlite3
import sys

# Direct database check without importing models
conn = sqlite3.connect('capstone_repo.db')
cursor = conn.cursor()

# Check what tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f'Tables in database: {tables}')

# Check users table columns
if 'users' in tables:
    cursor.execute('PRAGMA table_info(users)')
    columns = [row[1] for row in cursor.fetchall()]
    print(f'Users table columns: {columns}')
    
    if 'full_name' in columns:
        print('✓ full_name column exists in users table')
    else:
        print('✗ full_name column does NOT exist in users table - MIGRATION NEEDED')
else:
    print('users table does not exist')

conn.close()
sys.exit(0)



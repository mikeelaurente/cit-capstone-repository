import sqlite3

conn = sqlite3.connect('capstone_repo.db')
cursor = conn.cursor()

try:
    # Add full_name column to users table
    cursor.execute('ALTER TABLE users ADD COLUMN full_name VARCHAR NULL')
    conn.commit()
    print('✓ full_name column added to users table')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('✓ full_name column already exists')
    else:
        raise

# Verify the column exists
cursor.execute('PRAGMA table_info(users)')
columns = [row[1] for row in cursor.fetchall()]
print(f'Users table columns: {columns}')

if 'full_name' in columns:
    print('✓ Verification: full_name column exists')
else:
    print('✗ Verification: full_name column missing')

conn.close()

import sqlite3

"""
Script to initialize a database from schema.sql.
"""

with open('schema.sql', 'r') as f:
    conn = sqlite3.connect('test.db')
    cur = conn.cursor()
    cur.executescript(f.read())
    conn.commit()
    conn.close()
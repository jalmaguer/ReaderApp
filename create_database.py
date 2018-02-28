import sqlite3

"""
Script to initialize a database from schema.sql.
"""


def create_data_base(db):
    with open('schema.sql', 'r') as f:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.executescript(f.read())
        conn.commit()
        conn.close()

if __name__ == '__main__':
    create_data_base('test.db')

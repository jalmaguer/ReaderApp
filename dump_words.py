import sqlite3
import csv

"""
Script to dump words from known_words table to .csv
"""

conn = sqlite3.connect('reader_app.db')
cur = conn.cursor()
cur.execute('SELECT word FROM known_words')

with open('data/known_words.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    rows = cur.fetchall()
    writer.writerows(rows)
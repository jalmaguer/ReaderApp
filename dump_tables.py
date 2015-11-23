import sqlite3
import csv

"""
Script to dumb database tables to csv files for database migrations.
"""

def table_to_csv(table_name, column_names):
    raw_sql = 'SELECT {column_string} FROM {table_name}'
    column_string = ', '.join(column_names)
    sql = raw_sql.format(table_name=table_name, 
                         column_string=column_string)
    filename = 'data/{}.csv'.format(table_name)
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        writer.writerows(rows)

tables = {'texts': ('id', 'collection_id', 'title', 'text'),
          'known_words': ('word',),
          'learning_words': ('word',),
          'text_word_counts': ('text_id', 'word', 'word_count'),
          'total_word_counts': ('word', 'word_count'),
          'collections': ('id', 'name')}

conn = sqlite3.connect('reader_app.db')

for table, column_names in tables.items():
    table_to_csv(table, column_names)

conn.close()
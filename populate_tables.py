import sqlite3
import csv

"""
Script to populate a newly created database from csv files
"""

def csv_to_table(table_name, column_names):
    raw_sql = """INSERT INTO {table_name} ({column_string})
                 VALUES ({question_mark_string})"""
    column_string = ', '.join(column_names)
    question_mark_string = ', '.join(len(column_names)*['?'])
    sql = raw_sql.format(table_name=table_name, 
                         column_string=column_string, 
                         question_mark_string=question_mark_string)
    filename = 'data/{}.csv'.format(table_name)
    with open(filename, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        cur = conn.cursor()
        for row in reader:
            cur.execute(sql, row)

tables = {'texts': ('id', 'collection_id', 'title', 'text'),
          'known_words': ('word',),
          'learning_words': ('word',),
          'text_word_counts': ('text_id', 'word', 'word_count'),
          'total_word_counts': ('word', 'word_count'),
          'collections': ('id', 'name')}

conn = sqlite3.connect('test.db')

for table, column_names in tables.items():
    csv_to_table(table, column_names)

conn.commit()
conn.close()
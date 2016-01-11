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

tables = {'texts': ('id', 'user_id', 'language_id', 'collection_id', 'title', 'text'),
          'known_words': ('user_id', 'language_id', 'word'),
          'learning_words': ('user_id', 'language_id', 'word'),
          'text_word_counts': ('user_id', 'language_id', 'text_id', 'word', 'word_count'),
          'total_word_counts': ('user_id', 'language_id', 'word', 'word_count'),
          'collections': ('id', 'user_id', 'language_id', 'name'),
          'languages': ('id', 'language'),
          'users': ('id', 'username', 'password')}

conn = sqlite3.connect('test.db')

for table, column_names in tables.items():
    csv_to_table(table, column_names)

conn.commit()
conn.close()
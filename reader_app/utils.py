from reader_app.db import get_db


def build_known_words_set(user_id, language_id):
    db = get_db()
    known_words = db.execute('SELECT word'
                             ' FROM known_word'
                             ' WHERE user_id=?'
                             ' AND language_id=?', (user_id, language_id)).fetchall()
    known_words_set = set(row[0] for row in known_words)
    return known_words_set


def build_text_word_counts_dict(text_id):
    db = get_db()
    query_result = db.execute('SELECT word, word_count'
                              ' FROM text_word_count'
                              ' WHERE text_id=?', (text_id,)).fetchall()
    word_counts = {row['word']: row['word_count'] for row in query_result}
    return word_counts


def build_stats_dict(word_counts, known_words):
    stats_dict = {}
    stats_dict['word_count'] = sum(count for count in word_counts.values())
    stats_dict['known_word_count'] = sum(count for word, count in word_counts.items() if word in known_words)
    stats_dict['unknown_word_count'] = sum(count for word, count in word_counts.items() if word not in known_words)
    stats_dict['percent_known'] = 100*stats_dict['known_word_count']/stats_dict['word_count']
    return stats_dict

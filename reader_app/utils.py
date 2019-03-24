from reader_app.db import get_db


def build_known_words_set(user_id, language_id):
    db = get_db()
    known_words = db.execute('SELECT word'
                             ' FROM known_word'
                             ' WHERE user_id=?'
                             ' AND language_id=?', (user_id, language_id)).fetchall()
    return known_words

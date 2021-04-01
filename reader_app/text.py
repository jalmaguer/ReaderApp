import re

from flask import Blueprint, redirect, render_template, request, url_for, g
from werkzeug.exceptions import abort

from reader_app.auth import login_required
from reader_app.db import get_db
from reader_app.utils import build_known_words_set, build_stats_dict, build_text_word_counts_dict


bp = Blueprint('text', __name__, url_prefix='/text')


def get_text(text_id):
    text = get_db().execute('SELECT id, title, body, language_id, collection_id FROM text WHERE id=?',
                            (text_id,)).fetchone()

    if text is None:
        abort(404, "Text id {} doesn't exist".format(text_id))

    return text


@bp.route('/<int:text_id>')
@login_required
def show_text(text_id):
    text = get_text(text_id)
    known_words = build_known_words_set(g.user['id'], text['language_id'])
    word_counts = build_text_word_counts_dict(text_id)
    token_tuple_lines = tokenize_text(text['body'], known_words)
    stats_dict = build_stats_dict(word_counts, known_words)
    return render_template('text.html',
                           text_id=text['id'],
                           title=text['title'],
                           language_id=text['language_id'],
                           token_tuple_lines=token_tuple_lines,
                           stats_dict=stats_dict)


@bp.route('/<int:text_id>/delete', methods=('POST',))
@login_required
def delete_text(text_id):
    #TODO: only allow users to delete their own texts
    text = get_text(text_id)
    db = get_db()
    db.execute('DELETE FROM text WHERE id=?', (text_id,))
    db.execute('DELETE FROM text_word_count WHERE text_id = ?', (text_id,))
    db.commit()
    return redirect(url_for('collection.show_collection', collection_id=text['collection_id']))


@bp.route('/update_word', methods=('POST',))
@login_required
def update_word():
    postObject = request.json
    print(postObject)
    word = postObject['word'].lower()
    db = get_db()

    removeFrom = postObject['removeFrom']
    addTo = postObject['addTo']
    language_id = postObject['languageID']

    if removeFrom == 'known':
        db.execute('DELETE FROM known_word'
                   ' WHERE user_id=?'
                   ' AND language_id=?'
                   ' AND word=?', (g.user['id'], language_id, word))

    if addTo == 'known':
        db.execute('INSERT INTO known_word (user_id, language_id, word) VALUES (?, ?, ?)', (g.user['id'], language_id, word))

    db.commit()
    return 'post successful'


def tokenize_text(text_body, known_words):
    lines = text_body.split('\n')
    token_tuple_lines = []
    for line in lines:
        tokens = re.findall('\w+|\W+', line)
        token_tuples = []
        for token in tokens:
            if token.lower() in known_words:
                token_tuples.append((token, 'known'))
            elif token.isalpha():
                token_tuples.append((token, 'unknown'))
            else:
                token_tuples.append((token, 'nonword'))
        token_tuple_lines.append(token_tuples)
    return token_tuple_lines

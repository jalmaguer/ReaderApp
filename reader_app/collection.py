from flask import Blueprint, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from reader_app.auth import login_required
from reader_app.db import get_db


bp = Blueprint('collection', __name__, url_prefix='/collection')


@bp.route('/<int:collection_id>')
@login_required
def show_collection(collection_id):
    """Show a list of text titles in the collection with links to full text."""
    db = get_db()
    texts = db.execute('SELECT id, title'
                       ' FROM text' 
                       ' WHERE collection_id=?', (collection_id,)).fetchall()
    if len(texts) == 0:
        collection = db.execute('SELECT name FROM collection WHERE id=?', (collection_id,)).fetchone()
        if collection is None:
            abort(404, "Collection id {} doesn't exist".format(collection_id))
    return render_template('collection.html', texts=texts, collection_id=collection_id)


@bp.route('<int:collection_id>/delete', methods=('POST',))
@login_required
def delete_collection(collection_id):
    #TODO: Only allow users to delete their own collections
    db = get_db()
    texts_in_collection = db.execute('SELECT COUNT(*) FROM text WHERE collection_id=?', [collection_id]).fetchone()[0]
    if texts_in_collection == 0:
        language_id = db.execute('SELECT language_id FROM collection WHERE id=?', (collection_id,)).fetchone()[0]
        db.execute('DELETE FROM collection WHERE id=?', (collection_id,))
        db.commit()
        return redirect(url_for('language.show_language', language_id=language_id))
    else:
        print('Cannot delete collection that is not empty')
        return redirect(url_for('collection.show_collection', collection_id=collection_id))


@bp.route('/<int:collection_id>/upload_text', methods=('POST',))
@login_required
def upload_text(collection_id):
    title = request.form['title']
    body = request.form['body']
    db = get_db()
    language_id = db.execute('SELECT language_id'
                             ' FROM collection'
                             ' WHERE id=?', (collection_id,)).fetchone()[0]
    db.execute('INSERT INTO text (user_id, language_id, collection_id, title, body)'
               ' VALUES (?, ?, ?, ?, ?)',
               (g.user['id'], language_id, collection_id, title, body))
    db.commit()
    return redirect(url_for('collection.show_collection', collection_id=collection_id))

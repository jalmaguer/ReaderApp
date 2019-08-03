from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from reader_app.auth import login_required
from reader_app.db import get_db


bp = Blueprint('language', __name__, url_prefix='/language')


@bp.route('/add_language', methods=('POST',))
@login_required
def add_language():
    """Create a new language for the current user."""
    name = request.form['language']
    error = None

    if not name:
        error = 'Language name is required.'

    if error is not None:
        flash(error)
    else:
        db = get_db()
        db.execute('INSERT INTO language (name, user_id)'
                   ' VALUES (?, ?)',
                   (name, g.user['id']))
        db.commit()
        return redirect(url_for('index'))


@bp.route('/<int:language_id>')
@login_required
def show_language(language_id):
    """Show a list of collections of texts for a particular language"""
    db = get_db()
    collections = db.execute('SELECT id, name'
                             ' FROM collection'
                             ' WHERE user_id=?'
                             ' AND language_id=?',
                             (g.user['id'], language_id)).fetchall()
    return render_template('language.html', collections=collections, language_id=language_id)


@bp.route('<int:language_id>/delete', methods=('POST',))
@login_required
def delete_language(language_id):
    #TODO: Only allow users to delete their own languages
    db = get_db()
    collections_in_language = db.execute('SELECT COUNT(*) FROM collection WHERE language_id=?', (language_id,)).fetchone()[0]
    if collections_in_language == 0:
        db.execute('DELETE FROM language WHERE id=?', (language_id,))
        db.commit()
        return redirect(url_for('index'))
    else:
        print('Cannot delete language that is not empty')
        return redirect(url_for('language.show_language', language_id=language_id))


@bp.route('/<int:language_id>/add_collection', methods=('POST',))
@login_required
def add_collection(language_id):
    """Add new collection to language."""
    name = request.form['name']
    error = None

    if not name:
        error = 'Collection name is required.'

    if error is not None:
        flash(error)
    else:
        db = get_db()
        db.execute('INSERT INTO collection (user_id, language_id, name)'
                   ' VALUES (?, ?, ?)',
                   (g.user['id'], language_id, name))
        db.commit()
        return redirect(url_for('language.show_language', language_id=language_id))

    return redirect(url_for('language.show_language', language_id=language_id))


@bp.route('/<int:language_id>/known_words')
@login_required
def show_known_words(language_id):
    db = get_db()
    known_words = db.execute('SELECT word'
                             ' FROM known_word'
                             ' WHERE user_id=?'
                             ' AND language_id=?',
                             (g.user['id'], language_id)).fetchall()
    print(known_words)
    return render_template('known_words.html', known_words=known_words)

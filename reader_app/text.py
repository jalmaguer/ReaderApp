from flask import Blueprint, redirect, render_template, url_for
from werkzeug.exceptions import abort

from reader_app.auth import login_required
from reader_app.db import get_db


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
    return render_template('text.html', text=text)


@bp.route('/<int:text_id>/delete', methods=('POST',))
@login_required
def delete_text(text_id):
    #TODO: only allow users to delete their own texts
    text = get_text(text_id)
    db = get_db()
    db.execute('DELETE FROM text WHERE id=?', (text_id,))
    db.commit()
    return redirect(url_for('collection.show_collection', collection_id=text['collection_id']))

import sqlite3
from flask import Flask, render_template, request, g, url_for, redirect, jsonify
from flask.ext.login import UserMixin, login_required, login_user, logout_user, LoginManager
from config import MS_TRANSLATOR_CLIENT_ID, MS_TRANSLATOR_CLIENT_SECRET, USERS
import re
from collections import defaultdict
import requests

#create our application
app = Flask(__name__)
app.config.from_object('config')

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    if username not in USERS:
        return

    user = User()
    user.id = username
    return user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))

def connect_to_db():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    g.db = connect_to_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    if request.form['pw'] == USERS[username]['pw']:
        user = User()
        user.id = username
        login_user(user)
        return redirect(url_for('index'))

    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """
    Show a list of the collections of texts
    """
    cur = g.db.execute('SELECT id, name FROM collections')
    collections = [dict(collection_id=row[0], name=row[1]) for row in cur.fetchall()]
    return render_template('index.html', collections=collections)

@app.route('/collections/<int:collection_id>')
@login_required
def show_collection(collection_id):
    """
    Show a list of text titles in the collection with links to full text.
    """
    cur = g.db.execute('SELECT id, title FROM texts WHERE collection_id=?', [collection_id])
    texts = [dict(text_id=row[0], title=row[1]) for row in cur.fetchall()]
    return render_template('collection.html', texts=texts, collection_id=collection_id)

@app.route('/collections/<int:collection_id>/stats')
@login_required
def show_collection_stats(collection_id):
    """
    Show the top 100 unknown words, words overall, and learning words in all texts
    in a collection along with the word counts.
    """
    cur = g.db.execute("""SELECT word, SUM(word_count) FROM text_word_counts
                          WHERE text_id IN (SELECT id FROM texts WHERE collection_id=?)
                          GROUP BY word
                          ORDER BY SUM(word_count) DESC, word ASC
                          LIMIT 100""", [collection_id])
    top_overall_words = [(row[0], row[1]) for row in cur.fetchall()]
    cur = g.db.execute("""SELECT word, SUM(word_count) FROM text_word_counts
                          WHERE text_id IN (SELECT id FROM texts WHERE collection_id=?)
                          AND word NOT IN (SELECT word FROM known_words)
                          AND word NOT IN (SELECT word FROM learning_words)
                          GROUP BY word
                          ORDER BY SUM(word_count) DESC, word ASC
                          LIMIT 100""", [collection_id])
    top_unknown_words = [(row[0], row[1]) for row in cur.fetchall()]
    cur = g.db.execute("""SELECT word, SUM(word_count) FROM text_word_counts
                          WHERE text_id IN (SELECT id FROM texts WHERE collection_id=?)
                          AND word IN (SELECT word FROM learning_words)
                          GROUP BY word
                          ORDER BY SUM(word_count) DESC, word ASC
                          LIMIT 100""", [collection_id])
    top_learning_words = [(row[0], row[1]) for row in cur.fetchall()]
    word_counts = build_collection_word_counts_dict(collection_id)
    known_words = build_known_words_set()
    stats_dict = build_stats_dict(word_counts, known_words)
    return render_template('stats.html', top_overall_words=top_overall_words,
                                         top_unknown_words=top_unknown_words,
                                         top_learning_words=top_learning_words,
                                         stats_dict=stats_dict)

@app.route('/stats')
@login_required
def show_stats():
    """
    Show the top 100 unknown words, words overall, and learning words in all texts
    along with the counts.
    """
    cur = g.db.execute("""SELECT word, word_count FROM total_word_counts
                          ORDER BY word_count DESC, word ASC
                          LIMIT 100""")
    top_overall_words = [(row[0], row[1]) for row in cur.fetchall()]
    cur = g.db.execute("""SELECT word, word_count FROM total_word_counts
                          WHERE word NOT IN (SELECT word FROM known_words)
                          AND word NOT IN (SELECT word FROM learning_words)
                          ORDER BY word_count DESC, word ASC
                          LIMIT 100""")
    top_unknown_words = [(row[0], row[1]) for row in cur.fetchall()]
    cur = g.db.execute("""SELECT word, word_count FROM total_word_counts
                          WHERE word IN (SELECT word FROM learning_words)
                          ORDER BY word_count DESC, word ASC
                          LIMIT 100""")
    top_learning_words = [(row[0], row[1]) for row in cur.fetchall()]
    cur = g.db.execute('SELECT word, word_count FROM total_word_counts')
    word_counts = {row[0]: row[1] for row in cur.fetchall()}
    known_words = build_known_words_set()
    stats_dict = build_stats_dict(word_counts, known_words)
    return render_template('stats.html', top_overall_words=top_overall_words,
                                         top_unknown_words=top_unknown_words,
                                         top_learning_words=top_learning_words,
                                         stats_dict=stats_dict)

@app.route('/known_words')
@login_required
def show_known_words():
    """
    Show a list of all the known words.
    """
    cur = g.db.execute('SELECT word FROM known_words')
    words = [row[0] for row in cur.fetchall()]
    return render_template('known_words.html', words=words)

@app.route('/learning_words')
@login_required
def show_learning_words():
    """
    Show a list of all the words being learned.
    """
    cur = g.db.execute('SELECT word FROM learning_words')
    words = [row[0] for row in cur.fetchall()]
    return render_template('learning_words.html', words=words)

@app.route('/collections/<int:collection_id>/upload_text', methods=['POST'])
@login_required
def upload_text(collection_id):
    """
    Upload text to texts table, upload word counts from text to text_word_counts tables,
    and update the total_word_counts table. 
    """
    if request.method == 'POST':
        title = request.form['title']
        text = request.form['text']
        cur = g.db.execute('INSERT INTO texts (title, collection_id, text) VALUES (?, ?, ?)', [title, collection_id, text])
        text_id = cur.lastrowid
        tokens = re.split('(\w*)', text)
        words = [token.lower() for token in tokens if token.isalpha()]
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1
        word_count_tuples = [(text_id, key, value) for key, value in word_counts.items()]
        g.db.executemany('INSERT INTO text_word_counts VALUES (?, ?, ?)', word_count_tuples)
        update_total_word_counts()
        g.db.commit()
    return redirect(url_for('show_collection', collection_id=collection_id))

@app.route('/create_collection', methods=['POST'])
@login_required
def create_collection():
    """
    Create a new collection
    """
    if request.method == 'POST':
        name = request.form['name']
        cur = g.db.execute('INSERT INTO collections (name) VALUES (?)', [name])
        g.db.commit()
    return redirect(url_for('index'))

@app.route('/texts/<int:text_id>')
@login_required
def show_text(text_id):
    """
    Retrieve text from database, create a set of known words, create a dictionary of word_counts in the
    text by querying the text_word_counts table, create a list of words and counts for all the unknown 
    words that appear more than once in the text, and create a dictionary of statistics about the text.
    """
    cur = g.db.execute('SELECT title, text FROM texts WHERE id=?', [text_id])
    row = cur.fetchone()
    title = row[0]
    text = row[1]
    known_words = build_known_words_set()
    learning_words = build_learning_words_set()
    known_or_learning_words = known_words.union(learning_words)
    token_tuple_lines = tokenize_text(text, known_words, learning_words)
    word_counts = build_text_word_counts_dict(text_id)
    top_unknown_words = [(count, word) for word, count in word_counts.items() if count > 1 and word not in known_or_learning_words]
    top_unknown_words.sort(reverse=True)
    top_learning_words = [(count, word) for word, count in word_counts.items() if count > 1 and word in learning_words]
    top_learning_words.sort(reverse=True)
    stats_dict = build_stats_dict(word_counts, known_words)
    return render_template('text.html', 
                            text_id=text_id,
                            title=title,
                            token_tuple_lines=token_tuple_lines,
                            top_unknown_words=top_unknown_words,
                            top_learning_words=top_learning_words,
                            stats_dict=stats_dict)

@app.route('/delete_text/<int:text_id>', methods=['POST'])
@login_required
def delete_text(text_id):
    """
    Delete text from texts table as well as all the word counts associated with it in the text_word_counts
    table, and update the total_word_counts table.
    """
    g.db.execute('DELETE FROM texts WHERE id = ?', [text_id])
    g.db.execute('DELETE FROM text_word_counts WHERE text_id = ?', [text_id])
    update_total_word_counts()
    g.db.commit()
    return redirect(url_for('index'))

@app.route('/delete_collection/<int:collection_id>', methods=['POST'])
@login_required
def delete_collection(collection_id):
    """
    Delete collection from collections table.  Will only allow a collection to be deleted if it is empty.
    """
    cur = g.db.execute('SELECT COUNT(*) FROM texts WHERE collection_id=?', [collection_id])
    texts_in_collection = cur.fetchone()[0]
    if texts_in_collection == 0:
        g.db.execute('DELETE FROM collections WHERE id=?', [collection_id])
        g.db.commit()
        return redirect(url_for('index'))
    else:
        print('Can not delete collection that is not empty')
        return redirect(url_for('show_collection', collection_id=collection_id))

@app.route('/update_word', methods=['POST'])
@login_required
def update_word():
    """
    Updates word in database when postObject is passed from client.  The postObject is a javascript object
    that contains fields for the word, the table to remove the word from, and the table to add the word to.
    Nothing happens when one of these fields is 'unknown' because there is no unknown words table.
    """
    postObject = request.json
    word = postObject['word']
    removeFrom = postObject['removeFrom']
    addTo = postObject['addTo']

    if removeFrom == 'known':
        g.db.execute('DELETE FROM known_words WHERE word = ?', [word])
    elif removeFrom == 'learning':
        g.db.execute('DELETE FROM learning_words WHERE word = ?', [word])

    if addTo == 'known':
        g.db.execute('INSERT INTO known_words (word) VALUES (?)', [word])
    elif addTo == 'learning':
        g.db.execute('INSERT INTO learning_words (word) VALUES (?)', [word])

    g.db.commit()
    return 'post succesful'

@app.route('/translate', methods=['POST'])
@login_required
def translate():
    return jsonify({'text': microsoft_translate(request.form['text'])})

def tokenize_text(text, known_words, learning_words):
    """
    Breaks up text into a list of lines where each lines is a list of tuples containing a token
    and whether it is known, unknown, or a non-word.  Takes a text as a string and a set of
    known known words as input.
    """
    lines = text.split('\n')
    token_tuple_lines = []
    for line in lines:
        tokens = re.split('(\w*)', line)
        token_tuples = []
        for token in tokens:
            if token.lower() in known_words:
                token_tuples.append((token, 'known'))
            elif token.lower() in learning_words:
                token_tuples.append((token, 'learning'))
            elif token.isalpha():
                token_tuples.append((token, 'unknown'))
            else:
                token_tuples.append((token, 'nonword'))
        token_tuple_lines.append(token_tuples)
    return token_tuple_lines

def build_stats_dict(word_counts, known_words):
    """
    Calculates a dictionary of statistics for a text or collection.  Shows the number of words in a text, the number of known words,
    the number of unknown words, and the percent of words that are known.
    """
    stats_dict = {}
    stats_dict['word_count'] = sum(count for count in word_counts.values())
    stats_dict['known_word_count'] = sum(count for word, count in word_counts.items() if word in known_words)
    stats_dict['unknown_word_count'] = sum(count for word, count in word_counts.items() if word not in known_words)
    stats_dict['percent_known'] = 100*stats_dict['known_word_count']/stats_dict['word_count']
    return stats_dict

def update_total_word_counts():
    """
    Runs the proper SQL statements to update the total_word_counts table.
    """
    g.db.execute('DELETE FROM total_word_counts')
    g.db.execute("""INSERT INTO total_word_counts
                    SELECT word, SUM(word_count)
                    FROM text_word_counts
                    GROUP BY word""")
    g.db.commit()

def build_known_words_set():
    """
    Builds a set composed of all the words in the known_words table.
    """
    cur = g.db.execute('SELECT word FROM known_words')
    known_words = set(row[0] for row in cur.fetchall())
    return known_words

def build_learning_words_set():
    """
    Builds a set composed of all the words in the learning_words table.
    """
    cur = g.db.execute('SELECT word FROM learning_words')
    learning_words = set(row[0] for row in cur.fetchall())
    return learning_words

def build_text_word_counts_dict(text_id):
    """
    Builds a dictionary of word counts in a particular text.
    """
    cur = g.db.execute('SELECT word, word_count FROM text_word_counts WHERE text_id = ?', [text_id])
    word_counts = {row[0]: row[1] for row in cur.fetchall()}
    return word_counts

def build_collection_word_counts_dict(collection_id):
    """
    Build a dictionary of word counts in a collection
    """
    cur = g.db.execute("""SELECT word, SUM(word_count)
                          FROM text_word_counts
                          WHERE text_id IN (SELECT id FROM texts WHERE collection_id=?)
                          GROUP BY word""", [collection_id])
    word_counts = {row[0]: row[1] for row in cur.fetchall()}
    return word_counts

def microsoft_translate(text):
    # get access token
    params = {
        'client_id': MS_TRANSLATOR_CLIENT_ID,
        'client_secret': MS_TRANSLATOR_CLIENT_SECRET,
        'scope': 'http://api.microsofttranslator.com',
        'grant_type': 'client_credentials'}
    url = 'https://datamarket.accesscontrol.windows.net/v2/OAuth2-13'
    r = requests.post(url, data=params)
    token = r.json()['access_token']

    # translate
    params = {'appId': 'Bearer ' + token,
              'from': 'de',
              'to': 'en',
              'text': text}
    url = 'http://api.microsofttranslator.com/V2/Ajax.svc/Translate'
    r = requests.get(url, params=params)
    r.encoding = 'utf-8-sig'
    translation = r.text[1:-1]
    return translation

if __name__ == '__main__':
    app.run()
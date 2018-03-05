import sqlite3
from flask import Flask, render_template, request, g, url_for, redirect, jsonify
from flask_login import UserMixin, login_required, login_user, logout_user, LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from config import MS_TRANSLATOR_CLIENT_ID, MS_TRANSLATOR_CLIENT_SECRET
import re
from collections import defaultdict
import requests
from newspaper import Article

#create our application
app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class Text(db.Model):
    __tablename__ = 'texts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    language_id = db.Column(db.Integer, nullable=False)
    collection_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String, nullable=False)
    text = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<Text %r>' % self.title

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

class KnownWord(db.Model):
    __tablename__ = 'known_words'

    user_id = db.Column(db.Integer, primary_key=True, nullable=False)
    language_id = db.Column(db.Integer, primary_key=True, nullable=False)
    word = db.Column(db.String, primary_key=True, nullable=False)

    def __repr__(self):
        return '<KnownWord %r>' % self.word

class LearningWord(db.Model):
    __tablename__ = 'learning_words'

    user_id = db.Column(db.Integer, primary_key=True, nullable=False)
    language_id = db.Column(db.Integer, primary_key=True, nullable=False)
    word = db.Column(db.String, primary_key=True, nullable=False)

    def __repr__(self):
        return '<LearningWord %r>' % self.word

class ProperNoun(db.Model):
    __tablename__ = 'proper_nouns'

    user_id = db.Column(db.Integer, primary_key=True, nullable=False)
    collection_id = db.Column(db.Integer, primary_key=True, nullable=False)
    word = db.Column(db.String, primary_key=True, nullable=False)

    def __repr__(self):
        return '<ProperNoun %r>' % self.word

class TextWordCount(db.Model):
    __tablename__ = 'text_word_counts'

    user_id = db.Column(db.Integer, primary_key=True, nullable=False)
    language_id = db.Column(db.Integer, primary_key=True, nullable=False)
    text_id = db.Column(db.Integer, primary_key=True, nullable=False)
    word = db.Column(db.String, primary_key=True, nullable=False)
    word_count = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<TextWordCount %r>' % self.word

class TotalWordCount(db.Model):
    __tablename__ = 'total_word_counts'

    user_id = db.Column(db.Integer, primary_key=True, nullable=False)
    language_id = db.Column(db.Integer, primary_key=True, nullable=False)
    word = db.Column(db.String, primary_key=True, nullable=False)
    word_count = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<TotalWordCount %r>' % self.word

class Language(db.Model):
    __tablename__ = 'languages'

    id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<Language %r>' % self.language

class Collection(db.Model):
    __tablename__ = 'collections'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    language_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<Collection %r>' % self.name

@login_manager.user_loader
def user_loader(user_id):
    cur = g.db.execute('SELECT id, username FROM users WHERE id=?', [user_id])
    row = cur.fetchone()
    username = row[1]
    user = User()
    user.id = user_id
    user.username = username
    return user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))

def connect_to_db():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    g.db = connect_to_db()
    g.user = current_user

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
    cur = g.db.execute('SELECT id, username, password FROM users WHERE username=?', [username])
    row = cur.fetchone()
    user_id = row[0]
    password = row[2]
    if row is None:
        return redirect(url_for('login'))
    if request.form['pw'] == password:
        user = User()
        user.id = user_id
        user.username = username
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
    Show a list of languages that collections can be created for.
    """
    languages = Language.query.all()
    return render_template('languages.html', languages=languages)

@app.route('/languages/<int:language_id>')
@login_required
def show_language_collections(language_id):
    """
    Show a list of the collections of the text for a particular language.
    """
    collections = Collection.query.filter_by(user_id=g.user.id, language_id=language_id).all()
    return render_template('index.html', collections=collections, language_id=language_id)

@app.route('/collections/<int:collection_id>')
@login_required
def show_collection(collection_id):
    """
    Show a list of text titles in the collection with links to full text.
    """
    texts = Text.query.filter_by(collection_id=collection_id).all()
    return render_template('collection.html', texts=texts, collection_id=collection_id)

@app.route('/collections/<int:collection_id>/stats')
@login_required
def show_collection_stats(collection_id):
    """
    Show the top 100 unknown words, words overall, and learning words in all texts
    in a collection along with the word counts.
    """
    collection_text_ids = db.session.query(Text.id).filter_by(collection_id=collection_id)
    known_words = db.session.query(KnownWord.word)
    learning_words = db.session.query(LearningWord.word)
    proper_nouns = db.session.query(ProperNoun.word).filter_by(collection_id=collection_id)
    top_overall_words = (db.session
                           .query(TextWordCount.word, func.sum(TextWordCount.word_count))
                           .filter(TextWordCount.text_id.in_(collection_text_ids))
                           .group_by(TextWordCount.word)
                           .order_by(func.sum(TextWordCount.word_count).desc(), TextWordCount.word)
                           .limit(100)
                           .all())
    top_unknown_words = (db.session
                            .query(TextWordCount.word, func.sum(TextWordCount.word_count))
                            .filter(TextWordCount.text_id.in_(collection_text_ids))
                            .filter(~TextWordCount.word.in_(known_words))
                            .filter(~TextWordCount.word.in_(learning_words))
                            .filter(~TextWordCount.word.in_(proper_nouns))
                            .group_by(TextWordCount.word)
                            .order_by(func.sum(TextWordCount.word_count).desc(), TextWordCount.word)
                            .limit(100)
                            .all())
    top_learning_words = (db.session
                            .query(TextWordCount.word, func.sum(TextWordCount.word_count))
                            .filter(TextWordCount.text_id.in_(collection_text_ids))
                            .filter(TextWordCount.word.in_(learning_words))
                            .group_by(TextWordCount.word)
                            .order_by(func.sum(TextWordCount.word_count).desc(), TextWordCount.word)
                            .limit(100)
                            .all())
    language_id = db.session.query(Collection.language_id).filter_by(id=collection_id).scalar()
    word_counts = build_collection_word_counts_dict(collection_id)
    known_words = build_known_words_set(g.user.id, language_id)
    stats_dict = build_stats_dict(word_counts, known_words)
    return render_template('stats.html', top_overall_words=top_overall_words,
                                         top_unknown_words=top_unknown_words,
                                         top_learning_words=top_learning_words,
                                         stats_dict=stats_dict,
                                         language_id=language_id,
                                         collection_id=collection_id)

@app.route('/languages/<int:language_id>/stats')
@login_required
def show_language_stats(language_id):
    """
    Show the top 100 unknown words, words overall, and learning words in all texts
    along with the counts.
    """
    known_words = db.session.query(KnownWord.word)
    learning_words = db.session.query(LearningWord.word)
    top_overall_words = (db.session
                           .query(TotalWordCount.word, TotalWordCount.word_count)
                           .filter_by(user_id=g.user.id, language_id=language_id)
                           .order_by(TotalWordCount.word_count.desc(), TotalWordCount.word)
                           .limit(100)
                           .all())
    top_unknown_words = (db.session
                           .query(TotalWordCount.word, TotalWordCount.word_count)
                           .filter(~TotalWordCount.word.in_(known_words))
                           .filter(~TotalWordCount.word.in_(learning_words))
                           .filter_by(user_id=g.user.id, language_id=language_id)
                           .order_by(TotalWordCount.word_count.desc(), TotalWordCount.word)
                           .limit(100)
                           .all())
    top_learning_words = (db.session
                            .query(TotalWordCount.word, TotalWordCount.word_count)
                            .filter(TotalWordCount.word.in_(learning_words))
                            .filter_by(user_id=g.user.id, language_id=language_id)
                            .order_by(TotalWordCount.word_count.desc(), TotalWordCount.word)
                            .limit(100)
                            .all())
    word_counts = TotalWordCount.query.filter_by(user_id=g.user.id, language_id=language_id)
    word_counts_dict = {row.word: row.word_count for row in word_counts}
    known_words = build_known_words_set(g.user.id, language_id)
    stats_dict = build_stats_dict(word_counts_dict, known_words)
    return render_template('stats.html', top_overall_words=top_overall_words,
                                         top_unknown_words=top_unknown_words,
                                         top_learning_words=top_learning_words,
                                         stats_dict=stats_dict,
                                         language_id=language_id)

@app.route('/known_words/<int:language_id>')
@login_required
def show_known_words(language_id):
    """
    Show a list of all the known words.
    """
    cur = g.db.execute("""SELECT word
                          FROM known_words
                          WHERE user_id=?
                          AND language_id=?""", [g.user.id, language_id])
    words = [row[0] for row in cur.fetchall()]
    return render_template('known_words.html', words=words)

@app.route('/learning_words/<int:language_id>')
@login_required
def show_learning_words(language_id):
    """
    Show a list of all the words being learned.
    """
    cur = g.db.execute("""SELECT word
                          FROM learning_words
                          WHERE user_id=?
                          AND language_id=?""", [g.user.id, language_id])
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
        cur = g.db.execute('SELECT language_id FROM collections WHERE id = ?', [collection_id])
        row = cur.fetchone()
        language_id = row[0]
        cur = g.db.execute("""INSERT INTO texts (user_id, language_id, collection_id, title, text) 
                              VALUES (?, ?, ?, ?, ?)""", [g.user.id, language_id, collection_id, title, text])
        text_id = cur.lastrowid
        tokens = re.split('(\w*)', text)
        words = [token.lower() for token in tokens if token.isalpha()]
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1
        word_count_tuples = [(g.user.id, language_id, text_id, key, value) for key, value in word_counts.items()]
        g.db.executemany("""INSERT INTO text_word_counts (user_id, language_id, text_id, word, word_count)
                            VALUES (?, ?, ?, ?, ?)""", word_count_tuples)
        update_total_word_counts(g.user.id, language_id)
        g.db.commit()
    return redirect(url_for('show_collection', collection_id=collection_id))

@app.route('/add_language', methods=['POST'])
@login_required
def add_language():
    """
    Add new language
    """
    if request.method == 'POST':
        language = request.form['language']
        cur = g.db.execute('INSERT INTO languages (language) VALUES (?)', [language])
        g.db.commit()
    return redirect(url_for('index'))

@app.route('/languages/<int:language_id>/create_collection', methods=['POST'])
@login_required
def create_collection(language_id):
    """
    Create a new collection
    """
    if request.method == 'POST':
        name = request.form['name']
        cur = g.db.execute('INSERT INTO collections (user_id, language_id, name) VALUES (?, ?, ?)', [g.user.id, language_id, name])
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
    #TODO: need to fix this so that users can't go to each others texts by simply inputting the correct URL
    cur = g.db.execute('SELECT title, text, language_id, collection_id FROM texts WHERE id=?', [text_id])
    row = cur.fetchone()
    title = row[0]
    text = row[1]
    language_id = row[2]
    collection_id = row[3]
    known_words = build_known_words_set(g.user.id, language_id)
    learning_words = build_learning_words_set(g.user.id, language_id)
    proper_nouns = build_proper_nouns_set(g.user.id, collection_id)
    word_union_set = known_words.union(learning_words).union(proper_nouns)
    token_tuple_lines = tokenize_text(text, known_words, learning_words, proper_nouns)
    word_counts = build_text_word_counts_dict(text_id)
    top_unknown_words = [(count, word) for word, count in word_counts.items() if count > 1 and word not in word_union_set]
    top_unknown_words.sort(reverse=True)
    top_learning_words = [(count, word) for word, count in word_counts.items() if count > 1 and word in learning_words]
    top_learning_words.sort(reverse=True)
    stats_dict = build_stats_dict(word_counts, known_words.union(proper_nouns))
    return render_template('text.html', 
                            text_id=text_id,
                            title=title,
                            language_id=language_id,
                            collection_id=collection_id,
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
    #TODO: only allow users to delete their own texts
    cur = g.db.execute('SELECT language_id FROM texts WHERE id = ?', [text_id])
    language_id = cur.fetchone()[0]
    g.db.execute('DELETE FROM texts WHERE id = ?', [text_id])
    g.db.execute('DELETE FROM text_word_counts WHERE text_id = ?', [text_id])
    update_total_word_counts(g.user.id, language_id)
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
    language_id = postObject['languageID']
    collection_id = postObject['collectionID']

    if removeFrom == 'known':
        g.db.execute("""DELETE FROM known_words
                        WHERE user_id = ?
                        AND language_id = ?
                        AND word = ?""", [g.user.id, language_id, word])
    elif removeFrom == 'learning':
        g.db.execute("""DELETE FROM learning_words
                        WHERE user_id = ?
                        AND language_id = ?
                        AND word = ?""", [g.user.id, language_id, word])
    elif removeFrom == 'proper':
        g.db.execute("""DELETE FROM proper_nouns
                        WHERE user_id = ?
                        AND collection_id = ?
                        AND word = ?""", [g.user.id, collection_id, word])

    if addTo == 'known':
        g.db.execute('INSERT INTO known_words (user_id, language_id, word) VALUES (?, ?, ?)', [g.user.id, language_id, word])
    elif addTo == 'learning':
        g.db.execute('INSERT INTO learning_words (user_id, language_id, word) VALUES (?, ?, ?)', [g.user.id, language_id, word])
    elif addTo == 'proper':
        g.db.execute('INSERT INTO proper_nouns (user_id, collection_id, word) VALUES (?, ?, ?)', [g.user.id, collection_id, word])

    g.db.commit()
    return 'post succesful'

@app.route('/translate', methods=['POST'])
@login_required
def translate():
    return jsonify({'text': microsoft_translate(request.form['text'], int(request.form['languageID']))})

@app.route('/collections/<int:collection_id>/preview_article', methods=['POST'])
@login_required
def preview_article(collection_id):
    if request.method == 'POST':
        url = request.form['url']
        article = Article(url)
        print('downloading article')
        article.download()
        article.parse()
        return render_template('preview_article.html',
                               collection_id=collection_id,
                               title=article.title,
                               text=article.text)

def tokenize_text(text, known_words, learning_words, proper_nouns):
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
            elif token.lower() in proper_nouns:
                token_tuples.append((token, 'proper'))
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

def update_total_word_counts(user_id, language_id):
    """
    Runs the proper SQL statements to update the total_word_counts table.
    """
    g.db.execute("""DELETE FROM total_word_counts
                    WHERE user_id=?
                    AND language_id=?""", [user_id, language_id])
    g.db.execute("""INSERT INTO total_word_counts
                    SELECT user_id, language_id, word, SUM(word_count)
                    FROM text_word_counts
                    WHERE user_id=?
                    AND language_id=?
                    GROUP BY user_id, language_id, word""", [user_id, language_id])
    g.db.commit()

def build_known_words_set(user_id, language_id):
    """
    Builds a set composed of all the words in the known_words table.
    """
    cur = g.db.execute("""SELECT word
                          FROM known_words
                          WHERE user_id=?
                          AND language_id=?""", [user_id, language_id])
    known_words = set(row[0] for row in cur.fetchall())
    return known_words

def build_learning_words_set(user_id, language_id):
    """
    Builds a set composed of all the words in the learning_words table.
    """
    cur = g.db.execute("""SELECT word 
                          FROM learning_words
                          WHERE user_id=?
                          AND language_id=?""", [user_id, language_id])
    learning_words = set(row[0] for row in cur.fetchall())
    return learning_words

def build_proper_nouns_set(user_id, collection_id):
    """
    Builds a set composer of all the proper nouns in a collection.
    """
    cur = g.db.execute("""SELECT word 
                          FROM proper_nouns
                          WHERE user_id=?
                          AND collection_id=?""", [user_id, collection_id])
    proper_nouns = set(row[0] for row in cur.fetchall())
    return proper_nouns


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

def microsoft_translate(text, language_id):
    language_code_dict = {1: 'de', 2: 'es', 3: 'pt', 4: 'fr'}
    language_code = language_code_dict[language_id]

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
              'from': language_code,
              'to': 'en',
              'text': text}
    url = 'http://api.microsofttranslator.com/V2/Ajax.svc/Translate'
    r = requests.get(url, params=params)
    r.encoding = 'utf-8-sig'
    translation = r.text[1:-1]
    return translation

if __name__ == '__main__':
    app.run()
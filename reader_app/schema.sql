DROP TABLE IF EXISTS text;
DROP TABLE IF EXISTS known_word;
DROP TABLE IF EXISTS learning_word;
DROP TABLE IF EXISTS proper_noun;
DROP TABLE IF EXISTS text_word_count;
DROP TABLE IF EXISTS total_word_count;
DROP TABLE IF EXISTS collection;
DROP TABLE IF EXISTS language;
DROP TABLE IF EXISTS user;

CREATE TABLE text (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    collection_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (language_id) REFERENCES language (id),
    FOREIGN KEY (collection_id) REFERENCES collection (id)
);

CREATE TABLE collection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (language_id) REFERENCES language (id)
);

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE language (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE text_word_count (
    user_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    text_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (language_id) REFERENCES language (id),
    FOREIGN KEY (text_id) REFERENCES text (id)
);

CREATE TABLE total_word_count (
    user_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (language_id) REFERENCES language (id)
);

CREATE TABLE known_word (
    user_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    PRIMARY KEY (user_id, language_id, word),
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (language_id) REFERENCES language (id)
);

CREATE TABLE learning_word (
    user_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    PRIMARY KEY (user_id, language_id, word),
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (language_id) REFERENCES language (id)
);
DROP TABLE IF EXISTS texts;
CREATE TABLE texts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    collection_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL
);

DROP TABLE IF EXISTS known_words;
CREATE TABLE known_words (
    user_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    PRIMARY KEY (user_id, language_id, word)
);

DROP TABLE IF EXISTS learning_words;
CREATE TABLE learning_words (
    user_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    PRIMARY KEY (user_id, language_id, word)
);

DROP TABLE IF EXISTS text_word_counts;
CREATE TABLE text_word_counts (
    user_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    text_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    word_count INTEGER NOT NULL
);

DROP TABLE IF EXISTS total_word_counts;
CREATE TABLE total_word_counts (
    user_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    word_count INTEGER NOT NULL
);

DROP TABLE IF EXISTS collections;
CREATE TABLE collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    name TEXT NOT NULL
);

DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);

DROP TABLE IF EXISTS languages;
CREATE TABLE languages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language TEXT NOT NULL
);
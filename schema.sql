DROP TABLE IF EXISTS texts;
CREATE TABLE texts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL
);

DROP TABLE IF EXISTS known_words;
CREATE TABLE known_words (
    word TEXT PRIMARY KEY NOT NULL
);

DROP TABLE IF EXISTS learning_words;
CREATE TABLE learning_words (
    word TEXT PRIMARY KEY NOT NULL
);

DROP TABLE IF EXISTS text_word_counts;
CREATE TABLE text_word_counts (
    text_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    word_count INTEGER NOT NULL
);

DROP TABLE IF EXISTS total_word_counts;
CREATE TABLE total_word_counts (
    word TEXT NOT NULL,
    word_count INTEGER NOT NULL
);

DROP TABLE IF EXISTS collections;
CREATE TABLE collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
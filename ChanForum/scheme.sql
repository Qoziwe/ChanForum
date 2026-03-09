/* Database Schema for ChanForum (Used by database_sqlite.py) */

/* USERS DATABASE */
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    profile_image TEXT DEFAULT NULL,
    uniq_id TEXT NOT NULL UNIQUE
);

CREATE TABLE user_friends (
    user_id TEXT NOT NULL,
    friend_id TEXT NOT NULL,
    PRIMARY KEY (user_id, friend_id),
    FOREIGN KEY (user_id) REFERENCES users(uniq_id),
    FOREIGN KEY (friend_id) REFERENCES users(uniq_id)
);

/* POSTS DATABASE */
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    description TEXT,
    post_image TEXT DEFAULT NULL,
    like_count INTEGER DEFAULT 0,
    author TEXT NOT NULL,
    user_uniq_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE post_likes (
    user_id INTEGER,
    post_id INTEGER,
    valuelike INTEGER,
    PRIMARY KEY (user_id, post_id)
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    comment_content TEXT NOT NULL,
    author TEXT NOT NULL,
    user_id TEXT NOT NULL
);
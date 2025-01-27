CREATE TABLE post_likes (
    user_id INTEGER,
    post_id INTEGER,
    valuelike INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (post_id) REFERENCES posts(id),
    PRIMARY KEY (user_id, post_id)
);


/*
CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    comment_content TEXT NOT NULL,
    author TEXT NOT NULL,
    user_id TEXT NOT NULL
);

CREATE TABLE post_likes (
    user_id INTEGER,
    post_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (post_id) REFERENCES posts(id),
    PRIMARY KEY (user_id, post_id)
);



CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    description TEXT NOT NULL,
    post_image BLOB DEFAULT NULL,
    like_count INTEGER DEFAULT 0,
    
    author TEXT NOT NULL,
    user_uniq_id INTEGER
);

ALTER TABLE posts ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE posts ADD COLUMN last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

OR POST
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    post_image BLOB DEFAULT NULL,
    user_uniq_id INTEGER
);

ALTER TABLE posts ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

FOR USERS
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    password INTEGER NOT NULL,
    uniq_id INT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    password INTEGER NOT NULL,
    profile_image BLOB DEFAULT NULL,
    uniq_id INT NOT NULL
);


*/
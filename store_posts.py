# putting the posts in DB script

import sqlite3

def create_db(db_name="reddit_posts.db"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            title TEXT,
            selftext TEXT,
            author TEXT,
            created_utc INTEGER,
            upvotes INTEGER,
            tickers TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_post(post, tickers, db_name="reddit_posts.db"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO posts (id, title, selftext, author, created_utc, upvotes, tickers)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        post.id,
        post.title,
        getattr(post, 'selftext', ''),
        str(post.author),
        int(post.created_utc),
        int(post.score),
        ",".join(tickers)
    ))
    rows_affected = c.rowcount
    conn.commit()
    conn.close()
    return rows_affected

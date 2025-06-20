import praw
from dotenv import load_dotenv
import os
import re
import csv
from store_posts import create_db, insert_post

# Load environment variables from .env file
load_dotenv()

# PRAW setup
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD")
)

def load_tickers_and_names_from_csv(csv_filename):
    """Loads tickers and a name-to-ticker map from the CSV."""
    tickers = set()
    name_map = {}
    with open(csv_filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Get ticker
            symbol = row.get('Symbol') or row.get('ACT Symbol')
            if symbol and symbol.isalpha():
                tickers.add(symbol)
                
                # Get company name
                name = row.get('Security Name')
                # Clean up the name for better matching (e.g., "Apple Inc." -> "Apple")
                if name:
                    # A simple cleaning, can be improved later
                    clean_name = name.split(' ')[0].replace('.', '').replace(',', '')
                    name_map[clean_name.lower()] = symbol # Store in lowercase for case-insensitive matching

    print(f"Loaded {len(tickers)} tickers and {len(name_map)} company names.")
    return tickers, name_map

def extract_tickers(text, valid_tickers, name_map):
    """Extracts tickers based on symbols AND company names."""
    found_tickers = set()
    
    # 1. Find explicit tickers (e.g., $TSLA, AAPL)
    # Using a more robust regex for tickers
    for match in re.findall(r'\b[A-Z]{1,5}\b', text):
        if match in valid_tickers:
            found_tickers.add(match)
            
    # 2. Find company names from our map
    # We iterate through the text word by word for simplicity
    for word in text.lower().split():
        if word in name_map:
            found_tickers.add(name_map[word])
            
    return found_tickers

def run_scraper(subreddits, limit_per_subreddit=100):
    """
    Scrapes specified subreddits for new posts, extracts tickers, and saves them to the database.
    """
    print("--- Starting Reddit Scraper ---")
    # PRAW setup (it's better to initialize it inside the function if you run this as a long-term job)
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT"),
        username=os.getenv("REDDIT_USERNAME"),
        password=os.getenv("REDDIT_PASSWORD")
    )

    valid_tickers, name_to_ticker_map = load_tickers_and_names_from_csv('nasdaq-listed-symbols.csv')
    create_db()  # Ensure DB and table exist

    new_posts_found = 0
    for subreddit_name in subreddits:
        print(f"Scraping r/{subreddit_name}...")
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.new(limit=limit_per_subreddit):
            full_text = f"{post.title} {getattr(post, 'selftext', '')}"
            tickers = extract_tickers(full_text, valid_tickers, name_to_ticker_map)
            
            if tickers:
                # The insert_post function returns the number of rows inserted (1 if new, 0 if ignored)
                rows_inserted = insert_post(post, tickers)
                if rows_inserted > 0:
                    new_posts_found += 1
                    print(f"  -> Saved new post: {post.title} | Tickers: {tickers}")

    print(f"--- Scraper Finished. Found {new_posts_found} new posts. ---")

if __name__ == "__main__":
    # This block runs only when you execute reddit_scraper.py directly
    # It's useful for a one-off manual run.
    run_scraper(subreddits=["stocks", "wallstreetbets"], limit_per_subreddit=100)

# sentiment analysis from here
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Load FinBERT model and tokenizer (do this once at the start)
tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")

def get_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=1)
        labels = ['negative', 'neutral', 'positive']
        sentiment = labels[probs.argmax()]
        score = probs.max().item()
    return sentiment, score

import sqlite3

def add_sentiment_to_db(db_name="reddit_posts.db"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    # Add sentiment columns if not present
    c.execute("ALTER TABLE posts ADD COLUMN sentiment TEXT")
    c.execute("ALTER TABLE posts ADD COLUMN sentiment_score REAL")
    conn.commit()
    # Get posts without sentiment
    c.execute("SELECT id, title, selftext FROM posts WHERE sentiment IS NULL")
    posts = c.fetchall()
    for post_id, title, selftext in posts:
        text = f"{title} {selftext}"
        sentiment, score = get_sentiment(text)
        c.execute("UPDATE posts SET sentiment=?, sentiment_score=? WHERE id=?", (sentiment, score, post_id))
        print(f"Updated {post_id} with sentiment {sentiment} ({score:.2f})")
    conn.commit()
    conn.close()
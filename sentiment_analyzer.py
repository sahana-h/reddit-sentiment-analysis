import sqlite3
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# --- Model Loading (do this once) ---
print("Loading FinBERT model...")
tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")
print("Model loaded.")
# ------------------------------------

def get_sentiment(text):
    """
    Analyzes the sentiment of a given text using FinBERT.
    """
    # Truncate text to fit model's max length
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        # The labels are in the order: Positive, Negative, Neutral for this model
        labels = ['positive', 'negative', 'neutral']
        sentiment = labels[probs.argmax()]
        score = probs.max().item()
    return sentiment, score

def analyze_and_update_db(db_name="reddit_posts.db"):
    """
    Adds sentiment columns to the DB, then analyzes any posts that are missing sentiment.
    """
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    # Add sentiment columns if they don't exist
    try:
        c.execute("ALTER TABLE posts ADD COLUMN sentiment TEXT")
        c.execute("ALTER TABLE posts ADD COLUMN sentiment_score REAL")
        print("Added sentiment columns to the database.")
    except sqlite3.OperationalError:
        print("Sentiment columns already exist.") # Columns already exist, which is fine

    # Get posts that haven't been analyzed yet
    c.execute("SELECT id, title, selftext FROM posts WHERE sentiment IS NULL")
    posts_to_analyze = c.fetchall()

    if not posts_to_analyze:
        print("No new posts to analyze.")
        return

    print(f"Found {len(posts_to_analyze)} posts to analyze...")
    for post_id, title, selftext in posts_to_analyze:
        text = f"{title}. {selftext}"
        sentiment, score = get_sentiment(text)
        
        # Update the database with the new sentiment
        c.execute(
            "UPDATE posts SET sentiment = ?, sentiment_score = ? WHERE id = ?",
            (sentiment, score, post_id)
        )
        print(f"Updated post {post_id} with sentiment: {sentiment} ({score:.2f})")

    conn.commit()
    conn.close()
    print("Database updated successfully.")

if __name__ == "__main__":
    analyze_and_update_db()
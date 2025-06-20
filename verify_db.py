import sqlite3

def view_first_5_posts(db_name="reddit_posts.db"):
    """Connects to the DB and prints the first 5 rows."""
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        # Get column names
        c.execute("PRAGMA table_info(posts)")
        columns = [col[1] for col in c.fetchall()]
        print("Columns:", columns)
        print("-" * 50)

        # Get first 5 rows
        c.execute("SELECT * FROM posts LIMIT 5")
        rows = c.fetchall()

        if not rows:
            print("No data found in the 'posts' table.")
            return

        for row in rows:
            print(dict(zip(columns, row)))

    except sqlite3.OperationalError as e:
        print(f"An error occurred: {e}")
        print("Did you run the scraper and analyzer first?")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    view_first_5_posts()
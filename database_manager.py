import sqlite3
import time

def delete_old_posts(db_name="reddit_posts.db", days_to_keep=90):
    """
    Deletes posts from the database that are older than a specified number of days.
    """
    print(f"--- Running Database Cleanup: Deleting posts older than {days_to_keep} days ---")
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        # Calculate the timestamp for the cutoff date
        cutoff_timestamp = time.time() - (days_to_keep * 24 * 60 * 60)

        # Execute the delete command
        c.execute("DELETE FROM posts WHERE created_utc < ?", (cutoff_timestamp,))
        
        rows_deleted = c.rowcount
        conn.commit()
        
        print(f"Cleanup complete. Deleted {rows_deleted} old posts.")

    except sqlite3.OperationalError as e:
        print(f"Database cleanup failed: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Example of how to run it manually for testing
    # Deletes posts older than 30 days
    delete_old_posts(days_to_keep=30) 
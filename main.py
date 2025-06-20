from reddit_scraper import run_scraper
from sentiment_analyzer import analyze_and_update_db
from database_manager import delete_old_posts
import time

def run_update_cycle():
    """
    Runs the full data pipeline: scrape, analyze, and clean up.
    """
    print("="*50)
    print("STARTING NEW UPDATE CYCLE...")
    print("="*50)
    
    # 1. Scrape for new posts from specified subreddits
    # We scrape from .new() to get the freshest content
    run_scraper(
        subreddits=["stocks", "wallstreetbets", "investing"],
        limit_per_subreddit=200 # Scrape 200 of the newest posts from each
    )
    
    # 2. Analyze sentiment for any posts that haven't been processed yet
    analyze_and_update_db()
    
    # 3. Clean up posts older than 90 days to keep the database fresh
    delete_old_posts(days_to_keep=90)
    
    print("\nUPDATE CYCLE COMPLETE.\n")


if __name__ == "__main__":
    # This script is designed to be run by a scheduler like cron.
    # It will run the cycle once and then exit.
    run_update_cycle()

    # --- Optional: For continuous running without cron ---
    # If you want the script to run forever without a scheduler,
    # you can uncomment the code below.
    #
    # while True:
    #     run_update_cycle()
    #     sleep_duration = 3600  # Sleep for 1 hour (3600 seconds)
    #     print(f"Sleeping for {sleep_duration / 60} minutes...")
    #     time.sleep(sleep_duration) 
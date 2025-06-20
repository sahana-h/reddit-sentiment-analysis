# import streamlit as st

# st.set_page_config(page_title="RetailRadar", layout="wide", initial_sidebar_state="expanded")

# st.title("RetailRadar: Real-Time Reddit Sentiment Dashboard for Stocks")
# st.write("Welcome! This dashboard will let you explore Reddit sentiment for your favorite stocks in real time.")

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# --- Page Configuration ---
# This must be the first Streamlit command in your script
st.set_page_config(
    page_title="RetailRadar: Reddit Sentiment Dashboard",
    layout="wide", # Use "wide" layout for more space
)

# --- Database Connection & Data Loading ---
@st.cache_data(ttl=600) # Cache data for 10 minutes
def load_data():
    """Loads post data from the SQLite database into a pandas DataFrame."""
    try:
        conn = sqlite3.connect("reddit_posts.db")
        # Load the data, converting the timestamp to a readable datetime format
        df = pd.read_sql_query("SELECT * FROM posts", conn)
        df['created_utc'] = pd.to_datetime(df['created_utc'], unit='s')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame() # Return empty dataframe on error

# --- Main Application ---
st.title("RetailRadar: Reddit Sentiment Dashboard")
st.markdown("Analyze real-time sentiment trends for stocks mentioned on Reddit.")

# Load the data
df = load_data()

# Check if data is loaded
if df.empty:
    st.warning("No data found. Please run the scraper (`reddit_scraper.py`) and analyzer (`sentiment_analyzer.py`) first.")
else:
    st.success(f"Successfully loaded {len(df)} posts from the database.")
    
    # --- Display Raw Data (for debugging) ---
    with st.expander("View Raw Data"):
        st.dataframe(df)
    

    # --- Ticker Selection ---
    # First, get a unique list of all tickers mentioned in the database
    all_tickers = df['tickers'].str.split(',').explode().str.strip().unique()
    selected_ticker = st.selectbox("Enter or select a stock ticker:", options=all_tickers)

    # Filter the DataFrame to only include posts that mention the selected ticker
    ticker_df = df[df['tickers'].str.contains(selected_ticker, na=False)].copy()
    
    if ticker_df.empty:
        st.warning(f"No posts found for ticker: {selected_ticker}")
    else:
        st.header(f"Sentiment Analysis for ${selected_ticker}")

        # --- Resample Data for Charting ---
        # We group data by day to get daily average sentiment and mention volume
        ticker_df.set_index('created_utc', inplace=True)
        daily_sentiment = ticker_df['sentiment_score'].resample('D').mean()
        daily_volume = ticker_df['id'].resample('D').count()

        daily_sentiment = daily_sentiment.interpolate()

        # Create a new DataFrame for charting
        chart_df = pd.DataFrame({
            'Average Sentiment': daily_sentiment,
            'Mentions': daily_volume
        }).reset_index()


        # --- Sentiment Over Time Line Chart ---
        st.subheader("Sentiment Over Time")
        fig_sentiment = px.line(
            chart_df,
            x='created_utc',
            y='Average Sentiment',
            title=f'Daily Average Sentiment for ${selected_ticker}',
            labels={'created_utc': 'Date', 'Average Sentiment': 'Avg. Sentiment Score'}
        )
        # Add a horizontal line at 0 for reference if you have scores below 0
        # fig_sentiment.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_sentiment, use_container_width=True)


        # --- Mention Volume Bar Chart ---
        st.subheader("Mention Volume")
        fig_volume = px.bar(
            chart_df,
            x='created_utc',
            y='Mentions',
            title=f'Daily Mention Volume for ${selected_ticker}',
            labels={'created_utc': 'Date', 'Mentions': 'Number of Mentions'}
        )
        st.plotly_chart(fig_volume, use_container_width=True)

        # --- Display Recent Posts ---
        st.subheader("Recent Posts Mentioning this Ticker")
        st.dataframe(ticker_df[['title', 'sentiment', 'sentiment_score']].sort_index(ascending=False).head(10))

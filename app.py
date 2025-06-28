# import streamlit as st

# st.set_page_config(page_title="RetailRadar", layout="wide", initial_sidebar_state="expanded")

# st.title("RetailRadar: Real-Time Reddit Sentiment Dashboard for Stocks")
# st.write("Welcome! This dashboard will let you explore Reddit sentiment for your favorite stocks in real time.")

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from stock_price_analyzer import (
    get_sentiment_price_comparison, 
    calculate_sentiment_price_correlation, 
    get_prediction_accuracy
)

# --- Page Configuration ---
# This must be the first Streamlit command in your script
st.set_page_config(
    page_title="RetailRadar: Reddit Sentiment Dashboard",
    page_icon="🔎",
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
st.title("🔎 RetailRadar: Reddit Sentiment Dashboard")
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

        # --- NEW: Sentiment vs Price Analysis ---
        st.header("📈 Sentiment vs Stock Price Analysis")
        
        # Add a slider for the analysis period
        days_back = st.slider("Analysis Period (days)", min_value=7, max_value=90, value=30, step=7)
        
        if st.button("Analyze Sentiment vs Price"):
            with st.spinner("Fetching stock price data and calculating correlations..."):
                try:
                    # Get sentiment and price data
                    sentiment_df, price_df, combined_df = get_sentiment_price_comparison(
                        selected_ticker, days_back=days_back
                    )
                    
                    if not combined_df.empty:
                        # Calculate correlations and accuracy
                        correlations = calculate_sentiment_price_correlation(combined_df)
                        accuracy = get_prediction_accuracy(combined_df)
                        
                        # Display metrics
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                "Sentiment-Price Correlation", 
                                f"{correlations.get('sentiment_price_corr', 0):.3f}"
                            )
                        
                        with col2:
                            st.metric(
                                "Sentiment-Return Correlation", 
                                f"{correlations.get('sentiment_return_corr', 0):.3f}"
                            )
                        
                        with col3:
                            st.metric(
                                "Prediction Accuracy", 
                                f"{accuracy.get('accuracy', 0):.1%}"
                            )
                        
                        # Create dual-axis chart showing sentiment and price
                        st.subheader("Sentiment vs Stock Price Overlay")
                        
                        fig = make_subplots(
                            rows=2, cols=1,
                            subplot_titles=('Sentiment Score', 'Stock Price'),
                            vertical_spacing=0.1
                        )
                        
                        # Add sentiment line
                        fig.add_trace(
                            go.Scatter(
                                x=combined_df.index,
                                y=combined_df['Sentiment_Score'],
                                name='Sentiment Score',
                                line=dict(color='blue')
                            ),
                            row=1, col=1
                        )
                        
                        # Add stock price line
                        fig.add_trace(
                            go.Scatter(
                                x=combined_df.index,
                                y=combined_df['Stock_Price'],
                                name='Stock Price',
                                line=dict(color='green')
                            ),
                            row=2, col=1
                        )
                        
                        fig.update_layout(height=600, showlegend=True)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display detailed correlation analysis
                        st.subheader("📊 Correlation Analysis")
                        
                        correlation_data = {
                            'Metric': [
                                'Sentiment vs Price',
                                'Sentiment vs Daily Return', 
                                'Sentiment vs Price Change %',
                                'Lagged Sentiment vs Return',
                                'R-squared (Sentiment-Price)',
                                'R-squared (Sentiment-Return)'
                            ],
                            'Value': [
                                correlations.get('sentiment_price_corr', 0),
                                correlations.get('sentiment_return_corr', 0),
                                correlations.get('sentiment_change_corr', 0),
                                correlations.get('sentiment_lagged_return_corr', 0),
                                correlations.get('sentiment_price_r2', 0),
                                correlations.get('sentiment_return_r2', 0)
                            ]
                        }
                        
                        corr_df = pd.DataFrame(correlation_data)
                        corr_df['Value'] = corr_df['Value'].round(4)
                        st.dataframe(corr_df, use_container_width=True)
                        
                        # Display prediction accuracy
                        st.subheader("🎯 Prediction Accuracy")
                        
                        accuracy_data = {
                            'Metric': [
                                'Overall Accuracy',
                                'Precision (Positive Predictions)',
                                'Recall (Positive Predictions)',
                                'Total Predictions',
                                'Correct Predictions'
                            ],
                            'Value': [
                                f"{accuracy.get('accuracy', 0):.1%}",
                                f"{accuracy.get('precision', 0):.1%}",
                                f"{accuracy.get('recall', 0):.1%}",
                                accuracy.get('total_predictions', 0),
                                accuracy.get('correct_predictions', 0)
                            ]
                        }
                        
                        acc_df = pd.DataFrame(accuracy_data)
                        st.dataframe(acc_df, use_container_width=True)
                        
                        # Interpretation
                        st.subheader("💡 Interpretation")
                        
                        sentiment_corr = correlations.get('sentiment_price_corr', 0)
                        if abs(sentiment_corr) > 0.7:
                            st.success("Strong correlation detected! Sentiment appears to be a good predictor of stock price movements.")
                        elif abs(sentiment_corr) > 0.4:
                            st.info("Moderate correlation detected. Sentiment shows some predictive value.")
                        elif abs(sentiment_corr) > 0.2:
                            st.warning("Weak correlation detected. Sentiment may have limited predictive value.")
                        else:
                            st.error("Very weak or no correlation detected. Sentiment may not be a reliable predictor for this stock.")
                        
                        # Show the raw data
                        with st.expander("View Raw Sentiment-Price Data"):
                            st.dataframe(combined_df)
                            
                    else:
                        st.error(f"No sufficient data found for {selected_ticker} in the last {days_back} days. Try a longer period or a different stock.")
                        
                except Exception as e:
                    st.error(f"Error analyzing sentiment vs price: {e}")
                    st.info("Make sure you have yfinance installed: `pip install yfinance`")

        # --- Display Recent Posts ---
        st.subheader("Recent Posts Mentioning this Ticker")
        st.dataframe(ticker_df[['title', 'sentiment', 'sentiment_score']].sort_index(ascending=False).head(10))

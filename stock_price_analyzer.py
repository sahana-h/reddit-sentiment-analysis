import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3

def get_stock_price_data(ticker, start_date, end_date=None):
    """
    Fetch stock price data for a given ticker and date range.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'TSLA')
        start_date (datetime): Start date for price data
        end_date (datetime): End date for price data (defaults to today)
    
    Returns:
        pandas.DataFrame: Daily OHLCV data with date index
    """
    if end_date is None:
        end_date = datetime.now()
    
    try:
        # Fetch stock data
        stock = yf.Ticker(ticker)
        price_data = stock.history(start=start_date, end=end_date)
        
        if price_data.empty:
            print(f"No price data found for {ticker}")
            return pd.DataFrame()
        
        # Convert timezone-aware index to timezone-naive
        price_data.index = price_data.index.tz_localize(None)
        
        return price_data
    
    except Exception as e:
        print(f"Error fetching price data for {ticker}: {e}")
        return pd.DataFrame()

def calculate_price_changes(price_data):
    """
    Calculate daily price changes and returns.
    
    Args:
        price_data (pandas.DataFrame): Stock price data from yfinance
    
    Returns:
        pandas.DataFrame: Price data with additional columns for changes
    """
    if price_data.empty:
        return price_data
    
    # Calculate daily returns
    price_data['Daily_Return'] = price_data['Close'].pct_change()
    
    # Calculate price change from previous day
    price_data['Price_Change'] = price_data['Close'] - price_data['Close'].shift(1)
    
    # Calculate percentage change
    price_data['Price_Change_Pct'] = price_data['Close'].pct_change() * 100
    
    return price_data

def get_sentiment_price_comparison(ticker, db_name="reddit_posts.db", days_back=30):
    """
    Get sentiment data and price data for comparison.
    
    Args:
        ticker (str): Stock ticker to analyze
        db_name (str): Database file name
        days_back (int): Number of days to look back
    
    Returns:
        tuple: (sentiment_df, price_df, combined_df)
    """
    # Get sentiment data from database
    conn = sqlite3.connect(db_name)
    
    # Get posts for this ticker within the date range
    start_date = datetime.now() - timedelta(days=days_back)
    start_timestamp = int(start_date.timestamp())
    
    query = """
    SELECT created_utc, sentiment_score, sentiment, upvotes
    FROM posts 
    WHERE tickers LIKE ? AND created_utc >= ?
    ORDER BY created_utc
    """
    
    sentiment_df = pd.read_sql_query(
        query, 
        conn, 
        params=[f'%{ticker}%', start_timestamp]
    )
    
    conn.close()
    
    if sentiment_df.empty:
        print(f"No sentiment data found for {ticker}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # Convert timestamps to datetime (timezone-naive)
    sentiment_df['date'] = pd.to_datetime(sentiment_df['created_utc'], unit='s')
    sentiment_df.set_index('date', inplace=True)
    
    # Resample sentiment data to daily averages
    daily_sentiment = sentiment_df['sentiment_score'].resample('D').mean()
    daily_sentiment = daily_sentiment.interpolate()  # Fill gaps
    
    # Get price data for the same period
    price_data = get_stock_price_data(ticker, start_date)
    price_data = calculate_price_changes(price_data)
    
    if price_data.empty:
        return sentiment_df, pd.DataFrame(), pd.DataFrame()
    
    # Combine sentiment and price data
    combined_df = pd.DataFrame({
        'Sentiment_Score': daily_sentiment,
        'Stock_Price': price_data['Close'],
        'Daily_Return': price_data['Daily_Return'],
        'Price_Change_Pct': price_data['Price_Change_Pct']
    })
    
    # Remove rows with NaN values
    combined_df = combined_df.dropna()
    
    return sentiment_df, price_data, combined_df

def calculate_sentiment_price_correlation(combined_df):
    """
    Calculate correlation between sentiment and price movements.
    
    Args:
        combined_df (pandas.DataFrame): Combined sentiment and price data
    
    Returns:
        dict: Correlation metrics
    """
    if combined_df.empty or len(combined_df) < 2:
        return {}
    
    correlations = {}
    
    # Calculate correlations
    correlations['sentiment_price_corr'] = combined_df['Sentiment_Score'].corr(combined_df['Stock_Price'])
    correlations['sentiment_return_corr'] = combined_df['Sentiment_Score'].corr(combined_df['Daily_Return'])
    correlations['sentiment_change_corr'] = combined_df['Sentiment_Score'].corr(combined_df['Price_Change_Pct'])
    
    # Calculate lagged correlations (sentiment today vs price tomorrow)
    if len(combined_df) > 1:
        sentiment_lagged = combined_df['Sentiment_Score'].shift(1)
        correlations['sentiment_lagged_return_corr'] = sentiment_lagged.corr(combined_df['Daily_Return'])
        correlations['sentiment_lagged_change_corr'] = sentiment_lagged.corr(combined_df['Price_Change_Pct'])
    
    # Calculate R-squared values
    correlations['sentiment_price_r2'] = correlations['sentiment_price_corr'] ** 2
    correlations['sentiment_return_r2'] = correlations['sentiment_return_corr'] ** 2
    
    return correlations

def get_prediction_accuracy(combined_df, threshold=0.02):
    """
    Calculate how well sentiment predicts price direction.
    
    Args:
        combined_df (pandas.DataFrame): Combined sentiment and price data
        threshold (float): Minimum price change to consider significant
    
    Returns:
        dict: Prediction accuracy metrics
    """
    if combined_df.empty or len(combined_df) < 2:
        return {}
    
    # Create lagged sentiment (sentiment today predicts price tomorrow)
    combined_df['Sentiment_Lagged'] = combined_df['Sentiment_Score'].shift(1)
    combined_df['Price_Direction'] = np.where(combined_df['Price_Change_Pct'] > threshold, 1, 
                                             np.where(combined_df['Price_Change_Pct'] < -threshold, -1, 0))
    combined_df['Sentiment_Direction'] = np.where(combined_df['Sentiment_Lagged'] > 0.5, 1,
                                                 np.where(combined_df['Sentiment_Lagged'] < 0.5, -1, 0))
    
    # Remove NaN values
    df_clean = combined_df.dropna()
    
    if len(df_clean) == 0:
        return {}
    
    # Calculate accuracy metrics
    correct_predictions = (df_clean['Sentiment_Direction'] == df_clean['Price_Direction']).sum()
    total_predictions = len(df_clean)
    accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
    
    # Calculate precision and recall for positive predictions
    positive_predictions = (df_clean['Sentiment_Direction'] == 1).sum()
    actual_positive = (df_clean['Price_Direction'] == 1).sum()
    true_positive = ((df_clean['Sentiment_Direction'] == 1) & (df_clean['Price_Direction'] == 1)).sum()
    
    precision = true_positive / positive_predictions if positive_predictions > 0 else 0
    recall = true_positive / actual_positive if actual_positive > 0 else 0
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'total_predictions': total_predictions,
        'correct_predictions': correct_predictions
    }

if __name__ == "__main__":
    # Test the functions
    ticker = "TSLA"
    sentiment_df, price_df, combined_df = get_sentiment_price_comparison(ticker, days_back=30)
    
    if not combined_df.empty:
        correlations = calculate_sentiment_price_correlation(combined_df)
        accuracy = get_prediction_accuracy(combined_df)
        
        print(f"Analysis for {ticker}:")
        print("Correlations:", correlations)
        print("Prediction Accuracy:", accuracy)
    else:
        print(f"No data available for {ticker}") 
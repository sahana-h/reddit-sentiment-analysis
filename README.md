# 🔍 RetailRadar: Real-Time Reddit Sentiment Dashboard for Stocks

RetailRadar is an interactive web dashboard that analyzes Reddit posts to uncover real-time sentiment trends around publicly traded stocks. By combining natural language processing (NLP) with financial market data, RetailRadar helps visualize how retail investor opinion fluctuates and whether it correlates with actual stock performance.

## Features

- **Ticker-Level Sentiment Tracking**: Enter any stock ticker to view sentiment trends over time
- **Real Reddit Posts Viewer**: Click on sentiment peaks/dips to view representative Reddit posts
- **Custom NLP Model**: Uses FinBERT for finance-specific sentiment analysis
- **Automated Data Pipeline**: Continuously scrapes and analyzes new Reddit posts
- **Interactive Visualizations**: Beautiful charts showing sentiment vs. mention volume
- **Company Name Recognition**: Detects both ticker symbols (TSLA) and company names (Tesla)

## Technology Stack

- **Backend**: Python, PRAW (Reddit API), Hugging Face Transformers
- **NLP**: FinBERT for financial sentiment analysis
- **Database**: SQLite for data storage
- **Data Processing**: Pandas for data manipulation and analysis
- **Frontend**: Streamlit for the web dashboard
- **Visualization**: Plotly for interactive charts
- **Automation**: Cron jobs for scheduled updates

## Prerequisites

- Python 3.8 or higher
- A Reddit account (for API access)
- Git

## Installation Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/retailradar.git
cd retailradar
```

### 2. Create a Virtual Environment
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install streamlit pandas plotly praw python-dotenv transformers torch requests
```

### 4. Set Up Reddit API Credentials

1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Fill in:
   - **Name**: RetailRadar
   - **Type**: Script
   - **Redirect URI**: http://localhost:8080
4. After creating, note your credentials:
   - **personal use script** (client_id)
   - **secret** (client_secret)
   - **username** (your Reddit username)
   - **password** (your Reddit password)

### 5. Create Environment File
Create a `.env` file in the project root:
```
REDDIT_CLIENT_ID=your_personal_use_script
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
REDDIT_USER_AGENT=RetailRadar by /u/your_username
```

### 6. Download Stock Ticker Data
Download a CSV file of NASDAQ-listed symbols and save it as `nasdaq-listed-symbols.csv` in the project root.

## How to Run

### Quick Start (Automated Pipeline)
Run the complete automated pipeline that scrapes, analyzes, and updates the database:
```bash
python main.py
```

### Individual Components

#### 1. Scrape Reddit Posts
Scrape posts from specified subreddits and extract stock tickers:
```bash
python reddit_scraper.py
```

#### 2. Analyze Sentiment
Run sentiment analysis on scraped posts:
```bash
python sentiment_analyzer.py
```

#### 3. Clean Database
Remove old posts to keep the database lean:
```bash
python database_manager.py
```

#### 4. Launch Dashboard
Start the interactive web dashboard:
```bash
streamlit run app.py
```

## Automation Setup

### Using Cron (macOS/Linux)
Set up automatic updates by adding a cron job:

1. Open your crontab:
```bash
crontab -e
```

2. Add this line to run updates every hour:
```bash
0 * * * * /path/to/your/project/env/bin/python /path/to/your/project/main.py >> /path/to/your/project/cron.log 2>&1
```

### Manual Continuous Running
For testing without cron, you can run the script continuously:
```bash
python main.py
```
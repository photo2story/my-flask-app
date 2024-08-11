# config.py
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import pytz
load_dotenv()

# Discord configuration
DISCORD_APPLICATION_TOKEN = os.getenv('DISCORD_APPLICATION_TOKEN', 'your_token_here')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 'your_channel_id_here'))
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', 'your_webhook_url_here')

# Investment and backtest configuration
START_DATE = os.getenv('START_DATE', '2019-01-02')
END_DATE = datetime.today().strftime('%Y-%m-%d')
INITIAL_INVESTMENT = int(os.getenv('INITIAL_INVESTMENT', 1000000))
MONTHLY_INVESTMENT = int(os.getenv('MONTHLY_INVESTMENT', 0))

# Data URLs
CSV_URL = os.getenv('CSV_URL', 'https://raw.githubusercontent.com/photo2story/my-flutter-app/main/static/images/stock_market.csv')
GITHUB_API_URL = os.getenv('GITHUB_API_URL', 'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images')

STOCKS = {
    'Technology': ['AAPL', 'MSFT', 'NVDA', 'GOOG', 'AMZN', 'META', 'CRM', 'ADBE', 'AMD', 'ACN', 'QCOM', 'CSCO', 'INTU', 'IBM', 'PDD', 'NOW', 'ARM', 'INTC', 'ANET', 'ADI', 'KLAC', 'PANW', 'AMT'],
    'Financials': [ 'V', 'MA', 'BAC', 'WFC', 'BLK', 'BX', 'GS', 'C', 'KKR'],
    'Consumer Cyclical': ['TSLA', 'AMZN', 'HD', 'NKE', 'MCD', 'SBUX', 'TJX', 'BKNG', 'CMG', 'TGT', 'LOW', 'EXPE', 'DG', 'JD'],
    'Healthcare': ['LLY', 'UNH', 'ABBV', 'JNJ', 'MRK', 'TMO', 'ABT', 'PFE', 'DHR', 'CVS', 'CI', 'GILD', 'AMGN', 'ISRG', 'REGN', 'VRTX', 'HCA'],
    'Communication Services': ['META', 'GOOGL', 'NFLX', 'DIS', 'VZ', 'T', 'CMCSA', 'SPOT', 'TWTR', 'ROKU', 'LYFT', 'UBER', 'EA'],
    'Industrials': ['GE', 'UPS', 'BA', 'CAT', 'MMM', 'HON', 'RTX', 'DE', 'LMT', 'NOC', 'UNP', 'WM', 'ETN', 'CSX', 'FDX'],
    'Consumer Defensive': ['WMT', 'KO', 'PEP', 'PG', 'COST', 'MDLZ', 'CL', 'PM', 'MO', 'KHC', 'HSY', 'KR', 'GIS', 'EL', 'STZ', 'MKC'],
    'Energy': ['XOM', 'CVX', 'COP', 'EOG', 'PSX', 'MPC', 'VLO', 'OKE', 'KMI', 'WMB', 'SLB', 'HAL', 'BKR'],
    'Basic Materials': ['LIN', 'ALB', 'NEM', 'FMC', 'APD', 'CF', 'ECL', 'LYB', 'PPG', 'SHW', 'CE', 'DD'],
    'Real Estate': ['AMT', 'PLD', 'EQIX', 'PSA', 'AVB', 'SPG', 'O', 'VICI', 'EXR', 'MAA', 'EQR'],
    'Utilities': ['NEE', 'DUK', 'SO', 'AEP', 'EXC', 'D', 'SRE', 'XEL', 'ED', 'ES', 'PEG', 'WEC']
}


# Stock market CSV path
STOCK_MARKET_CSV_PATH = os.getenv('STOCK_MARKET_CSV_PATH', 'path/to/stock_market.csv')

def initialize_trading_days(stock_data):
    first_day = stock_data.index.min()
    first_trading_day = first_day + timedelta(days=1)
    first_saving_day = first_day + timedelta(days=1)

    if first_trading_day.weekday() >= 1:
        first_trading_day += timedelta(days=7 - first_trading_day.weekday())

    return first_trading_day, first_saving_day

def should_invest_today(current_date, first_trading_day):
    if current_date.weekday() == 0 or (current_date.day <= 7 and current_date >= first_trading_day):
        return True
    return False

def monthly_deposit(current_date, prev_month, monthly_investment, cash, invested_amount):
    signal = ''
    if prev_month != f"{current_date.year}-{current_date.month}":
       cash += monthly_investment
       invested_amount += monthly_investment
       signal = 'Monthly invest'
       prev_month = f"{current_date.year}-{current_date.month}"
    return cash, invested_amount, signal, prev_month

# 추가된 함수: 분석 검증
# 미국 동부 표준시(EST)로 시간 설정
us_eastern = pytz.timezone('US/Eastern')
korea_time = datetime.now().astimezone(pytz.timezone('Asia/Seoul'))
us_market_close = korea_time.astimezone(us_eastern).replace(hour=16, minute=0, second=0, microsecond=0)
us_market_close_in_korea_time = us_market_close.astimezone(pytz.timezone('Asia/Seoul'))

# 기본적인 미국 주식시장 휴일 리스트 (업데이트 필요)
us_market_holidays = {
    "New Year's Day": (1, 1),
    "Independence Day": (7, 4),
    "Christmas Day": (12, 25),
    # 다른 주요 휴일 추가
}

def is_us_market_holiday(date):
    for holiday in us_market_holidays.values():
        if (date.month, date.day) == holiday:
            return True
    return False

from datetime import datetime, timedelta

def is_stock_analysis_complete(ticker):
    result_file_path = os.path.join('static', 'images', f'result_VOO_{ticker}.csv')
    if not os.path.exists(result_file_path):
        return False
    
    df = pd.read_csv(result_file_path, parse_dates=['Date'])
    if df['Date'].min().strftime('%Y-%m-%d') != START_DATE:
        return False
    
    latest_data_date = df['Date'].max()
    
    # 최신 데이터 날짜 출력
    print(f"Latest data date in dataset for {ticker}: {latest_data_date.strftime('%Y-%m-%d')}")

    return True


def is_gemini_analysis_complete(ticker):
    report_file_path = os.path.join('static', 'images', f'report_{ticker}.txt')
    
    if not os.path.exists(report_file_path):
        return False
    
    try:
        with open(report_file_path, 'r', encoding='utf-8') as file:
            first_line = file.readline().strip()
            today_date_str = datetime.now().strftime('%Y-%m-%d')
            
            if today_date_str in first_line:
                return True
            else:
                return False
    except Exception as e:
        print(f"Error reading report file for {ticker}: {e}")
        return False


if __name__ == '__main__':
    # 분석할 티커 설정
    ticker = 'TSLA'
    stock_analysis_complete = is_stock_analysis_complete(ticker )
    gemini_analysis_complete = is_gemini_analysis_complete(ticker )
    print(f"Stock analysis complete for {ticker}: {stock_analysis_complete}")
    print(f"Gemini analysis complete for {ticker}: {gemini_analysis_complete}")
    
# python config.py    
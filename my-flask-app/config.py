# config.py
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import pytz
import pandas_market_calendars as mcal

load_dotenv()

# Discord configuration
DISCORD_APPLICATION_TOKEN = os.getenv('DISCORD_APPLICATION_TOKEN', 'your_token_here')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 'your_channel_id_here'))
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', 'your_webhook_url_here')

# Investment and backtest configuration
START_DATE = os.getenv('START_DATE', '2019-01-02')
END_DATE = datetime.today().strftime('%Y-%m-%d')
INITIAL_INVESTMENT = int(os.getenv('INITIAL_INVESTMENT', 100000))
MONTHLY_INVESTMENT = int(os.getenv('MONTHLY_INVESTMENT', 1000))
option_strategy = 'default'

# Data URLs
CSV_URL = os.getenv('CSV_URL', 'https://raw.githubusercontent.com/photo2story/my-flutter-app/main/static/images/stock_market.csv')
GITHUB_API_URL = os.getenv('GITHUB_API_URL', 'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images')

# 프로젝트 루트 경로 설정
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# static/images 폴더 경로 설정 (프로젝트 루트 기준)
STATIC_IMAGES_PATH = os.path.join(PROJECT_ROOT, 'static', 'images')

# VOO 캐시 파일 경로 설정
VOO_CACHE_FILE = os.path.join(STATIC_IMAGES_PATH, 'cached_voo_data.csv')

# 기타 CSV 파일 경로 설정 (예: stock_market.csv)
CSV_PATH = os.path.join(STATIC_IMAGES_PATH, 'stock_market.csv')

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
    'Utilities': ['NEE', 'DUK', 'SO', 'AEP', 'EXC', 'D', 'SRE', 'XEL', 'ED', 'ES', 'PEG', 'WEC'],
    'Index, Coin': ['VOO', 'QQQ', 'BTC-USD']
}

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
    current_month = f"{current_date.year}-{current_date.month}"

    if prev_month != current_month:
       cash += monthly_investment
       invested_amount += monthly_investment
       signal = 'Monthly invest'
       prev_month = current_month

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

def get_us_last_trading_day(date):
    """
    주어진 날짜에 가장 가까운 미국 주식시장의 마지막 거래일을 반환합니다.
    """
    nyse = mcal.get_calendar('NYSE')
    schedule = nyse.schedule.loc[date - pd.DateOffset(days=7):date]
    last_trading_day = schedule.index[-1]
    return last_trading_day

def is_stock_analysis_complete(ticker):
    result_file_path = os.path.join(STATIC_IMAGES_PATH, f'result_VOO_{ticker}.csv')
    
    # 파일이 존재하지 않으면 False 반환
    if not os.path.exists(result_file_path):
        return False
    
    # 파일을 읽어옴
    df = pd.read_csv(result_file_path, parse_dates=['Date'])
    
    # 파일의 시작 날짜가 설정된 START_DATE와 일치하는지 확인
    if df['Date'].min().strftime('%Y-%m-%d') != START_DATE:
        return False
    
    # 파일의 마지막 날짜가 현재 설정된 END_DATE와 일치하는지 확인
    latest_data_date = df['Date'].max().strftime('%Y-%m-%d')
    if latest_data_date != END_DATE:
        print(f"Data is incomplete for {ticker}. Latest date: {latest_data_date}, Expected end date: {END_DATE}")
        return False
    
    # 최신 데이터 날짜 출력
    print(f"Latest data date in dataset for {ticker}: {latest_data_date}")

    # 시작 날짜와 마지막 날짜가 모두 일치하면 True 반환
    return True


def is_gemini_analysis_complete(ticker):
    report_file_path = os.path.join(STATIC_IMAGES_PATH, f'report_{ticker}.txt')
    
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

def is_cache_valid(cache_file, start_date):
    """
    캐시 파일이 유효한지 확인:
    - 파일이 존재하는지 확인.
    - 파일의 마지막 날짜가 미국 주식시장의 마지막 거래일과 일치하는지 확인.
    - 파일의 데이터가 START_DATE 이후인지 확인.
    """
    if not os.path.exists(cache_file):
        print("Cache file does not exist.")
        return False
    
    df = pd.read_csv(cache_file, parse_dates=['Date'])
    
    # 시작 날짜 확인
    min_date_in_cache = df['Date'].min().strftime('%Y-%m-%d')
    print(f"Start date in cache: {min_date_in_cache}")
    
    if min_date_in_cache != start_date:
        print(f"Start date mismatch: {min_date_in_cache} != {start_date}")
        return False
    
    # 마지막 거래일 확인
    latest_data_date = df['Date'].max()
    last_trading_day = get_us_last_trading_day(datetime.today())

    # 현재 시간이 장 마감 이후인지 확인
    current_time = datetime.now(us_eastern)
    if current_time < us_market_close:
        print("Market is not closed yet, using previous trading day's data.")
        last_trading_day = get_us_last_trading_day(datetime.today() - timedelta(days=1))

    print(f"Latest data date in cache: {latest_data_date}, Last trading day: {last_trading_day}")

    if latest_data_date != last_trading_day:
        print(f"Data is not up-to-date. Latest data date: {latest_data_date}, Last trading day: {last_trading_day}")
        return False

    print("Cache is valid.")
    return True

# Example function to ensure that the dates match the US market close:
def ensure_valid_dates(df):
    """
    주어진 DataFrame의 날짜가 미국 시장 종료 시간에 맞는지 확인합니다.
    """
    df['Date'] = pd.to_datetime(df['Date'])
    # 미국 시간으로 종가를 확인하기 위해 날짜를 동부 표준시로 변환
    df['Date'] = df['Date'].dt.tz_localize('UTC').dt.tz_convert(us_eastern)
    
    # 장 마감 이후 데이터가 맞는지 확인 (16:00:00 이후)
    valid_dates = df[df['Date'].dt.time >= datetime.time(16, 0)]
    
    if valid_dates.empty:
        print("No valid dates found matching the US market close times.")
    else:
        print(f"Valid dates found: {valid_dates['Date'].min()} to {valid_dates['Date'].max()}")

    return valid_dates

# 이 함수들을 봇의 다른 부분에서 호출하여 유효성을 검토할 수 있습니다.
if __name__ == '__main__':
    # 분석할 티커 설정
    ticker = 'TSLA'
    stock_analysis_complete = is_stock_analysis_complete(ticker)
    gemini_analysis_complete = is_gemini_analysis_complete(ticker)
    print(f"Stock analysis complete for {ticker}: {stock_analysis_complete}")
    print(f"Gemini analysis complete for {ticker}: {gemini_analysis_complete}")
    
# python config.py

# def get_end_date_from_cache(cache_file):
#     """
#     Get the latest date from the cache file.
#     """
#     if os.path.exists(cache_file):
#         df = pd.read_csv(cache_file, parse_dates=['Date'])
#         latest_data_date = df['Date'].max().strftime('%Y-%m-%d')
#         return latest_data_date
#     return datetime.today().strftime('%Y-%m-%d')

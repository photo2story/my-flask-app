## Get_data.py

import yfinance as yf
import pandas_ta as ta
import pandas as pd
import requests
import numpy as np
import FinanceDataReader as fdr
from github_operations import ticker_path  # stock_market.csv 파일 경로
import os
import sys

NaN = np.nan

# 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_ppo(prices, short_window=12, long_window=26, signal_window=9):
    short_ema = prices.ewm(span=short_window, adjust=False).mean()
    long_ema = prices.ewm(span=long_window, adjust=False).mean()
    ppo = ((short_ema - long_ema) / long_ema) * 100
    ppo_signal = ppo.ewm(span=signal_window, adjust=False).mean()
    ppo_histogram = ppo - ppo_signal
    return ppo, ppo_signal, ppo_histogram

def calculate_mfi(high_prices, low_prices, close_prices, volumes, length=14):
    typical_prices = (high_prices + low_prices + close_prices) / 3
    raw_money_flows = typical_prices * volumes
  
    positive_flows = []
    negative_flows = []
  
    for i in range(1, len(typical_prices)):
        if typical_prices[i] > typical_prices[i-1]:
            positive_flows.append(raw_money_flows[i])
            negative_flows.append(0)
        else:
            positive_flows.append(0)
            negative_flows.append(raw_money_flows[i])
  
    mfi_values = []
  
    for i in range(length, len(typical_prices)):
        positive_mf_sum = np.sum(positive_flows[i-length:i])
        negative_mf_sum = np.sum(negative_flows[i-length:i])
  
        if negative_mf_sum == 0:
            mfi = 100  # Prevent division by zero, MFI is 100 when there are only positive flows
        else:
            mr = positive_mf_sum / negative_mf_sum
            mfi = 100 - (100 / (1 + mr))
  
        mfi_values.append(mfi)
  
    # Initialize an array with NaNs for the initial periods
    mfi_values_full = np.empty(len(typical_prices))
    mfi_values_full[:] = np.nan
    # Replace the calculated values starting from the 'length' index
    mfi_values_full[-len(mfi_values):] = mfi_values  # Corrected line
    return mfi_values_full

def load_industry_info():
    industry_df = pd.read_csv(ticker_path)  # stock_market.csv 파일 경로
    industry_dict = dict(zip(industry_df['Symbol'], industry_df['Industry']))
    return industry_dict

def get_stock_data(ticker, start_date, end_date):
    # 파일 경로 지정
    safe_ticker = ticker.replace('/', '-')
    file_path = os.path.join('static', 'images', f'data_{safe_ticker}.csv')

    # 기존 데이터가 있으면 읽어오기
    if os.path.exists(file_path):
        existing_data = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')
        last_date = existing_data.index.max().strftime('%Y-%m-%d')

        # 마지막 날짜 이후의 데이터만 가져오기
        if last_date < end_date:
            new_data = fdr.DataReader(ticker, last_date, end_date)
            new_data = process_data(new_data)  # 데이터 처리 함수 호출
            combined_data = pd.concat([existing_data, new_data])
            combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
            combined_data.to_csv(file_path)
        else:
            combined_data = existing_data
    else:
        combined_data = fdr.DataReader(ticker, start_date, end_date)
        combined_data = process_data(combined_data)
        combined_data.to_csv(file_path)

    return combined_data

def process_data(stock_data):
    # Custom indicator calculations (RSI, MFI, etc.)
    stock_data['RSI_14'] = calculate_rsi(stock_data['Close'], window=14)
  
    stock_data.ta.bbands(length=20, std=2, append=True)
    stock_data['UPPER_20'] = stock_data['BBL_20_2.0'] + 2 * (stock_data['BBM_20_2.0'] - stock_data['BBL_20_2.0'])
    stock_data['LOWER_20'] = stock_data['BBM_20_2.0'] - 2 * (stock_data['BBM_20_2.0'] - stock_data['BBL_20_2.0'])
    stock_data.ta.aroon(length=25, append=True)

    high_prices = stock_data['High'].values
    low_prices = stock_data['Low'].values
    close_prices = stock_data['Close'].values
    volumes = stock_data['Volume'].values
    stock_data['MFI_14'] = calculate_mfi(high_prices, low_prices, close_prices, volumes, length=14)
  
    stock_data.ta.sma(close='Close', length=5, append=True)
    stock_data.ta.sma(close='Close', length=10, append=True)
    stock_data.ta.sma(close='Close', length=20, append=True)
    stock_data.ta.sma(close='Close', length=60, append=True)
    stock_data.ta.sma(close='Close', length=120, append=True)
    stock_data.ta.sma(close='Close', length=240, append=True)
    stock_data.ta.stoch(high='high', low='low', k=20, d=10, append=True)
    stock_data.ta.stoch(high='high', low='low', k=14, d=3, append=True)
    stock_data['Stock'] = ticker

    sector_df = pd.read_csv(ticker_path)  # stock_market.csv 파일 경로
    sector_dict = dict(zip(sector_df['Symbol'], sector_df['Sector']))
    if ticker in sector_dict:
        stock_data['Sector'] = sector_dict[ticker]
    else:
        stock_data['Sector'] = sector_dict.get(ticker, 'Unknown')

    return stock_data

def get_price_info(ticker):
    api_key = 'Alpha_API'
    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}'
    response = requests.get(url)
    data = response.json()

    if 'Exchange' in data:
        market = data['Exchange']
        return market
    else:
        return "알 수 없음"

if __name__ == "__main__":
    # Industry 정보 불러오기
    industry_info = load_industry_info()
  
    # 티커와 기간 지정
    ticker = 'BTC-USD'
    start_date = '2019-01-01'
    end_date = '2024-09-02'
  
    # 주식 데이터 가져오기
    stock_data = get_stock_data(ticker, start_date, end_date)
    print(stock_data)
    print(np.__version__)
    print(pd.__version__)
    print(ta.__version__)


## python Get_data.py    
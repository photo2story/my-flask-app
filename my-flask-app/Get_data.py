## Get_data.py

import yfinance as yf
import pandas_ta as ta
import pandas as pd
import requests
import numpy as np
import FinanceDataReader as fdr
import os
import sys

from github_operations import ticker_path  # stock_market.csv 파일 경로

# 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

NaN = np.nan

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

def calculate_bollinger_bands(prices, window=20, num_std_dev=2):
    rolling_mean = prices.rolling(window=window).mean()
    rolling_std = prices.rolling(window=window).std()

    upper_band = rolling_mean + (rolling_std * num_std_dev)
    lower_band = rolling_mean - (rolling_std * num_std_dev)

    return upper_band, rolling_mean, lower_band

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
            mfi = 100
        else:
            mr = positive_mf_sum / negative_mf_sum
            mfi = 100 - (100 / (1 + mr))

        mfi_values.append(mfi)

    mfi_values_full = np.empty(len(typical_prices))
    mfi_values_full[:] = np.nan
    mfi_values_full[-len(mfi_values):] = mfi_values
    return mfi_values_full

def load_industry_info():
    industry_df = pd.read_csv(ticker_path)
    industry_dict = dict(zip(industry_df['Symbol'], industry_df['Industry']))
    return industry_dict

def get_stock_data(ticker, start_date, end_date):
    """
    주어진 티커와 날짜 범위에 해당하는 주가 데이터를 가져오고, 파일에 저장.
    필요한 경우 새 데이터를 불러오고, 저장된 데이터에 이어서 업데이트를 수행합니다.
    """
    safe_ticker = ticker.replace('/', '-')
    
    # static/images 폴더 경로 설정
    folder_path = os.path.join('static', 'images')
    
    # 폴더가 없을 경우 생성
    os.makedirs(folder_path, exist_ok=True)
    
    # 파일을 static/images 폴더 아래에 저장
    file_path = os.path.join(folder_path, f'data_{safe_ticker}.csv')

    # 파일이 이미 존재하는지 확인
    if os.path.exists(file_path):
        # 기존 데이터를 로드
        existing_data = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')
        last_date = existing_data.index.max().strftime('%Y-%m-%d')
        first_date = existing_data.index.min().strftime('%Y-%m-%d')

        if last_date < end_date:
            # 마지막 날짜 이후의 데이터를 새로 가져옴
            new_data = fdr.DataReader(ticker, last_date, end_date)
            new_data = process_data(new_data, ticker)
            combined_data = pd.concat([existing_data, new_data])
            combined_data = combined_data[~combined_data.index.duplicated(keep='last')]  # 중복된 날짜 제거
            combined_data.to_csv(file_path)  # 업데이트된 데이터를 파일에 저장
        else:
            combined_data = existing_data
    else:
        # 파일이 없으면 전체 데이터를 가져옴
        combined_data = fdr.DataReader(ticker, start_date, end_date)
        combined_data = process_data(combined_data, ticker)
        combined_data.to_csv(file_path)  # 파일로 처음 저장
        first_date = combined_data.index.min().strftime('%Y-%m-%d')
        last_date = combined_data.index.max().strftime('%Y-%m-%d')

    print(f"Loaded data for {ticker} from {first_date} to {end_date}")
    
    return combined_data, first_date, last_date


def process_data(stock_data, ticker):
    # 데이터가 20개 미만일 경우 경고 메시지를 출력하고 처리 건너뛰기
    if len(stock_data) < 20:
        print(f"Warning: Not enough data to calculate Bollinger Bands for {ticker}. Minimum 20 data points required.")
        return stock_data  # 데이터가 부족한 경우 기존 데이터 반환
    
    stock_data.ffill(inplace=True)
    stock_data.bfill(inplace=True)

    # RSI, Bollinger Bands
    stock_data['RSI_14'] = calculate_rsi(stock_data['Close'], window=14)
    stock_data['bb_upper_ta'], stock_data['bb_middle_ta'], stock_data['bb_lower_ta'] = calculate_bollinger_bands(stock_data['Close'])

    # Aroon, MFI
    stock_data.ta.aroon(length=25, append=True)
    stock_data['MFI_14'] = calculate_mfi(stock_data['High'].values, stock_data['Low'].values, stock_data['Close'].values, stock_data['Volume'].values, length=14)
    
    # SMA (이동평균선)
    stock_data.ta.sma(close='Close', length=5, append=True)
    stock_data.ta.sma(close='Close', length=10, append=True)
    stock_data.ta.sma(close='Close', length=20, append=True)
    stock_data.ta.sma(close='Close', length=60, append=True)
    stock_data.ta.sma(close='Close', length=120, append=True)
    stock_data.ta.sma(close='Close', length=240, append=True)

    # Stochastic
    stock_data.ta.stoch(high='High', low='Low', k=20, d=10, append=True)
    stock_data.ta.stoch(high='High', low='Low', k=14, d=3, append=True)

    # PPO (Price Percentage Oscillator)
    try:
        stock_data['ppo'], stock_data['ppo_signal'], stock_data['ppo_histogram'] = calculate_ppo(stock_data['Close'])
    except Exception as e:
        print(f"Error calculating PPO for {ticker}: {e}")
        stock_data['ppo'], stock_data['ppo_signal'], stock_data['ppo_histogram'] = np.nan, np.nan, np.nan

    stock_data['Stock'] = ticker

    # Sector 정보 추가
    sector_df = pd.read_csv(ticker_path)
    sector_dict = dict(zip(sector_df['Symbol'], sector_df['Sector']))
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
    industry_info = load_industry_info()

    ticker = 'BTC-USD'
    start_date = '2019-01-01'
    end_date = '2024-09-02'

    stock_data, first_stock_data_date = get_stock_data(ticker, start_date, end_date)
    print(stock_data)
    print(np.__version__)
    print(pd.__version__)
    print(ta.__version__)

## python Get_data.py    
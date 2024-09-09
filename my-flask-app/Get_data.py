## Get_data.py

import pandas_ta as ta
import pandas as pd
import requests
import numpy as np
import FinanceDataReader as fdr
import os
import sys
import config
import yfinance as yf
from datetime import datetime, timedelta

# 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
CSV_PATH = config.CSV_PATH

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
    industry_df = pd.read_csv(CSV_PATH)
    industry_dict = dict(zip(industry_df['Symbol'], industry_df['Industry']))
    return industry_dict

import os
import pandas as pd
import yfinance as yf

import os
import pandas as pd
import yfinance as yf

def get_stock_data(ticker, start_date, end_date, add_past_data=False, past_start_date=None):
    safe_ticker = ticker.replace('/', '-')
    print(safe_ticker)
    
    # static/images 폴더 경로 설정
    folder_path = config.STATIC_IMAGES_PATH
    file_path = os.path.join(folder_path, f'data_{safe_ticker}.csv')

    try:
        if os.path.exists(file_path):
            existing_data = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')
            first_saved_date = existing_data.index[0].strftime('%Y-%m-%d')  # 기존 데이터의 첫 날짜
            last_saved_date = existing_data.index[-1].strftime('%Y-%m-%d')  # 기존 데이터의 마지막 날짜
            print(f"Existing data found for {ticker}, last saved date: {last_saved_date}, first saved date: {first_saved_date}")

            # 새로운 데이터를 가져와서 업데이트 (현재 마지막 날짜 이후 데이터)
            if last_saved_date < end_date:
                new_start_date = (pd.to_datetime(last_saved_date) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                print(f"Fetching new data from {new_start_date} to {end_date} for {ticker}.")
                new_data = yf.download(safe_ticker, start=new_start_date, end=end_date)

                if not new_data.empty:
                    # 중복된 인덱스(날짜) 제거
                    new_data = new_data[~new_data.index.duplicated(keep='first')]
                    existing_data = pd.concat([existing_data, new_data])
                    existing_data = existing_data[~existing_data.index.duplicated(keep='first')]  # 중복 제거
                else:
                    print(f"No new data found for {ticker}.")

            # 과거 데이터 추가 (현재 첫 번째 날짜 이전 데이터)
            if add_past_data and past_start_date and first_saved_date > past_start_date:
                print(f"Fetching past data from {past_start_date} to {first_saved_date} for {ticker}.")
                past_data = yf.download(safe_ticker, start=past_start_date, end=first_saved_date)

                if not past_data.empty:
                    past_data = past_data[~past_data.index.duplicated(keep='first')]  # 중복 제거
                    existing_data = pd.concat([past_data, existing_data])
                    existing_data = existing_data[~existing_data.index.duplicated(keep='first')]  # 중복 제거
                else:
                    print(f"No past data found for {ticker}.")
        
        else:
            # 기존 파일이 없으면 전체 데이터를 가져옴
            print(f"No existing data found for {ticker}, fetching from {start_date} to {end_date}.")
            existing_data = yf.download(safe_ticker, start=start_date, end=end_date)

            if existing_data.empty:
                print(f"No data found for {ticker}.")
                return pd.DataFrame(), start_date, end_date

        # 데이터 처리
        existing_data = process_data(existing_data, ticker)
    
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame(), start_date, end_date

    # 데이터 파일을 static/images 폴더 아래에 저장
    existing_data.to_csv(file_path)  # 업데이트된 데이터를 파일로 저장

    # 마지막 데이터의 실제 날짜 가져오기
    last_available_date = existing_data.index[-1].strftime('%Y-%m-%d')
    first_available_date = existing_data.index[0].strftime('%Y-%m-%d')

    # 로깅 메시지에서 실제 데이터를 사용하여 출력
    print(f"Loaded data for {ticker} from {first_available_date} to {last_available_date}")
    
    return existing_data, first_available_date, last_available_date

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
    sector_df = pd.read_csv(CSV_PATH)
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
    # 테스트 실행
    ticker = 'AAPL'
    start_date = '2015-01-01'
    end_date = datetime.today().strftime('%Y-%m-%d')
    # Apple 주식(AAPL) 데이터를 테스트로 가져오기
    try:
        stock_data = yf.download('AAPL', start_date, end_date)
        print(stock_data)  # 데이터가 정상적으로 가져와지는지 확인
    except Exception as e:
        print(f"오류 발생: {e}")



## python Get_data.py    

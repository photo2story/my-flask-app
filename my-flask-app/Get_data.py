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


def get_stock_data(ticker, start_date, end_date, add_past_data=False, past_start_date=None):
    """
    주어진 티커와 날짜 범위에 해당하는 주가 데이터를 가져오고 새로 생성하여 처리합니다.
    필요 시 과거 데이터를 추가로 가져옵니다.

    add_past_data: 과거 데이터를 추가로 가져올지 여부
    past_start_date: 과거 데이터를 가져오는 경우의 시작일
    """
    # 티커가 6글자 이상인 경우, 한국 주식으로 판단하고 '.KS' 접미사를 붙임
    original_ticker = ticker
    if len(ticker) == 6 and ticker.isdigit():
        safe_ticker = f'{ticker}.KS'
    else:
        safe_ticker = ticker.replace('/', '-')

    print(f"Processing data for ticker: {safe_ticker}")

    # static/images 폴더 경로 설정
    # folder_path = config.STATIC_IMAGES_PATH
    folder_path = config.STATIC_DATA_PATH

    # 경로가 존재하는지 확인 (존재하지 않으면 강제 종료)
    if not os.path.exists(folder_path):
        print(f"Error: Directory {folder_path} does not exist.")
        raise FileNotFoundError(f"Critical error: Required directory {folder_path} not found. Exiting.")
    
    # 저장할 파일 경로는 원래의 티커명으로 설정
    file_path = os.path.join(folder_path, f'data_{original_ticker}.csv')

    try:
        # 기존 파일이 존재하면 데이터를 로드
        if os.path.exists(file_path):
            existing_data = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')
            first_saved_date = existing_data.index[0].strftime('%Y-%m-%d')
            last_saved_date = existing_data.index[-1].strftime('%Y-%m-%d')
            print(f"Existing data found for {original_ticker}, first saved date: {first_saved_date}, last saved date: {last_saved_date}")

            # 새로운 데이터를 추가
            if last_saved_date < end_date:
                new_start_date = (pd.to_datetime(last_saved_date) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                print(f"Fetching new data from {new_start_date} to {end_date} for {original_ticker}.")
                try:
                    new_data = yf.download(safe_ticker, start=new_start_date, end=end_date)
                except Exception as e:
                    print(f"Failed to download new data for {original_ticker}: {e}")
                    new_data = pd.DataFrame()  # 비어있는 데이터프레임으로 초기화

                if not new_data.empty:
                    new_data = new_data[~new_data.index.duplicated(keep='first')]
                    existing_data = pd.concat([existing_data, new_data])
                    existing_data = existing_data[~existing_data.index.duplicated(keep='first')]  # 중복 제거
                    print(f"New data successfully added for {original_ticker}.")
                else:
                    print(f"No new data found for {original_ticker}.")
            else:
                print(f"No new data needed for {original_ticker}. Data is already up-to-date.")

            # 과거 데이터 추가
            if add_past_data and past_start_date and first_saved_date > past_start_date:
                print(f"Fetching past data from {past_start_date} to {first_saved_date} for {original_ticker}.")
                try:
                    past_data = yf.download(safe_ticker, start=past_start_date, end=first_saved_date)
                except Exception as e:
                    print(f"Failed to download past data for {original_ticker}: {e}")
                    past_data = pd.DataFrame()  # 비어있는 데이터프레임으로 초기화

                if not past_data.empty:
                    past_data = past_data[~past_data.index.duplicated(keep='first')]
                    existing_data = pd.concat([past_data, existing_data])
                    existing_data = existing_data[~existing_data.index.duplicated(keep='first')]  # 중복 제거
                    print(f"Past data successfully added for {original_ticker}.")
                else:
                    print(f"No past data found for {original_ticker}.")
            else:
                print(f"No past data fetching required for {original_ticker}.")
        
        else:
            # 기존 파일이 없으면 전체 데이터를 새로 가져옴
            print(f"No existing data found for {original_ticker}, fetching from {start_date} to {end_date}.")
            try:
                existing_data = yf.download(safe_ticker, start=start_date, end=end_date)
            except Exception as e:
                print(f"Failed to fetch data for {original_ticker}: {e}")
                return pd.DataFrame(), start_date, end_date

            if existing_data.empty:
                print(f"No data found for {original_ticker}.")
                return pd.DataFrame(), start_date, end_date

            print(f"Data successfully fetched for {original_ticker} from {start_date} to {end_date}.")

        # 데이터 처리 (필요한 추가 분석 또는 수정)
        existing_data = process_data(existing_data, original_ticker)
    
    except Exception as e:
        print(f"Error fetching data for {original_ticker}: {e}")
        return pd.DataFrame(), start_date, end_date

    # 데이터를 저장
    try:
        existing_data.to_csv(file_path)
        print(f"Data saved successfully for {original_ticker} at {file_path}")
    except PermissionError:
        print(f"Permission error: Unable to save data for {original_ticker} at {file_path}. Please check folder permissions.")
    except Exception as e:
        print(f"Error saving data for {original_ticker} at {file_path}: {e}")
    
    # 마지막 데이터의 날짜 반환
    last_available_date = existing_data.index[-1].strftime('%Y-%m-%d')
    first_available_date = existing_data.index[0].strftime('%Y-%m-%d')

    print(f"Loaded data for {original_ticker} from {first_available_date} to {last_available_date}")
    
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

def test_fetch_and_process_stock_data():
    """
    Test function to verify stock data fetching and processing.
    """
    tickers = ['IONQ']  # Test with different tickers (Apple, Hyundai, Microsoft)
    start_date = '2019-01-01'
    end_date = datetime.today().strftime('%Y-%m-%d')

    for ticker in tickers:
        print(f"\nTesting ticker: {ticker}")
        try:
            stock_data, first_available_date, last_available_date = get_stock_data(ticker, start_date, end_date)
            
            if stock_data.empty:
                print(f"Test failed: No data fetched for {ticker}")
            else:
                print(f"Test passed: Data fetched for {ticker} from {first_available_date} to {last_available_date}")
                print(stock_data)  # Display sample data for validation

        except Exception as e:
            print(f"Test failed: Error fetching data for {ticker}: {e}")
            continue

    # Additional testing for invalid ticker
    print("\nTesting invalid ticker: INVALID_TICKER")
    try:
        stock_data, first_available_date, last_available_date = get_stock_data('INVALID_TICKER', start_date, end_date)
        if stock_data.empty:
            print("Test passed: No data returned for invalid ticker.")
        else:
            print("Test failed: Data should not have been returned for invalid ticker.")
    except Exception as e:
        print(f"Test passed: Error handled correctly for invalid ticker: {e}")

if __name__ == "__main__":
    test_fetch_and_process_stock_data()

## python Get_data.py    

## Get_data.py


import yfinance as yf
import pandas_ta as ta
import pandas as pd
import requests
import numpy as np
import FinanceDataReader as fdr
from github_operations import ticker_path # stock_market.csv 파일 경로
from datetime import datetime, timedelta
import os
NaN = np.nan

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
    industry_df = pd.read_csv(ticker_path)# stock_market.csv 파일 경로
    industry_dict = dict(zip(industry_df['Symbol'], industry_df['Industry']))
    return industry_dict
  
def get_start_date(ticker):
    # Fetch stock data for the past year or more to ensure we get the earliest available data
    stock_data = fdr.DataReader(ticker, '2021-01-01')  # Replace with a date far enough back in time
    # Return the actual start date of the data
    return stock_data.index.min()

def calculate_indicators(stock_data):
    # RSI 계산
    try:
        rsi_series = stock_data.ta.rsi(length=14)
        stock_data['RSI_14'] = rsi_series
    except Exception as e:
        print(f"Error calculating RSI: {e}")
        stock_data['RSI_14'] = 0

    # Bollinger Bands 계산
    try:
        bbands_df = stock_data.ta.bbands(length=20, std=2)
        stock_data['UPPER_20'] = bbands_df['BBU_20_2.0'] if 'BBU_20_2.0' in bbands_df else 0
        stock_data['LOWER_20'] = bbands_df['BBL_20_2.0'] if 'BBL_20_2.0' in bbands_df else 0
    except Exception as e:
        print(f"Error calculating Bollinger Bands: {e}")
        stock_data['UPPER_20'] = 0
        stock_data['LOWER_20'] = 0

    # Aroon 계산
    try:
        aroon_df = stock_data.ta.aroon(length=25)
        stock_data['AROONU_25'] = aroon_df['AROONU_25'] if 'AROONU_25' in aroon_df else 0
        stock_data['AROOND_25'] = aroon_df['AROOND_25'] if 'AROOND_25' in aroon_df else 0
    except Exception as e:
        print(f"Error calculating Aroon: {e}")
        stock_data['AROONU_25'] = 0
        stock_data['AROOND_25'] = 0

    # MFI 계산
    try:
        high_prices = stock_data['High'].values
        low_prices = stock_data['Low'].values
        close_prices = stock_data['Close'].values
        volumes = stock_data['Volume'].values
        stock_data['MFI_14'] = calculate_mfi(high_prices, low_prices, close_prices, volumes, length=14)
    except Exception as e:
        print(f"Error calculating MFI: {e}")
        stock_data['MFI_14'] = 0

    # 이동평균 계산 (pandas의 rolling을 사용)
    try:
        stock_data['SMA_5'] = stock_data['Close'].rolling(window=5).mean()
        stock_data['SMA_10'] = stock_data['Close'].rolling(window=10).mean()
        stock_data['SMA_20'] = stock_data['Close'].rolling(window=20).mean()
        stock_data['SMA_60'] = stock_data['Close'].rolling(window=60).mean()
        stock_data['SMA_120'] = stock_data['Close'].rolling(window=120).mean()
        stock_data['SMA_240'] = stock_data['Close'].rolling(window=240).mean()
    except Exception as e:
        print(f"Error calculating SMAs: {e}")
        stock_data['SMA_5'] = stock_data['SMA_10'] = stock_data['SMA_20'] = stock_data['SMA_60'] = stock_data['SMA_120'] = stock_data['SMA_240'] = 0

    # Stochastic Oscillator 계산
    try:
        stoch_df_20 = stock_data.ta.stoch(high='High', low='Low', k=20, d=10)
        stock_data['STOCHk_20_10_3'] = stoch_df_20['STOCHk_20_10_3'] if 'STOCHk_20_10_3' in stoch_df_20.columns else 0
        stock_data['STOCHd_20_10_3'] = stoch_df_20['STOCHd_20_10_3'] if 'STOCHd_20_10_3' in stoch_df_20.columns else 0

        stoch_df_14 = stock_data.ta.stoch(high='High', low='Low', k=14, d=3)
        stock_data['STOCHk_14_3_3'] = stoch_df_14['STOCHk_14_3_3'] if 'STOCHk_14_3_3' in stoch_df_14.columns else 0
        stock_data['STOCHd_14_3_3'] = stoch_df_14['STOCHd_14_3_3'] if 'STOCHd_14_3_3' in stoch_df_14.columns else 0
    except Exception as e:
        print(f"Error calculating Stochastic Oscillator: {e}")
        stock_data['STOCHk_20_10_3'] = stock_data['STOCHd_20_10_3'] = stock_data['STOCHk_14_3_3'] = stock_data['STOCHd_14_3_3'] = 0

    return stock_data



def get_stock_data(ticker, start_date, end_date):
    # 문자열로 입력된 start_date와 end_date를 Timestamp로 변환
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # 파일 경로 설정
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images', f'result_VOO_{ticker}.csv'))

    # CSV 파일이 존재하는지 확인
    if os.path.exists(file_path):
        stock_data = pd.read_csv(file_path, index_col=0, parse_dates=True)
        first_stock_data_date = stock_data.index.min()
        last_stock_data_date = stock_data.index.max()

        # Timestamps를 비교하여 캐시된 데이터의 범위 확인
        if first_stock_data_date <= start_date and last_stock_data_date >= end_date:
            print("Using cached data")
            stock_data = calculate_indicators(stock_data)
            return stock_data.loc[start_date:end_date], first_stock_data_date

        # 데이터가 부족한 경우 추가로 데이터를 가져옴
        if last_stock_data_date < end_date:
            print("Fetching additional data after the last date in the cache")
            new_data = fdr.DataReader(ticker, last_stock_data_date + timedelta(days=1), end_date)
            new_data = calculate_indicators(new_data)
            stock_data = pd.concat([stock_data, new_data])

        if first_stock_data_date > start_date:
            print("Fetching additional data before the first date in the cache")
            new_data = fdr.DataReader(ticker, start_date, first_stock_data_date - timedelta(days=1))
            new_data = calculate_indicators(new_data)
            stock_data = pd.concat([new_data, stock_data])
            
        stock_data['Stock'] = ticker   

    else:
        # 새 데이터를 불러와 초기화
        stock_data = fdr.DataReader(ticker, start_date, end_date)
        stock_data = calculate_indicators(stock_data)
        first_stock_data_date = stock_data.index.min()
        stock_data['Stock'] = ticker

    return stock_data, first_stock_data_date


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
    ticker = 'TSLA'
    start_date = '2024-01-01'
    end_date = '2024-06-01'
  
    # 주식 데이터 가져오기
    stock_data = get_stock_data(ticker, start_date, end_date)
    print(stock_data)
    print(np.__version__)
    print(pd.__version__)
    print(ta.__version__)
    
## python Get_data.py    
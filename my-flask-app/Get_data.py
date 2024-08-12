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
    # 지표 계산 로직
    stock_data.ta.rsi(length=14, append=True)
    stock_data.ta.bbands(length=20, std=2, append=True)
    # stock_data['UPPER_20'] = stock_data['BBL_20_2.0'] + 2 * (stock_data['BBM_20_2.0'] - stock_data['BBL_20_2.0'])
    # stock_data['LOWER_20'] = stock_data['BBM_20_2.0'] - 2 * (stock_data['BBM_20_2.0'] - stock_data['BBL_20_2.0'])
    
    # 볼린저 밴드 상단과 하단 값 계산
    if 'BBL_20_2.0' in stock_data.columns and 'BBM_20_2.0' in stock_data.columns:
        stock_data['UPPER_20'] = stock_data['BBL_20_2.0'] + 2 * (stock_data['BBM_20_2.0'] - stock_data['BBL_20_2.0'])
        stock_data['LOWER_20'] = stock_data['BBM_20_2.0'] - 2 * (stock_data['BBM_20_2.0'] - stock_data['BBL_20_2.0'])
    else:
        stock_data['UPPER_20']  = 0
        stock_data['LOWER_20']  = 0
        
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

    return stock_data

def get_stock_data(ticker, start_date, end_date):
    # start_date와 end_date가 문자열인 경우 datetime으로 변환
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    # 파일 경로 설정
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images', f'result_VOO_{ticker}.csv'))

    # CSV 파일이 존재하는지 확인
    if os.path.exists(file_path):
        # 기존 파일에서 데이터를 불러옵니다.
        stock_data = pd.read_csv(file_path, index_col=0, parse_dates=True)
        first_stock_data_date = stock_data.index.min()
        last_stock_data_date = stock_data.index.max()

        # 날짜 형식을 통일하기 위해 datetime 객체로 변환
        if isinstance(first_stock_data_date, str):
            first_stock_data_date = datetime.strptime(first_stock_data_date, '%Y-%m-%d')
        if isinstance(last_stock_data_date, str):
            last_stock_data_date = datetime.strptime(last_stock_data_date, '%Y-%m-%d')

        # 데이터 범위가 요청된 범위를 모두 포함하는지 확인
        if first_stock_data_date <= start_date and last_stock_data_date >= end_date:
            print("Using cached data")
            stock_data = calculate_indicators(stock_data)
            return stock_data.loc[start_date:end_date], first_stock_data_date

        # 필요한 경우 추가 데이터 가져오기
        if last_stock_data_date < end_date:
            print("Fetching additional data after the last date in the cache")
            additional_data = fdr.DataReader(ticker, last_stock_data_date + timedelta(days=1), end_date)
            additional_data = calculate_indicators(additional_data)
            stock_data = pd.concat([stock_data, additional_data])

        if first_stock_data_date > start_date:
            print("Fetching additional data before the first date in the cache")
            additional_data = fdr.DataReader(ticker, start_date, first_stock_data_date - timedelta(days=1))
            additional_data = calculate_indicators(additional_data)
            stock_data = pd.concat([additional_data, stock_data])

    else:
        # 캐시된 데이터가 없으면 전체 데이터를 불러옵니다.
        stock_data = fdr.DataReader(ticker, start_date, end_date)
        stock_data = calculate_indicators(stock_data)

    # Industry 정보 추가
    sector_df = pd.read_csv(ticker_path)  # stock_market.csv 파일 경로
    sector_dict = dict(zip(sector_df['Symbol'], sector_df['Sector']))
    if ticker in sector_dict:
        stock_data['Sector'] = sector_dict[ticker]
    else:
        stock_data['Sector'] = sector_dict.get(ticker, 'Unknown')
    
    stock_data['Stock'] = ticker    

    print(stock_data)
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
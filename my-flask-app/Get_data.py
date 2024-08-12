## Get_data.py


import yfinance as yf
import pandas_ta as ta
import pandas as pd
import requests
import numpy as np
import FinanceDataReader as fdr
from github_operations import ticker_path # stock_market.csv 파일 경로
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

    return stock_data

def get_stock_data(ticker, start_date, end_date):
    # FinanceDataReader를 사용하여 주식 데이터 불러오기
    print('get_stock_data.1:',ticker)
    # print(start_date)
    stock_data = fdr.DataReader(ticker, start_date, end_date)

    stock_data.columns = stock_data.columns.astype(str)
  
    stock_data = calculate_indicators(stock_data)
    stock_data['Stock'] = ticker


    # Industry 정보 추가
    sector_df = pd.read_csv(ticker_path)# stock_market.csv 파일 경로
    sector_dict = dict(zip(sector_df['Symbol'], sector_df['Sector']))
    if ticker in sector_dict:
        stock_data['Sector'] = sector_dict[ticker]
    else:
        stock_data['Sector'] = sector_dict.get(ticker, 'Unknown')

    # 데이터 프레임에서 최소 날짜를 얻습니다.
    min_stock_data_date = stock_data.index.min()
    print(stock_data)
    return stock_data, min_stock_data_date

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
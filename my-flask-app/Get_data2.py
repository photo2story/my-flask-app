import FinanceDataReader as fdr
import os
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd


# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)
name = 'AAPL'

# df1 = yf.download(name, period='1y')
# print('Result of yf.download(name, period=5y)')
# print(df1)
# print('\n')

raw_datas = 100
t_end = datetime.today()
t_start = '2019-01-02'
df3 = yf.download(name, start= t_start, end= t_end)
print(df3)


# Apple 주식(AAPL) 데이터를 테스트로 가져오기
try:
    stock_data = fdr.DataReader('AAPL', '2023-01-01', '2023-12-31')
    print(stock_data.head())  # 데이터가 정상적으로 가져와지는지 확인
except Exception as e:
    print(f"오류 발생: {e}")
       


## python Get_data2.py    
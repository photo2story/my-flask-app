#### get_ticker.py
import pandas as pd
import FinanceDataReader as fdr
import csv, os, io, requests
from github_operations import ticker_path  # stock_market.csv 파일 경로
import yfinance as yf
import investpy
import config


# ticker_path = os.getenv('CSV_URL', 'https://raw.githubusercontent.com/photo2story/my-flutter-app/main/static/images/stock_market.csv')
# CSV_URL = 'https://raw.githubusercontent.com/photo2story/my-flutter-app/main/static/images/stock_market.csv'
ticker_path = config.CSV_PATH

def get_ticker_name(ticker):
    df = pd.read_csv(ticker_path, encoding='utf-8')  # stock_market.csv 파일 경로 인코딩 설정
    result = df.loc[df['Symbol'] == ticker, 'Name']
    name = result.iloc[0] if not result.empty else None
    return name

def get_ticker_market(ticker):
    df = pd.read_csv(ticker_path, encoding='utf-8')  # stock_market.csv 파일 경로 인코딩 설정
    result = df.loc[df['Symbol'] == ticker, 'Market']
    market = result.iloc[0] if not result.empty else None
    return market

def get_stock_info(ticker):
    info = yf.Ticker(ticker).info
    return {
        'Stock': ticker,
        'Industry': info.get('industry'),
        'Beta': info.get('beta'),
        'Sector': info.get('sector')
    }

def update_stock_market_csv(file_path, tickers_to_update):
    df = pd.read_csv(ticker_path, encoding='utf-8-sig')  # Specify encoding
    for i, row in df.iterrows():
        ticker = row['Symbol']
        if ticker in tickers_to_update:
            stock_info = get_stock_info(ticker)
            if stock_info:
                for key, value in stock_info.items():
                    df.at[i, key] = value
            else:
                # 데이터가 없는 경우 기본값을 설정합니다.
                df.at[i, 'Sector'] = 'Unknown'
                df.at[i, 'Stock'] = 'Unknown Stock'
                df.at[i, 'Industry'] = 'Unknown Industry'
                df.at[i, 'Beta'] = 0.0
                df.at[i, 'marketcap'] = 0.0                
    
    df.to_csv(ticker_path, index=False, encoding='utf-8-sig')  # Specify encoding

def load_tickers():
    ticker_dict = {}
    response = requests.get(CSV_URL)
    response.raise_for_status()
    csv_data = response.content.decode('utf-8')
    csv_reader = csv.reader(io.StringIO(csv_data))
    for rows in csv_reader:
        if len(rows) >= 2:
            ticker_dict[rows[1]] = rows[0]
    return ticker_dict

def search_tickers(stock_name, ticker_dict):
    stock_name_lower = stock_name.lower()
    return [(ticker, name) for name, ticker in ticker_dict.items() if stock_name_lower in name.lower()]

def search_ticker_list_KR():
    url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
    response = requests.get(url)
    response.encoding = 'euc-kr'  # Korean encoding
    df_listing = pd.read_html(response.text, header=0)[0]
    cols_ren = {
        '회사명': 'Name',
        '종목코드': 'Symbol',
        '업종': 'Sector',
    }
    df_listing = df_listing.rename(columns=cols_ren)
    df_listing['market'] = 'KRX'
    df_listing['Symbol'] = df_listing['Symbol'].apply(lambda x: '{:06d}'.format(x))
    df_KR = df_listing[['Symbol', 'Name', 'market', 'Sector']]
    return df_KR

def search_ticker_list_US():
    df_amex = fdr.StockListing('AMEX')
    df_nasdaq = fdr.StockListing('NASDAQ')
    df_nyse = fdr.StockListing('NYSE')
    try:
        df_ETF_US = fdr.StockListing("ETF/US")
        df_ETF_US['market'] = "us_ETF"
        columns_to_select = ['Symbol', 'Name', 'market']
        df_ETF_US = df_ETF_US[columns_to_select]
    except Exception as e:
        print(f"An error occurred while fetching US ETF listings: {e}")
        df_ETF_US = pd.DataFrame(columns=['Symbol', 'Name', 'market'])
    df_amex['market'] = "AMEX"
    df_nasdaq['market'] = "NASDAQ"
    df_nyse['market'] = "NYSE"
    columns_to_select = ['Symbol', 'Name', 'market']
    df_amex = df_amex[columns_to_select]
    df_nasdaq = df_nasdaq[columns_to_select]
    df_nyse = df_nyse[columns_to_select]
    data_frames_US = [df_nasdaq, df_nyse, df_amex, df_ETF_US]
    df_US = pd.concat(data_frames_US, ignore_index=True)
    df_US['Sector'] = 'none'
    df_US = df_US[['Symbol', 'Name', 'market', 'Sector']]
    return df_US

def search_ticker_list_US_ETF():
    df_etfs = investpy.etfs.get_etfs(country='united states')
    df_US_ETF = df_etfs[['symbol', 'name']].copy()
    df_US_ETF['market'] = 'US_ETF'
    df_US_ETF['Sector'] = 'US_ETF'
    df_US_ETF.columns = ['Symbol', 'Name', 'market', 'Sector']
    return df_US_ETF

def get_ticker_list_all():
    df_KR = search_ticker_list_KR()
    df_US = search_ticker_list_US()
    df_US_ETF = search_ticker_list_US_ETF()
    df_combined = pd.concat([df_KR, df_US, df_US_ETF], ignore_index=True)
    df_combined.to_csv(ticker_path, encoding='utf-8-sig', index=False)
    return df_combined

def get_ticker_from_korean_name(name):
    df_KR = search_ticker_list_KR()
    result = df_KR.loc[df_KR['Name'] == name, 'Symbol']
    ticker = result.iloc[0] if not result.empty else None
    return ticker

async def search_tickers_and_respond(ctx, query):
    ticker_dict = load_tickers()
    matching_tickers = search_tickers(query, ticker_dict)
    if not matching_tickers:
        await ctx.send("No search results.")
        return
    response_message = "Search results:\n"
    response_messages = []
    for symbol, name in matching_tickers:
        line = f"{symbol} - {name}\n"
        if len(response_message) + len(line) > 2000:
            response_messages.append(response_message)
            response_message = "Search results (continued):\n"
        response_message += line
    if response_message:
        response_messages.append(response_message)
    for message in response_messages:
        await ctx.send(message)
    print(f'Sent messages for query: {query}')

def is_valid_stock(stock):  # Check if the stock is in the stock market CSV
    try:
        url = 'https://raw.githubusercontent.com/photo2story/my-flutter-app/main/static/images/stock_market.csv'
        stock_market_df = pd.read_csv(url, encoding='utf-8')  # Specify encoding
        return stock in stock_market_df['Symbol'].values
    except Exception as e:
        print(f"Error checking stock market CSV: {e}")
        return False
    
import pandas as pd
import yfinance as yf
import os

def get_market_cap(ticker):
    """
    주어진 티커의 시가총액을 반환하는 함수.
    :param ticker: 주식 티커
    :return: 시가총액 (없으면 0 반환)
    """
    try:
        stock = yf.Ticker(ticker)
        market_cap = stock.info.get('marketCap')
        if market_cap is None:
            print(f"Market cap for {ticker} not found.")
            return 0
        print(f"Ticker: {ticker}, Market Cap: {market_cap}")
        return market_cap
    except Exception as e:
        print(f"Error fetching market cap for {ticker}: {e}")
        return 0

def update_market_cap_in_csv(csv_url):
    """
    CSV 파일을 읽어 티커의 시가총액을 업데이트하는 함수.
    NYSE와 NASDAQ 시장의 주식만 포함.
    :param csv_url: CSV 파일 URL
    """
    response = requests.get(csv_url)
    response.raise_for_status()
    csv_data = response.content.decode('utf-8')
    df = pd.read_csv(io.StringIO(csv_data))

    # NYSE와 NASDAQ 주식 필터링
    filtered_df = df[df['Market'].isin(['NYSE', 'NASDAQ'])]

    # marketCap 열이 없으면 새로 추가
    if 'marketCap' not in df.columns:
        df['marketCap'] = 0.0

    total_tickers = len(filtered_df)
    for index, row in filtered_df.iterrows():
        ticker = row['Symbol']
        market_cap = get_market_cap(ticker)
        df.at[index, 'marketCap'] = market_cap
        print(f"Processed {index + 1}/{total_tickers} - {ticker}")

    # 업데이트된 데이터프레임을 로컬에 저장 (원격에 저장하려면 추가 작업 필요)
    df.to_csv('updated_stock_market.csv', index=False)
    print(f"Updated CSV saved to updated_stock_market.csv")

if __name__ == "__main__":
    # 시가총액 업데이트
    # update_market_cap_in_csv(CSV_URL)


    
    
    tickers_to_update = ['QQQ']
    update_stock_market_csv(ticker_path, tickers_to_update)
    print("Stock information updated.")
    
#  .\.venv\Scripts\activate
#  python get_ticker.py
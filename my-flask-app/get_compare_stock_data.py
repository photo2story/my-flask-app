# get_compare_stock_data.py

import os
import sys
import pandas as pd
import numpy as np
import requests
import io


# 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from git_operations import move_files_to_images_folder  # git_operations 모듈에서 함수 가져오기

GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com/photo2story/my-flutter-app/main/static/images"

async def fetch_csv(ticker):
    url = f"{GITHUB_RAW_BASE_URL}/result_{ticker}.csv"
    try:
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        return df
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data for {ticker}: {e}")
        return None
    except pd.errors.EmptyDataError:
        print(f"No data found for {ticker}.")
        return None

def read_and_process_csv(file_path):
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])  # Date 열을 datetime 형식으로 변환
    file_name_parts = os.path.splitext(os.path.basename(file_path))[0].split('_')
    ticker = file_name_parts[-1]
    
    if 'rate' in df.columns and 'rate_vs' in df.columns:
        result_df = df[['Date', 'rate', 'rate_vs']].copy()
        result_df = result_df.rename(columns={'rate': f'rate_{ticker}_5D', 'rate_vs': 'rate_VOO_20D'})
    else:
        raise KeyError(f"'rate' or 'rate_vs' columns not found in file: {file_path}")
    
    return result_df

def calculate_divergence(df, ticker):
    divergence = df[f'rate_{ticker}_5D'] - df['rate_VOO_20D']
    return divergence

def save_simplified_csv(file_path, ticker):
    df = read_and_process_csv(file_path)
    
    divergence = calculate_divergence(df, ticker)
    df['Divergence'] = np.round(divergence, 2)

    if 'Divergence' in df.columns:
        max_divergence = df['Divergence'].max()
        min_divergence = df['Divergence'].min()
        df['Relative_Divergence'] = ((df['Divergence'] - min_divergence) / (max_divergence - min_divergence)) * 100
        df['Relative_Divergence'] = np.round(df['Relative_Divergence'], 2)
    else:
        print(f"Divergence column not found in dataframe for {ticker}")
        return

    simplified_df = df.iloc[::40].reset_index(drop=True)
    
    folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images'))
    simplified_file_path = os.path.join(folder_path, f'result_{ticker}.csv')
    simplified_df.to_csv(simplified_file_path, index=False)
    print(f"Simplified CSV saved: {simplified_file_path}")

    if not df.empty:
        latest_entry = df.iloc[-1]
        current_divergence = latest_entry['Divergence']
        current_relative_divergence = latest_entry['Relative_Divergence']
    
        print(f"Current Divergence for {ticker}: {current_divergence} (max {max_divergence}, min {min_divergence})")
        print(f"Current Relative Divergence for {ticker}: {current_relative_divergence}")

async def collect_relative_divergence():
    tickers = [stock for sector, stocks in config.STOCKS.items() for stock in stocks]
    results = pd.DataFrame(columns=['Ticker', 'Divergence', 'Relative_Divergence', 'Previous_Relative_Divergence'])
    
    for ticker in tickers:
        df = await fetch_csv(ticker)
        if df is not None and 'Relative_Divergence' in df.columns:
            latest_relative_divergence = df['Relative_Divergence'].iloc[-1]
            latest_divergence = df['Divergence'].iloc[-1]
            
            if len(df) > 20:  # 데이터가 충분한지 확인
                previous_relative_divergence = df['Relative_Divergence'].iloc[-20]
            else:
                previous_relative_divergence = None  # 데이터가 충분하지 않다면 None 설정
            
            results = pd.concat([results, pd.DataFrame({
                'Ticker': [ticker], 
                'Divergence': [latest_divergence], 
                'Relative_Divergence': [latest_relative_divergence],
                'Previous_Relative_Divergence': [previous_relative_divergence]
            })], ignore_index=True)
        else:
            print(f"Data for {ticker} is not available or missing 'Relative_Divergence' column.")
    
    # 결과를 CSV 파일로 저장
    folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images'))
    collect_relative_divergence_path = os.path.join(folder_path, f'results_relative_divergence.csv')
    results.to_csv(collect_relative_divergence_path, index=False)

    print(results)
    
    # 파일 이동 및 깃 커밋 푸시 작업
    await move_files_to_images_folder()
    
    return results



if __name__ == "__main__":
    import asyncio
    asyncio.run(collect_relative_divergence())

# python get_compare_stock_data.py
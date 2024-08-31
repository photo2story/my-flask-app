# get_compare_stock_data.py

import os
import sys
import pandas as pd
import numpy as np
import requests
import io
import datetime

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

def calculate_potential_profit_and_loss(df, current_rel_divergence):
    max_rel_divergence = df['Relative_Divergence'].max()
    min_rel_divergence = df['Relative_Divergence'].min()
    
    max_potential_profit = max_rel_divergence - current_rel_divergence
    max_potential_loss = current_rel_divergence - min_rel_divergence
    
    max_time = df[df['Relative_Divergence'] == max_rel_divergence]['Date'].values[0]
    min_time = df[df['Relative_Divergence'] == min_rel_divergence]['Date'].values[0]
    current_time = df.iloc[-1]['Date']
    
    time_to_max = (pd.to_datetime(max_time) - pd.to_datetime(current_time)).days
    time_to_min = (pd.to_datetime(min_time) - pd.to_datetime(current_time)).days
    
    return max_potential_profit, max_potential_loss, time_to_max, time_to_min

async def collect_relative_divergence():
    tickers = [stock for sector, stocks in config.STOCKS.items() for stock in stocks]
    results = pd.DataFrame(columns=['Ticker', 'Divergence', 'Relative_Divergence', 
                                    'Delta_Previous_Relative_Divergence', 'Max_Potential_Profit', 
                                    'Max_Potential_Loss', 'Time_To_Max', 'Time_To_Min'])
    
    for ticker in tickers:
        df = await fetch_csv(ticker)
        if df is None or df.empty or 'Relative_Divergence' not in df.columns:
            print(f"Data for {ticker} is not available or missing necessary columns.")
            continue
        
        try:
            latest_entry = df.iloc[-1]  # 마지막 데이터를 가져옴
            if latest_entry.isna().all():
                print(f"Data for {ticker} is empty or contains only NA values, skipping...")
                continue

            latest_relative_divergence = latest_entry['Relative_Divergence']
            latest_divergence = latest_entry['Divergence']
            delta_previous_relative_divergence = latest_entry.get('Delta_Previous_Relative_Divergence', 0)
            max_potential_profit, max_potential_loss, time_to_max, time_to_min = calculate_potential_profit_and_loss(df, latest_relative_divergence)

            results = pd.concat([results, pd.DataFrame({
                'Ticker': [ticker], 
                'Divergence': [latest_divergence], 
                'Relative_Divergence': [latest_relative_divergence],
                'Delta_Previous_Relative_Divergence': [delta_previous_relative_divergence],
                'Max_Potential_Profit': [max_potential_profit],
                'Max_Potential_Loss': [max_potential_loss],
                'Time_To_Max': [time_to_max],
                'Time_To_Min': [time_to_min]
            })], ignore_index=True)
        except Exception as e:
            print(f"Error processing data for {ticker}: {e}")
            continue
    
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
    tickers = [
        'AAPL', 'MSFT', 'NVDA', 'GOOG', 'AMZN', 'META', 'CRM', 'ADBE', 'AMD', 'ACN', 'QCOM', 'CSCO',
        'INTU', 'IBM', 'PDD', 'NOW', 'ARM', 'INTC', 'ANET', 'ADI', 'KLAC', 'PANW', 'AMT', 'V', 'MA',
        'BAC', 'WFC', 'BLK', 'BX', 'GS', 'C', 'KKR', 'TSLA', 'HD', 'NKE', 'MCD', 'SBUX', 'TJX', 'BKNG',
        'CMG', 'TGT', 'LOW', 'EXPE', 'DG', 'JD', 'LLY', 'UNH', 'ABBV', 'JNJ', 'MRK', 'TMO', 'ABT', 'PFE',
        'DHR', 'CVS', 'CI', 'GILD', 'AMGN', 'ISRG', 'REGN', 'VRTX', 'HCA', 'GOOGL', 'NFLX', 'DIS', 'VZ',
        'T', 'CMCSA', 'SPOT', 'TWTR', 'ROKU', 'LYFT', 'UBER', 'EA', 'GE', 'UPS', 'BA', 'CAT', 'MMM', 'HON',
        'RTX', 'DE', 'LMT', 'NOC', 'UNP', 'WM', 'ETN', 'CSX', 'FDX', 'WMT', 'KO', 'PEP', 'PG', 'COST',
        'MDLZ', 'CL', 'PM', 'MO', 'KHC', 'HSY', 'KR', 'GIS', 'EL', 'STZ', 'MKC', 'XOM', 'CVX', 'COP', 'EOG',
        'PSX', 'MPC', 'VLO', 'OKE', 'KMI', 'WMB', 'SLB', 'HAL', 'BKR', 'LIN', 'ALB', 'NEM', 'FMC', 'APD',
        'CF', 'ECL', 'LYB', 'PPG', 'SHW', 'CE', 'DD', 'AMT', 'PLD', 'EQIX', 'PSA', 'AVB', 'SPG', 'O', 'VICI',
        'EXR', 'MAA', 'EQR', 'NEE', 'DUK', 'SO', 'AEP', 'EXC', 'D', 'SRE', 'XEL', 'ED', 'ES', 'PEG', 'WEC'
    ]
    for ticker in tickers:
        asyncio.run(collect_relative_divergence())


# python get_compare_stock_data.py
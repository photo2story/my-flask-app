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
    
    # 최대와 최소에 도달하는데 걸린 시간 계산
    max_time = df[df['Relative_Divergence'] == max_rel_divergence]['Date'].values[0]
    min_time = df[df['Relative_Divergence'] == min_rel_divergence]['Date'].values[0]
    current_time = df.iloc[-1]['Date']
    
    time_to_max = (pd.to_datetime(max_time) - pd.to_datetime(current_time)).days
    time_to_min = (pd.to_datetime(min_time) - pd.to_datetime(current_time)).days
    
    return max_potential_profit, max_potential_loss, time_to_max, time_to_min

def save_simplified_csv(ticker):
    # 파일 경로 설정
    folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images'))
    file_path = os.path.join(folder_path, f'result_VOO_{ticker}.csv')
    
    # 파일이 존재하지 않으면 건너뜁니다.
    if not os.path.exists(file_path):
        print(f"File not found for ticker {ticker}, skipping...")
        return
        
    # 데이터 로드 및 필요한 열만 선택
    df = pd.read_csv(file_path, parse_dates=['Date'], usecols=['Date', 'rate', 'rate_vs'])
    
    # 이격도(Divergence) 계산
    df['Divergence'] = np.round(df['rate'] - df['rate_vs'], 2)
    df = df.rename(columns={'rate': f'rate_{ticker}_5D', 'rate_vs': 'rate_VOO_20D'})
    
    # 상대 이격도(Relative Divergence) 계산
    max_divergence = df['Divergence'].max()
    min_divergence = df['Divergence'].min()
    df['Relative_Divergence'] = np.round(((df['Divergence'] - min_divergence) / (max_divergence - min_divergence)) * 100, 2)
    
    # 이전 상대 이격도 변화량(Delta Previous Relative Divergence) 계산
    df['Delta_Previous_Relative_Divergence'] = df['Relative_Divergence'].diff(periods=20).fillna(0).round(2)

    # 현재 Relative Divergence
    current_rel_divergence = df.iloc[-1]['Relative_Divergence']
    
    # 추가된 필드: 최대 수익, 최대 손실, 최대 및 최소 도달 시간
    df['Max_Potential_Profit'], df['Max_Potential_Loss'], df['Time_To_Max'], df['Time_To_Min'] = calculate_potential_profit_and_loss(df, current_rel_divergence)
    
    # 간소화된 데이터프레임 생성 (20개 단위로 샘플링)
    simplified_df = df[['Date', f'rate_{ticker}_5D', 'rate_VOO_20D', 'Divergence', 'Relative_Divergence', 
                        'Delta_Previous_Relative_Divergence', 'Max_Potential_Profit', 'Max_Potential_Loss', 
                        'Time_To_Max', 'Time_To_Min']].iloc[::20].reset_index(drop=True)
    
    # 마지막 데이터 추가 (concat 사용)
    if not simplified_df.iloc[-1].equals(df.iloc[-1]):
        simplified_df = pd.concat([simplified_df, df.iloc[[-1]]], ignore_index=True)
    
    # 파일 저장
    simplified_file_path = os.path.join(folder_path, f'result_{ticker}.csv')
    simplified_df.to_csv(simplified_file_path, index=False)
    print(f"Simplified CSV saved: {simplified_file_path}")

    # 마지막 데이터를 출력
    latest_entry = df.iloc[-1]
    print(f"Current Divergence for {ticker}: {latest_entry['Divergence']} (max {max_divergence}, min {min_divergence})")
    print(f"Current Relative Divergence for {ticker}: {latest_entry['Relative_Divergence']}")
    print(f"Delta Previous Relative Divergence for {ticker}: {latest_entry['Delta_Previous_Relative_Divergence']}")
    print(f"Max Potential Profit for {ticker}: {latest_entry['Max_Potential_Profit']}")
    print(f"Max Potential Loss for {ticker}: {latest_entry['Max_Potential_Loss']}")
    print(f"Time To Max for {ticker}: {latest_entry['Time_To_Max']} days")
    print(f"Time To Min for {ticker}: {latest_entry['Time_To_Min']} days")

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
            latest_relative_divergence = latest_entry['Relative_Divergence']
            latest_divergence = latest_entry['Divergence']
            delta_previous_relative_divergence = latest_entry.get('Delta_Previous_Relative_Divergence', 0)
            max_potential_profit, max_potential_loss, time_to_max, time_to_min = calculate_potential_profit_and_loss(df, latest_relative_divergence)

            if latest_entry.isna().all():
                print(f"Data for {ticker} is empty or contains only NA values, skipping...")
                continue

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
    # ticker = 'TSLA'
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
        save_simplified_csv(ticker)
    asyncio.run(collect_relative_divergence())

# python get_compare_stock_data.py
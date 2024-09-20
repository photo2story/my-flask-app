# get_compare_stock_data.py

import os
import sys
import pandas as pd
import numpy as np
import requests
import io
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from git_operations import move_files_to_images_folder  # git_operations 모듈에서 함수 가져오기

# GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images"
GITHUB_RAW_BASE_URL = config.STATIC_IMAGES_PATH
folder_path = config.STATIC_IMAGES_PATH

# GitHub에서 CSV 파일을 가져오는 함수
def fetch_csv(ticker):
    url = f"{GITHUB_RAW_BASE_URL}/result_VOO_{ticker}.csv"
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

# CSV 파일을 간소화하고 로컬에 저장하는 함수
async def save_simplified_csv(ticker):
    # CSV 파일 읽기
    df = pd.read_csv(f"{config.STATIC_IMAGES_PATH}/result_VOO_{ticker}.csv")
    
    if df is None:
        print(f"Skipping processing for {ticker} due to missing data.")
        return
    
    if df.empty or len(df) < 20:
        print(f"Not enough data to calculate Bollinger Bands for {ticker}. Minimum 20 data points required.")
        return
    
    # 필요한 열 선택
    df = df[['Date', 'rate', 'rate_vs']]
    
    # 이격도 계산
    df['Divergence'] = df['rate'] - df['rate_vs']
    df['Divergence'] = df['Divergence'].round(2)
    
    # 열 이름 변경
    df = df.rename(columns={'rate': f'rate_{ticker}_5D', 'rate_vs': 'rate_VOO_20D'})
    
    # 상대 이격도 계산
    min_divergence = df['Divergence'].min()
    df['Relative_Divergence'] = ((df['Divergence'] - min_divergence) / (df['Divergence'].cummax() - min_divergence)) * 100
    df['Relative_Divergence'] = df['Relative_Divergence'].round(2)
    
    # max_divergence 값 업데이트
    df['Max_Divergence'] = df['Divergence'].cummax().round(2)
    
    # 이전 상대 이격도 변화량 계산
    df['Delta_Previous_Relative_Divergence'] = df['Relative_Divergence'].diff(periods=20).fillna(0).round(2)
    
    # Expected_Return 필드를 추가
    df['Expected_Return'] = ((100 - df['Relative_Divergence']) / 100 * df['Max_Divergence']).round(2)
    
    # 간소화된 CSV 파일 저장
    simplified_df = df[['Date', f'rate_{ticker}_5D', 'rate_VOO_20D', 'Divergence', 'Relative_Divergence', 
                        'Delta_Previous_Relative_Divergence', 'Max_Divergence', 'Expected_Return']].iloc[::20].reset_index(drop=True)
    
    # 마지막 데이터가 이미 포함되지 않았다면 추가
    if not simplified_df['Date'].iloc[-1] == df['Date'].iloc[-1]:
        last_row = df.iloc[-1]
        simplified_df = pd.concat([simplified_df, last_row.to_frame().T], ignore_index=True)
        
    # simplified_df가 비어있는지 체크
    if simplified_df.empty:
        print(f"Skipping {ticker} because simplified_df is empty.")
        return
    
    # 파일 저장
    folder_path = config.STATIC_IMAGES_PATH
    simplified_file_path = os.path.join(folder_path, f'result_{ticker}.csv')
    simplified_df.to_csv(simplified_file_path, index=False)
    await move_files_to_images_folder()
    print(f"Simplified CSV saved: {simplified_file_path}")
    
    # 최종 데이터 출력
    latest_entry = df.iloc[-1]
    print(f"Current Divergence for {ticker}: {latest_entry['Divergence']} (max {latest_entry['Max_Divergence']}, min {min_divergence})")
    print(f"Current Relative Divergence for {ticker}: {latest_entry['Relative_Divergence']}")
    print(f"Delta Previous Relative Divergence for {ticker}: {latest_entry['Delta_Previous_Relative_Divergence']}")
    print(f"Expected Return for {ticker}: {latest_entry['Expected_Return']}")
    
    # collect_relative_divergence 호출
    await collect_relative_divergence(ticker, simplified_df)

async def collect_relative_divergence(ticker, simplified_df):
    try:
        # 마지막 데이터 추출
        latest_entry = simplified_df.iloc[-1]

        # simplified_df에 있는 값을 바로 참조
        latest_relative_divergence = latest_entry['Relative_Divergence']
        latest_divergence = latest_entry['Divergence']
        delta_previous_relative_divergence = latest_entry.get('Delta_Previous_Relative_Divergence', 0)
        max_divergence = latest_entry['Max_Divergence']  # 계산된 값 가져오기
        expected_return = latest_entry['Expected_Return']  # 계산된 값 가져오기

        # 디버깅 출력을 추가하여 값들을 확인
        print(f"Processing {ticker}:")
        print(f"Latest Divergence: {latest_divergence}")
        print(f"Max Divergence: {max_divergence}")
        print(f"Expected Return: {expected_return}")

        # results_relative_divergence.csv 파일이 존재하면 읽어오기
        results_file_path = os.path.join(config.STATIC_IMAGES_PATH, 'results_relative_divergence.csv')
        
        if os.path.exists(results_file_path):
            results = pd.read_csv(results_file_path)
        else:
            results = pd.DataFrame(columns=['Ticker', 'Divergence', 'Relative_Divergence', 
                                            'Delta_Previous_Relative_Divergence', 'Max_Divergence', 
                                            'Expected_Return'])

        # 기존 티커 제거 (중복 방지)
        print(f"Before removing {ticker}, results size: {len(results)}")
        results = results[results['Ticker'] != ticker]
        print(f"After removing {ticker}, results size: {len(results)}")

        # 새로운 데이터 추가
        new_entry = pd.DataFrame({
            'Ticker': [ticker], 
            'Divergence': [latest_divergence], 
            'Relative_Divergence': [latest_relative_divergence],
            'Delta_Previous_Relative_Divergence': [delta_previous_relative_divergence],
            'Max_Divergence': [max_divergence],
            'Expected_Return': [expected_return]
        })

        # 새로운 데이터가 추가되는지 확인
        updated_results = pd.concat([results, new_entry], ignore_index=True)
        print(f"Added {ticker}, updated results size: {len(updated_results)}")

        # 기대수익으로 정렬하고 랭킹 필드를 추가하여 CSV 저장
        updated_results = updated_results.sort_values(by='Expected_Return', ascending=False).reset_index(drop=True)
        updated_results['Rank'] = updated_results.index + 1  # 랭킹 필드 추가

        # 컬럼 순서를 조정하여 랭킹 필드가 첫 번째로 오도록 설정 (선택 사항)
        cols = ['Rank'] + [col for col in updated_results.columns if col != 'Rank']
        updated_results = updated_results[cols]

        # CSV 파일 저장
        updated_results.to_csv(results_file_path, mode='w', index=False)
        # *** 이미지 파일 등 이동 및 업로드 ***
        await move_files_to_images_folder()
            
        print(f"Updated relative divergence data for {ticker} saved to {results_file_path}")

    except Exception as e:
        print(f"Error processing data for {ticker}: {e}")


if __name__ == "__main__":
    print("Starting data processing...")
    # 비동기 함수는 asyncio.run()을 통해 실행해야 함
    asyncio.run(collect_relative_divergence())
    print("Data processing complete...")



# if __name__ == "__main__":
    # print("Starting data processing...")
    # ticker = 'QQQ'
    # save_simplified_csv(ticker)


#  python get_compare_stock_data.py
# if __name__ == "__main__":
#     import asyncio
#     tickers = [
#         'AAPL', 'MSFT', 'NVDA', 'GOOG', 'AMZN', 'META', 'CRM', 'ADBE', 'AMD', 'ACN', 'QCOM', 'CSCO',
#         'INTU', 'IBM', 'PDD', 'NOW', 'ARM', 'INTC', 'ANET', 'ADI', 'KLAC', 'PANW', 'AMT', 'V', 'MA',
#         'BAC', 'WFC', 'BLK', 'BX', 'GS', 'C', 'KKR', 'TSLA', 'HD', 'NKE', 'MCD', 'SBUX', 'TJX', 'BKNG',
#         'CMG', 'TGT', 'LOW', 'EXPE', 'DG', 'JD', 'LLY', 'UNH', 'ABBV', 'JNJ', 'MRK', 'TMO', 'ABT', 'PFE',
#         'DHR', 'CVS', 'CI', 'GILD', 'AMGN', 'ISRG', 'REGN', 'VRTX', 'HCA', 'GOOGL', 'NFLX', 'DIS', 'VZ',
#         'T', 'CMCSA', 'SPOT', 'TWTR', 'ROKU', 'LYFT', 'UBER', 'EA', 'GE', 'UPS', 'BA', 'CAT', 'MMM', 'HON',
#         'RTX', 'DE', 'LMT', 'NOC', 'UNP', 'WM', 'ETN', 'CSX', 'FDX', 'WMT', 'KO', 'PEP', 'PG', 'COST',
#         'MDLZ', 'CL', 'PM', 'MO', 'KHC', 'HSY', 'KR', 'GIS', 'EL', 'STZ', 'MKC', 'XOM', 'CVX', 'COP', 'EOG',
#         'PSX', 'MPC', 'VLO', 'OKE', 'KMI', 'WMB', 'SLB', 'HAL', 'BKR', 'LIN', 'ALB', 'NEM', 'FMC', 'APD',
#         'CF', 'ECL', 'LYB', 'PPG', 'SHW', 'CE', 'DD', 'AMT', 'PLD', 'EQIX', 'PSA', 'AVB', 'SPG', 'O', 'VICI',
#         'EXR', 'MAA', 'EQR', 'NEE', 'DUK', 'SO', 'AEP', 'EXC', 'D', 'SRE', 'XEL', 'ED', 'ES', 'PEG', 'WEC', 'BTC-USD'
#     ]
#     for ticker in tickers:
#         save_simplified_csv(ticker)
    

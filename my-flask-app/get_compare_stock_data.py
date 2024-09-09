# get_compare_stock_data.py

import os
import sys
import pandas as pd
import numpy as np
import requests
import io

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from git_operations import move_files_to_images_folder  # git_operations 모듈에서 함수 가져오기

# GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com/photo2story/my-flutter-app/main/static/images"
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
def save_simplified_csv(ticker):
    # GitHub에서 데이터를 가져오기 위해 fetch_csv 함수를 사용
    # df = fetch_csv(ticker)
    # result_VOO_{ticker}.csv을 읽어와서 데이터프레임으로 변환
    df= pd.read_csv(f"{config.STATIC_IMAGES_PATH}/result_VOO_{ticker}.csv")
    
    if df is None:
        print(f"Skipping processing for {ticker} due to missing data.")
        return
    
    if df.empty or len(df) < 20:
        print(f"Not enough data to calculate Bollinger Bands for {ticker}. Minimum 20 data points required.")
        return
    
    # 필요한 열만 선택하여 새로운 DataFrame 생성
    df = df[['Date', 'rate', 'rate_vs']]
    # print(df)
    
    # 이격도(Divergence) 계산
    df['Divergence'] = np.round(df['rate'] - df['rate_vs'], 2)
    df = df.rename(columns={'rate': f'rate_{ticker}_5D', 'rate_vs': 'rate_VOO_20D'})
    
    # 상대 이격도(Relative Divergence) 계산
    min_divergence = df['Divergence'].min()
    df['Relative_Divergence'] = np.round(((df['Divergence'] - min_divergence) / (df['Divergence'].cummax() - min_divergence)) * 100, 2)
    
    # max_divergence 값 업데이트
    df['Max_Divergence'] = df['Divergence'].cummax()
    
    # 이전 상대 이격도 변화량(Delta Previous Relative Divergence) 계산
    df['Delta_Previous_Relative_Divergence'] = df['Relative_Divergence'].diff(periods=20).fillna(0).round(2)
    
    # Expected_Return 필드를 추가
    df['Expected_Return'] = ((100 - df['Relative_Divergence']) / 100 * df['Max_Divergence']).round(2)
    
    # 간소화된 CSV를 저장할 로컬 경로 설정 ('result_{ticker}.csv' 파일로 저장)
    simplified_df = df[['Date', f'rate_{ticker}_5D', 'rate_VOO_20D', 'Divergence', 'Relative_Divergence', 'Delta_Previous_Relative_Divergence', 'Max_Divergence', 'Expected_Return']].iloc[::20].reset_index(drop=True)
    # print(simplified_df)
    
    # 마지막 데이터가 이미 포함되지 않았다면 추가
    if not simplified_df['Date'].iloc[-1] == df['Date'].iloc[-1]:
        last_row = df.iloc[-1]
        if last_row[f'rate_{ticker}_5D'] != 0 or last_row['rate_VOO_20D'] != 0:
            simplified_df = pd.concat([simplified_df, last_row.to_frame().T], ignore_index=True)
    
    # 파일 저장
    folder_path = config.STATIC_IMAGES_PATH
    simplified_file_path = os.path.join(folder_path, f'result_{ticker}.csv')
    simplified_df.to_csv(simplified_file_path, index=False)
    print(f"Simplified CSV saved: {simplified_file_path}")

    # 마지막 데이터를 출력
    latest_entry = df.iloc[-1]
    print(f"Current Divergence for {ticker}: {latest_entry['Divergence']} (max {latest_entry['Max_Divergence']}, min {min_divergence})")
    print(f"Current Relative Divergence for {ticker}: {latest_entry['Relative_Divergence']}")
    print(f"Delta Previous Relative Divergence for {ticker}: {latest_entry['Delta_Previous_Relative_Divergence']}")
    print(f"Expected Return for {ticker}: {latest_entry['Expected_Return']}")



import os
import pandas as pd
import asyncio

async def collect_relative_divergence():
    tickers = [stock for sector, stocks in config.STOCKS.items() for stock in stocks]
    results = pd.DataFrame(columns=['Ticker', 'Divergence', 'Relative_Divergence', 
                                    'Delta_Previous_Relative_Divergence', 'Max_Divergence', 
                                    'Expected_Return'])
    
# 상대 이격도 데이터 수집 함수
async def collect_relative_divergence():
    # config.STOCKS에서 모든 티커를 가져옵니다.
    tickers = [stock for sector, stocks in config.STOCKS.items() for stock in stocks]
    
    # 결과를 저장할 데이터프레임 초기화
    results = pd.DataFrame(columns=['Ticker', 'Divergence', 'Relative_Divergence', 
                                    'Delta_Previous_Relative_Divergence', 'Max_Divergence', 
                                    'Expected_Return'])

    # 티커별로 파일을 확인하고 데이터 추출
    for ticker in tickers:
        file_path = os.path.join(folder_path, f"result_{ticker}.csv")
        
        # 파일 존재 여부 확인
        if not os.path.exists(file_path):
            print(f"File for {ticker} does not exist. Skipping...")
            continue

        try:
            # CSV 파일에서 데이터 읽기
            df = pd.read_csv(file_path)
            
            # CSV 파일에 필요한 컬럼이 없거나 데이터가 비어있을 경우 스킵
            if df.empty or 'Relative_Divergence' not in df.columns:
                print(f"Data for {ticker} is not available or missing necessary columns.")
                continue

            # 마지막 행의 데이터를 사용하여 필요한 값 추출
            latest_entry = df.iloc[-1]
            
            # 결측치가 모두 있는 행은 스킵
            if latest_entry.isna().all():
                print(f"Data for {ticker} is empty or contains only NA values, skipping...")
                continue
            
            # 필요한 데이터 추출
            latest_relative_divergence = latest_entry['Relative_Divergence']
            latest_divergence = latest_entry['Divergence']
            delta_previous_relative_divergence = latest_entry.get('Delta_Previous_Relative_Divergence', 0)
            max_divergence = latest_entry['Max_Divergence']
            expected_return = latest_entry['Expected_Return']

            # 결과를 데이터프레임에 추가
            results = pd.concat([results, pd.DataFrame({
                'Ticker': [ticker], 
                'Divergence': [latest_divergence], 
                'Relative_Divergence': [latest_relative_divergence],
                'Delta_Previous_Relative_Divergence': [delta_previous_relative_divergence],
                'Max_Divergence': [max_divergence],
                'Expected_Return': [expected_return]
            })], ignore_index=True)

        except Exception as e:
            print(f"Error processing data for {ticker}: {e}")
            continue
    
    # 결과를 로컬 파일로 저장
    collect_relative_divergence_path = os.path.join(folder_path, 'results_relative_divergence.csv')
    results.to_csv(collect_relative_divergence_path, index=False)

    # 파일을 이미지 폴더로 이동 (비동기 함수로 실행)
    await move_files_to_images_folder()

    return results

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
    

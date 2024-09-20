# get_classify_stock.py
import os
import sys
import pandas as pd
import requests
import io
import matplotlib.pyplot as plt

# 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from git_operations import move_files_to_images_folder

# GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images"
GITHUB_RAW_BASE_URL = config.STATIC_IMAGES_PATH

async def fetch_csv(ticker):
    url = f"{GITHUB_RAW_BASE_URL}/result_{ticker}.csv"
    # try:
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

def classify_stock(rate_avg, divergence_avg, frequency):
    if rate_avg > 0.2:
        if divergence_avg > 0.15:
            return 'HighYield_HighVolatility_HighFrequency' if frequency > 0.5 else 'HighYield_HighVolatility_LowFrequency'
        else:
            return 'HighYield_LowVolatility_HighFrequency' if frequency > 0.5 else 'HighYield_LowVolatility_LowFrequency'
    else:
        if divergence_avg > 0.15:
            return 'LowYield_HighVolatility_HighFrequency' if frequency > 0.5 else 'LowYield_HighVolatility_LowFrequency'
        else:
            return 'LowYield_LowVolatility_HighFrequency' if frequency > 0.5 else 'LowYield_LowVolatility_LowFrequency'

async def collect_and_classify_stocks():
    tickers = [stock for sector, stocks in config.STOCKS.items() for stock in stocks]
    classification_results = []

    for ticker in tickers:
        df = await fetch_csv(ticker)
        if df is not None:
            if f'rate_{ticker}_5D' in df.columns and 'Divergence' in df.columns:
                rate_avg = df[f'rate_{ticker}_5D'].mean()
                divergence_avg = df['Divergence'].mean()
                frequency = (df['Relative_Divergence'] > 50).mean()

                classification = classify_stock(rate_avg, divergence_avg, frequency)
                classification_results.append({'Ticker': ticker, 'Rate': rate_avg, 'Divergence': divergence_avg, 'Frequency': frequency, 'Classification': classification})
            else:
                print(f"Data for {ticker} is not available or missing necessary columns.")
        else:
            print(f"Failed to fetch data for {ticker} or no data found.")
    
    classification_df = pd.DataFrame(classification_results)
    classification_df.to_csv('stock_classification.csv', index=False)
    print(classification_df)
    
    # 히트맵 생성
    create_custom_plot(classification_df)
    
    # 파일 이동 및 깃 커밋 푸시 작업
    await move_files_to_images_folder()

def create_custom_plot(df):
    plt.figure(figsize=(12, 8))
    for index, row in df.iterrows():
        font_size = 10 + (row['Rate'] / df['Rate'].max()) * 20
        plt.text(row['Frequency'], row['Divergence'], row['Ticker'], fontsize=font_size, ha='center', va='center')
    
    plt.xlabel('Frequency')
    plt.ylabel('Divergence')
    plt.title('Stocks Classification: Frequency vs Divergence with Rate Size')
    plt.grid(True)
    plt.savefig('stock_classification_plot.png')
    plt.show()

if __name__ == "__main__":
    import asyncio
    asyncio.run(collect_and_classify_stocks())

# python get_classify_stock.py
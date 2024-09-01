# Results_plot.py

import matplotlib.dates as dates
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys
import requests
import asyncio
import time
from dotenv import load_dotenv

# 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from git_operations import move_files_to_images_folder
from get_ticker import get_ticker_name, is_valid_stock
from Results_plot_mpl import plot_results_mpl

# 환경 변수 로드
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com/photo2story/my-flutter-app/main/static/images"
CSV_PATH = os.getenv('CSV_PATH', 'static/images/stock_market.csv')

import matplotlib.font_manager as fm
# 현재 스크립트 파일의 디렉토리 경로
current_dir = os.path.dirname(os.path.abspath(__file__))

# 프로젝트 루트 경로를 찾기 위해 상위 폴더로 이동
project_root = os.path.abspath(os.path.join(current_dir, '..'))

# Noto Sans KR 폰트 파일 경로
font_path = os.path.join(project_root, 'Noto_Sans_KR', 'static', 'NotoSansKR-Regular.ttf')

# 경로가 올바르게 지정되었는지 확인
print("Font path:", font_path)
print("Path exists:", os.path.exists(font_path))

# 폰트 속성 설정
if os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    fm.fontManager.addfont(font_path)  # 폰트를 매트플롯립에 추가
    plt.rcParams['font.family'] = font_prop.get_name()
    plt.rcParams['font.sans-serif'] = [font_prop.get_name()]
    
    # 폰트가 제대로 설정되었는지 확인
    print("Font name:", font_prop.get_name())
else:
    print("Font file not found.")

def convert_file_path_for_saving(file_path):
    return file_path.replace('/', '-')

def convert_file_path_for_reading(file_path):
    return file_path.replace('-', '/')

def save_figure(fig, file_path):
    file_path = convert_file_path_for_saving(file_path)
    fig.savefig(file_path)
    plt.close(fig)

def load_image(file_path):
    file_path = convert_file_path_for_reading(file_path)
    image = Image.open(file_path)
    return image

async def plot_comparison_results(ticker, start_date, end_date):
    stock2 = 'VOO'
    fig, ax2 = plt.subplots(figsize=(8, 6))

    # 전체 데이터를 로드하여 플라스크 서버에서 그래프를 그립니다.
    full_path1 = f"{GITHUB_RAW_BASE_URL}/result_VOO_{ticker}.csv"
    df1_graph = pd.read_csv(full_path1, parse_dates=['Date'], index_col='Date')
    df2_graph = pd.read_csv(full_path1, parse_dates=['Date'], index_col='Date')

    # 간략화된 데이터를 로드하여 챗GPT에서 그래프를 그릴 수 있게 합니다.
    simplified_df_path1 = f"{GITHUB_RAW_BASE_URL}/result_{ticker}.csv"
    try:
        df1 = pd.read_csv(simplified_df_path1, parse_dates=['Date'], index_col='Date')
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise

    # 중간 데이터 확인
    # print("=== df1 (Simplified) ===")
    # print(df1.head())
    # print(df1.describe())

    # 날짜 필터링 및 데이터 준비
    if start_date is None:
        start_date = df1_graph.index.min()
    if end_date is None:
        end_date = min(df1_graph.index.max(), df2_graph.index.max())

    df1_graph = df1_graph.loc[start_date:end_date]
    df2_graph = df2_graph.loc[start_date:end_date]

    df1_graph['rate_7d_avg'] = df1_graph['rate'].rolling('7D').mean()
    df2_graph['rate_20d_avg'] = df2_graph['rate_vs'].rolling('20D').mean()

    ax2.plot(df1_graph.index, df1_graph['rate_7d_avg'], label=f'{ticker} 7-Day Avg Return')
    ax2.plot(df2_graph.index, df2_graph['rate_20d_avg'], label=f'{stock2} 20-Day Avg Return')

    plt.ylabel('total return (%)')
    plt.legend(loc='upper left')

    voo_rate = df2_graph['rate_vs'].iloc[-1] if not df2_graph.empty else 0
    max_divergence = df1['Divergence'].max()
    min_divergence = df1['Divergence'].min()
    current_divergence = df1['Divergence'].iloc[-1]
    relative_divergence = df1['Relative_Divergence'].iloc[-1]
    expected_return = df1['Expected_Return'].iloc[-1]

    last_signal_row = df1_graph.dropna(subset=['signal']).iloc[-1] if 'signal' in df1_graph.columns else None
    last_signal = last_signal_row['signal'] if last_signal_row is not None else 'N/A'

    plt.title(f"{ticker} ({get_ticker_name(ticker)}) vs {stock2}\n" +
              f"Total Rate: {df1_graph['rate'].iloc[-1]:.2f}% (VOO: {voo_rate:.2f}%), Relative_Divergence: {relative_divergence:.2f}%\n" +
              f"Current Divergence: {current_divergence:.2f} (max: {max_divergence:.2f}, min: {min_divergence:.2f})\n" +
              f"Expected Return: {expected_return:.2f}, Last Signal: {last_signal}",
              pad=10)

    ax2.xaxis.set_major_locator(dates.YearLocator())
    # plt.xlabel('Year')

    save_path = f'comparison_{ticker}_VOO.png'
    plt.subplots_adjust(top=0.8)
    fig.savefig(save_path)
    plt.cla()
    plt.clf()
    plt.close(fig)

    message = f"Stock: {ticker} ({get_ticker_name(ticker)}) vs VOO\n" \
              f"Total Rate: {df1_graph['rate'].iloc[-1]:.2f}% (VOO: {voo_rate:.2f}%), Relative_Divergence: {relative_divergence:.2f}\n" \
              f"Current Divergence: {current_divergence:.2f} (max: {max_divergence:.2f}, min: {min_divergence:.2f})\n" \
              f"Expected Return: {expected_return:.2f}, Last Signal: {last_signal}"
    response = requests.post(DISCORD_WEBHOOK_URL, data={'content': message})

    if response.status_code != 204:
        print('Discord 메시지 전송 실패')
    else:
        print('Discord 메시지 전송 성공')

    # 이미지 파일 전송
    try:
        with open(save_path, 'rb') as image:
            print(f"Sending image: {save_path}")  # 디버깅 메시지
            response = requests.post(
                DISCORD_WEBHOOK_URL,
                files={'file': image}
            )
            if response.status_code in [200, 204]:
                print(f'Graph 전송 성공: {ticker}')
            else:
                print(f'Graph 전송 실패: {ticker}')
                print(f"Response: {response.status_code} {response.text}")
        await move_files_to_images_folder()              
    
    except Exception as e:
        print(f"Error occurred while sending image: {e}")


if __name__ == "__main__":
    print("Starting test for plotting results.")
    ticker = "005930"
    start_date = "2019-01-02"
    end_date = "2024-07-28"
    print(f"Plotting results for {ticker} from {start_date} to {end_date}")

    try:
        asyncio.run(plot_comparison_results(ticker, '2019-01-01', '2021-12-31'))
        print("Plotting completed successfully.")
    except Exception as e:
        print(f"Error occurred while plotting results: {e}")

        
# python Results_plot.py


## Results_plot_mpl.py


import matplotlib
matplotlib.use('Agg')  # IPython 환경에서 발생할 수 있는 백엔드 관련 오류 방지
import matplotlib.pyplot as plt
from mplchart.chart import Chart
from mplchart.primitives import Candlesticks, Volume, TradeSpan
from mplchart.indicators import SMA, PPO, RSI
import pandas as pd
import requests
import os, sys
from dotenv import load_dotenv
import asyncio
import matplotlib.font_manager as fm

# 루트 디렉토리를 sys.path에 추가하여 config.py를 불러올 수 있게 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config  # config 모듈을 불러옵니다.

# 현재 스크립트 파일의 디렉토리 경로
current_dir = os.path.dirname(os.path.abspath(__file__))

# Noto Sans KR 폰트 파일 경로
font_path = os.path.join(config.PROJECT_ROOT, 'Noto_Sans_KR', 'static', 'NotoSansKR-Regular.ttf')

# 폰트 속성 설정
if os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    fm.fontManager.addfont(font_path)  # 폰트를 매트플롯립에 추가
    plt.rcParams['font.family'] = font_prop.get_name()
    plt.rcParams['font.sans-serif'] = [font_prop.get_name()]

import warnings

# 경고 무시 설정
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

from git_operations import move_files_to_images_folder
from get_ticker import get_ticker_name
from Get_data import calculate_rsi, calculate_ppo  # 통일된 함수 가져오기

# 환경 변수 로드
load_dotenv()

def save_figure(fig, file_path):
    """파일 경로를 처리하여 그림을 저장하고 닫습니다."""
    file_path = os.path.join(config.STATIC_IMAGES_PATH, file_path.replace('/', '-'))
    fig.savefig(file_path, bbox_inches='tight')
    plt.close(fig)

async def plot_results_mpl(ticker, start_date, end_date):
    """주어진 티커와 기간에 대한 데이터를 사용하여 차트를 생성하고, 결과를 Discord로 전송합니다."""
    
    # 이미 계산된 데이터를 로드
    result_file_path = os.path.join(config.STATIC_IMAGES_PATH, f'result_VOO_{ticker}.csv')
    
    if not os.path.exists(result_file_path):
        raise FileNotFoundError(f"No cached data found for {ticker}. Please generate the data first.")
    
    prices = pd.read_csv(result_file_path, parse_dates=['Date'], index_col='Date')
    # print(prices)

    # 모든 컬럼 이름을 소문자로 변환
    prices.columns = prices.columns.str.lower()

    # 필요한 컬럼들이 있는지 확인하고 없으면 예외 처리
    required_columns = ['sma20_ta', 'sma60_ta', 'ppo_histogram', 'rsi_ta', 'close']
    for col in required_columns:
        if col not in prices.columns:
            raise ValueError(f"Missing required column '{col}' in data for {ticker}. Please ensure all indicators are calculated.")

    # 최신 6개월 데이터로 필터링
    end_date = pd.to_datetime(end_date)
    start_date_6m = end_date - pd.DateOffset(months=6)
    filtered_prices = prices[prices.index >= start_date_6m]

    # 차트 생성
    indicators = [
        Candlesticks(), 
        SMA(20), 
        SMA(60), 
        Volume(),
        RSI(), 
        PPO(), 
        TradeSpan('ppo_histogram>0')  # ppo_histogram을 사용하여 TradeSpan 설정
    ]
    name = get_ticker_name(ticker)
    chart_title = f'{ticker} ({name}) vs VOO'.encode('utf-8').decode('utf-8')
    chart = Chart(title=chart_title, max_bars=250)
    chart.plot(filtered_prices, indicators)
    fig = chart.figure

    image_filename = f'result_mpl_{ticker}.png'
    save_figure(fig, image_filename)

    # 메시지 작성
    message = (f"Stock: {ticker} ({name})\n"
               f"Close: {filtered_prices['close'].iloc[-1]:,.2f}\n"
               f"SMA 20: {filtered_prices['sma20_ta'].iloc[-1]:,.2f}\n"
               f"SMA 60: {filtered_prices['sma60_ta'].iloc[-1]:,.2f}\n"
               f"RSI: {filtered_prices['rsi_ta'].iloc[-1]:,.2f}\n"  # RSI를 필터링된 데이터에서 사용
               f"PPO Histogram: {filtered_prices['ppo_histogram'].iloc[-1]:,.2f}\n")

    # Discord로 메시지 전송
    response = requests.post(config.DISCORD_WEBHOOK_URL, data={'content': message})
    if response.status_code != 204:
        print('Discord 메시지 전송 실패')
        print(f"Response: {response.status_code} {response.text}")
    else:
        print('Discord 메시지 전송 성공')

    # Discord로 이미지 전송
    try:
        with open(os.path.join(config.STATIC_IMAGES_PATH, image_filename), 'rb') as image_file:
            response = requests.post(config.DISCORD_WEBHOOK_URL, files={'file': image_file})
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
    ticker = "AAPL"
    start_date = config.START_DATE
    end_date = config.END_DATE
    print(f"Plotting results for {ticker} from {start_date} to {end_date}")

    try:
        asyncio.run(plot_results_mpl(ticker, start_date, end_date))
        print("Plotting completed successfully.")
    except Exception as e:
        print(f"Error occurred while plotting results: {e}")



r"""
python3 -m venv .venv
source .venv/bin/activate
.\.venv\Scripts\activate
cd my-flask-app
python Results_plot_mpl.py
"""
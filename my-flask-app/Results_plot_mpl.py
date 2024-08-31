## Results_plot_mpl.py


import matplotlib
matplotlib.use('Agg')  # IPython 환경에서 발생할 수 있는 백엔드 관련 오류 방지
import matplotlib.pyplot as plt
from mplchart.chart import Chart
from mplchart.primitives import Candlesticks, Volume, TradeSpan
from mplchart.indicators import SMA, PPO, RSI
import pandas as pd
import requests
import FinanceDataReader as fdr
import os, sys
from dotenv import load_dotenv
import asyncio
import matplotlib.font_manager as fm

# 현재 스크립트 파일의 디렉토리 경로
current_dir = os.path.dirname(os.path.abspath(__file__))

# Noto Sans KR 폰트 파일 경로 (Regular 스타일 사용)
font_path = os.path.join(current_dir, '..', 'Noto_Sans_KR', 'NotoSansKR-Regular.ttf')

# 폰트 속성 설정
font_prop = fm.FontProperties(fname=font_path)

# Matplotlib 기본 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans KR'
plt.rcParams['font.sans-serif'] = ['Noto Sans KR']

import warnings

# 경고 무시 설정
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

# 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from git_operations import move_files_to_images_folder
from get_ticker import get_ticker_name
from Get_data import calculate_rsi, calculate_ppo  # 통일된 함수 가져오기

# 환경 변수 로드
load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

def save_figure(fig, file_path):
    """파일 경로를 처리하여 그림을 저장하고 닫습니다."""
    file_path = file_path.replace('/', '-')
    fig.savefig(file_path, bbox_inches='tight')
    plt.close(fig)

async def plot_results_mpl(ticker, start_date, end_date):
    """주어진 티커와 기간에 대한 데이터를 사용하여 차트를 생성하고, 결과를 Discord로 전송합니다."""
    prices = fdr.DataReader(ticker, start_date, end_date)
    prices.dropna(inplace=True)
    
    # 이동 평균 계산 (전체 데이터를 사용)
    prices['SMA20'] = prices['Close'].rolling(window=20).mean()
    prices['SMA60'] = prices['Close'].rolling(window=60).mean()

    # PPO 계산 (통일된 함수 사용)
    prices['PPO_value'], prices['PPO_signal'], prices['PPO_histogram'] = calculate_ppo(prices['Close'])

    # RSI 계산 (통일된 함수 사용)
    prices['RSI'] = calculate_rsi(prices['Close'])

    # 최신 6개월 데이터로 필터링
    end_date = pd.to_datetime(end_date)
    start_date_6m = end_date - pd.DateOffset(months=6)
    filtered_prices = prices[prices.index >= start_date_6m]

    # 차트 생성
    indicators = [
        Candlesticks(), SMA(20), SMA(60), Volume(),
        RSI(), PPO(), TradeSpan('ppohist>0')
    ]
    name = get_ticker_name(ticker)
    chart_title = f'{ticker} ({name}) vs VOO'.encode('utf-8').decode('utf-8')
    chart = Chart(title=chart_title, max_bars=250)
    chart.plot(filtered_prices, indicators)
    fig = chart.figure
    # fig.tight_layout()  # 레이아웃 조정 추가
    image_filename = f'result_mpl_{ticker}.png'
    save_figure(fig, image_filename)

    # 메시지 작성
    message = (f"Stock: {ticker} ({name})\n"
               f"Close: {filtered_prices['Close'].iloc[-1]:,.2f}\n"
               f"SMA 20: {filtered_prices['SMA20'].iloc[-1]:,.2f}\n"
               f"SMA 60: {filtered_prices['SMA60'].iloc[-1]:,.2f}\n"
               f"RSI: {filtered_prices['RSI'].iloc[-1]:,.2f}\n"  # RSI 추가
               f"PPO Histogram: {filtered_prices['PPO_histogram'].iloc[-1]:,.2f}\n")

    # Discord로 메시지 전송
    response = requests.post(DISCORD_WEBHOOK_URL, data={'content': message})
    if response.status_code != 204:
        print('Discord 메시지 전송 실패')
        print(f"Response: {response.status_code} {response.text}")
    else:
        print('Discord 메시지 전송 성공')

    # Discord로 이미지 전송
    try:
        with open(image_filename, 'rb') as image_file:
            response = requests.post(DISCORD_WEBHOOK_URL, files={'file': image_file})
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
        asyncio.run(plot_results_mpl(ticker, '2021-01-01', '2021-12-31'))
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
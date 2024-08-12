# gemini.py

import os
import sys
import pandas as pd
import requests
from dotenv import load_dotenv
import google.generativeai as genai
import shutil
import asyncio
from datetime import datetime  # 추가된 부분

# 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from git_operations import move_files_to_images_folder
from get_earning import get_recent_eps_and_revenue
from get_earning_fmp import get_recent_eps_and_revenue_fmp

# 환경 변수 로드
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
FMP_API_KEY = os.getenv('FMP_API_KEY')
GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com/photo2story/my-flutter-app/main/static/images"
CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'stock_market.csv'))

# Gemini API 구성
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# CSV 파일에서 티커명과 회사 이름을 매핑하는 딕셔너리 생성
def create_ticker_to_name_dict(csv_path):
    df = pd.read_csv(csv_path)
    ticker_to_name = dict(zip(df['Symbol'], df['Name']))
    return ticker_to_name

# 기존에 있는 create_ticker_to_name_dict 함수에 있는 df 출력문을 제거합니다.
ticker_to_name = create_ticker_to_name_dict(CSV_PATH)

def download_csv(ticker):
    ticker_vs_voo_url = f"{GITHUB_RAW_BASE_URL}/result_VOO_{ticker}.csv"
    simplified_ticker_url = f"{GITHUB_RAW_BASE_URL}/result_{ticker}.csv"
    response_ticker = requests.get(ticker_vs_voo_url)
    response_simplified = requests.get(simplified_ticker_url)

    if response_ticker.status_code == 200 and response_simplified.status_code == 200:
        with open(f'result_VOO_{ticker}.csv', 'wb') as f:
            f.write(response_ticker.content)
        with open(f'result_{ticker}.csv', 'wb') as f:
            f.write(response_simplified.content)
        return True
    else:
        return False

def format_earnings_text(earnings_data):
    if not earnings_data:
        return "No earnings data available."

    has_revenue = any(isinstance(entry, tuple) and len(entry) >= 4 for entry in earnings_data)

    if has_revenue:
        earnings_text = "| 날짜 | EPS | 매출 |\n|---|---|---|\n"
    else:
        earnings_text = "| 날짜 | EPS | 예상 EPS |\n|---|---|---|\n"

    for entry in earnings_data:
        if isinstance(entry, tuple):
            if has_revenue:
                if len(entry) == 5:
                    end, filed, actual_eps, revenue, estimated_revenue = entry
                    earnings_text += f"| {filed} | {actual_eps} | {revenue / 1e9:.2f} B$ |\n"
                elif len(entry) == 4:
                    end, filed, actual_eps, revenue = entry
                    earnings_text += f"| {filed} | {actual_eps} | {revenue / 1e9:.2f} B$ |\n"
            else:
                if len(entry) == 3:
                    end, actual_eps, estimated_eps = entry
                    earnings_text += f"| {end} | {actual_eps} | {estimated_eps} |\n"
                else:
                    earnings_text += "| Invalid data format |\n"
        else:
            earnings_text += "| Invalid data format |\n"
    
    return earnings_text

async def analyze_with_gemini(ticker):
    try:
        start_message = f"Starting analysis for {ticker}"
        print(start_message)
        requests.post(DISCORD_WEBHOOK_URL, data={'content': start_message})

        if not download_csv(ticker):
            error_message = f'Error: The file for {ticker} does not exist.'
            print(error_message)
            requests.post(DISCORD_WEBHOOK_URL, data={'content': error_message})
            return

        voo_file = f'result_VOO_{ticker}.csv'
        simplified_file = f'result_{ticker}.csv'
        df_voo = pd.read_csv(voo_file)
        df_simplified = pd.read_csv(simplified_file)

        final_rate = df_voo['rate'].iloc[-1]
        final_rate_vs = df_voo['rate_vs'].iloc[-1]
        Close = df_voo['Close'].iloc[-1]
        sma_5 = df_voo['sma05_ta'].iloc[-1]
        sma_20 = df_voo['sma20_ta'].iloc[-1]
        sma_60 = df_voo['sma60_ta'].iloc[-1]
        rsi = df_voo['rsi_ta'].iloc[-1]
        ppo = df_voo['ppo_histogram'].iloc[-1]

        max_divergence = df_simplified['Divergence'].max()
        min_divergence = df_simplified['Divergence'].min()
        current_divergence = df_simplified['Divergence'].iloc[-1]
        relative_divergence = df_simplified['Relative_Divergence'].iloc[-1]
        delta_Previous_Relative_Divergence = df_simplified['Delta_Previous_Relative_Divergence'].iloc[-1]

        recent_earnings = get_recent_eps_and_revenue(ticker)
        if recent_earnings is None or all(entry[3] is None for entry in recent_earnings):
            print(f"Primary data source failed for {ticker}, attempting secondary source...")
            recent_earnings = get_recent_eps_and_revenue_fmp(ticker)
            if recent_earnings is None:
                raise Exception("No recent earnings data found from secondary source.")
                
        print(f"Recent earnings data for {ticker}: {recent_earnings}")
        
        earnings_text = format_earnings_text(recent_earnings)
        print(f"Earnings Text for {ticker}: {earnings_text}")

        prompt_voo = f"""
        1) 제공된 자료의 수익율(rate)와 S&P 500(VOO)의 수익율(rate_vs)과 비교해서 이격된 정도를 알려줘 (간단하게 자료 맨마지막날의 누적수익율차이):
           리뷰할 주식티커명 = {ticker}
           회사이름과 회사 개요 설명해줘(1줄로)
           리뷰주식의 누적수익률 = {final_rate}
           기준이 되는 비교주식(S&P 500, VOO)의 누적수익율 = {final_rate_vs}
           이격도 (max: {max_divergence}, min: {min_divergence}, 현재: {current_divergence}, 상대이격도: {relative_divergence})

        2) 제공된 자료의 최근 주가 변동(간단하게: 5일, 20일, 60일 이동평균 수치로):
           종가 = {Close}
           5일이동평균 = {sma_5}
           20일이동평균 = {sma_20}
           60일이동평균 = {sma_60}
        3) 제공된 자료의 RSI, PPO 인덱스 지표와 delta_Previous_Relative_Divergence를 분석해줘 (간단하게):
           RSI = {rsi}
           PPO = {ppo}
           최근 상대이격도 변화량 = {delta_Previous_Relative_Divergence} , (-): 단기하락, (+): 단기상승
        4) 최근 실적 및 전망: 제공된 자료의 실적을 분석해줘(간단하게)
           실적 = {earnings_text} 표로 제공된 실적을 분석해줘
           가장 최근 실적은 예상치도 함께 포함해서 검토해줘
        5) 종합적으로 분석해줘(1~4번까지의 요약)
        6) 레포트는 한글로 만들어줘
        """
        
        print(f"Sending prompt to Gemini API for {ticker}")
        response_ticker = model.generate_content(prompt_voo)
        
        report_text = f"{datetime.now().strftime('%Y-%m-%d')} - Analysis Report\n" + response_ticker.text
        # print(report_text)

        success_message = f"Gemini API 분석 완료: {ticker}\n{report_text}"
        print(success_message)
        requests.post(DISCORD_WEBHOOK_URL, json={'content': success_message})

        report_file = f'report_{ticker}.txt'
        destination_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images'))
        report_file_path = os.path.join(destination_dir, report_file)

        # 기존 파일이 있을 경우 삭제하지 않고 덮어쓰기 모드로 파일을 열어 작성
        with open(report_file_path, 'w', encoding='utf-8') as file:
            file.write(report_text)

        # 필요한 파일들을 이동
        shutil.move(voo_file, os.path.join(destination_dir, voo_file))
        await move_files_to_images_folder()


        return f'Gemini Analysis for {ticker} (VOO) has been sent to Discord and saved as a text file.'

    except Exception as e:
        error_message = f"{ticker} 분석 중 오류 발생: {e}"
        print(error_message)
        requests.post(DISCORD_WEBHOOK_URL, data={'content': error_message})

# 환경 변수 로드
load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com/photo2story/my-flutter-app/main/static/images"

async def send_report_to_discord(ticker):
    """기존에 생성된 보고서를 Discord로 전송합니다."""
    try:
        report_file_url = f"{GITHUB_RAW_BASE_URL}/report_{ticker}.txt"
        response = requests.get(report_file_url)
        response.raise_for_status()
        report_text = response.text
        success_message = f"Existing Gemini Analysis for {ticker}:\n{report_text}"
        print(success_message)
        requests.post(DISCORD_WEBHOOK_URL, data={'content': success_message})
    except requests.exceptions.RequestException as e:
        error_message = f"Error retrieving report for {ticker}: {e}"
        print(error_message)
        requests.post(DISCORD_WEBHOOK_URL, data={'content': error_message})
    except Exception as e:
        error_message = f"Error sending report to Discord: {e}"
        print(error_message)
        requests.post(DISCORD_WEBHOOK_URL, data={'content': error_message})


if __name__ == '__main__':
    ticker = 'NVDA'
    asyncio.run(send_report_to_discord(ticker))




# source .venv/bin/activate
# python gemini.py     
 

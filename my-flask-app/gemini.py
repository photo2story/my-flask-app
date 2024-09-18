# gemini.py

import os
import sys
import pandas as pd
import requests
from dotenv import load_dotenv
import google.generativeai as genai
import shutil
import asyncio
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from git_operations import move_files_to_images_folder
from get_earning import get_recent_eps_and_revenue
from get_earning_fmp import get_recent_eps_and_revenue_fmp

# 프로젝트 루트 경로 설정
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# static/images 폴더 경로 설정 (프로젝트 루트 기준)
STATIC_IMAGES_PATH = os.path.join(PROJECT_ROOT, 'static', 'images')

# 기타 CSV 파일 경로 설정
CSV_PATH = os.path.join(STATIC_IMAGES_PATH, 'stock_market.csv')

# 환경 변수 로드
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
FMP_API_KEY = os.getenv('FMP_API_KEY')

# Google Generative AI 설정
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 주식 티커와 이름 매칭 딕셔너리 생성
def create_ticker_to_name_dict(csv_path):
    df = pd.read_csv(csv_path)
    ticker_to_name = dict(zip(df['Symbol'], df['Name']))
    return ticker_to_name

# CSV 파일에서 티커 정보를 읽어옴
ticker_to_name = create_ticker_to_name_dict(CSV_PATH)

# CSV 파일을 다운로드 대신 로컬 폴더에서 찾는 함수
def download_csv(ticker):
    # GitHub 대신 로컬 폴더 경로에서 CSV 파일을 찾음
    ticker_vs_voo_path = os.path.join(STATIC_IMAGES_PATH, f'result_VOO_{ticker}.csv')
    simplified_ticker_path = os.path.join(STATIC_IMAGES_PATH, f'result_{ticker}.csv')

    # 파일이 존재하는지 확인
    if os.path.exists(ticker_vs_voo_path) and os.path.exists(simplified_ticker_path):
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

        company_name = ticker_to_name.get(ticker, "Unknown Company")
        
        # 로컬에서 CSV 파일을 읽어옴
        voo_file = os.path.join(STATIC_IMAGES_PATH, f'result_VOO_{ticker}.csv')
        simplified_file = os.path.join(STATIC_IMAGES_PATH, f'result_{ticker}.csv')

        # voo_file을 읽어옴
        try:
            df_voo = pd.read_csv(voo_file)
        except FileNotFoundError:
            print(f"{voo_file} 파일을 찾을 수 없습니다.")
            return

        # simplified_file을 읽어옴
        try:
            df_simplified = pd.read_csv(simplified_file)
        except FileNotFoundError:
            print(f"{simplified_file} 파일을 찾을 수 없습니다.")
            return

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
        
        Expected_Return = df_simplified['Expected_Return'].iloc[-1]

        earnings_text = "No earnings data available."  # 기본값 설정

        try:
            recent_earnings = get_recent_eps_and_revenue(ticker)
            if recent_earnings is None or all(entry[3] is None for entry in recent_earnings):
                print(f"Primary data source failed for {ticker}, attempting secondary source...")
                recent_earnings = get_recent_eps_and_revenue_fmp(ticker)
                if recent_earnings is not None:
                    earnings_text = format_earnings_text(recent_earnings)
            else:
                earnings_text = format_earnings_text(recent_earnings)
        except Exception as e:
            print(f"No earnings data found for {ticker}. Skipping earnings section. Error: {e}")

        print(f"Earnings Text for {ticker}: {earnings_text}")

        prompt_voo = f"""
       1) 제공된 자료의 수익율(rate)와 S&P 500(VOO)의 수익율(rate_vs)과 비교해서 이격된 정도를 알려줘 (간단하게 자료 맨마지막날의 누적수익율차이):
           리뷰할 주식티커명 = {ticker}
           회사이름 = {company_name}과 회사 개요 설명해줘(1줄로)
           리뷰주식의 누적수익률 = {final_rate}
           기준이 되는 비교주식(S&P 500, VOO)의 누적수익율 = {final_rate_vs}
           이격도 (max: {max_divergence}, min: {min_divergence}, 현재: {current_divergence}, 상대이격도: {relative_divergence})
           (상대이격도는 최소~최대 변동폭을 100으로 했을 때 현재의 위치를 나타내고 있어, 예를 들면 상대이격도 90이면 비교주식(S&P 500, VOO)보다 90% 더 우월하다는 것이 아니라 과거 데이터의 90% 위치한다는 의미야)
        2) 제공된 자료의 최근 주가 변동(간단하게: 5일, 20일, 60일 이동평균 수치로):
           종가 = {Close}
           5일이동평균 = {sma_5}
           20일이동평균 = {sma_20}
           60일이동평균 = {sma_60}
        3) 제공된 자료의 RSI, PPO 인덱스 지표와 Delta_Previous_Relative_Divergence,Expected_Return 을 분석해줘 (간단하게):
           RSI = {rsi}
           PPO = {ppo}
           최근(20일) 상대이격도 변화량 = {delta_Previous_Relative_Divergence} , (-): 단기하락, (+): 단기상승
           기대수익(%) = {Expected_Return}, 현재 적립 투자금액에 대한 최대 5년 예상 기대 수익율
        4) 최근 실적 및 전망: 제공된 자료의 실적을 분석해줘(간단하게)
           실적 = {earnings_text} 표로 제공된 실적을 분석해줘
           가장 최근 실적은 예상치도 함께 포함해서 검토해줘
        5) 종합적으로 분석해줘(1~4번까지의 요약)
        6) 레포트는 영어로 만들어줘
        """

        print(f"Sending prompt to Gemini API for {ticker}")
        response_ticker = model.generate_content(prompt_voo)
        
        # Split the report into two parts
        report_text = f"{datetime.now().strftime('%Y-%m-%d')} - Analysis Report\n" + response_ticker.text
        part1 = report_text[:2000]  # First part (1~3)
        part2 = report_text[2000:]  # Second part (4~6)

        # Send the first part to Discord
        print(f"Sending part 1 to Discord for {ticker}")
        requests.post(DISCORD_WEBHOOK_URL, json={'content': part1})

        # Send the second part to Discord
        print(f"Sending part 2 to Discord for {ticker}")
        requests.post(DISCORD_WEBHOOK_URL, json={'content': part2})

        # Save the full report to a text file
        report_file = f'report_{ticker}.txt'
        destination_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images'))
        report_file_path = os.path.join(destination_dir, report_file)

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

if __name__ == '__main__':
    ticker = '006400'
    asyncio.run(analyze_with_gemini(ticker))

# source .venv/bin/activate
# python gemini.py     
 
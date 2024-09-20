# gpt.py
import os
import pandas as pd
import requests
from io import StringIO
from dotenv import load_dotenv
import openai
from git_operations import move_files_to_images_folder
import config

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
# GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images"
GITHUB_RAW_BASE_URL =config.STATIC_IMAGES_PATH
# CSV_PATH = os.getenv('CSV_PATH', 'static/images/stock_market.csv')
CSV_PATH = config.CSV_PATH

# OpenAI API 구성
openai.api_key = OPENAI_API_KEY

# CSV 파일에서 티커명과 회사 이름, 개요를 매핑하는 딕셔너리 생성
def create_ticker_to_info_dict(csv_path):
    df = pd.read_csv(csv_path)
    ticker_to_info = dict(zip(df['Symbol'], zip(df['Name'])))
    return ticker_to_info

ticker_to_info = create_ticker_to_info_dict(CSV_PATH)

def download_csv(ticker):
    ticker_vs_voo_url = f"{GITHUB_RAW_BASE_URL}/result_VOO_{ticker}.csv"
    response = requests.get(ticker_vs_voo_url)

    if response.status_code == 200:
        with open(f'result_VOO_{ticker}.csv', 'wb') as f:
            f.write(response.content)
        return True
    else:
        return False

def fetch_dynamic_data(ticker):
    # OpenAI GPT-4를 사용하여 동적인 데이터를 생성합니다.
    prompt = f"""
    제공된 자료의 수익율(rate)와 S&P 500(VOO)의 수익율(rate_vs)과 비교해서 이격된 정도를 알려줘:
    리뷰할 주식티커명 = {ticker}

    회사이름과 회사 개요(1줄로)

    제공된 자료의 최근 주가 변동(간단하게: 5일, 20일, 60일 이동평균 수치로):

    제공된 자료의 RSI, PPO 인덱스 지표를 분석해줘 (간단하게):

    최근 실적 및 전망(최근 뉴스 웹검색해서 간단하게: 올해 매출 실적/예측, 주당 순이익/예측, 다음 분기 전망)

    애널리스트 의견(최근 뉴스 웹검색해서 간단하게: 올해 애널리스트 buy? sell?)

    레포트는 ["candidates"][0]["content"]["parts"][0]["text"]의 구조의 텍스트로 만들어줘

    레포트는 한글로 만들어줘
    """
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=500
    )
    dynamic_data = response.choices[0].text.strip()
    return dynamic_data

def generate_stock_report(ticker, dynamic_data):
    # CSV 데이터 가져오기
    url = f"https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/result_VOO_{ticker}.csv"
    response = requests.get(url)
    df = pd.read_csv(StringIO(response.text))
    
    # 필요한 데이터 추출
    final_rate = df['rate'].iloc[-1]
    final_rate_vs = df['rate_vs'].iloc[-1]
    sma_5 = df['sma05_ta'].iloc[-1]
    sma_20 = df['sma20_ta'].iloc[-1]
    sma_60 = df['sma60_ta'].iloc[-1]
    rsi = df['rsi_ta'].iloc[-1]
    ppo = df['ppo_histogram'].iloc[-1]

    # 회사 이름과 개요 가져오기
    company_name, company_overview = ticker_to_info.get(ticker, (ticker, "No overview available"))
    
    # 보고서 생성
    report = f"""
## {ticker} 주식 분석 보고서

### 회사 정보
- **회사 이름**: {company_name}
- **개요**: {company_overview}

### 성과 비교
- **{ticker} 누적 수익률**: {final_rate:.1f}%
- **S&P 500 (VOO) 누적 수익률**: {final_rate_vs:.1f}%
- **차이**: {final_rate - final_rate_vs:.1f}%
- **요약**: {ticker}는 S&P 500보다 {final_rate - final_rate_vs:.1f}% 더 높은 성과를 보이고 있습니다.

### 최근 주가 변동
- **5일 이동평균**: ${sma_5:.2f}
- **20일 이동평균**: ${sma_20:.2f}
- **60일 이동평균**: ${sma_60:.2f}
- **추세**: {ticker}는 단기적으로 상승세를 보이고 있습니다.

### 기술적 지표
- **RSI**: {rsi:.2f} (중립)
- **PPO**: {ppo:.2f} (약한 매도 신호, 약간의 약세 상황)

{dynamic_data}

[Investing.com {ticker} 검색](https://www.google.com/search?q=Investing.com+{ticker})
[Investing.com 컨센서스 전망 {ticker}](https://www.google.com/search?q=Investing.com+consensus-estimates+{ticker})
"""
    return report

def analyze_with_gpt(ticker):
    try:
        # 시작 메시지 전송
        start_message = f"GPT-4o mini를 사용하여 {ticker} 분석을 시작합니다."
        print(start_message)
        response = requests.post(DISCORD_WEBHOOK_URL, data={'content': start_message})

        # CSV 파일 다운로드
        if not download_csv(ticker):
            error_message = f'Error: The file for {ticker} does not exist.'
            print(error_message)
            response = requests.post(DISCORD_WEBHOOK_URL, data={'content': error_message})
            return error_message

        # 동적 데이터 가져오기
        dynamic_data = fetch_dynamic_data(ticker)

        # 보고서 생성
        report = generate_stock_report(ticker, dynamic_data)

        # 디스코드 웹훅 메시지로 전송
        success_message = f"GPT-4o mini 분석 완료: {ticker}\n{report}"
        print(success_message)
        response = requests.post(DISCORD_WEBHOOK_URL, data={'content': success_message})

        # 리포트를 텍스트 파일로 저장
        report_file = f'report_{ticker}.txt'
        with open(report_file, 'w', encoding='utf-8') as file:
            file.write(report)

        # 리포트를 static/images 폴더로 이동 및 커밋
        move_files_to_images_folder()

        return f'GPT-4o mini Analysis for {ticker} (VOO) has been sent to Discord and saved as a text file.'

    except Exception as e:
        error_message = f"{ticker} 분석 중 오류 발생: {e}"
        print(error_message)
        response = requests.post(DISCORD_WEBHOOK_URL, data={'content': error_message})
        return error_message

if __name__ == '__main__':
    pass




"""
source .venv/bin/activate
python gpt.py    
"""
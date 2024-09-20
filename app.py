# app.py
import os
import sys
import asyncio
import threading
import requests
import io
from dotenv import load_dotenv
from flask import Flask, render_template, send_from_directory, jsonify, request
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
from flask_cors import CORS


# Add my-flutter-app directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'my-flask-app')))

# 사용자 정의 모듈 임포트
import config  # config.py 임포트
from git_operations import move_files_to_images_folder
from get_ticker import load_tickers, search_tickers_and_respond, get_ticker_name, update_stock_market_csv, get_ticker_from_korean_name
from Results_plot import plot_comparison_results
from Results_plot_mpl import plot_results_mpl
from github_operations import ticker_path
from backtest_send import backtest_and_send
from get_ticker import is_valid_stock
from gemini import analyze_with_gemini#, send_report_to_discord
from gpt import analyze_with_gpt
from get_compare_stock_data import save_simplified_csv  # 추가된 부분

# 명시적으로 .env 파일 경로를 지정하여 환경 변수 로드
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
CORS(app)

app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["DISCORD_CLIENT_ID"] = os.getenv("DISCORD_CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = os.getenv("DISCORD_CLIENT_SECRET")
app.config["DISCORD_REDIRECT_URI"] = os.getenv("DISCORD_REDIRECT_URI")
app.config["DISCORD_BOT_TOKEN"] = os.getenv("DISCORD_BOT_TOKEN")

discord_oauth = DiscordOAuth2Session(app)

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# GitHub API URL
repo_url = 'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images'

# .env 파일에서 GITHUB_TOKEN 가져오기
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# 헤더 설정 (인증을 위해 토큰 사용)
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# 요청 보내기
response = requests.get(repo_url, headers=headers)

# 응답 확인
# if response.status_code == 200:
#     files = response.json()
#     for file in files:
#         # print(file['name'])
# else:
#     print(f"Error: {response.status_code}, {response.text}")
    

@app.route('/')
def index():
    return send_from_directory('', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('', path)

@app.route('/generate_description', methods=['POST'])
def generate_description():
    data = request.get_json()
    stock_ticker = data.get('stock_ticker')
    description = f"Description for {stock_ticker}"
    return jsonify({"description": description})

@app.route('/save_search_history', methods=['POST'])
def save_search_history():
    data = request.json
    stock_name = data.get('stock_name')
    print(f'Saved {stock_name} to search history.')
    return jsonify({"success": True})

# 로컬의 이미지 파일 경로 설정 (예: static/images 폴더 경로)
LOCAL_IMAGES_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'images'))

# 이미지 파일이 저장된 디렉토리 경로
IMAGE_DIRECTORY = 'static/images'

# 검토된 티커 목록 제공 API
@app.route('/api/get_reviewed_tickers', methods=['GET'])
def get_reviewed_tickers():
    try:
        # GitHub API URL (프라이빗 리포지토리)
        repo_url = 'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images'
        
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(repo_url, headers=headers)
        
        if response.status_code == 200:
            # API 응답에서 파일 이름 추출
            files = response.json()
            tickers = [file['name'].split('_')[1] for file in files if file['name'].startswith('comparison_') and file['name'].endswith('_VOO.png')]
            return jsonify(tickers)
        else:
            return jsonify({'error': f'GitHub API request failed with status code {response.status_code}'}), response.status_code

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    
# 리포트 및 이미지 제공 API
@app.route('/api/get_images', methods=['GET'])
def get_images():
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'No ticker provided'}), 400

    # GitHub API URL
    comparison_image_url = f'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images/comparison_{ticker}_VOO.png'
    result_image_url = f'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images/result_mpl_{ticker}.png'
    report_file_url = f'https://api.github.com/repos/photo2story/my-flutter-app/contents/static/images/report_{ticker}.txt'

    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3.raw'  # 콘텐츠를 그대로 받아오기 위함
    }

    # 비교 이미지 요청
    comparison_image = ''
    comparison_response = requests.get(comparison_image_url, headers=headers)
    if comparison_response.status_code == 200:
        comparison_image = comparison_image_url.replace('api.github.com/repos', 'raw.githubusercontent.com').replace('contents/', '')

    # 결과 이미지 요청
    result_image = ''
    result_response = requests.get(result_image_url, headers=headers)
    if result_response.status_code == 200:
        result_image = result_image_url.replace('api.github.com/repos', 'raw.githubusercontent.com').replace('contents/', '')

    # 리포트 파일 요청
    report_text = ''
    report_response = requests.get(report_file_url, headers=headers)
    if report_response.status_code == 200:
        report_text = report_response.text

    return jsonify({
        'comparison_image': comparison_image,
        'result_image': result_image,
        'report': report_text
    })

        
# 파일을 서빙하는 엔드포인트
@app.route('/static/images/<path:filename>')
def serve_image(filename):
    try:
        print(f"Serving image: {filename}")
        return send_from_directory(IMAGE_DIRECTORY, filename)
    except Exception as e:
        print(f"Error serving image {filename}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
async def analyze():
    data = request.get_json()
    message = data.get('message')
    
    # 메시지 분석 및 적절한 티커 할당 (예: "애플 최근 실적 말해줘")
    ticker = None
    if "애플" in message:
        ticker = "AAPL"
    elif "마이크로소프트" in message:
        ticker = "MSFT"
    # 추가적인 조건을 여기서 처리

    if ticker:
        result = await analyze_with_gemini(ticker)
        return jsonify({'response': result})
    else:
        return jsonify({'response': '요청을 이해할 수 없습니다. 다른 질문을 해주세요.'})
    
def fetch_csv_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        csv_data = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_data))
        df.fillna('', inplace=True)
        return df
    except requests.exceptions.RequestException as e:
        print(f'Error fetching CSV data: {e}')
        return None

@app.route('/data')
def data():
    df = fetch_csv_data(config.CSV_URL)
    if df is None:
        return "Error fetching data", 500
    return df.to_html()

@app.route('/execute_stock_command', methods=['POST'])
def execute_stock_command():
    data = request.get_json()
    stock_ticker = data.get('stock_ticker')
    if not stock_ticker:
        return jsonify({'error': 'No stock ticker provided'}), 400

    try:
        async def send_stock_command():
            await send_command_to_bot(stock_ticker)

        asyncio.create_task(send_stock_command())
        return jsonify({'message': 'Command executed successfully'}), 200
    except Exception as e:
        print(f"Error while executing stock command: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/send_discord_command', methods=['POST'])
def send_discord_command():
    data = request.json
    command = data.get('command')
    print(f"Received command: {command}")  # 디버깅 메시지 추가

    # MockContext와 MockBot 클래스 정의
    class MockContext:
        async def send(self, message):
            print(f"MockContext.send: {message}")

    class MockBot:
        async def change_presence(self, status=None, activity=None):
            print(f"MockBot.change_presence: status={status}, activity={activity}")

    if command:
        try:
            command_parts = command.split()
            main_command = command_parts[0].lower()
            query = command_parts[1].upper() if len(command_parts) > 1 else None

            async def process_stock_command(stock_names):
                ctx = MockContext()
                bot = MockBot()

                for stock_name in stock_names:
                    await ctx.send(f'Analyzing {stock_name}...')
                    try:
                        await backtest_and_send(ctx, stock_name, 'modified_monthly', bot)
                    except Exception as e:
                        await ctx.send(f'Error during analysis of {stock_name}.')
                        print(f'Error processing {stock_name}: {e}')

                    try:
                        await plot_comparison_results(stock_name, config.START_DATE, config.END_DATE)
                        await plot_results_mpl(stock_name, config.START_DATE, config.END_DATE)
                        await ctx.send(f'Results for {stock_name} ready.')
                    except Exception as e:
                        await ctx.send(f"Error plotting {stock_name}.")
                        print(f"Error plotting {stock_name}: {e}")

                    await asyncio.sleep(1)

            async def process_gemini_command(tickers):
                ctx = MockContext()

                for ticker in tickers:
                    await ctx.send(f'Gemini analysis for {ticker} is starting...')
                    try:
                        result = await analyze_with_gemini(ticker)
                    except Exception as e:
                        await ctx.send(f'Error during Gemini analysis of {ticker}.')
                        print(f'Error analyzing {ticker} with Gemini: {e}')
                        continue

                    try:
                        await ctx.send(f'Results for {ticker} displayed successfully.')
                    except Exception as e:
                        await ctx.send(f"Error displaying results for {ticker}.")
                        print(f"Error displaying results for {ticker}: {e}")

                    await asyncio.sleep(1)

            async def process_buddy_command(stock_names):
                ctx = MockContext()
                bot = MockBot()

                for stock_name in stock_names:
                    await process_stock_command([stock_name])  # stock 명령 호출
                    await asyncio.sleep(1)
                    await process_gemini_command([stock_name])  # gemini 명령 호출
                    await asyncio.sleep(1)
                    print(f'Results for {stock_name} displayed successfully.')

                if not query:
                    results = await collect_relative_divergence()

            async def execute_command():
                stock_names = [query] if query else [stock for sector, stocks in config.STOCKS.items() for stock in stocks]

                if main_command == "stock":
                    await process_stock_command(stock_names)
                elif main_command == "gemini":
                    await process_gemini_command(stock_names)
                elif main_command == "buddy":
                    await process_buddy_command(stock_names)
                else:
                    return jsonify({'message': 'Unknown command'}), 400

            asyncio.run(execute_command())

            return jsonify({'message': f'{main_command} command executed successfully'}), 200
        except Exception as e:
            print(f"Error executing command: {e}")
            return jsonify({'message': 'Error executing command'}), 500
    return jsonify({'message': 'Invalid command'}), 400


def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    from bot import run_bot
    threading.Thread(target=run_flask).start()
    asyncio.run(run_bot())

# source .venv/bin/activate
# #  .\.venv\Scripts\activate
# #  python app.py 
# pip install huggingface_hub
# huggingface-cli login
# EEVE-Korean-Instruct-10.8B-v1.0-GGUF
# ollama create EEVE-Korean-Instruct-10.8B -f Modelfile-V02
# ollama create EEVE-Korean-10.8B -f EEVE-Korean-Instruct-10.8B-v1.0-GGUF/Modelfile
# pip install ollama
# pip install chromadb
# pip install langchain
# ollama create EEVE-Korean-10.8B -f Modelfile
# git push heroku main
# heroku logs --tail -a he-flutter-app

# source .venv/bin/activate
# #  .\.venv\Scripts\activate
# #  python app.py 
# pip install huggingface_hub
# huggingface-cli login
# EEVE-Korean-Instruct-10.8B-v1.0-GGUF
# ollama create EEVE-Korean-Instruct-10.8B -f Modelfile-V02
# ollama create EEVE-Korean-10.8B -f EEVE-Korean-Instruct-10.8B-v1.0-GGUF/Modelfile
# pip install ollama
# pip install chromadb
# pip install langchain
# ollama create EEVE-Korean-10.8B -f Modelfile
# git push heroku main
# heroku logs --tail -a he-flutter-app
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
import config  # config.py 임포트

# Add my-flutter-app directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'my-flask-app')))

# 사용자 정의 모듈 임포트
from git_operations import move_files_to_images_folder
from get_ticker import load_tickers, search_tickers_and_respond, get_ticker_name, update_stock_market_csv, get_ticker_from_korean_name
from Results_plot import plot_comparison_results
from Results_plot_mpl import plot_results_mpl
from github_operations import ticker_path
from backtest_send import backtest_and_send
from get_ticker import is_valid_stock
from gemini import analyze_with_gemini, send_report_to_discord
from gpt import analyze_with_gpt
from get_compare_stock_data import save_simplified_csv  # 추가된 부분

# 명시적으로 .env 파일 경로를 지정하여 환경 변수 로드
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

app = Flask(__name__, static_url_path='', static_folder='')
CORS(app)

app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["DISCORD_CLIENT_ID"] = os.getenv("DISCORD_CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = os.getenv("DISCORD_CLIENT_SECRET")
app.config["DISCORD_REDIRECT_URI"] = os.getenv("DISCORD_REDIRECT_URI")
app.config["DISCORD_BOT_TOKEN"] = os.getenv("DISCORD_BOT_TOKEN")

discord_oauth = DiscordOAuth2Session(app)

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

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

@app.route('/api/get_images', methods=['GET'])
def get_images():
    image_folder = os.path.join(app.static_folder, 'images')
    images = [filename for filename in os.listdir(image_folder) if filename.endswith('.png')]
    return jsonify(images)

@app.route('/api/get_reviewed_tickers', methods=['GET'])
def get_reviewed_tickers():
    image_folder = os.path.join(app.static_folder, 'images')
    tickers = [filename.split('_')[1] for filename in os.listdir(image_folder)
               if filename.startswith('comparison_') and filename.endswith('_VOO.png')]
    return jsonify(tickers)

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

    if command:
        try:
            if command.lower() == "ping":
                print("Executing ping command...")  # 디버깅 메시지 추가
                
                # ctx를 직접 생성하지 않기 때문에 MockContext와 MockBot을 사용합니다.
                class MockContext:
                    async def send(self, message):
                        print(f"MockContext.send: {message}")

                class MockBot:
                    async def change_presence(self, status=None, activity=None):
                        print(f"MockBot.change_presence: status={status}, activity={activity}")

                ctx = MockContext()
                bot = MockBot()
                
                # 비동기 함수를 동기 컨텍스트에서 실행하기 위해 asyncio.run 사용
                asyncio.run(backtest_and_send(ctx, 'AAPL', 'modified_monthly', bot))

                # 결과 플롯팅 및 전송
                try:
                    asyncio.run(plot_comparison_results('AAPL', config.START_DATE, config.END_DATE))
                    asyncio.run(plot_results_mpl('AAPL', config.START_DATE, config.END_DATE))
                    ctx.send(f'Results for AAPL displayed successfully.')
                except Exception as e:
                    ctx.send(f"An error occurred while plotting AAPL: {e}")
                    print(f"Error plotting AAPL: {e}")

                return jsonify({'message': 'ping command executed successfully'}), 200
            else:
                return jsonify({'message': 'Unknown command'}), 400
        except Exception as e:
            print(f"Error executing command: {str(e)}")
            return jsonify({'message': f'Error executing command: {str(e)}'}), 500
    return jsonify({'message': 'Invalid command'}), 400



def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

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
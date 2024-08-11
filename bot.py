# bot.py

import os
import sys
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import tasks, commands
import certifi
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import config  # config.py 임포트
import google.generativeai as genai

os.environ['SSL_CERT_FILE'] = certifi.where()

# Add my-flask-app directory to sys.path
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
from get_compare_stock_data import save_simplified_csv, read_and_process_csv  # 추가된 부분

load_dotenv()

TOKEN = os.getenv('DISCORD_APPLICATION_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
H_APIKEY = os.getenv('H_APIKEY')
H_SECRET = os.getenv('H_SECRET')
H_ACCOUNT = os.getenv('H_ACCOUNT')
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')  # Gemini API 키 로드

GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com/photo2story/my-flutter-app/main/static/images"
CSV_PATH = f"{GITHUB_RAW_BASE_URL}/stock_market.csv"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='', intents=intents)

bot_started = False

# Gemini API 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@bot.event
async def on_ready():
    global bot_started
    if not bot_started:
        print(f'Logged in as {bot.user.name}')
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f'Bot has successfully logged in as {bot.user.name}')
        else:
            print(f'Failed to get channel with ID {CHANNEL_ID}')
        bot_started = True

@bot.command()
async def gchat(ctx, *, query: str = None):
    if query is None or query.strip() == "":
        await ctx.send("제미니와 대화하려면 메시지를 입력해주세요.")
        return

    try:
        # 제미니와의 대화 요청
        response = model.generate_content(query)
        await ctx.send(response.text)
    except Exception as e:
        await ctx.send(f"Gemini와의 대화 중 오류가 발생했습니다: {e}")


@bot.command()
async def stock(ctx, *, query: str = None):
    if query:
        stock_names = [query.upper()]
    else:
        stock_names = [stock for sector, stocks in config.STOCKS.items() for stock in stocks]

    for stock_name in stock_names:
        stock_analysis_complete = config.is_stock_analysis_complete(stock_name)

        if stock_analysis_complete:
            await ctx.send(f"Stock analysis for {stock_name} is already complete. Displaying results.")
            await backtest_and_send(ctx, stock_name, 'modified_monthly', bot)

        else:
            await ctx.send(f'Stock analysis for {stock_name} is not complete. Proceeding with analysis.')
            try:
                # Analysis logic
                await backtest_and_send(ctx, stock_name, 'modified_monthly', bot)
            except Exception as e:
                await ctx.send(f'An error occurred while processing {stock_name}: {e}')
                print(f'Error processing {stock_name}: {e}')

        # Display results
        try:
            await plot_comparison_results(stock_name, config.START_DATE, config.END_DATE)
            await plot_results_mpl(stock_name, config.START_DATE, config.END_DATE)
            await ctx.send(f'Results for {stock_name} displayed successfully.')
        except Exception as e:
            await ctx.send(f"An error occurred while plotting {stock_name}: {e}")
            print(f"Error plotting {stock_name}: {e}")

        await asyncio.sleep(1)

@bot.command()
async def gemini(ctx, *, query: str = None):
    if query:
        tickers = [query.upper()]
    else:
        tickers = [stock for sector, stocks in config.STOCKS.items() for stock in stocks]
        
    for ticker in tickers: 
        # 1) 제미니 분석 리포트 유효성 확인
        gemini_analysis_complete = config.is_gemini_analysis_complete(ticker)
        gemini_analysis_complete = False
        if not gemini_analysis_complete: # 1.1) 유효하지 않다면 분석 실행
            await ctx.send(f'Gemini analysis for {ticker} is not complete. Proceeding with analysis.')
            try:
                result = await analyze_with_gemini(ticker)
                # await ctx.send(result)
            except Exception as e:
                error_message = f'An error occurred while analyzing {ticker} with Gemini: {e}'
                await ctx.send(error_message)
                print(f'Error analyzing {ticker} with Gemini: {e}')
                continue  # 다음 티커로 넘어감

        # 2) 레포트 전송
        try:
            # await send_report_to_discord(ticker)
            await ctx.send(f'Results for {ticker} displayed successfully.')
        except Exception as e:
            await ctx.send(f"Error displaying results for {ticker}: {e}")
            print(f"Error displaying results for {ticker}: {e}")

        await asyncio.sleep(1)  # 각 티커 처리 사이에 5초 대기


@bot.command()
async def buddy(ctx, *, query: str = None):
    if query:
        stock_names = [query.upper()]
    else:
        stock_names = [stock for sector, stocks in config.STOCKS.items() for stock in stocks]

    for stock_name in stock_names:
        # stock 명령 호출
        await ctx.invoke(bot.get_command("stock"), query=stock_name)
        await asyncio.sleep(1)  # 각 명령 호출 사이에 10초 대기

        # gemini 명령 호출
        await ctx.invoke(bot.get_command("gemini"), query=stock_name)
        await asyncio.sleep(1)  # 각 명령 호출 사이에 10초 대기
        print(f'Results for {stock_name} displayed successfully.')
        
    # query가 없는 경우에만 collect_relative_divergence 호출
    if not query:
        results = await collect_relative_divergence()        
        
@bot.command()
async def ticker(ctx, *, query: str = None):
    print(f'Command received: ticker with query: {query}')
    if query is None:
        await ctx.send("Please enter ticker stock name or ticker.")
        return

    await search_tickers_and_respond(ctx, query)

@bot.command()
async def ping(ctx):
    if ctx.message.id not in processed_message_ids:
        processed_message_ids.add(ctx.message.id)
        await ctx.send(f'pong: {bot.user.name}')
        print(f'Ping command received and responded with pong.')

@bot.command()
async def account(ctx, ticker: str):
    try:
        ticker = ticker.upper()  # 티커를 대문자로 변환
        exchange = get_market_from_ticker(ticker)
        last_price = get_ticker_price(H_APIKEY, H_SECRET, H_ACCOUNT, exchange, ticker)
        await ctx.send(f'The exchange for {ticker} is {exchange}')
        await ctx.send(f'Last price of {ticker} is {last_price}')
    except Exception as e:
        await ctx.send(f'An error occurred: {e}')
        print(f'Error processing account for {ticker}: {e}')

async def run_bot():
    await bot.start(TOKEN)

def run_server():
    port = int(os.environ.get('PORT', 8080))
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f'Starting server on port {port}')
    httpd.serve_forever()

if __name__ == '__main__':
    # HTTP 서버 시작
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # 봇 실행
    asyncio.run(run_bot())



r"""
\.venv\Scripts\activate
python3 -m venv .venv
source .venv/bin/activate
python bot.py   
docker build -t asia.gcr.io/my-flask-app-429017/bot .
docker push asia.gcr.io/my-flask-app-429017/bot
gcloud run deploy bot --image asia.gcr.io/my-flask-app-429017/bot --platform managed --region asia-northeast3 --allow-unauthenticated

원격저장소 내용으로 강제 업데이트
git fetch origin
git checkout main
git reset --hard origin/main
로컬내용을 원격저장소에 강제업데이트
git push origin main --force

nix-shell
"""
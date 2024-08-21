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

os.environ['SSL_CERT_FILE'] = certifi.where()

# Add my-flask-app directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'my-flask-app')))

# 사용자 정의 모듈 임포트
from git_operations import move_files_to_images_folder
from get_ticker import load_tickers, search_tickers_and_respond, get_ticker_name, update_stock_market_csv, get_ticker_from_korean_name
# from estimate_stock import estimate_stock
from Results_plot import plot_results_all
from Results_plot_mpl import plot_results_mpl
from github_operations import ticker_path
from backtest_send import backtest_and_send
from get_ticker  import is_valid_stock

# get_account_balance 모듈 임포트
from get_account_balance import get_balance, get_ticker_price, get_market_from_ticker
from get_compare_stock_data import load_sector_info, merge_csv_files

# gemini 모듈 임포트
from gemini import analyze_with_gemini

load_dotenv()

TOKEN = os.getenv('DISCORD_APPLICATION_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
H_APIKEY = os.getenv('H_APIKEY')
H_SECRET = os.getenv('H_SECRET')
H_ACCOUNT = os.getenv('H_ACCOUNT')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='', intents=intents)

processed_message_ids = set()

def check_duplicate_message():
    async def predicate(ctx):
        if ctx.message.id in processed_message_ids:
            return False
        processed_message_ids.add(ctx.message.id)
        return True
    return commands.check(predicate)

bot_started = False

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

@tasks.loop(minutes=5)
async def send_msg():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send('Hello')
        print(f'Message sent to channel {CHANNEL_ID}')
    else:
        print(f"Failed to find channel with ID: {CHANNEL_ID}")

@bot.command()
async def buddy(ctx):
    loop = asyncio.get_running_loop()

    for sector, stocks in config.STOCKS.items():
        await ctx.send(f'Processing sector: {sector}')
        for stock_data in stocks:
            stock = stock_data['ticker'] if isinstance(stock_data, dict) else stock_data
            await backtest_and_send(ctx, stock, 'modified_monthly', bot)
            if is_valid_stock(stock):
                try:
                    plot_results_mpl(stock, config.START_DATE, config.END_DATE)
                except KeyError as e:
                    await ctx.send(f"An error occurred while plotting {stock}: {e}")
                    print(f"Error plotting {stock}: {e}")
            await asyncio.sleep(2)

        print("Updating stock market CSV...")
        await loop.run_in_executor(None, update_stock_market_csv, ticker_path, [s['ticker'] if isinstance(s, dict) else s for s in stocks])
        
        print("Loading sector info...")
        sector_dict = await loop.run_in_executor(None, load_sector_info)
        
        print("Merging CSV files...")
        path = '.'
        await loop.run_in_executor(None, merge_csv_files, path, sector_dict)

        await ctx.send(f"백테스팅 결과가 섹터별로 정리되었습니다.")
        move_files_to_images_folder()

        for stock_data in stocks:
            stock = stock_data['ticker'] if isinstance(stock_data, dict) else stock_data
            result = analyze_with_gemini(stock)
            await ctx.send(result)
            await asyncio.sleep(10)
        move_files_to_images_folder()

@bot.command(name='ticker')
@check_duplicate_message()
async def ticker(ctx, *, query: str = None):
    print(f'Command received: ticker with query: {query}')
    if query is None:
        await ctx.send("Please enter ticker stock name or ticker.")
        return

    await search_tickers_and_respond(ctx, query)

@bot.command(name='stock')
@check_duplicate_message()
async def stock(ctx, *args):
    stock_name = ' '.join(args)
    await ctx.send(f'Arguments passed by command: {stock_name}')
    try:
        info_stock = str(stock_name).upper()
        if info_stock.startswith('K '):
            korean_stock_name = info_stock[2:].upper()
            korean_stock_code = get_ticker_from_korean_name(korean_stock_name)
            if korean_stock_code is None:
                await ctx.send(f'Cannot find the stock {korean_stock_name}.')
                return
            else:
                info_stock = korean_stock_code

        await ctx.send(f'Running backtest_and_send for {info_stock}')
        await backtest_and_send(ctx, info_stock, option_strategy='1', bot=bot)
        
        await ctx.send(f'Plotting results for {info_stock}')
        plot_results_mpl(info_stock, config.START_DATE, config.END_DATE)
        move_files_to_images_folder()
        await ctx.send(f'Successfully processed {info_stock}')
        
    except Exception as e:
        await ctx.send(f'An error occurred: {e}')
        print(f'Error processing {info_stock}: {e}')

@bot.command(name='show_all')
@check_duplicate_message()
async def show_all(ctx):
    try:
        await plot_results_all()
        await ctx.send("All results have been successfully displayed.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        print(f"Error: {e}")

@bot.command(name='ping')
@check_duplicate_message()
async def ping(ctx):
    await ctx.send(f'pong: {bot.user.name}')
    print(f'Ping command received and responded with pong.')

@bot.command(name='account')
@check_duplicate_message()
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

@bot.command(name='gemini')
@check_duplicate_message()
async def gemini(ctx, ticker: str):
    try:
        ticker = ticker.upper()  # 티커를 대문자로 변환
        report = analyze_with_gemini(ticker)
        await ctx.send(report)
    except Exception as e:
        await ctx.send(f'An error occurred while analyzing {ticker} with Gemini API: {e}')
        print(f'Error processing Gemini analysis for {ticker}: {e}')

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


#  .\.venv\Scripts\activate
# source .venv/bin/activate
# # python bot.py    
# docker build -t asia.gcr.io/my-flask-app-429017/bot .
# docker push asia.gcr.io/my-flask-app-429017/bot
# gcloud run deploy bot --image asia.gcr.io/my-flask-app-429017/bot --platform managed --region asia-northeast3 --allow-unauthenticated

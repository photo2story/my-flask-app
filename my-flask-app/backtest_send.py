# backtest_send.py
import requests
import os, sys
import pandas as pd
import matplotlib.pyplot as plt
from discord.ext import commands
import discord
import asyncio

# 사용자 정의 모듈 임포트
from Results_plot import plot_comparison_results
from get_ticker import get_ticker_name, is_valid_stock
from get_compare_stock_data import save_simplified_csv
from git_operations import move_files_to_images_folder
from Get_data import get_stock_data
import My_strategy
from Data_export import export_csv

# Import configuration
import config

# 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

option_strategy = config.option_strategy  # 시뮬레이션 전략 설정

# VOO 데이터를 가져오거나 캐시된 데이터를 사용하는 함수
async def get_voo_data(option_strategy, ctx):
    if config.is_cache_valid(config.VOO_CACHE_FILE, config.START_DATE):
        await ctx.send("Using cached VOO data.")
        cached_voo_data = pd.read_csv(config.VOO_CACHE_FILE, parse_dates=['Date'])
    else:
        await ctx.send("Fetching new VOO data.")
        stock_data2, first_stock_data_date = get_stock_data('VOO', config.START_DATE, config.END_DATE)
        result_df2 = My_strategy.my_strategy(stock_data2, option_strategy)
        
        # 여기서 result_df2가 DataFrame인지 확인
        if not isinstance(result_df2, pd.DataFrame):
            raise TypeError(f"Expected DataFrame from my_strategy, got {type(result_df2)}")
        
        result_df2.rename(columns={'rate': 'rate_vs'}, inplace=True)
        
        await ctx.send("Saving new VOO data to cache.")
        result_df2.to_csv(config.VOO_CACHE_FILE, index=False)
        cached_voo_data = result_df2
    
    return cached_voo_data

# 백테스트를 수행하고 결과를 전송하는 함수
async def backtest_and_send(ctx, stock, option_strategy, bot=None):
    if bot is None:
        raise ValueError("bot 변수는 None일 수 없습니다.")
    
    await ctx.send(f"Backtesting and sending command for: {stock}")
    
    if not is_valid_stock(stock):
        message = f"Stock market information updates needed for {stock}."
        await ctx.send(message)
        print(message)
        return
    
    try:
        await ctx.send(f'Fetching data for {stock}.')
        
        # 주식 데이터 가져오기
        stock_data, first_stock_data_date = get_stock_data(stock, config.START_DATE, config.END_DATE)
        await ctx.send(f'Running strategy for {stock}.')
        
        # my_strategy 함수 호출 및 반환값 확인
        stock_result_df = My_strategy.my_strategy(stock_data, option_strategy)
        
        if not isinstance(stock_result_df, pd.DataFrame):
            raise TypeError(f"my_strategy returned {type(stock_result_df)} instead of DataFrame")
        
        if stock_result_df.empty:
            raise ValueError("my_strategy returned an empty DataFrame")
        
        print('stock_result_df:', stock_result_df.head())  # 첫 몇 줄만 출력
        
        await ctx.send(f'Exporting data for {stock}.')
        
        # VOO 데이터 가져오기 (캐시된 데이터 사용 또는 새로 가져오기)
        voo_data_df = await get_voo_data(option_strategy, ctx)
        
        if not isinstance(voo_data_df, pd.DataFrame):
            raise TypeError(f"get_voo_data returned {type(voo_data_df)} instead of DataFrame")
        
        if voo_data_df.empty:
            raise ValueError("get_voo_data returned an empty DataFrame")

        await ctx.send(f'Combining data for {stock} with VOO data.')
        
        # 날짜 형식 통일
        stock_result_df['Date'] = pd.to_datetime(stock_result_df['Date'])
        voo_data_df['Date'] = pd.to_datetime(voo_data_df['Date'])
        
        # 날짜를 기준으로 병합
        combined_df = pd.merge(stock_result_df, voo_data_df[['Date', 'rate_vs']], on='Date', how='inner')
        
        # 병합 후 결측치 채우기
        combined_df.fillna(0, inplace=True)
        print(combined_df.head())  # 첫 몇 줄만 출력

        # 유효하지 않은 끝부분 제거: 'price' 가 0인 행 제거
        combined_df = combined_df[(combined_df['price'] != 0)]

        # 결과 CSV 파일로 저장하기
        safe_ticker = stock.replace('/', '-')
        file_path = os.path.join('static', 'images', f'result_VOO_{safe_ticker}.csv')
        await ctx.send(f'Saving results to {file_path}.')
        combined_df.to_csv(file_path, float_format='%.2f', index=False)
        
        # CSV 파일 간소화
        await ctx.send(f'Simplifying CSV for {stock}.')
        save_simplified_csv(stock)

        # 파일 이동 및 깃헙 커밋/푸시
        await move_files_to_images_folder()
        await bot.change_presence(status=discord.Status.online, activity=discord.Game("Waiting"))
        await ctx.send(f"Backtest and send process completed successfully for {stock}.")
    
    except Exception as e:
        error_message = f"An error occurred while processing {stock}: {str(e)}\n"
        error_message += f"Error type: {type(e)}\n"
        error_message += f"Error location: {e.__traceback__.tb_frame.f_code.co_filename}, line {e.__traceback__.tb_lineno}"
        await ctx.send(error_message)
        print(error_message)

# 테스트 코드 추가
async def test_backtest_and_send():
    class MockContext:
        async def send(self, message):
            print(f"MockContext.send: {message}")

    class MockBot:
        async def change_presence(self, status=None, activity=None):
            print(f"MockBot.change_presence: status={status}, activity={activity}")

    ctx = MockContext()
    bot = MockBot()
    stock = "QQQ"
    
    try:
        # 캐시 유효성 검사 및 결과 출력
        if config.is_cache_valid(config.VOO_CACHE_FILE, config.START_DATE):
            print(f"Using cached VOO data for testing.")
        else:
            print(f"VOO cache is not valid or missing. New data will be fetched.")
        
        # backtest_and_send 함수 실행
        await backtest_and_send(ctx, stock, option_strategy='default', bot=bot)
        
        # VOO 데이터가 유효한 데이터프레임인지 확인
        voo_data_df = await get_voo_data(option_strategy, ctx)
        if isinstance(voo_data_df, pd.DataFrame):
            print("VOO data is a valid DataFrame.")
            print(f"VOO data head:\n{voo_data_df.head()}")
        else:
            raise ValueError("VOO data is not a valid DataFrame.")
        
        # 주식 데이터가 유효한 데이터프레임인지 확인
        stock_data, first_stock_data_date = get_stock_data(stock, config.START_DATE, config.END_DATE)
        if isinstance(stock_data, pd.DataFrame):
            print(f"{stock} data is a valid DataFrame.")
            print(f"{stock} data head:\n{stock_data.head()}")
        else:
            raise ValueError(f"{stock} data is not a valid DataFrame.")
        
        # 결과 비교를 위한 그래프 생성 함수 실행
        await plot_comparison_results(stock, START_DATE, END_DATE)

        print("Backtesting completed successfully.")
    
    except Exception as e:
        print(f"Error occurred while backtesting: {e}")

# 메인 실행부
if __name__ == "__main__":
    print("Starting test for back-testing.")
    asyncio.run(test_backtest_and_send())

    # python backtest_send.py        



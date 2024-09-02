# backtest_send.py
import requests
import os, sys
import pandas as pd
import matplotlib.pyplot as plt
from discord.ext import commands
import discord  # discord 모듈 추가
import asyncio

# 사용자 정의 모듈 임포트
from Results_plot import plot_comparison_results
from get_ticker import get_ticker_name, is_valid_stock
from get_compare_stock_data import save_simplified_csv  # 추가된 부분
from git_operations import move_files_to_images_folder
from Get_data import get_stock_data
import My_strategy
from Data_export import export_csv
# Import configuration
import config
# 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

option_strategy =config.option_strategy # 시뮬레이션 전략 설정

# backtest_and_send.py
async def get_voo_data(option_strategy, ctx):
    # config.py에서 VOO_CACHE_FILE과 is_cache_valid 함수를 사용합니다.
    
    if config.is_cache_valid(config.VOO_CACHE_FILE, config.START_DATE):
        await ctx.send("Using cached VOO data.")
        # 캐시된 데이터를 불러옵니다.
        cached_voo_data = pd.read_csv(config.VOO_CACHE_FILE)
    else:
        await ctx.send("Fetching new VOO data.")
        # VOO 데이터를 새로 가져옵니다.
        stock_data2, _ = get_stock_data('VOO', config.START_DATE, config.END_DATE)
        result_df2 = My_strategy.my_strategy(stock_data2, option_strategy)
        result_df2.rename(columns={'rate': 'rate_vs'}, inplace=True)
        
        await ctx.send("Saving new VOO data to cache.")
        # 새로 가져온 데이터를 캐시 파일로 저장합니다.
        result_df2.to_csv(config.VOO_CACHE_FILE, index=False)
        cached_voo_data = result_df2
    
    return cached_voo_data

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
        stock_data, _ = get_stock_data(stock, config.START_DATE, config.END_DATE)
        await ctx.send(f'Running strategy for {stock}.')
        result_df = My_strategy.my_strategy(stock_data, option_strategy)
        print(result_df)

        
        # VOO 데이터 가져오기 (캐시된 데이터 사용 또는 새로 가져오기)
        result_df2 = await get_voo_data(option_strategy, ctx)
        print(result_df)

        
        await ctx.send(f'Combining data for {stock} with VOO data.')
        # VOO 데이터와 합침
        # 주식 데이터와 VOO 데이터 병합
        combined_df = result_df.join(result_df2['rate_vs'])

        # 날짜 컬럼을 기준으로 병합된 데이터프레임을 필터링
        # VOO 데이터의 마지막 날짜 기준으로 데이터를 자릅니다.
        voo_last_date = result_df2.index[-1]  # VOO 데이터의 마지막 날짜
        combined_df = combined_df[combined_df.index <= voo_last_date]

        # 누락된 값을 0으로 채우기
        combined_df.fillna(0, inplace=True)

        # 유효하지 않은 끝부분 제거: 'rate' 또는 'rate_vs'가 0인 행 제거
        combined_df = combined_df[(combined_df['rate'] != 0) & (combined_df['rate_vs'] != 0)]

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
        error_message = f"An error occurred while processing {stock}: {e}"
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
    stock = "BTC-USD"
    
    try:
        # VOO 데이터가 캐시되어 있는지 확인하고 출력
        if config.is_cache_valid(config.VOO_CACHE_FILE, config.START_DATE):
            print(f"Using cached VOO data for testing.")
        else:
            print(f"VOO cache is not valid or missing. New data will be fetched.")

        # backtest_and_send 함수 실행
        await backtest_and_send(ctx, stock, option_strategy='monthly', bot=bot)
        
        # 결과 비교를 위한 그래프 생성 함수 실행
        await plot_comparison_results(stock, config.START_DATE, config.END_DATE)

        print("Backtesting completed successfully.")
    except Exception as e:
        print(f"Error occurred while backtesting: {e}")

# 메인 실행부
if __name__ == "__main__":
    print("Starting test for back-testing.")
    asyncio.run(test_backtest_and_send())

    # python backtest_send.py        



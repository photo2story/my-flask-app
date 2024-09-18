# backtest_send.py
import requests
import os, sys
import pandas as pd
import matplotlib.pyplot as plt
from discord.ext import commands
import discord
import asyncio
import traceback  # 추가

# 사용자 정의 모듈 임포트
from Results_plot import plot_comparison_results
from get_compare_stock_data import save_simplified_csv
from git_operations import move_files_to_images_folder
from Get_data import get_stock_data  # 여기에서 stock 데이터를 가져옴
import My_strategy
from Data_export import export_csv
from get_ticker import is_valid_stock

# Import configuration
import config

# 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

option_strategy = config.option_strategy  # 시뮬레이션 전략 설정

# VOO 데이터를 가져오거나 캐시된 데이터를 사용하는 함수
async def get_voo_data(option_strategy, first_date, last_date, ctx):
    # 캐시 무효화: 캐시 파일이 없거나 유효하지 않으면 새 데이터를 다운로드합니다.
    if not config.is_cache_valid(config.VOO_CACHE_FILE, first_date, last_date):
        await ctx.send(f"Fetching new VOO data from {first_date} to {last_date}")
        voo_data, _, _ = get_stock_data('VOO', first_date, last_date)
        voo_data_df = My_strategy.my_strategy(voo_data, option_strategy)
        voo_data_df.rename(columns={'rate': 'rate_vs'}, inplace=True)  # 'rate' 열을 'rate_vs'로 이름 변경
        
        # 새로운 데이터를 캐시에 저장
        await ctx.send("Saving new VOO data to cache.")
        voo_data_df.to_csv(config.VOO_CACHE_FILE, index=False)
        cached_voo_data = voo_data_df
    else:
        await ctx.send("Using cached VOO data.")
        cached_voo_data = pd.read_csv(config.VOO_CACHE_FILE, parse_dates=['Date'])

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
        await ctx.send(f'get_data for {stock}.')
        
        # 주식 데이터 가져오기 (기초 주가 데이터를 가져오는 것만 수행)
        stock_data, first_date, last_date = get_stock_data(stock, config.START_DATE, config.END_DATE)
        print('Fetched stock_data:', stock_data.head())  # 디버깅 출력
        
        if stock_data.empty:
            await ctx.send(f"No stock data found for {stock}.")
            return

        # 시뮬레이션 실행
        await ctx.send(f'Running strategy for {stock}.')
        stock_result_df = My_strategy.my_strategy(stock_data, option_strategy)
        print('Strategy result (stock_result_df):', stock_result_df.head())  # 디버깅 출력
        
        if stock_result_df.empty:
            await ctx.send(f"No strategy result data for {stock}.")
            return
        
        # VOO 데이터 가져오기 (캐시된 데이터 사용 또는 새로 가져오기)
        voo_data_df = await get_voo_data(option_strategy, first_date, last_date, ctx)
        print('Fetched voo_data_df:', voo_data_df.head())  # 디버깅 출력

        await ctx.send(f'Combining data for {stock} with VOO data.')
        
        # 날짜 형식 통일
        stock_result_df['Date'] = pd.to_datetime(stock_result_df['Date'])
        voo_data_df['Date'] = pd.to_datetime(voo_data_df['Date'])

        # first_date에 맞춰 VOO의 rate_vs 값을 변환
        reset_date = pd.to_datetime(first_date)  # 검토할 티커의 처음 날짜 (first_date)
        reset_value = voo_data_df.loc[voo_data_df['Date'] == reset_date, 'rate_vs'].values[0]  # first_date의 rate_vs 값
        voo_data_df['rate_vs'] = voo_data_df['rate_vs'] - reset_value  # first_date부터 rate_vs 값을 0으로 설정

        # stock_result_df와 voo_data_df 병합
        print(f"Merging stock data and VOO data for {stock}.")  # 병합 전 디버깅 메시지
        combined_df = pd.merge(stock_result_df, voo_data_df[['Date', 'rate_vs']], on='Date', how='inner')
        
        if combined_df.empty:
            await ctx.send(f"No combined data for {stock}.")
            return
        
        # 병합 후 결측치 채우기
        combined_df.fillna(0, inplace=True)
        print('Merged and filled combined_df:', combined_df.head())  # 병합 후 디버깅 출력

        # 유효하지 않은 끝부분 제거: 'price' 가 0인 행 제거
        print(f"Filtering combined data for {stock}.")  # 필터링 전 디버깅 메시지
        combined_df = combined_df[(combined_df['price'] != 0)]
        print('Filtered combined_df:', combined_df.head())  # 필터링 후 디버깅 출력

        # CSV 파일로 내보내기
        await ctx.send(f'Exporting data to CSV for {stock}.')
        safe_ticker = stock.replace('/', '-')
        file_path = os.path.join(config.STATIC_IMAGES_PATH, f'result_VOO_{safe_ticker}.csv')
        await ctx.send(f'Saving results to {file_path}.')
        combined_df.to_csv(file_path, float_format='%.2f', index=False)
        
        # CSV 파일 간소화
        await ctx.send(f'Simplifying CSV for {stock}.')
        await save_simplified_csv(stock)

        # 파일 이동 및 깃헙 커밋/푸시
        await move_files_to_images_folder()
        await bot.change_presence(status=discord.Status.online, activity=discord.Game("Waiting"))
        await ctx.send(f"Backtest and send process completed successfully for {stock}.")
    
    except Exception as e:
        error_message = f"An error occurred while processing {stock}: {e}"
        error_trace = traceback.format_exc()  # 스택 트레이스 추가
        await ctx.send(error_message)
        await ctx.send(f"Traceback: {error_trace}")  # 스택 트레이스도 전송
        print(error_message)
        print(error_trace)  # 스택 트레이스 콘솔에도 출력


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
    stock = "AAPL"
    
    try:
        # 캐시 확인 및 데이터 가져오기
        if config.is_cache_valid(config.VOO_CACHE_FILE, config.START_DATE, config.END_DATE):
            print(f"Using cached VOO data for testing.")
        else:
            print(f"VOO cache is not valid or missing. New data will be fetched.")

        # backtest_and_send 함수 실행
        await backtest_and_send(ctx, stock, option_strategy='default', bot=bot)
        
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



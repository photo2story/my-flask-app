# backtest_send.py
import os, sys
import pandas as pd
import matplotlib.pyplot as plt
import asyncio
from datetime import datetime  # 날짜 처리 추가

# 루트 디렉토리를 sys.path에 추가하여 config.py를 불러올 수 있게 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'my-flask-app')))
import config  # config 모듈을 불러옵니다.

# 사용자 정의 모듈 임포트
from Results_plot import plot_comparison_results
from get_ticker import get_ticker_name, is_valid_stock
from get_compare_stock_data import save_simplified_csv
from git_operations import move_files_to_images_folder
from Get_data import get_stock_data
import My_strategy
from Data_export import export_csv

option_strategy = config.option_strategy  # 시뮬레이션 전략 설정

async def get_voo_data(option_strategy, ctx):
    if config.is_cache_valid(config.VOO_CACHE_FILE, config.START_DATE):
        await ctx.send("Using cached VOO data.")
        cached_voo_data = pd.read_csv(config.VOO_CACHE_FILE)
        return cached_voo_data
    else:
        await ctx.send("Fetching new VOO data.")
        stock_data2, _ = get_stock_data('VOO', config.START_DATE, config.END_DATE)
        result_df2 = My_strategy.my_strategy(stock_data2, option_strategy)
        result_df2.rename(columns={'rate': 'rate_vs'}, inplace=True)
        
        await ctx.send("Saving new VOO data to cache.")
        result_df2.to_csv(config.VOO_CACHE_FILE, index=False)
        return result_df2

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
        # VOO 데이터 가져오기 (캐시된 데이터 사용 또는 새로 가져오기)
        result_df2 = await get_voo_data(option_strategy, ctx)
        
        # VOO 데이터의 최종 날짜 가져오기 및 변환
        voo_last_date = result_df2['Date'].max()

        # voo_last_date가 Timestamp 객체일 경우, 이를 datetime.date 객체로 변환
        if isinstance(voo_last_date, pd.Timestamp):
            voo_last_date = voo_last_date.date()

        # END_DATE와 비교하여 더 작은 값 선택
        end_date = min(voo_last_date, datetime.strptime(config.END_DATE, '%Y-%m-%d').date())
        
        await ctx.send(f'Fetching data for {stock} up to {end_date}.')
        
        # 주식 데이터 가져오기 (재설정된 END_DATE 사용)
        stock_data, _ = get_stock_data(stock, config.START_DATE, end_date)
        await ctx.send(f'Running strategy for {stock}.')
        result_df = My_strategy.my_strategy(stock_data, option_strategy)
        
        await ctx.send(f'Combining data for {stock} with VOO data.')
        
        # 주식 데이터와 VOO 데이터 병합
        combined_df = result_df.merge(result_df2[['Date', 'rate_vs']], on='Date', how='left')

        # 누락된 값을 0으로 채우기
        combined_df.fillna(method='ffill', inplace=True)  # 이전 값으로 채우기

        # 주요 거래 데이터 열 정의
        main_columns = ['price', 'Open', 'High', 'Low', 'Close', 'Volume']

        # 주요 거래 데이터가 모두 유효한 행만 유지
        combined_df = combined_df[combined_df[main_columns].apply(lambda row: all(row != 0) and all(row.notna()), axis=1)]

        # 병합 후 마지막 날짜 점검
        last_date_combined = combined_df['Date'].max()
        await ctx.send(f'Final date in combined data: {last_date_combined}')

        # 안전한 파일 이름 생성
        safe_ticker = stock.replace('/', '-')
        file_path = os.path.join(config.STATIC_IMAGES_PATH, f'result_VOO_{safe_ticker}.csv')

        # 파일 저장
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



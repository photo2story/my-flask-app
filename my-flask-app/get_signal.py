#### get_signal.py

import pandas as pd
import numpy as np
NaN = np.nan

from Get_data import calculate_rsi, calculate_ppo  # 통일된 함수를 utils.py에 작성했다고 가정

def calculate_ppo_buy_sell_signals(stock_data, index, short_window, long_window, signal_window):
    # PPO 히스토그램 계산
    ppo, ppo_signal, ppo_histogram = calculate_ppo(stock_data['Close'], short_window, long_window, signal_window)
    
    # 매수/매도 신호 결정
    SMA_20_turn = stock_data['SMA_10'].iloc[index] > stock_data['SMA_20'].iloc[index]
    SMA_60_turn = stock_data['SMA_20'].iloc[index] > stock_data['SMA_60'].iloc[index] and stock_data['SMA_60'].iloc[index] > stock_data['SMA_120'].iloc[index]
    PPO_BUY = SMA_60_turn and ppo_histogram.iloc[index] > 1.1
    PPO_SELL = not SMA_20_turn and ppo_histogram.iloc[index] < 1.1

    # ppo_histogram을 stock_data에 저장
    stock_data.loc[index, 'ppo_histogram'] = ppo_histogram.iloc[index]
    
    return PPO_BUY, PPO_SELL, ppo_histogram.iloc[index], SMA_20_turn, SMA_60_turn



# 테스트를 위한 예제 데이터 생성
def create_example_data():
    np.random.seed(0)  # 결과 일관성을 위해 시드 설정
    dates = pd.date_range(start="2020-01-01", periods=100)
    close_prices = np.random.uniform(100, 200, size=100)
    stock_data = pd.DataFrame({'Close': close_prices}, index=dates)
  
    # SMA_60과 SMA_120 추가
    stock_data['SMA_10'] = stock_data['Close'].rolling(window=10).mean()
    stock_data['SMA_20'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['SMA_60'] = stock_data['Close'].rolling(window=60).mean()
    stock_data['SMA_120'] = stock_data['Close'].rolling(window=120).mean()
    return stock_data
  
# 테스트 코드
if __name__ == "__main__":
    stock_data = create_example_data()

    # PPO 매수 및 매도 신호 계산
    # 여기서는 마지막 날짜(인덱스 99)에 대한 신호를 계산합니다.
    PPO_BUY, PPO_SELL, SMA_20_turn, SMA_60_turn  = calculate_ppo_buy_sell_signals(stock_data, 99, short_window=12, long_window=26, signal_window=9)

    print("PPO Buy Signal:", PPO_BUY)
    print("PPO Sell Signal:", PPO_SELL)
    print("SMA 20 Turn:", SMA_20_turn)
    print("SMA 60 Turn:", SMA_60_turn)
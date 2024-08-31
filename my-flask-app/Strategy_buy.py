# Strategy_buy.py

from datetime import datetime

def strategy_buy(current_date, price, performance, PPO_BUY, option_strategy):
    # 초기화
    perform_buy_amount = 0
    buy_signal = None

    # 기본 전략: PPO_BUY 시 100%, 아니면 50% 투자
    if option_strategy == 'default':
        perform_buy_amount = 1.0 if PPO_BUY else 0.5
    
    # 변형 적립식 전략: 수익률이 양수일 때만 투자하지 않음
    elif option_strategy == 'modified_monthly':
        current_month = current_date.month
        if performance > 0 and (current_month >= 5 and current_month <= 10):
            perform_buy_amount = 0  # 5월부터 10월까지 수익률이 양수인 경우 매수하지 않음
        else:
            perform_buy_amount = 1.0 if PPO_BUY else 0.5
    
    # 적립식 투자 전략: 매월 100% 투자
    elif option_strategy == 'monthly':
        perform_buy_amount = 1.0
    
    # 매수 신호 설정
    if perform_buy_amount > 0:
        buy_percent = int(perform_buy_amount * 100)
        buy_signal = f'buy {buy_percent}%'

    return perform_buy_amount, buy_signal




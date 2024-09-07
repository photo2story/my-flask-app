# My_strategy.py
def my_strategy(stock_data, option_strategy):
    result = []  # 거래 결과를 초기화, 저장하는 용도
    portfolio_value = 0  # 계좌 잔고
    cash = config.INITIAL_INVESTMENT  # 현금
    deposit = 0  # 보관금
    invested_amount = config.INITIAL_INVESTMENT
    monthly_investment = config.MONTHLY_INVESTMENT
    account_balance = 0
    shares = 0
    recent_high = 0
    recent_low = float('inf')
    Invest_day = False
    Sudden_fall = False
    signal = ''
    prev_month = None  # 현재 월을 비교하여 다르다면, 이는 새로운 달이 시작
    currency = 1
    stock_ticker = stock_data.iloc[0]['Stock']
    
    if '.K' in stock_ticker or stock_data.iloc[0]['Sector'] == 'KRX':
        currency = 1
    
    PPO_BUY = False  # Initialize neither buy nor sell signal is active
   

    PPO_SELL = False

    # Initialize the first trading day and first saving day
    first_trading_day, first_saving_day = config.initialize_trading_days(stock_data)

    # Loop over data
    for i, row in stock_data.iterrows():
        current_date = row.name
        
        # 매달 적립 수행
        cash, invested_amount, signal, prev_month = config.monthly_deposit(current_date, prev_month, monthly_investment, cash, invested_amount)
        
        # 투자 결정 확인
        Invest_day = config.should_invest_today(current_date, first_trading_day)
        
        # Calculate current price and performance
        price = row['Close'] * currency  # 종가(원화환산)
        Open = row['Open'] * currency  # 개장가(원화환산)
        High = row['High'] * currency  # 최고가(원화환산)
        Low = row['Low'] * currency  # 최저가(원화환산)
        Close = row['Close'] * currency  # 종가(원화환산)
        Volume = row['Volume']  # 거래량
        performance = (price - recent_high) / recent_high if recent_high else 0
  
        # Update recent high and low
        recent_high = max(recent_high, price)
        recent_low = min(recent_low, price)

        # 사용할 지표들
        rsi_ta = row['RSI_14']
        mfi_ta = row['MFI_14']
        bb_upper_ta = row['bb_upper_ta']
        bb_lower_ta = row['bb_lower_ta']
        aroon_up_ta = row['AROONU_25']
        aroon_down_ta = row['AROOND_25']
        sma05_ta = row['SMA_5']
        sma20_ta = row['SMA_20']
        sma60_ta = row['SMA_60']
        sma120_ta = row['SMA_120']
        sma240_ta = row['SMA_240']
        stochk_ta = row['STOCHk_20_10_3']
        stochd_ta = row['STOCHd_20_10_3']
        
        # Get_data에서 이미 계산된 PPO histogram 값 사용
        ppo_histogram = row['ppo_histogram']

        # SMA 20 및 SMA 60 교차점 체크
        SMA_20_turn = sma20_ta > sma60_ta
        SMA_60_turn = sma60_ta > sma120_ta

        # PPO 매수 및 매도 신호 계산 (이미 ppo_histogram이 계산됨)
        PPO_BUY = SMA_60_turn and ppo_histogram > 1.1
        PPO_SELL = not SMA_20_turn and ppo_histogram < 1.1

        # 수수료 적용
        buy_price = price * 1.005  # 매수 시 수수료 0.5% 적용
        sell_price = price * 0.995  # 매도 시 수수료 0.5% 적용

        if performance < -0.4 and (aroon_up_ta == 0 and bb_lower_ta > row['Close']): 
            Sudden_fall = True 
            signal = 'Sudden fall'
            shares_to_sell = 0.5 * shares 
            shares -= shares_to_sell 
            cash += shares_to_sell * sell_price * 0.5 
            deposit += shares_to_sell * sell_price * 0.5 
            signal = 'sell 50 %' + ' ' + signal

        if Sudden_fall:
            if SMA_60_turn or PPO_BUY:
                shares_to_buy_depot = 0.5 * max(0, deposit) // buy_price 
                shares_to_buy_cash = 1.0 * max(0, cash) // buy_price 
                shares += shares_to_buy_depot + shares_to_buy_cash 
                deposit -= shares_to_buy_depot * buy_price 
                cash -= shares_to_buy_cash * buy_price 
                signal = 'sudden fall + sma trend rise'
                Sudden_fall = False
        elif Invest_day and PPO_BUY:
            shares_to_buy = 0.5 * min(cash, monthly_investment) // buy_price
            shares += shares_to_buy
            cash -= shares_to_buy * buy_price
            signal = 'weekly trade' + ' ' + signal

        if portfolio_value >= 2 * invested_amount and cash > invested_amount and not PPO_BUY:
            shares_to_sell = 0.5 * shares
            shares -= shares_to_sell
            cash += shares_to_sell * sell_price * 0.5
            deposit += shares_to_sell * sell_price * 0.5
            signal = 'Act1 end!  sell 50%' + ' ' + signal

        sell_result = strategy_sell(current_date, rsi_ta, PPO_SELL, stock_ticker, Sudden_fall, option_strategy)
        
        if isinstance(sell_result, tuple):
            ta_sell_amount, sell_signal, Sudden_fall = sell_result
        else:
            ta_sell_amount = sell_result
            sell_signal = '' + ' ' + signal

        if Invest_day and ta_sell_amount > 0:
            shares_to_sell = ta_sell_amount * shares
            shares -= shares_to_sell
            cash += shares_to_sell * sell_price
            signal = sell_signal + ' ' + signal

        buy_result = strategy_buy(current_date, price, performance, PPO_BUY, option_strategy)
        
        if isinstance(buy_result, tuple):
            perform_buy_amount, buy_signal = buy_result
        else:
            perform_buy_amount = buy_result
            buy_signal = '' + signal

        if Invest_day and perform_buy_amount > 0:
            shares_to_buy = perform_buy_amount * cash // buy_price
            shares += shares_to_buy
            cash -= shares_to_buy * buy_price
            signal = 'week +' + buy_signal + ' ' + signal

        portfolio_value = shares * price
        account_balance = portfolio_value + cash + deposit

        rate = (account_balance / invested_amount - 1) * 100

        result.append([
            current_date, price/currency, Open/currency, High/currency, 
            Low/currency, Close/currency, Volume, bb_upper_ta, bb_lower_ta, 
            sma05_ta, sma20_ta, sma60_ta, sma120_ta, sma240_ta, 
            recent_high/currency, aroon_up_ta, aroon_down_ta, ppo_histogram, 
            SMA_20_turn, SMA_60_turn, recent_low/currency, account_balance, 
            deposit, cash, portfolio_value, shares, rate, invested_amount, 
            signal, rsi_ta, stochk_ta, stochd_ta, stock_ticker
        ])
    # result 리스트를 데이터프레임으로 변환하여 반환
    result_df = pd.DataFrame(result, columns=[
        'Date', 'price', 'Open', 'High', 'Low', 'Close', 'Volume', 
        'bb_upper_ta', 'bb_lower_ta', 'sma05_ta', 'sma20_ta', 'sma60_ta', 'sma120_ta', 
        'sma240_ta', 'Recent_high', 'aroon_up_ta', 'aroon_down_ta', 'ppo_histogram', 
        'SMA_20_turn', 'SMA_60_turn', 'Recent_low', 'account_balance', 
        'deposit', 'cash', 'portfolio_value', 'shares', 'rate', 'invested_amount', 
        'signal', 'rsi_ta', 'stochk_ta', 'stochd_ta', 'stock_ticker'
    ])

    return result_df


# python My_strategy.py


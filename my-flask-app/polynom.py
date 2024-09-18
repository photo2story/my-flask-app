# polynom.py

import pandas as pd
import numpy as np
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import os
import config

def calculate_growth_rate(series, years):
    """ Calculate annualized growth rate based on the last `years` data points. """
    if len(series) < 1:
        return 0
    start_value = series.iloc[-years]
    end_value = series.iloc[-1]
    growth_rate = (end_value / start_value) ** (1 / years) - 1
    return growth_rate

def perform_prophet_prediction(ticker, target_column):
    file_path = os.path.join(config.STATIC_IMAGES_PATH, f'result_VOO_{ticker}.csv')
    data = pd.read_csv(file_path)
    
    # Prophet requires columns named 'ds' and 'y'
    df = pd.DataFrame({
        'ds': pd.to_datetime(data['Date']),
        'y': data[target_column]
    }).dropna()
    
    # Fit the model
    model = Prophet(yearly_seasonality=True, daily_seasonality=False, weekly_seasonality=False)
    model.fit(df)
    
    # Create future dataframe for predictions
    future_dates = model.make_future_dataframe(periods=365*10)  # 10 years into the future
    
    # Make predictions
    forecast = model.predict(future_dates)
    
    # Function to get the closest date prediction
    def get_closest_prediction(target_date):
        closest_date = min(forecast['ds'], key=lambda x: abs(x - target_date))
        return forecast[forecast['ds'] == closest_date]['yhat'].values[0]
    
    # Get predictions for 3, 5, and 10 years in the future
    last_date = df['ds'].iloc[-1]
    predict_3 = get_closest_prediction(last_date + pd.DateOffset(years=3))
    predict_5 = get_closest_prediction(last_date + pd.DateOffset(years=5))
    predict_10 = get_closest_prediction(last_date + pd.DateOffset(years=10))
    
    # 추세 보정: 최근 몇 년 간의 성장률을 계산하여 반영
    growth_rate = calculate_growth_rate(df['y'], 5)  # 최근 5년 성장률
    adjusted_predict_3 = predict_3 * (1 + growth_rate * 3)  # 3년 후 예측 보정
    adjusted_predict_5 = predict_5 * (1 + growth_rate * 5)  # 5년 후 예측 보정
    adjusted_predict_10 = predict_10 * (1 + growth_rate * 10)  # 10년 후 예측 보정
    
    # Perform cross-validation
    df_cv = cross_validation(model, initial='730 days', period='180 days', horizon='365 days')
    df_p = performance_metrics(df_cv)
    rmse = df_p['rmse'].mean()
    
    return adjusted_predict_3, adjusted_predict_5, adjusted_predict_10, rmse

def perform_combined_prediction_with_voo(ticker, sp500_ticker='VOO'):
    # VOO 데이터를 먼저 예측 (rate_vs 컬럼 사용)
    voo_predict_3, voo_predict_5, voo_predict_10, voo_rmse = perform_prophet_prediction(sp500_ticker, 'rate_vs')
    
    # 개별 주식의 예측 (rate 컬럼 사용)
    stock_predict_3, stock_predict_5, stock_predict_10, stock_rmse = perform_prophet_prediction(ticker, 'rate')
    
    return stock_predict_3, stock_predict_5, stock_predict_10, voo_rmse, stock_rmse

# 테스트 코드
if __name__ == "__main__":
    stock_ticker = "TSLA"
    sp500_ticker = "VOO"

    predict_3, predict_5, predict_10, voo_rmse, stock_rmse = perform_combined_prediction_with_voo(stock_ticker, sp500_ticker)

    print(f"{stock_ticker} 3년 후 예측 값: {predict_3}")
    print(f"{stock_ticker} 5년 후 예측 값: {predict_5}")
    print(f"{stock_ticker} 10년 후 예측 값: {predict_10}")
    print(f"VOO RMSE: {voo_rmse}")
    print(f"{stock_ticker} RMSE: {stock_rmse}")

# python polynom.py

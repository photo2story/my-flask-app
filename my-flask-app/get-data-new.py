import FinanceDataReader as fdr

# Apple 주식(AAPL) 데이터를 테스트로 가져오기
try:
    stock_data = fdr.DataReader('AAPL', '2023-01-01', '2023-12-31')
    print(stock_data.head())  # 데이터가 정상적으로 가져와지는지 확인
except Exception as e:
    print(f"오류 발생: {e}")


## python get-data-new.py 실행 결과    
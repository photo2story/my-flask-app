import FinanceDataReader as fdr

# Apple 주식(AAPL) 데이터를 테스트로 가져오기
try:
    stock_data = fdr.DataReader('AAPL', '2023-01-01', '2023-12-31')
    print(stock_data.head())  # 데이터가 정상적으로 가져와지는지 확인
except Exception as e:
    print(f"오류 발생: {e}")
    
cache_dir = os.path.expanduser("~/.cache/FinanceDataReader")  # 캐시 경로
if os.path.exists(cache_dir):
    os.system(f"rm -rf {cache_dir}")  # 캐시 삭제    


## python Get_data2.py    
import pandas as pd

# CSV 파일 읽기 (UTF-8 인코딩)
file_path = 'stock_market.csv'
df = pd.read_csv(file_path, encoding='utf-8')

# NaN 값을 적절한 값으로 대체
df['Sector'].fillna('Unknown Sector', inplace=True)
df['Stock'].fillna('Unknown Stock', inplace=True)
df['Industry'].fillna('Unknown Industry', inplace=True)
df['Beta'].fillna(0, inplace=True)

# 변경된 데이터프레임을 다시 CSV 파일로 저장 (UTF-8 인코딩)
df.to_csv(file_path, index=False, encoding='utf-8')

print("CSV 파일이 성공적으로 업데이트되었습니다.")

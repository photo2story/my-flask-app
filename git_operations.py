# git_operations.py
import git
import os
import glob
import shutil
import requests
import pandas as pd
import io

# 리포지토리 경로 설정
repo_path = os.path.abspath(os.path.dirname(__file__))  # 현재 디렉토리의 절대 경로를 사용

# 리포지토리 객체 생성
try:
    repo = git.Repo(repo_path)
except git.exc.InvalidGitRepositoryError:
    print(f'Invalid Git repository at path: {repo_path}')
    repo = None

# 외부 URL에서 CSV 데이터를 가져오는 함수
def fetch_csv_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTP 에러가 발생하면 예외 발생
        csv_data = response.content.decode('utf-8')
        return pd.read_csv(io.StringIO(csv_data))
    except requests.exceptions.RequestException as e:
        print(f'Error fetching CSV data: {e}')
        return None

async def move_files_to_images_folder():
    if repo is None:
        print('No valid Git repository. Skipping git operations.')
        return

    patterns = ["*.png", "*.csv", "*.report","*.txt"]
    destination_folder = os.path.join('static', 'images')  # 'app.static_folder' 대신 경로를 명시적으로 설정

    # 외부 URL에서 CSV 데이터 다운로드
    df = fetch_csv_data(csv_url)
    if df is not None:
        csv_path = os.path.join(destination_folder, 'stock_market.csv')
        os.makedirs(destination_folder, exist_ok=True)
        df.to_csv(csv_path, index=False)
        print(f"Downloaded CSV to {csv_path}")
    else:
        print("Failed to download CSV data.")

    for pattern in patterns:
        for file in glob.glob(pattern):
            if file != "stock_market.csv":
                shutil.move(file, os.path.join(destination_folder, os.path.basename(file)))
                print(f"Moved {file} to {destination_folder}")

    # 파일 이동 후 깃허브 커밋 및 푸시
    try:
        repo.git.add(all=True)  # 모든 변경 사항 추가
        repo.index.commit('Auto-commit moved files')
        origin = repo.remote(name='origin')
        origin.push()
        print('Changes pushed to GitHub')
    except Exception as e:
        print(f'Error during git operations: {e}')

# CSV 파일 URL
csv_url = 'https://raw.githubusercontent.com/photo2story/my-flutter-app/main/my-flask-app/stock_market.csv'

# CSV 데이터 가져오기 예시
df = fetch_csv_data(csv_url)
if df is not None:
    print(df.head())
else:
    print("Failed to fetch CSV data.")




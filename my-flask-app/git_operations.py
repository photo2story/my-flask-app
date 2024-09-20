# git_operations.py
import git
import os
import glob
import shutil
import requests
import pandas as pd
import io
import config

# 리포지토리 경로 설정
# repo_path = os.path.abspath(os.path.dirname(__file__))  # 현재 디렉토리의 절대 경로를 사용
# 프로젝트 루트 경로 설정
repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
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
        response.raise_for_status()
        csv_data = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_data))

        # 문자열 열에 대해서만 빈 문자열로 채우고, 숫자형 열은 0으로 채우기
        df[df.select_dtypes(['object']).columns] = df.select_dtypes(['object']).fillna('')
        df[df.select_dtypes(['number']).columns] = df.select_dtypes(['number']).fillna(0)

        return df
    except requests.exceptions.RequestException as e:
        print(f'Error fetching CSV data: {e}')
        return None



import base64

# 파일을 GitHub 저장소에 업로드하는 함수 (토큰 없이)
def upload_file_to_github(file_path, repo_name, destination_path):
    with open(file_path, 'rb') as file:
        content = file.read()

    base64_content = base64.b64encode(content).decode('utf-8')

    url = f'https://api.github.com/repos/{repo_name}/contents/{destination_path}'

    data = {
        "message": f"Add {os.path.basename(file_path)}",
        "content": base64_content
    }

    # 토큰 없이 요청 보냄
    response = requests.put(url, json=data)

    if response.status_code == 201:
        print(f'Successfully uploaded {file_path} to GitHub')
    else:
        print(f'Error uploading {file_path} to GitHub: {response.status_code}, {response.text}')

# 비동기 함수 수정: 로컬 이동 후 원격으로 파일 업로드
async def move_files_to_images_folder():
    if repo is None:
        print('No valid Git repository. Skipping git operations.')
        return

    patterns = ["*.png", "*.csv", "*.report", "*.txt"]
    destination_folder = config.STATIC_IMAGES_PATH

    # GitHub 저장소 관련 정보
    repo_name = "photo2story/my-flask-app"  # 퍼블릭으로 만든 GitHub 저장소 경로

    for pattern in patterns:
        for file in glob.glob(pattern):
            if file != "stock_market.csv":
                shutil.move(file, os.path.join(destination_folder, os.path.basename(file)))  # 로컬 파일 이동
                print(f"Moved {file} to {destination_folder}")

                # 원격 GitHub 저장소에 파일 업로드 (토큰 없이)
                destination_path = f"static/images/{os.path.basename(file)}"
                upload_file_to_github(os.path.join(destination_folder, os.path.basename(file)), repo_name, destination_path)

    # 파일 이동 후 로컬 Git 커밋 및 푸시
    try:
        repo.git.add(all=True)  # 모든 변경 사항 추가
        repo.index.commit('Auto-commit moved files')
        origin = repo.remote(name='origin')
        origin.push()
        print('Changes pushed to GitHub')
    except Exception as e:
        print(f'Error during git operations: {e}')


# CSV 파일 URL
# csv_url = 'https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/stock_market.csv'
csv_url = config.CSV_PATH

# 테스트 코드
if __name__ == "__main__":
    # df = fetch_csv_data(csv_url)
    # csv파일을 읽어온다.
    df = pd.read_csv(csv_url)
    if df is not None:
        print(df.head())
    else:
        print("Failed to fetch CSV data.")

# python git_operations.py



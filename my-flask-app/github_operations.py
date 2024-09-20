# github_operations.py
import requests
import base64
import os
import pandas as pd
from dotenv import load_dotenv
import config

load_dotenv()

GITHUB_TOKEN = os.getenv('PERSONAL_ACCESS_TOKEN')
GITHUB_REPO_OWNER = os.getenv('GITHUB_REPO_OWNER')
GITHUB_REPO_NAME = os.getenv('GITHUB_REPO_NAME')

ticker_path = 'https://raw.githubusercontent.com/photo2story/my-flask-app/main/static/images/stock_market.csv'
ticker_path = config.CSV_PATH

def save_csv_to_github(dataframe, file_name, commit_message):
    url = f'https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{file_name}'
    csv_content = dataframe.to_csv(index=False)

    response = requests.get(url, headers={'Authorization': f'token {GITHUB_TOKEN}'})
    if response.status_code == 200:
        sha = response.json()['sha']
    else:
        sha = None

    data = {
        'message': commit_message,
        'content': base64.b64encode(csv_content.encode()).decode(),
        'branch': 'main',
        'sha': sha
    }
    response = requests.put(url, headers={'Authorization': f'token {GITHUB_TOKEN}'}, json=data)
    if response.status_code == 201 or response.status_code == 200:
        print(f'Successfully saved {file_name} to GitHub')
    else:
        print(f'Failed to save {file_name} to GitHub: {response.json()}')

def save_image_to_github(image_path, commit_message):
    url = f'https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{os.path.basename(image_path)}'

    with open(image_path, 'rb') as image_file:
        image_content = base64.b64encode(image_file.read()).decode()

    response = requests.get(url, headers={'Authorization': f'token {GITHUB_TOKEN}'})
    if response.status_code == 200:
        sha = response.json()['sha']
    else:
        sha = None

    data = {
        'message': commit_message,
        'content': image_content,
        'branch': 'main',
        'sha': sha
    }
    response = requests.put(url, headers={'Authorization': f'token {GITHUB_TOKEN}'}, json=data)
    if response.status_code == 201 or response.status_code == 200:
        print(f'Successfully saved {os.path.basename(image_path)} to GitHub')
    else:
        print(f'Failed to save {os.path.basename(image_path)} to GitHub: {response.json()}')

# def is_valid_stock(stock):
#     try:
#         stock_market_df = pd.read_csv(ticker_path)
#         return stock in stock_market_df['Symbol'].values
#     except Exception as e:
#         print(f"Error checking stock market CSV: {e}")
#         return False

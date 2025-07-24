# from notion_client import Client # Notionを操作する準備
# from dotenv import load_dotenv # 環境変数の読み込み
from bs4 import BeautifulSoup # スクレイピング
import requests, json, os, typing

# .envファイルを読み込む
# load_dotenv()

# --- Annict設定 ---
ANNICT_TOKEN = os.getenv('ANNICT_TOKEN')

# --- Notion設定 ---
# NOTION_TOKEN = Client(auth=os.getenv('NOTION_TOKEN'))
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('DATABASE_ID')

# --- スクレイピング設定 --
ANNICT_URL = 'https://api.annict.com/v1/works?'
NOTION_URL = 'https://api.notion.com'

# --- 定数の設定 ---

# --- アプリ内ルール ---
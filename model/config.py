from notion_client import Client # Notionを操作する準備
from dotenv import load_dotenv # 環境変数の読み込み
import os, typing

# .envファイルを読み込む
load_dotenv()

# --- Annict設定 ---
ANNICT_TOKEN = os.getenv('ANNICT_TOKEN')

# --- Notion設定 ---
NOTION_TOKEN = Client(auth=os.getenv('NOTION_TOKEN'))
# NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('DATABASE_ID')

# --- スクレイピング設定 --
ANNICT_URL = 'https://api.annict.com/v1/works?'
NOTION_URL = 'https://api.notion.com'

# --- 定数の設定 ---
WAITE_TIME = 2
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
# F12 > console > navigator.userAgent
# UESR_AGENT = 
CHROMEDRIVER_PATH = 'C:/Users/frontier-Python/Desktop/AniTime_app/chromedriver.exe'
# CHROMEDRIVER_PATH = 'C:\Users\frontier-Python\Desktop\AniTime_app\chromedriver.exe'

# --- アプリ内ルール ---
from notion_client import Client  # Notionを操作する準備
from dotenv import load_dotenv  # 環境変数の読み込み
import os

# .envファイルを読み込む
load_dotenv()

# --- Annict設定 ---
ANNICT_TOKEN = os.getenv("ANNICT_TOKEN")

# --- Notion設定 ---
NOTION_TOKEN = Client(auth=os.getenv("NOTION_TOKEN"))
DATABASE_ID = os.getenv("DATABASE_ID")
# NOTION_TOKEN = os.getenv("NOTION_TOKEN")

# --- ベースURL設定 --
ANNICT_WORK_URL = "https://api.annict.com/v1/works?"
ANNICT_STAFFS_URL = "https://api.annict.com/v1/staffs?"
NOTION_URL = "https://api.notion.com"

# --- 定数の設定 ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
DATABASE_TITLE = "anime_schedule_db"


# ---Notionのヘッダ情報の設定---
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


"""プラットフォームホワイトリスト一覧（適宜追加）"""
PLATFORMS = (
    "ABEMA",
    "dアニメストア",
    "Prime Video",
    "Netflix",
    "U-NEXT",
    "FOD",
    "AnimeFesta",
    "Hulu",
    "DMM TV",
    "アニメタイムズ",
    "Lemino",
    "Disney+（ディズニープラス）",
)

# --- アプリ内ルール ---
"""
配信開始フラグ
0:未配信
1:配信済み
"""
IS_START = 0

# スコア補正に使う語彙
CONTEXT_KEYWORDS = {
    "地上波同時": 3,
    "同時配信": 3,
    "見放題最速配信！": 4,
    "最速": 4,
    "1週間先行": 4,
    "地上波3日間先行": 4,
    "独占": 3,
    "見逃し": -3,
}

# アニメ放送枠
FRAME_KEYWORDS = {
    "ノイタミナ": 4,
    "スーパーアニメイズムTURBO": 3,
    "FRIDAY ANIME NIGHT": 3,
    "アガルアニメ": 2,
    "+Ultra": 2,
    "IMAnimation": 3,
}


# metaタグの範囲拡大
META_DATE_KEYS = [
    {"name": "date"},
    {"property": "og:updated_time"},
    {"property": "og:published_time"},
    {"property": "article:published_time"},
    {"itemprop": "datePublished"},
]

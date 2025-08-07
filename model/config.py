from notion_client import Client  # Notionを操作する準備
from dotenv import load_dotenv  # 環境変数の読み込み
import os

# .envファイルを読み込む
load_dotenv()

# --- Annict設定 ---
ANNICT_TOKEN = os.getenv("ANNICT_TOKEN")

# --- Notion設定 ---
NOTION_TOKEN = Client(auth=os.getenv("NOTION_TOKEN"))
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

# --- ベースURL設定 --
ANNICT_WORK_URL = "https://api.annict.com/v1/works?"
ANNICT_STAFFS_URL = "https://api.annict.com/v1/staffs?"
NOTION_URL = "https://api.notion.com"

# --- 定数の設定 ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"

"""プラットフォームホワイトリスト一覧（適宜追加）"""
PLATFORMS = (
    "Prime Video",
    "dアニメストア",
    "ABEMA",
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
    "地上波同時": 2,
    "同時配信": 2,
    "最速": 3,
    "1週間先行": 3,
    "独占": 3,
    "見逃し": -2,
}

# アニメ放送枠
FRAME_KEYWORDS = {
    "ノイタミナ": 3,
    "スーパーアニメイズムTURBO": 3,
    "FRIDAY ANIME NIGHT": 2,
    "アガルアニメ": 2,
    "+Ultra": 2,
    "IMAAnimation": 2,
}

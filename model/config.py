from dotenv import load_dotenv  # 環境変数の読み込み
import os

# .envファイルを読み込む
load_dotenv()

# --- Annict設定 ---
ANNICT_TOKEN = os.getenv("ANNICT_TOKEN")

# --- Notion設定 ---
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
# DATABASE_ID = os.getenv("DATABASE_ID")

# --- ベースURL設定 --
ANNICT_WORK_URL = "https://api.annict.com/v1/works?"
ANNICT_STAFFS_URL = "https://api.annict.com/v1/staffs?"
NOTION_URL = "https://api.notion.com"

# --- 定数の設定 ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
DATABASE_NAME = "anime_schedule_db"

PARENT_PAGE_ID = "2509fee9008f803695cacb513e8736a9"

# ---Notionのヘッダ情報の設定---
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


# ---季節の変換用辞書---
convert_season = {
    "winter": "冬",
    "spring": "春",
    "summer": "夏",
    "autumn": "秋"
}

day_of_week = {
  0: "月",
  1: "火",
  2: "水",
  3: "木",
  4: "金",
  5: "土",
  6: "日"
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

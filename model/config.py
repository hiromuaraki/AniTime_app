from notion_client import Client # Notionを操作する準備
from dotenv import load_dotenv # 環境変数の読み込み
import os

# .envファイルを読み込む
load_dotenv()

# --- Annict設定 ---
ANNICT_TOKEN = os.getenv('ANNICT_TOKEN')

# --- Notion設定 ---
NOTION_TOKEN = Client(auth=os.getenv('NOTION_TOKEN'))
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('DATABASE_ID')

# --- ベースURL設定 --
ANNICT_WORK_URL = 'https://api.annict.com/v1/works?'
ANNICT_STAFFS_URL = 'https://api.annict.com/v1/staffs?'
NOTION_URL = 'https://api.notion.com'

# --- 定数の設定 ---
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'

'''プラットフォームホワイトリスト一覧（適宜追加）'''
PLATFORMS = (
    'Prime Video', 'dアニメストア', 'ABEMA', 'Netflix','U-NEXT','FOD','AnimeFesta','Hulu','DMM TV', 
    'アニメタイムズ', 'Lemino', 'Disney+（ディズニープラス）')


ANIME_WAKU = (
  'IMAAnimation', 'スーパーアニメイズムTURBO', 'FRIDAY ANIME NIGHT', 'ノイタミナ', 'アガルアニメ','+Ultra'
)

# --- アプリ内ルール ---
'''
配信開始フラグ
0:未配信
1:配信済み
'''
IS_START = 0

# 修正前
# 正規表現パターン適宜追加
patterns = [
     # ⑥ 月日＋時:：分（コロン）
     r"(\d{1,2})月\s*(\d{1,2})日.*?(\d{1,2})[:：](\d{2})",
     
     # ⑧ 年月日 + 時:：分（コロン）
     r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日.*?(\d{1,2})[:：](\d{2})",
     
     # ⑦ 月日（曜日）＋時分
     r"(\d{1,2})月\s*(\d{1,2})日(?:\([月火水木金土日]\))?\s*(\d{1,2})時(\d{2})分",
     
     # ⑨ 年月日（曜日）+ 時分
     r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日(?:\([月火水木金土日]\))?\s*(\d{1,2})時(\d{2})分",
     
     # ③ 月日 + 時:分（曜日あり） 年なし
     r"(\d{1,2})月\s*(\d{1,2})日(?:（?[月火水木金土日]曜日?）?)?\s*(深夜)?\s*(\d{1,2})[:時：]\s*(\d{2})[分]?",
     
     # ② 年月日だけ（曜日あり）
     r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日（?[月火水木金土日]曜日?）?",     
     
     # ① 年月日（曜日） + 時:分（コロンまたは漢字）
     r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日(?:（?[月火水木金土日]曜日?）?)?\s*(深夜)?\s*(\d{1,2})[:時：]\s*(\d{2})[分]?",
     
     # ④ 曜日 + 時:分（"毎週金曜日23時00分" のような形式）
     r"(毎週)?([月火水木金土日])曜日\s*(深夜)?\s*(\d{1,2})[:時：]\s*(\d{2})[分]?",
     
     # ⑤ 時刻だけ（例：22時～）
     r"(深夜)?\s*(\d{1,2})[:時：]\s*(\d{2})[分]?"
 ]

# patterns = [
#     # ① 年月日 +（任意の曜日）+（任意の「深夜」）+ 時:分 or 時分
#     r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日(?:（?[月火水木金土日]曜日?）?)?\s*(?:より)?\s*(深夜)?\s*(\d{1,2})[:時：]\s*(\d{2})[分]?",

#     # ② 月日 +（任意の曜日）+（任意の「深夜」）+ 時:分 or 時分
#     r"(\d{1,2})月\s*(\d{1,2})日(?:（?[月火水木金土日]曜日?）?)?\s*(?:より)?\s*(深夜)?\s*(\d{1,2})[:時：]\s*(\d{2})[分]?",

#     # ③ 「毎週〇曜日 深夜 or 通常時刻」など、年・月・日がなく曜日と時刻だけのパターン（補足的）
#     # （あなたの主目的には関係しないが、補助情報として使える）
#     r"(?:毎週)?([月火水木金土日])曜日\s*(深夜)?\s*(\d{1,2})[:時：]\s*(\d{2})[分]?"
# ]

import model.config as config
from common.utils import sysdate, get_season
import entity.anime_info as anime_info
import requests


def exists_database_in_page(page_id: str, database_title: str, is_page=False) -> bool:
    """
    親ページ内にdatabaseが存在するか
    存在する場合はデータベースIDを返す.

    Args:
        page_id: 親ページ内のページID
        is_page: dbページの存在フラグ True: db作成済み/ False: 未作成（初回）

    Returns:
        is_page(dbページの存在フラグ)
        None(存在しない場合）
    """
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.get(url, headers=config.headers)
    # 400,500番台なら例外をキャッチし処理を終了
    response.raise_for_status()
    
    data = response.json()
    database_name = (data["results"][0]["child_database"]["title"] if data["results"] else "Non db")
    
    # dbの存在チェック
    # ページのタイトルが存在する＝db作成済み
    if database_name == database_title: is_page = True
    
    return is_page



def create_database(page_id: str, database_title: str) -> str:
    """
    データベースを新規作成.
    
    Args:
        parent_page_id: データベースID（Notionの親のページのID）
        database_title: データベース名（一意）
    
    Returns:
        db_id: データベースID
    """
    year, month, _ = sysdate()
    season = get_season(month+1)
    url = f"{config.NOTION_URL}/v1/databases"
    
    # ヘッダ情報を作成
    payload = {
    "parent": {"type": "page_id", "page_id": page_id},
    "title": [
        {"type": "text", "text": {"content": f'{year}{config.convert_season[season]}{database_title}'}}
    ],
    "properties": {
        "作品ID": {"type": "title", "title": {}},
        "開始済み": {
            "type": "select",
            "select": {
                "options": [
                    {"name": "配信前", "color": "red"},
                    {"name": "配信後", "color": "green"}
                ]
            }
        },
        "配信開始日": {"type": "date", "date": {}},
        "配信時間": {"type": "date", "date": {}},
        "曜日": {
            "type": "select",
            "select": {
                "options": [
                    {"name": "月", "color": "red"},
                    {"name": "火", "color": "gray"},
                    {"name": "水", "color": "brown"},
                    {"name": "木", "color": "orange"},
                    {"name": "金", "color": "yellow"},
                    {"name": "土", "color": "pink"},
                    {"name": "日", "color": "blue"}
                ]
            }
        },
        "Title": {"type": "rich_text", "rich_text": {}},
        "プラットフォーム": {
            "type": "select",
            "select": {
                "options": [
                    {"name": "ABEMA", "color": "pink"},
                    {"name": "dアニメストア", "color": "orange"},
                    {"name": "Prime Video", "color": "blue"},
                    {"name": "Netflix", "color": "red"},
                    {"name": "U-NEXT", "color": "gray"},
                    {"name": "FOD", "color": "default"},
                    {"name": "AnimeFesta", "color": "yellow"},
                    {"name": "Hulu", "color": "green"},
                    {"name": "DMM TV", "color": "pink"},
                    {"name": "アニメタイムズ", "color": "orange"},
                    {"name": "Lemino", "color": "brown"},
                    {"name": "Disney+（ディズニープラス）", "color": "default"}
                ]
            }
        },
        "制作会社": {"type": "rich_text", "rich_text": {}},
        "公式URL": {"type": "url", "url": {}},
        "memo": {"type": "rich_text", "rich_text": {}}
        }
    }
    # テーブルを新規作成
    response = requests.post(url, headers=config.headers, json=payload)
    response.raise_for_status()
    db_id = response.json()["id"].replace("-", "")
    print(f"[INFO] 新規データベース作成完了: {database_title}")
    
    return db_id
    


def create_anime_info(earliest_list: dict) -> dict:
    """
    Notion.テーブルへ登録するヘッダ情報を作成.

    Args:

    Returns:
    
    """
    return {}


def insert(earliest_list: dict, db_id: str) -> bool:
    """
    放送情報の件数分連続してテーブルへ登録.
    
    Args:
        earliest_list: 

    Returns:
        True :成功
        False: 失敗
    """
    return True
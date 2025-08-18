from common.utils import get_sysdate, get_season
from datetime import datetime
import model.config as config
from model.logging_config import setup_logger
import requests

# ロガーの準備
logging = setup_logger(name="default_logger", log_file="./logs/notion.log")

def exists_database_in_page(parent_page_id: str, database_name: str):
    """
    親ページ内にdatabaseが存在するかチェック.
    
    Args:
        parent_page_id: 親ページID
        database_name: データベース（命名規則 年4桁季節anime_schedule_db）

    Returns:
        database_id: データベースID
    """
    url = f"https://api.notion.com/v1/blocks/{parent_page_id}/children"
    response = requests.get(url, headers=config.headers)
    # 400,500番台なら例外をキャッチし処理を終了
    response.raise_for_status()
    
    data = response.json()
    if not data["results"]: return None
    
    # dbの存在チェック
    # ページのタイトルが存在する＝db作成済み（行がある）
    for child_db in data["results"]:
        if child_db["child_database"]["title"] == database_name:
            return child_db["id"]

    return None



def archive_database() -> None:
    """一つ前のDBをアーカイブ化"""
    url = url = f"https://api.notion.com/v1/blocks/{config.PARENT_PAGE_ID}/children"
    
    res = requests.get(url, headers=config.headers)
    res.raise_for_status()
    data = res.json()
    
    old_db = data["results"][-2]
    old_db_id = old_db["id"]
    db_name = old_db["child_database"]["title"]

    # 直近の古いDBをアーカイブ化
    patch_url = f"https://api.notion.com/v1/blocks/{old_db_id}"
    res = requests.patch(patch_url, headers=config.headers, json={"archived": True})
    res.raise_for_status()
    
    logging.info(f"Archived DB：{db_name} database_id: {old_db_id}")



def create_properties() -> dict:
    """プロパティ情報を作成."""
    properties = {
        "ID": {"type": "title", "title": {}},
        "開始": {
            "type": "select",
            "select": {
                "options": [
                    {"name": "×", "color": "red"},
                    {"name": "◯", "color": "green"}
                ]
            }
        },
        "配信日": {"type": "date", "date": {}},
        "配信時間": {"type": "rich_text", "rich_text": {}},
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
            "type": "multi_select",
            "multi_select": {
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
        
    return properties



def create_row(id, date, platform, title, production, url) -> dict:
    """
    行データを作成.

    Args:
        id: 連番ID
        date: [YYYY-MM-DD, HH:MM, 曜日]
        platform: プラットフォーム名
        title: アニメタイトル
        production: 制作会社名
        url: 公式URL

    Returns:
        Notion用のプロパティdict
    """
    dt = datetime.strptime(date[0], "%Y-%m-%d")
    start_date = dt.strftime("%Y-%m-%d")  # Notionに渡す形式（YYYY-MM-DD）
    # ※selectはデータベースにある選択肢と完全一致しないとエラー
    return {
        "ID": {"title": [{"text": {"content": str(id)}}]},
        "開始": {"select": {"name": "×".strip()}},
        "配信日": {"date": {"start": start_date}},
        "配信時間": {"rich_text": [{"text": {"content": date[1]}}]},
        "曜日": {"select": {"name": date[2].strip()}},
        "Title": {"rich_text": [{"text": {"content": title}}]},
        "プラットフォーム": {   
            "multi_select": [{"name": platform.strip()}]
        },
        # "プラットフォーム": {"multi_select": {"name": platform.strip()}},
        "制作会社": {"rich_text": [{"text": {"content": production}}]},
        "公式URL": {"url": url}
        # "memo": {"rich_text": [{"text": {"content": ""}}]}  # 空プロパティは行作成時は設定しない
    }






def create_database(parent_page_id: str, database_name: str) -> str:
    """
    データベース新規作成.
    
    Args:
        parent_page_id: データベースID（Notionの親ページID）
        database_name: データベース名（一意）
        success: データベース成功失敗フラグ
    
    Returns:
        db_id: データベースID
    """
    year, month, _ = get_sysdate()
    # season = get_season(month+1)
    # 検証用
    season = get_season(month+2)
    url = f"{config.NOTION_URL}/v1/databases"
    
    database_title = f"{year}{config.convert_season[season]}{database_name}"
    data = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": f'{database_title}'}}],
        "properties": create_properties()
    }
    
    # 空のDBを新規作成
    res = requests.post(url, headers=config.headers, json=data)
    res.raise_for_status()
    
    # DBの作成に成功した場合のみdb_idを設定
    db_id = ""
    if res.status_code == 200: 
        db_id = res.json()["id"]

    # 古いDBをアーカイブへ移動
    archive_database()
    logging.info(f"新規データベース作成完了: データベースID：{db_id} データベース名：{database_title}")
    
    return db_id



def insert(earliest_list: dict, db_id) -> None:
    """
    放送情報の件数分連続して行をテーブルへ登録.
    
    Args:
        earliest_list: 最速配信情報リスト {title: []}

    Returns:
        None
    """

    nt_url = "https://api.notion.com/v1/pages"
    success_count = 0
    fail_count = 0
    
    # IDは最大値＋1から開始
    current_id = 1
    
    # 配信情報をテーブルへ連続して登録
    for title, earliest_info in earliest_list.items():
        date, platform, production, url = earliest_info
        
        year, month, day = map(int, date[:10].split("-"))
        time_str = date[-8:-3]
        week_idx = datetime(year, month, day).weekday()
        dt = [date[:10], time_str, config.day_of_week[week_idx]]
        
        # 行データ作成
        row_data = create_row(
            current_id,
            dt,
            platform,
            title,
            production,
            url
        )
        
        data = {
            "parent": {"database_id": db_id},
            "properties": row_data
        }
        
        try:
            res = requests.post(nt_url, headers=config.headers, json=data)
            res.raise_for_status()
            logging.info(f"登録成功: {title} ({current_id})")
            success_count += 1
        except requests.exceptions.RequestException as e:
            logging.error(f"登録失敗: {e}, data={data}")
            fail_count += 1
        
        current_id += 1
    logging.info(f"登録処理完了: 成功 {success_count} 件 / 失敗 {fail_count} 件")
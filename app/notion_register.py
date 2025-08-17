from common.utils import get_sysdate, get_season
from datetime import datetime
import notion_client as notion
import model.config as config
import entity.anime_info as anime_info
from model.logging_config import setup_logger
import requests

# ロガーの準備
logging = setup_logger()

def exists_database_in_page(page_id: str, database_title: str, is_page=False) -> bool:
    """
    親ページ内にdatabaseが存在するかチェック.
    
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
    Notion DBに追加する行データを作成

    Args:
        id: 連番ID
        dt: [YYYY-MM-DD, HH:MM, 曜日]
        platform: プラットフォーム名
        title: アニメタイトル
        production: 制作会社名
        url: 公式URL
        db_options: DB上の選択肢リスト（曜日、プラットフォームなど）

    Returns:
        Notion用のプロパティdict
    """
    dt = datetime.strptime(date[0], "%Y-%m-%d")
    start_date = dt.strftime("%Y-%m-%d")  # Notionに渡す形式（YYYY-MM-DD）
    return {
        "ID": {"title": [{"text": {"content": str(id)}}]},
        "開始": {"select": {"name": "×".strip()}},  # データベースに存在する選択肢のみ
        "配信日": {"date": {"start": start_date}},
        "配信時間": {"rich_text": [{"text": {"content": date[1]}}]},
        "曜日": {"select": {"name": date[2].strip()}},  # データベースに存在する選択肢のみ
        "Title": {"rich_text": [{"text": {"content": title}}]},
        "プラットフォーム": {"multi_select": {"name": platform.strip()}},  # データベースに存在する選択肢のみ
        "制作会社": {"rich_text": [{"text": {"content": production}}]},
        "公式URL": {"url": url}
        # "memo": {"rich_text": [{"text": {"content": ""}}]}  # 空文字でもOK
    }





def create_database(page_id: str, database_title: str) -> bool:
    """
    データベースを新規作成.
    
    Args:
        page_id: データベースID（NotionのページID）
        database_title: データベース名（一意）
    
    Returns:
        ok: データベース成功失敗フラグ
    """
    year, month, _ = get_sysdate()
    season = get_season(month+1)
    url = f"{config.NOTION_URL}/v1/databases"
    
    database_title = f"{year}{config.convert_season[season]}{database_title}"
    data = {
        "parent": {"type": "page_id", "page_id": page_id},
        "title": [{"type": "text", "text": {"content": f'{database_title}'}}],
        "properties": create_properties()
    }
    
    # テーブルを新規作成
    success = False
    response = requests.post(url, headers=config.headers, json=data)
    # DBの作成に成功した場合のみTrue
    if response.status_code == 200: success = True
    response.raise_for_status()
    
    # 新規データベースIDへ更新(環境変数は上書きされない)
    config.DATABASE_ID = response.json()["results"][0]["id"]
    print(f"[INFO] 新規データベース作成完了: {database_title}")
    
    return success



def insert(earliest_list: dict) -> bool:
    """
    放送情報の件数分連続してテーブルへ登録.
    
    Args:
        earliest_list: 

    Returns:
        True :成功
        False: 失敗
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
            "parent": {"database_id": config.DATABASE_ID},
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
    return True
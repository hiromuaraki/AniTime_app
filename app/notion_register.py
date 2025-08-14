import model.config as config
import entity.anime_info as anime_info
import requests, json, webbrowser

# 後で消すかも
def format_id_with_hyphens(id: str) -> str:
    """NotionのIDをハイフン付きにフォーマット."""
    return f"{id[0:8]}-{id[8:12]}-{id[12:16]}-{id[16:20]}-{id[20:]}"

# 後で消すかも
def open_in_browser(db_id: str) -> None:
    """データベースIDからURLを生成してブラウザで開く"""
    db_url = f"https://www.notion.so/{format_id_with_hyphens(db_id)}"
    print(f"[INFO] GUIで開くURL: {db_url}")
    webbrowser.open(db_url)



def find_database_in_page(parent_page_id, database_title: str):
    """
    親ページ内にdatabaseが存在するか
    存在する場合はデータベースIDを返す.

    Args:
        parent_page_id:
        database_name:

    Returns:
        id(データベースID)
        None(存在しない場合）
    """
    url = f"https://api.notion.com/v1/blocks/{parent_page_id}/children"
    response = requests.get(url, config.headers)
    # 400,500番台なら例外をキャッチし処理を終了
    response.raise_for_status()
    data = response.json()
    
    for child in data.get("results", []):
        if child["type"] == "child_database":
            if child["child_database"]["title"] == database_title:
                print(f"[INFO] 既存データベースを発見: {database_title}")
                return child["id"]
    return None



def create_database(parent_page_id, database_title: str) -> str:
    """
    データベースを新規作成.
    
    Args:
        parent_page_id: データベースID（Notionの親のページのID）
        database_title: データベー名（一意）
    
    Returns:
        db_id: データベースID
    """
    
    url = f"{config.NOTION_URL}/v1/databases"
    
    # ヘッダ情報を作成
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [
            {
                "type": "text",
                "text": {"content": database_title}
            }
        ],
        "properties": {
            "作品ID": {"title": {}},
            "配信開始日": {"title": {}},
            "配信時間": {"date": {}},
            "曜日": {"date": {}},
            "Title": {"date": {}},
            "プラットフォーム": {
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
            "制作会社": {"date": {}},
            "公式URL": {"date": {}},
            "memo": {"date": {}},
        }
    }
    # テーブルを新規作成
    response = requests.post(url, headers=config.headers, data=json.dumps(payload))
    response.raise_for_status()
    db_id = response.json()["id"].replace("-", "")
    print(f"[INFO] 新規データベース作成完了: {database_title}")
    open_in_browser(db_id)
    
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
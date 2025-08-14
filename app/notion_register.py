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



def find_database_in_page(parent_page_id: str, database_name: str) -> str:
    """
    親ページ内にdatabaseが存在するか
    存在する場合はデータベースIDを返す.

    Args:
        parent_page_id:
        database_name:

    Returns:
        db_id(データベースID)
    """
    return ""



def create_database(parent_page_id: int, database_name: str) -> str:
    """存在しない場合のみデータベースを作成."""
    return ""


def create_anime_info(earliest_list: dict) -> anime_info:
    """
    Notio.テーブルへ登録するヘッダ情報を作成.

    Args:

    Returns:
    
    """


def regist(earliest_list: dict, db_id: int) -> bool:
    """
    放送情報の件数分連続してテーブルへ登録.
    
    Args:
        earliest_list: 

    Returns:
    
    """
    return True
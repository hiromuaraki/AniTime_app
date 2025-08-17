import csv
import model.config as config
import common.utils as utils
from app.annict_get_api import get_works, get_staffs
from app.scraper import scrape_anime_info
from app.notion_register import (
  exists_database_in_page,
  create_database,
  insert
)


save_dir = "./works_info"
WORKS_CSV_FILE = "works_info.csv"
SCHEDULE_CSV_FILE = "anime_release_schedule.csv"
works_file_path = f"./works_info/{WORKS_CSV_FILE}"
schedule_file_path = f"./data/{SCHEDULE_CSV_FILE}"

# 現在の年月日を取得
year, month, _ = utils.get_sysdate()
season = utils.get_season(month+1)

def load_url_map() -> dict:
    """CSVからタイトル-URLマップを読み込む"""
    url_map = {}
    if not utils.exists_file_path(works_file_path):
        return url_map
    return utils.read_csv(works_file_path)


def get_url_map(force_refresh: bool = False) -> dict:
    """必要に応じてAPIから取得 or CSVから読み込み"""
    if force_refresh or not utils.exists_file_path(works_file_path):
        print("🔄 APIからURLマップを取得中...")
        works = fetch_works_api()
        save_works(works)

        url_map = {}
        
        for title, work in works.items():
            if len(work[0]) == 3:
                _, url, production = work[0]
                url_map[title] = (production, url)
        return url_map
    else:
        print("✅ ローカルCSVからURLマップを読み込みました")
        return load_url_map()


def save_works(works: dict):
    """アニメ情報ををCSVに保存"""
    if not utils.exists_file_path(save_dir):
        config.os.mkdir(save_dir)

    header = ["work_id", "title", "url", "production"]
    with open(works_file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for title, work in works.items():
            if len(work[0]) == 3:
                work_id, url, production = work[0]
                writer.writerow([work_id, title, url, production])


def url_join(url: str, params: str) -> str:
    """ターゲットURLを作成する関数"""
    return url + f"access_token={config.ANNICT_TOKEN}" + params.strip()


def fetch_works_api() -> dict:
    """APIから取得"""

    # アクセスURLの準備--works--
    # クール1か月前に切り替えるため+1で調整
    params = f"&filter_season={year}-{season}"
    target_url = url_join(config.ANNICT_WORK_URL, params)

    # AnnictAPIを実行しアニメの作品情報、関連制作会社をを取得
    works = get_works(target_url)

    # アクセスURLの準備--staffs--
    params = "&filter_work_id={}"
    target_url = url_join(config.ANNICT_STAFFS_URL, params)
    get_staffs(target_url, works)
    
    return works


# メイン処理
def main() -> None:
    """スクリプトのメイン処理"""
    url_map = get_url_map(force_refresh=False)

    # APIを強制的に再取得したい時だけ
    # url_map = get_url_map(force_refresh=True)

    # Webスクレイピングを実行 対応表のURLより最速配信「日時・プラットフォーム名」を取得
    earliest_list = None
    if not utils.exists_file_path(schedule_file_path):
        earliest_list = scrape_anime_info(url_map)
        # 配信日時をCSVに記録
        utils.write_csv(schedule_file_path, earliest_list)
    else:
        earliest_list = utils.read_csv(schedule_file_path, mode=2)
    
    # DBの存在チェック
    database_name = f'{year}{config.convert_season[season]}{config.DATABASE_TITLE}'
    is_db = exists_database_in_page(config.PARENT_PAGE_ID, database_name)
    
    # 存在しない場合のみテーブルを作成
    if not is_db:
        if create_database(config.PARENT_PAGE_ID, config.DATABASE_TITLE):
            pass
    # 行を連続してを追加
    if insert(earliest_list): print(f"Notionのテーブルへ登録成功✅ データベース名：{database_name}")
    else: print("登録失敗❎")

    
    # レコード件数を取得し0件でない場合のみ後続の処理を実行
    # テーブルへ登録するヘッダ情報を作成


    # Notion.テーブルへスクレイピングデータ登録
        # ここのロジックを考える
        # 重複したタイトルはスキップ、最速日時の調整 





# メイン処理の実行(テスト)
if __name__ == "__main__":
    main()

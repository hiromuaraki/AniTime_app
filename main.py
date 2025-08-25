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


# 現在の年月日を取得
year, month = utils.get_sysdate()[0:2]
# season = utils.get_season(month+1)
season = utils.get_season(month+2) # 検証用

WORKS_CSV_FILE = f"{year}_{season}.csv"
SCHEDULE_CSV_FILE = f"{year}_{season}_scrap.csv"
works_file_path = f"./data/works/{WORKS_CSV_FILE}"
schedule_file_path = f"./data/anime_schedule/{SCHEDULE_CSV_FILE}"



def get_url_map(force_refresh: bool = False) -> dict:
    """
    必要に応じてAPIから取得 or CSVから読み込み
    
    Args:
        force_refresh: CSV読み込みフラグ（True:API実行 False: ローカルCSV）

    Returns:
        {title: [url, production]}（対応表）
    """
    if force_refresh or not utils.exists_file_path(works_file_path):
        print("🔄 APIからURLマップを取得中...")
        works = fetch_works_api()
        save_works(works)
    else:
        print("✅ ローカルCSVからURLマップを読み込みました")
    return utils.read_csv(works_file_path)
        


def save_works(works: dict):
    """アニメ情報ををCSVに保存"""
    
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
    params = f"&filter_season={year}-{season}"
    target_url = url_join(config.ANNICT_WORK_URL, params)

    # AnnictAPIを実行アニメの作品情報取得
    works = get_works(target_url)

    # アクセスURLの準備--staffs--
    params = "&filter_work_id={}"
    target_url = url_join(config.ANNICT_STAFFS_URL, params)
    # 制作会社をを取得
    get_staffs(target_url, works)
    
    return works


# メイン処理
def main() -> None:
    """スクリプトのメイン処理"""
    earliest_list = {}
    
    # スクレイピングCSVの有無（現時点では手動削除）
    if not utils.exists_file_path(schedule_file_path):
        url_map = get_url_map(force_refresh=False)
        # Webスクレイピングを実行「配信日時・プラットフォーム」を取得
        earliest_list = scrape_anime_info(url_map)
        # 最速配信情報をCSVに記録
        utils.write_csv(schedule_file_path, earliest_list)
        earliest_list = utils.read_csv(schedule_file_path, mode=2)
    
    # DBの存在チェック
    database_name = f'{year}{config.convert_season[season]}{config.DATABASE_NAME}'
    db_id = exists_database_in_page(config.PARENT_PAGE_ID, database_name)
    
    # 存在しない場合のみテーブル作成＋行追加
    if db_id is None:
        # 新規DB作成時に古いDBをアーカイブ化して運用（論理削除）
        db_id = create_database(config.PARENT_PAGE_ID, config.DATABASE_NAME, [year, month])
        insert(earliest_list, db_id)





# メイン処理の実行(テスト)
if __name__ == "__main__":
    main()

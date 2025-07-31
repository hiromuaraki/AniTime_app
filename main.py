import csv
import model.config as config
import common.utils as utils
from app.annict_get_api import get_title_url_map, get_staffs
from app.scraper import scrape_anime_info


save_dir = './url_map_csv'
CSV_FILE = 'title_url_map.csv'


def load_url_map() -> dict:
    """CSVからタイトル-URLマップを読み込む"""
    if not config.os.path.exists(CSV_FILE):
        return {}
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        return {row[0]: row[1] for row in reader if len(row) == 2}


def get_url_map(force_refresh: bool=False) -> dict:
    """必要に応じてAPIから取得 or CSVから読み込み"""
    if force_refresh or not config.os.path.exists(CSV_FILE):
        print("🔄 APIからURLマップを取得中...")
        url_map, works_info = fetch_url_map_from_api()
        save_url_map(url_map)
        return url_map
    else:
        print("✅ ローカルCSVからURLマップを読み込みました")
        return load_url_map()


def save_url_map(title_url_dict: dict):
    """タイトル-URLマップをCSVに保存"""
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for title, url in title_url_dict.items():
            writer.writerow([title, url])



def fetch_url_map_from_api() -> tuple:
    """APIから取得"""
    # 現在の年月日を取得
    year, month, _ = utils.sysdate()

    # アクセスURLの準備--works--
    season = utils.get_season(month)
    params = f'access_token={config.ANNICT_TOKEN}&filter_season={year}-{season}'
    work_url = config.ANNICT_WORK_URL + params

    # AnnictAPIを実行しアニメの{タイトル：公式URL}対応表および作品情報をを取得
    title_url_map, works_info = get_title_url_map(work_url)
    get_staffs(works_info)
    return title_url_map, works_info




# メイン処理
def main() -> None:
  """スクリプトのメイン処理"""
  url_map = get_url_map(force_refresh=False)
  
  # APIを強制的に再取得した時だけ
  # url_map = get_url_map(force_refresh=True)
  # Webスクレイピングを実行 対応表のURLより最速配信「日時・プラットフォーム名」を取得
  earliest_list = scrape_anime_info(url_map)
  
  # スクレイピングデータを加工

  # NotionAPIを実行しアクセス

  # Notionのテーブルへスクレイピングデータを書き込む


# メイン処理の実行(テスト)
if __name__ == '__main__':
  main()
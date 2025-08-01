import csv
import model.config as config
import common.utils as utils
from app.annict_get_api import get_works, get_staffs
from app.scraper import scrape_anime_info


save_dir = './works_info'
CSV_FILE = 'works_info.csv'
file_path = f'./works_info/{CSV_FILE}'


def load_url_map() -> dict:
    """CSVからタイトル-URLマップを読み込む"""
    url_map = {}
    if not config.os.path.exists(file_path):
        return url_map
    
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            _, title, url, _ = row
            url_map[title] = url
        return url_map


def get_url_map(force_refresh: bool=False) -> dict:
    """必要に応じてAPIから取得 or CSVから読み込み"""
    if force_refresh or not config.os.path.exists(file_path):
        print("🔄 APIからURLマップを取得中...")
        works = fetch_url_map_from_api()
        save_works(works)
        
        url_map = {}
        for title, work in works.items():
            if len(work[0]) == 3:
                _,url,_ = work[0]
                url_map[title] = url 
        return url_map
    else:
        print("✅ ローカルCSVからURLマップを読み込みました")
        return load_url_map()


def save_works(works: dict):
    """アニメ情報ををCSVに保存"""
    if not config.os.path.exists(save_dir):
        config.os.mkdir(save_dir)
    
    header = ['work_id', 'title', 'url', 'prduction']
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for title, work in works.items():
            if len(work[0]) == 3:                
                work_id, url, production = work[0]
                writer.writerow([work_id, title, url, production])



def fetch_url_map_from_api() -> dict:
    """APIから取得"""
    # 現在の年月日を取得
    year, month, _ = utils.sysdate()

    # アクセスURLの準備--works--
    season = utils.get_season(month)
    params = f'access_token={config.ANNICT_TOKEN}&filter_season={year}-{season}'
    work_url = config.ANNICT_WORK_URL + params

    # AnnictAPIを実行しアニメの{タイトル：公式URL}対応表および作品情報をを取得
    works = get_works(work_url)
    get_staffs(works)
    return  works




# メイン処理
def main() -> None:
  """スクリプトのメイン処理"""
  url_map = get_url_map(force_refresh=False)
  
  # APIを強制的に再取得したい時だけ
  # url_map = get_url_map(force_refresh=True)
  # Webスクレイピングを実行 対応表のURLより最速配信「日時・プラットフォーム名」を取得
  earliest_list = scrape_anime_info(url_map)
  
  # スクレイピングデータを加工

  # NotionAPIを実行しアクセス

  # Notionのテーブルへスクレイピングデータを書き込む


# メイン処理の実行(テスト)
if __name__ == '__main__':
  main()
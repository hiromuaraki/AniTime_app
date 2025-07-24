import model.config as config
import common.utils as utils
from app.annict_get_api import get_title_url_map
from app.scraper import get_scrape_data

# メイン処理
def main() -> None:
  """スクリプトのメイン処理"""
  # 現在の年月日を取得
  year, month, _ = utils.sysdate()

  # アクセスURLの準備
  season = utils.get_season(month)
  params = f'filter_season={year}-{season}&access_token={config.ANNICT_TOKEN}'
  target_url = config.ANNICT_URL + params
  
  # AnnictAPIを実行しアニメの{タイトル：公式URL}対応表を取得
  title_url_map = get_title_url_map(target_url)
  
  # Webスクレイピングを実行 対応表のURLより最速配信「日時・曜日・配信サイト名」を取得
  response = get_scrape_data(title_url_map)
  # スクレイピングデータを加工

  # NotionAPIを実行しアクセス

  # Notionのテーブルへスクレイピングデータを書き込む
  pass


# メイン処理の実行(テスト)
if __name__ == '__main__':
  main()
import model.config as config
import common.utils as utils
from app.annict_get_api import get_title_url_map
from app.scraper import scrape_anime_info

# メイン処理
def main() -> None:
  """スクリプトのメイン処理"""
  # 現在の年月日を取得
  year, month, _ = utils.sysdate()

  # アクセスURLの準備--works--
  season = utils.get_season(month)
  params = f'access_token={config.ANNICT_TOKEN}&filter_season={year}-{season}'
  work_url = config.ANNICT_WORK_URL + params

  
  # AnnictAPIを実行しアニメの{タイトル：公式URL}対応表および作品情報をを取得
  title_url_map, works_info = get_title_url_map(work_url)
  
  # Webスクレイピングを実行 対応表のURLより最速配信「日時・プラットフォーム名」を取得
  response = scrape_anime_info(title_url_map)
  
  
  
  # スクレイピングデータを加工

  # NotionAPIを実行しアクセス

  # Notionのテーブルへスクレイピングデータを書き込む
  pass


# メイン処理の実行(テスト)
if __name__ == '__main__':
  main()
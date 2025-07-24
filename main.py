'''
アプリのメイン起動・フロー管理
'''
import model.config as config
import common.utils as utils
from app.annict_get_api import programs_data

# メイン処理
def main() -> None:
  # 現在の年月日を取得
  year, month, _ = utils.get_sysdate().split()

  # アクセスURLの準備
  f_date = '{}/{}/01 00:00'.format(year, month)
  program_conditions = 'sort_started_at=asc&filter_started_at_gt={}&access_token={}'.format(f_date, config.ANNICT_TOKEN)
  a_url = config.ANNICT_URL + program_conditions

  # AnnictAPIを実行し放送予定アニメの「タイトル・公式URL」の一覧を取得
  annict = programs_data(a_url)
  # Webスクレイピングを実行 公式URLより最速配信「日時・曜日・配信サイト名」を取得

  # スクレイピングデータを加工

  # NotionAPIを実行しアクセス

  # Notionのテーブルへスクレイピングデータを書き込む
  pass


# メイン処理の実行(テスト)
if __name__ == '__main__':
  main()
from model.config import typing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import model.config as config
import time
import re

# 全体的にロジックの確認と修正が必要、設計を確認し実装
# Selenium使わないかも

def setup_driver():
    """ブラウザを操作する為のWebDriverの初期設定"""
    options = Options()
    options.add_argument("--headless")  # ブラウザを表示しない
    options.add_argument(f"user-agent={config.USER_AGENT}")
    service = Service(config.CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def parse_broadcast_info(html) -> list:
    """
    - HTML から放送局＋日時テキストを抽出し、リストで返却
    - 戻り値: [(station, raw_time_str), ...]
    """
    
    # HTMLがうまく取得できておらず36行目で処理落ち
    print(html[:100])
    print(html[:200])
    print(html[:300])
    
    soup = BeautifulSoup(html, 'html.parser')

    text = soup.get_text(separator=' ')
    target_words = [
        'Prime','dアニメ','ABEMA','Netflix','U-NEXT','FOD','Hulu',
        'スーパーアニメイズムTURBO枠', 'ノイタミナ枠', 'Imanimation枠','アガルアニメ枠', 'ANiMAZiNG!!!枠']
    target_pattern = '|'.join(map(re.escape, target_words))
    # 放送局と日時の抽出
    pattern = re.compile(rf'{target_pattern}.*?([0-9]{1,2}月[0-9]{1,2}日[^\d]*?[0-9]{1,2}[:：][0-9]{2})')
    return pattern.findall(text)
    

# この処理も多分不要（Selenuium使うケースの場合を想定）
def fetch_page(driver, url, links_texts=('放送', 'ON AIR', 'on air', 'broadcast')) -> typing.Any:
    """
    - base URL を開き、link_textsに合致するリンクをクリックして放送情報ページへ遷移
    - 見つからなければ base URL のまま HTML を返す
    """
    driver.get(url)
    time.sleep(1)

    for text in links_texts:
        try:
            elem = driver.find_element(By.PARTIAL_LINK_TEXT, text)
            elem.click()
            time.sleep(1)
            break
        except:
            continue
    return driver.page_source


def scrape_anime_info(title_url_map: dict, on_air='onair') -> dict:
    """
    アニメの配信情報を公式サイトよりスクレイピングで取得

    Args:
        title_url_map（str, str）:配信情報を取得する為の対応表
        on_air：放送情報ページへ直接アクセスするurl(基本的にon airを指定)

    Returns:
        broadcast_info:アニメの配信情報を格納した辞書型リスト
        {title: [start_date, platform]....}
    # """
    
    # driverの初期設定
    # driver = setup_driver()
    
    broadcast_info = {}
    try:
        print(f"アクセス中：")
        # 対応表の件数分公式サイトへアクセスし放送情報を全取得する
        for title, base_url in title_url_map.items():
            html = requests.get(base_url + on_air)
        
            # 放送情報からBeautifulSoupで配信日時・プラットフォーム名を抽出する
            broadcast_info[title] = []
            broadcast_info[title].append(parse_broadcast_info(html))

    finally:
        # driverを閉じる
        # driver.close()
        return broadcast_info
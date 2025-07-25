from model.config import typing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import model.config as config
import time
import re

# 全体的にロジックの確認と修正が必要、設計を確認し実装

def setup_driver() -> None:
    """ブラウザを操作する為のWebDriverの初期設定"""
    options = Options()
    options.add_argument("--headless")  # ブラウザを表示しない(後で消す)
    options.add_argument(f"user-agent={config.USER_AGENT}")
    service = Service(config.CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def parse_broadcast_info(html) -> list:
    """
    - HTML から放送局＋日時テキストを抽出し、リストで返却
    - 戻り値: [(station, raw_time_str), ...]
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=' ')
    # 放送局と日付抽出の正規表現例
    pattern = re.compile(r'(TOKYO MX|BS11|ABEMA|dアニメ).*?([0-9]{1,2}月[0-9]{1,2}日[^\d]*?[0-9]{1,2}[:：][0-9]{2})')
    return pattern.findall(text)
    return []
    


def fetch_page(driver, url, links_texts=('放送', 'ON AIR', 'on air', 'broadcast')) -> typing.Any:
    """
    - base URL を開き、link_textsに合致するリンクをクリックして放送情報ページへ遷移
    - 見つからなければ base URL のまま HTML を返す
    """
    driver.get(url)
    time.sleep(config.WAITE_TIME)

    for text in links_texts:
        try:
            elem = driver.find_element(By.PARTIAL_LINK_TEXT, text)
            elem.click()
            time.sleep(config.WAITE_TIME)
            break
        except:
            continue
    return driver.page_source


def scrape_anime_info(title_url_map: dict) -> list:
    """
    アニメの配信情報を公式サイトよりスクレイピングで取得

    Args:
        title_url_map（str, str）:配信情報を取得する為の対応表

    Returns:
      要確認[]: アニメの配信情報
    # """
    
    # driverの初期設定
    driver = setup_driver()
    
    try:
        print(f"アクセス中：{""}")
        # 対応表の件数分公式サイトへアクセスし放送情報を全取得する
        for _, url in title_url_map:
            html = fetch_page(driver, url)



        # 放送情報からBeautifulSoupで配信日時・プラットフォーム名を抽出する
        pass
    finally:
        # driverを閉じる
      return []
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.error import HTTPError, URLError
from datetime import datetime
import model.config as config
import requests, re, time, typing

# 全体的にロジックの確認と修正が必要、設計を確認し実装
# Selenium使わないかも

# def setup_driver():
#     """ブラウザを操作する為のWebDriverの初期設定"""
#     options = Options()
#     options.add_argument("--headless")  # ブラウザを表示しない
#     options.add_argument(f"user-agent={config.USER_AGENT}")
#     service = Service(config.CHROMEDRIVER_PATH)
#     driver = webdriver.Chrome(service=service, options=options)
#     return driver


def parse_datetime_jp(text: str) -> datetime:
    """
    例: '8月5日 24:30' → datetime に変換
    """
    try:
        now = datetime.now()
        year = now.year
        m = re.search(r"(\d{1,2})月(\d{1,2})日[^\d]*?(\d{1,2})[:：](\d{2})", text)
        if m:
            month, day, hour, minute = map(int, m.groups())
            if hour >= 24:
                hour -= 24
                base = datetime(year, month, day, hour, minute)
                return base + datetime.timedelta(days=1)
            return datetime(year, month, day, hour, minute)
    except:
        return None
    return None

# ロジックの修正が必要
def extract_onair_times(text: str, platforms: tuple) -> list:
    """
    プラットフォーム名と日時を抽出し対応付ける関数
    
    Args:
        text: onairのページ情報
        platforms: 各行ごとのプラットフォーム名を確認
    Returns:
        result:対応付けされたリスト (プラットフォーム名, 日時）
    """
    result = []
    lines = text.splitlines()

    for line in lines:
        for platform in platforms:
            if platform in line:
                # 日時を探す
                d = re.search(r"([0-9]{1,2})月([0-9]{1,2})日.*?([0-9]{1,2})[:：]([0-9]{2})", line)
                if d:
                    date_str = f"{d.group(1)}月{d.group(2)}日 {d.group(3)}:{d.group(4)}"
                    result.append((platform, date_str))
    return result



def parse_broadcast_info(html: BeautifulSoup, title: str) -> list:
    """
    - HTML から放送局＋日時テキストを抽出し、リストで返却
    - 戻り値: [(station, raw_time_str), ...]

    Args:

    Returns:
    """
    try:
        soup = BeautifulSoup(html.content, 'html.parser', from_encoding='utf-8')
        text = soup.get_text(separator=' ')
        
        # 放送局と日時の抽出
        matches = extract_onair_times(text, config.PLATFORMS)
        
        for platform, time_str in matches:
            print(f"{title} → {platform} → {time_str}")
    
    except HTTPError as e:
        print(f"HTTP Error: {e.reason}")
    except URLError as e:
        print(f"URL Error: {e.reason}")

    finally:
           return matches
    
    
    

# この処理も多分不要（Selenuium使うケースの場合を想定）
# def fetch_page(driver, url, links_texts=('放送', 'ON AIR', 'on air', 'broadcast')) -> typing.Any:
#     """
#     - base URL を開き、link_textsに合致するリンクをクリックして放送情報ページへ遷移
#     - 見つからなければ base URL のまま HTML を返す
#     """
#     driver.get(url)
#     time.sleep(1)

#     for text in links_texts:
#         try:
#             elem = driver.find_element(By.PARTIAL_LINK_TEXT, text)
#             elem.click()
#             time.sleep(1)
#             break
#         except:
#             continue
#     return driver.page_source


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
    
    print(f"アクセス中：")
    broadcast_info = {}
    try:
        # 対応表の件数分公式サイトへアクセスし放送情報を全取得する
        for title, base_url in title_url_map.items():
            if base_url == '': continue
            if base_url[-1] != '/': on_air = '/' + on_air
            
            html = requests.get(base_url + on_air)
            # 放送情報からBeautifulSoupで配信日時・プラットフォーム名を抽出する
            broadcast_info[title] = []
            broadcast_info[title].append(parse_broadcast_info(html, title))
            time.sleep(1)
    finally:
        # driverを閉じる
        # driver.close()
        return broadcast_info
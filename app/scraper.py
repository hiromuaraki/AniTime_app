from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
from urllib.error import HTTPError, URLError
from datetime import datetime, timedelta
import model.config as config
import warnings
import requests, re, time, random


def parse_datetime_jp(text: str) -> datetime:
    """
    

    Args:

    Returns:

    """
    
    try:
        m = re.search(r"(\d{1,2})月(\d{1,2})日.*?(\d{1,2})[:：](\d{2})", text)
        if m:
            month, day, hour, minute = map(int, m.groups())
            now = datetime.now()
            dt = datetime(now.year, month, day, hour, minute)
            if hour >= 24:
                dt += timedelta(days=1)
            return dt
    except:
        return None
    return None
    

def extract_onair_times(text: str, platforms: tuple) -> list:
    """
    プラットフォーム名と日時を抽出し対応付ける関数
    
    Args:
        text: onairのページ情報
        platforms: プラットフォーム名一覧
    Returns:
        result:対応付けされたリスト (プラットフォーム名, 日時）
    """
    results = []
    lines = text.splitlines()

    for line in lines:
        for platform in platforms:
            if platform in line:
                dt = parse_datetime_jp(line)
                if dt:
                    results.append((platform, dt))
    return results



def find_earliest_per_platform(matches: list) -> list:
    """
    
    
    Args:


    Returns:

    """
    platform_map = {}
    for platform, dt in matches:
        if platform not in platform_map or dt < platform_map[platform]:
            platform_map[platform] = dt
    return sorted(platform_map.items(), key=lambda x: x[1])



def parse_broadcast_info(html: BeautifulSoup, title: str) -> list:
    """
    - HTML から放送局＋日時テキストを抽出し、リストで返却
    - 戻り値: [(station, raw_time_str), ...]

    Args:

    Returns:
    """
    try:
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
        soup = BeautifulSoup(html.content, 'html.parser', from_encoding='utf-8')
        text = soup.get_text(separator=' ') 
        
        # プラットフォーム名と日時の抽出
        matches = extract_onair_times(text, config.PLATFORMS)
        
        # 最速のプラットフォーム名と日時の抽出
        earliest_list = find_earliest_per_platform(matches)

        for platform, time_str in earliest_list:
            print(f"{title} → {platform} → {time_str}")
    
        return earliest_list
    except HTTPError as e:
        print(f"HTTP Error: {e.reason}")
    except URLError as e:
        print(f"URL Error: {e.reason}")
    


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
        for title, base_url in title_url_map.items():
            if base_url == '': continue
            if base_url[-1] != '/': on_air = '/' + on_air

            html = requests.get(base_url + on_air, timeout=10)
            # 放送情報からBeautifulSoupで配信日時・プラットフォーム名を抽出する
            broadcast_info[title] = []
            broadcast_info[title].append(parse_broadcast_info(html, title))
            time.sleep(random.uniform(1,1.5))

        return broadcast_info
    except Exception as e:
        print('スクレイピングエラー発生：リトライ前に少し待機', {e})
        time.sleep(5)
    time.sleep(random.uniform(1,2))
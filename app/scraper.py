from bs4 import BeautifulSoup
from urllib.error import HTTPError, URLError
from datetime import datetime, timedelta
import model.config as config
import requests, re, time, random, csv
import undetected_chromedriver as uc


def parse_datetime_jp(text: str):
    """
    日本語の日時表現から datetime を抽出する。
    対応形式:
    - 2025年7月12日12:00
    - 7月12日12:00（年なし）
    """
    patterns = [
        r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日.*?(\d{1,2})[:：](\d{2})",
        r"(\d{1,2})月\s*(\d{1,2})日.*?(\d{1,2})[:：](\d{2})",
    ]

    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            now = datetime.now()
            if len(m.groups()) == 5:
                year, month, day, hour, minute = map(int, m.groups())
            else:
                month, day, hour, minute = map(int, m.groups())
                year = now.year + (1 if (now.month > month and month < 3) else 0)

            # 深夜帯調整
            if hour >= 24:
                return datetime(year, month, day, hour%24, minute) + timedelta(days=1)
            return datetime(year, month, day, hour, minute)

    print(f"抽出範囲: {text[:50]}")




def extract_onair_times(text: str, radius=3) -> list:
    """
    テキストからプラットフォーム名と日時を抽出する関数

    Args:
        text: サイトHTMLから取得した全テキスト
        platforms: プラットフォーム名のタプル

    Returns:
        [(platform, datetime)] のリスト
    """
    results = []
    # 文字列の前後行を組み合わせた行を１行ずつリストでを取得
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    num_lines = len(lines)
    # 文字列の前後にマッチするプラットフォー名の存在チェック
    for i, line in enumerate(lines):
        for platform in config.PLATFORMS:
            if platform in line:
                # 周囲5行を見る（より広く）
                context = ' '.join(lines[max(0, i - radius): min(num_lines, i + radius + 1)])
                print(f'{context = }')
                print()
                dt = parse_datetime_jp(context)
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



def parse_broadcast_info(html, title: str) -> list:
    """
    HTMLからプラットフォームと日時を抽出し、最速配信情報にまとめる

    Args:
        html: requests.get で取得したHTMLレスポンス
        title: アニメのタイトル
        platforms: プラットフォーム一覧タプル

    Returns:
        [(platform, datetime)] のリスト
    """

    try:
        # HTMLを解析する準備
        soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
        
        # 改行区切りでテキスト全行取得
        text = soup.get_text(separator="\n")
        matches = extract_onair_times(text)
        earliest_list = find_earliest_per_platform(matches)
        
        for platform, dt in earliest_list:
            print(f"{title} → {platform} → {dt}")
        return earliest_list
    
    except HTTPError as e:
        print(f"HTTP Error: {e.reason}")
    except URLError as e:
        print(f"URL Error: {e.reason}")
    return []
    


def scrape_anime_info(title_url_map: dict, on_air='onair') -> dict:
    """
    アニメの配信情報を公式サイトよりスクレイピングで取得

    Args:
        title_url_map（str, str）:配信情報を取得する為の対応表
        on_air：放送情報ページへリクエストするurl(基本的にon airを指定)

    Returns:
        broadcast_info:アニメの配信情報を格納した辞書型リスト
        {title: [start_date, platform]....}
    """
    
    broadcast_info, ng_list = {}, {}
    html = ''
    # 403の対策（bot判定を避けるためリファラーを設定
    headers = {
      'User-Agent': config.USER_AGENT,
      'Referer': 'https://www.google.com/',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
      'Accept-Language': 'ja,en;q=0.9',
      'Connection': 'keep-alive'}
    
    print(f"アクセス中：")
    for title, base_url in title_url_map.items():
        if base_url == '': continue
        
        try:
            url = base_url.rstrip('/') + '/' + on_air
            res = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
            
            # 成功以外はNGリストへ追加し記録
            if res.status_code == 200:
                html = res.content
            elif res.status_code == 404:
                print(f'[WARN] 404 Not Found: {url} → base_urlで再試行')
                res = requests.get(base_url, headers=headers, timeout=5, allow_redirects=True)
                ng_list[title] = (res.url, res.status_code)
                html = res.content
            elif res.status_code == 403:
                print(f'[WARN] 403 Forbidden: {url} → undetected_chromedriver機動')
                driver = uc.Chrome()
                driver.get(base_url)
                html = driver.page_source
            else:
                html = None
                ng_list[title] = (res.url, res.status_code)
            
            # 放送情報からBeautifulSoupで配信日時・プラットフォーム名を抽出する
            if html is not None:
                broadcast_info[title] = parse_broadcast_info(html, title)
            
            print(f'タイトル={title} 最終URL:{res.url} ステータス:{res.status_code}')
                     
            time.sleep(random.uniform(1, 1.5))

        except requests.RequestException as e:
            print('スクレイピングエラー発生：リトライ前に少し待機', {e})
            time.sleep(2)
    
    # 抽出失敗タイトルをcsvへ書き出しNGリスト作成
    if len(ng_list):
        with open('./data/ng_list.csv', 'w', encoding='utf-8') as f:
            write = csv.writer(f)
            write.writerow(['番号','タイトル','URL','ステータスコード'])
            i = 1
            for title, ng in ng_list.items():
                url, status_code = ng
                write.writerow([i, title, url, status_code])
                i += 1

    return broadcast_info
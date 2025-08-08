from bs4 import BeautifulSoup
from urllib.error import HTTPError, URLError
from datetime import datetime
from model.handler import patterns_with_handlers, safe_datetime_with_25h, handler_md_only
from model.logging_config import setup_logger
import model.config as config
import requests, re, time, random, csv


# ロガーの準備
logging = setup_logger()

# この処理見直す
def score_context_near_match(context: str, match_start: int, window: int = 50) -> int:
    """指定した位置（match_start）の前後window文字分の文脈からスコアを計算"""
    # 新規追加
    start = max(0, match_start - window)
    end = min(len(context), match_start + window)
    sliced_context = context[start : end]
    
    score = sum({config.CONTEXT_KEYWORDS.get(k, 0) for k in config.CONTEXT_KEYWORDS if k in sliced_context})
    score += sum({config.FRAME_KEYWORDS.get(k, 0) for k in config.FRAME_KEYWORDS if k in sliced_context})
    return score


# この処理見直す
def extract_year_from_html(soup: BeautifulSoup) -> int:
    """HTMLから年を抽出（メタデータや本文から）"""
    # メタデータから公開日をチェック
    meta_date = soup.find("meta", {"name": "date"}) or soup.find("meta", {"property": "og:updated_time"})
    if meta_date and meta_date.get("content"):
        try:
            return int(meta_date["content"].split("-")[0])
        except (ValueError, IndexError):
            pass

    # 本文から年を検索
    year_pattern = re.compile(r"\b(20\d{2})\b")
    for text in soup.stripped_strings:
        match = year_pattern.search(text)
        if match:
            return int(match.group(1))

    # デフォルトは現在の年
    return datetime.now().year


# この処理見直す
def extract_base_date_from_html(soup: BeautifulSoup) -> datetime:
    """HTMLから基準日（放送開始日など）を抽出"""
    # date_pattern = re.compile(r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日")
    datetime_pattern = re.compile(
        r"(?P<month>\d{1,2})[月/](?P<day>\d{1,2})日?(?:\（?.?\）?)?\s*(?P<hour>\d{1,2}):(?P<minute>\d{2})")
    
    for text in soup.stripped_strings:
        match = datetime_pattern.search(text)
        if match:
            # 年月日フル
            year = extract_year_from_html(soup)
            month = int(match.group("month"))
            day = int(match.group("day"))
            hour = int(match.group("hour"))
            minute = int(match.group("minute"))
            return safe_datetime_with_25h(
                year, month, day, hour, minute)
    return datetime.now()



def call_handler(handler, match, year, base_date):
    """正規表現パターンにマッチしたhandlerを呼び出す"""
    argcount = handler.__code__.co_argcount
    if argcount == 1:
        return handler(match)
    elif argcount == 2:
        return handler(match, year)
    elif argcount == 3:
        return handler(match, year, base_date)
    else:
        raise ValueError("Unsupported handler argument count")



def extract_best_datetime_with_context(context: str, year: int, base_date: datetime):
    """
    コンテキストから最適な日時を抽出しスコアが最大の日時を返す.
    例）スコア：最速配信 or 独占 or 地上波同時などの特定のキーワードに設定している優先度

    Args:
        context:
        year:
        base_date:

    Returns:
        candidates: スコアが高い日時 
    
    """
    candidates = []

    for pattern in patterns_with_handlers:
        for match in pattern["pattern"].finditer(context):
            try:
                if pattern["id"] == 11:
                    # デフォルトで時分が00:00に設定されないように制御
                    dt = handler_md_only(match, context, year)
                else:
                    dt = call_handler(pattern["handler"], match, year, base_date)
                # 優先度が設定されていなければ優先度0を設定
                # この処理がおかしい？
                score = 1 + score_context_near_match(context, match.start()) + pattern.get("confidence", 0)
                if pattern.get("confidence", 0) == 0:
                    score -= 2 # 優先度が低いものがマッチした場合はペナルティでスコアを引く
                candidates.append((dt, score))
                logging.debug(
                    f"Matched pattern: ID: {pattern['id']}, {pattern['pattern'].pattern}, DateTime: {dt}, Score: {score}, Context: {context[:100]}"
                )
            except Exception as e:
                logging.warning(f"[extract error] {e} /ID: {pattern['id']} / pattern={pattern['pattern'].pattern} / text={match.group(0)}")
                print(f"[ERROR] handler実行中に例外発生: {e}")
                print(f"[DEBUG] handler: {pattern['handler']}, pattern: {pattern['pattern'].pattern}")
                print(f"[DEBUG] match: {match}")
                continue

    if not candidates:
        logging.warning(f"No datetime candidates found in context: {context[:100]}")
        return None

    # スコアが最大の日時を返す
    # candidates.sort(key=lambda x: x[1], reverse=True)
    # スコア最大 → 同スコアなら datetime 降順（遅い方）
    candidates.sort(key=lambda x: (x[1], x[0]), reverse=True)
    return candidates[0][0]


def extract_onair_times(soup: BeautifulSoup, year: int, base_date: datetime, radius=5) -> list:
    """
    テキストからプラットフォームと日時を抽出する.

    Args:
        soup: サイトHTMLから取得した放送情報
        year: 基準の年
        base_date: 放送開始日時の基準
        radius: 文章の前後5行を対象とする範囲

    Returns:
        [(platform, datetime)] のリスト
    
    """
    results = []
    ng_results = []
    
    # 文章を全文を走査し対応するプラットフォームの存在をチェックする為改行区切りで分割
    lines = [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
    num_lines = len(lines)

    # 全文から抽出
    for i, line in enumerate(lines):
        for platform in config.PLATFORMS:
            if platform in line:
                # 空白区切りでテキストを文章にし正規表現に一致した日時を抽出
                context = " ".join(lines[max(0, i - radius) : min(num_lines, i + radius + 1)])
                dt = extract_best_datetime_with_context(context, year, base_date)
                if dt:
                    results.append((platform, dt))
                else:
                    ng_results.append((platform, context[:200]))
                    logging.warning(f"No datetime for platform {platform} in context: {context[:100]}")

    # 失敗ケースをログに保存
    if ng_results:
        with open("./data/ng_datetime.log", "a", encoding="utf-8") as f:
            for platform, ctx in ng_results:
                f.write(f"[NG] {platform}:\n{ctx}\n---\n")

    return results


def find_earliest_per_platform(matches: list) -> list:
    """
    プラットフォームに対応した最速配信情報を返す

    Args:
        matches: 


    Returns:
        list[{str, datetime}]
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

    Returns:
        [(platform, datetime)] のリスト
    """

    try:
        # HTMLを解析する準備
        soup = BeautifulSoup(html, "html.parser", from_encoding="utf-8")

        # 年と基準日を抽出
        year = extract_year_from_html(soup)
        base_date = extract_base_date_from_html(soup)
        logging.info(f"Extracted year: {year}, base_date: {base_date} for title: {title}")

        # 放送情報を抽出
        matches = extract_onair_times(soup, year, base_date)
        earliest_list = find_earliest_per_platform(matches)

        for platform, dt in earliest_list:
            print(f"{title} → {platform} → {dt}")
            logging.info(f"Extracted: {title} → {platform} → {dt}")
            print()

        if not earliest_list:
            logging.warning(f"No broadcast info extracted for {title}")

        return earliest_list

    except HTTPError as e:
        print(f"HTTP Error: {e.reason}")
    except URLError as e:
        print(f"URL Error: {e.reason}")
    except Exception as e:
        print(f"Parsing Error: {e}")
    return []


def scrape_anime_info(title_url_map: dict, on_air="onair/") -> dict:
    """
    アニメの配信情報を公式サイトよりスクレイピングで取得

    Args:
        title_url_map（str, str）:配信情報を取得する為の対応表
        on_air：放送情報ページへリクエストするurl(基本的にonair/を指定)

    Returns:
        broadcast_info:アニメの配信情報を格納した辞書型リスト
        {title: [start_date, platform]....}
    """

    broadcast_info, ng_list = {}, {}
    html = ""
    
    other_on_airs = [
        "on-air/",
        "On-air/",
        "onair.html"
    ] 
    
    # 403の対策（bot判定を避けるためリファラーを設定
    headers = {
        "User-Agent": config.USER_AGENT,
        "Referer": "https://www.google.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Language": "ja,en;q=0.9",
        "Connection": "keep-alive",
    }

    print(f"アクセス中：")
    for title, base_url in title_url_map.items():
        if base_url == "":
            continue

        try:
            url = base_url.rstrip("/") + "/" + on_air
            res = requests.get(url, headers=headers, timeout=5, allow_redirects=True)

            if res.status_code == 200:
                html = res.content
            elif res.status_code == 404:
                # リクエスト成功以外は必ずベースURLを渡す
                res_base = requests.get(base_url, headers=headers, timeout=5, allow_redirects=True)
                
                for other_on_air in other_on_airs:
                    res = requests.get(base_url + other_on_air, headers=headers, timeout=5, allow_redirects=True)
                    if res.status_code == 200:
                        html = res.content
                        break
                if res.status_code != 200:
                    html = res_base.content
            elif res.status_code == 403:
                print(f"[WARN] 403 Forbidden: {url} → base_urlで再試行")
                res = requests.get(base_url, headers=headers, timeout=5, allow_redirects=True)
                html = res.content
            else:
                html = None

            # 成功以外はNGリストへ追加し記録
            if res.status_code != 200:
                ng_list[title] = (res.url, res.status_code)

            # 放送情報からBeautifulSoupで配信日時・プラットフォーム名を抽出する
            if html is not None:
                broadcast_info[title] = parse_broadcast_info(html, title)

            time.sleep(random.uniform(1, 1.5))

        except requests.RequestException as e:
            print("スクレイピングエラー発生：リトライ前に少し待機", {e})
            time.sleep(2)

    # 抽出失敗タイトルをcsvへ書き出しNGリスト作成
    if len(ng_list):
        with open("./data/ng_list.csv", "w", encoding="utf-8") as f:
            write = csv.writer(f)
            write.writerow(["番号", "タイトル", "URL", "ステータスコード"])
            i = 1
            for title, ng in ng_list.items():
                url, status_code = ng
                write.writerow([i, title, url, status_code])
                i += 1

    return broadcast_info
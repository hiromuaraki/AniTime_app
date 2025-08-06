from bs4 import BeautifulSoup
from urllib.error import HTTPError, URLError
from datetime import datetime, timedelta
from model.handler import patterns_with_handlers, safe_datetime_with_25h
from model.logging_config import setup_logger
import model.config as config
import requests, re, time, random, csv

# import undetected_chromedriver as uc

logging = setup_logger()




# 拡張された正規表現パターン
# patterns_with_handlers = [
#     # ① 完全日付（年あり）
#     {
#         "pattern": re.compile(
#             r'(?P<year>\d{4})年\s*(?P<month>\d{1,2})月\s*(?P<day>\d{1,2})日.*?(?P<hour>\d{1,2})[:：](?P<minute>\d{2})'
#         ),
#         "handler": lambda m: safe_datetime_with_25h(
#             int(m.group("year")),
#             int(m.group("month")),
#             int(m.group("day")),
#             int(m.group("hour")),
#             int(m.group("minute"))
#         )
#     },
#     # ② 年なし日付（曜日つき）
#     {
#         "pattern": re.compile(
#             r'(?P<month>\d{1,2})月(?P<day>\d{1,2})日(?:\((?:月|火|水|木|金|土|日)\))?\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2})'
#         ),
#         "handler": lambda m, year: safe_datetime_with_25h(
#             year,
#             int(m.group("month")),
#             int(m.group("day")),
#             int(m.group("hour")),
#             int(m.group("minute"))
#         )
#     },
#     # ③ 午前/午後形式
#     {
#         "pattern": re.compile(
#             r'(?P<month>\d{1,2})月(?P<day>\d{1,2})日\s*(?:午前|午後)(?P<hour>\d{1,2})[:：](?P<minute>\d{2})'
#         ),
#         "handler": lambda m, year: safe_datetime_with_25h(
#             year,
#             int(m.group("month")),
#             int(m.group("day")),
#             int(m.group("hour")) + (12 if "午後" in m.group(0) else 0),
#             int(m.group("minute"))
#         )
#     },
#     # ④ 「時刻＋配信」→ 翌日
#     {
#         "pattern": re.compile(r'(?P<hour>\d{1,2})[:：](?P<minute>\d{2})\s*配信'),
#         "handler": lambda m, year, base_date: safe_datetime_with_25h(
#             year, base_date.month, base_date.day,
#             int(m.group("hour")),
#             int(m.group("minute"))
#         ) + timedelta(days=1)
#     },
#     # ⑤ 毎週〇曜 深夜〇時
#     {
#         "pattern": re.compile(
#             r'毎週(?:月|火|水|木|金|土|日)曜(?:深夜)?\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2})'
#         ),
#         "handler": lambda m, year, base_date: safe_datetime_with_25h(
#             year, base_date.month, base_date.day,
#             int(m.group("hour")),
#             int(m.group("minute") or 0)
#         ) + timedelta(days=1)
#     },
#     # ⑥ 「〇月〇日配信開始」→ 時間なしは0:00
#     {
#         "pattern": re.compile(r'(?P<month>\d{1,2})月(?P<day>\d{1,2})日\s*配信開始'),
#         "handler": lambda m, year: safe_datetime_with_25h(
#             year, int(m.group("month")), int(m.group("day")), 0, 0
#         )
#     },
#     # ⑦ スラッシュ区切り「8/5(火) 25:00」
#     {
#         "pattern": re.compile(
#             r'(?P<month>\d{1,2})/(?P<day>\d{1,2})\s*(?:\((?:月|火|水|木|金|土|日)\))?\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2})'
#         ),
#         "handler": lambda m, year: safe_datetime_with_25h(
#             year,
#             int(m.group("month")),
#             int(m.group("day")),
#             int(m.group("hour")),
#             int(m.group("minute"))
#         )
#     },
#     # ⑧ 「〇月〇日」だけ→ 時間なしは0:00
#     {
#         "pattern": re.compile(r'(?P<month>\d{1,2})月(?P<day>\d{1,2})日'),
#         "handler": lambda m, year: safe_datetime_with_25h(
#             year, int(m.group("month")), int(m.group("day")), 0, 0
#         )
#     },
#     # ⑨ 時間範囲（例: 23:00〜24:00）
#     {
#         "pattern": re.compile(
#             r'(?P<month>\d{1,2})月(?P<day>\d{1,2})日\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2})\s*〜\s*\d{1,2}[:：]\d{2}'
#         ),
#         "handler": lambda m, year: safe_datetime_with_25h(
#             year,
#             int(m.group("month")),
#             int(m.group("day")),
#             int(m.group("hour")),
#             int(m.group("minute"))
#         )
#     }
# ]


def score_context(context: str) -> int:
    """文脈に応じてスコアを加算"""
    score = sum( config.CONTEXT_KEYWORDS.get(k, 0) for k in config.CONTEXT_KEYWORDS if k in context)
    score += sum(config.FRAME_KEYWORDS.get(k, 0) for k in config.FRAME_KEYWORDS if k in context)
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
    date_pattern = re.compile(r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日")
    for text in soup.stripped_strings:
        match = date_pattern.search(text)
        if match:
            year = extract_year_from_html(soup)
            return safe_datetime_with_25h(
                year, int(match.group("month")), int(match.group("day")), 0, 0)
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
    """コンテキストから最適な日時を抽出"""
    candidates = []

    for entry in patterns_with_handlers:
        for match in entry["pattern"].finditer(context):
            try:
                # handlerへ渡す引数の数を一致させる為の制御
                # argcount = entry["handler"].__code__.co_argcount
                # if argcount == 1:
                # dt = entry["handler"](match)
                # elif argcount == 2:
                # dt = entry["handler"](match, year)
                # elif argcount == 3:
                # dt = entry["handler"](match, year, base_date)
                # else:
                # raise ValueError("想定外の引数数")
                dt = call_handler(entry["handler"], match, year, base_date)
                # 優先度が設定されていなければ優先度0を設定
                score = 1 + score_context(context) + entry.get("confidence", 0)
                candidates.append((dt, score))
                logging.debug(
                    f"Matched pattern: {entry['pattern'].pattern}, DateTime: {dt}, Score: {score}, Context: {context[:100]}"
                )
            except Exception as e:
                logging.warning(f"[extract error] {e} / pattern={entry['pattern'].pattern} / text={match.group(0)}")
                print(f"[ERROR] handler実行中に例外発生: {e}")
                print(f"[DEBUG] handler: {entry['handler']}, pattern: {entry['pattern'].pattern}")
                print(f"[DEBUG] match: {match}")
                continue

    if not candidates:
        logging.warning(f"No datetime candidates found in context: {context[:100]}")
        return None

    # スコアが最大の日時を返す
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def extract_onair_times(soup: BeautifulSoup, year: int, base_date: datetime, radius=5) -> list:
    """
    テキストからプラットフォーム名と日時を抽出する

    Args:
        text: サイトHTMLから取得した全テキスト
        platforms: プラットフォーム名のタプル

    Returns:
        [(platform, datetime)] のリスト
    """
    results = []
    ng_results = []
    # テキストを文字列連結し1文にし行ごとに走査する為にテキストを改行区切りでリストにする
    lines = [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
    num_lines = len(lines)

    # フォールバック: 全文から抽出
    for i, line in enumerate(lines):
        for platform in config.PLATFORMS:
            if platform in line:
                # 空白区切りでテキストを1文にし正規表現に一致した日時を抽出
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
        soup = BeautifulSoup(html, "html.parser", from_encoding="utf-8")

        # 年と基準日を抽出（ここの処理を見直す）
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
        on_air：放送情報ページへリクエストするurl(基本的にon airを指定)

    Returns:
        broadcast_info:アニメの配信情報を格納した辞書型リスト
        {title: [start_date, platform]....}
    """

    broadcast_info, ng_list = {}, {}
    html = ""
    # 403の対策（bot判定を避けるためリファラーを設定
    headers = {
        "User-Agent": config.USER_AGENT,
        "Referer": "https://www.google.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Language": "ja,en;q=0.9",
        "Connection": "keep-alive",
    }

    print(f"アクセス中：")
    cnt_200 = 0  # デバッグ用
    cnt_404 = 0  # デバッグ用
    for title, base_url in title_url_map.items():
        if base_url == "":
            continue

        try:
            url = base_url.rstrip("/") + "/" + on_air
            res = requests.get(url, headers=headers, timeout=5, allow_redirects=True)

            if res.status_code == 200:
                html = res.content
                cnt_200 += 1
                print(f"リクエスト200 検索＝{cnt_200}回目, {title} : {url}")
                print(f"最終URL:{res.url}")
                print()
            elif res.status_code == 404:
                cnt_404 += 1
                print(f"リクエスト404 検索＝{cnt_404}回目, {title} : {url}")
                print(f"[WARN] 404 Not Found: {url} → base_urlで再試行")
                print()
                res = requests.get(base_url, headers=headers, timeout=5, allow_redirects=True)
                html = res.content
            elif res.status_code == 403:
                # この処理リクエストでいいかも
                print(f"[WARN] 403 Forbidden: {url} → base_urlで再試行")
                res = requests.get(base_url, headers=headers, timeout=5, allow_redirects=True)
                html = res.content
                # driver = uc.Chrome()
                # driver.get(base_url)
                # html = driver.page_source
            else:
                html = None

            # 成功以外はNGリストへ追加し記録(現状403の時しか作られないロジック)
            if res.status_code != 200:
                ng_list[title] = (res.url, res.status_code)

            # 放送情報からBeautifulSoupで配信日時・プラットフォーム名を抽出する
            if html is not None:
                broadcast_info[title] = parse_broadcast_info(html, title)

            time.sleep(random.uniform(1, 1.5))

        except requests.RequestException as e:
            print("スクレイピングエラー発生：リトライ前に少し待機", {e})
            time.sleep(2)
    print()
    print(f"リクエストコード＝200：{cnt_200}")
    print(f"リクエストコード＝404：{cnt_404}")

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

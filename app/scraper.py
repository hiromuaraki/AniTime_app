from bs4 import BeautifulSoup
from urllib.error import HTTPError, URLError
from datetime import datetime
from model.handler import patterns_with_handlers, safe_datetime_with_25h
from model.logging_config import setup_logger
import model.config as config
import requests, re, time, csv


# ロガーの準備
logging = setup_logger(name="scraper", log_file="./logs/scraper.log")


# --- 年抽出 ---
def extract_year_from_html(soup: BeautifulSoup) -> int:
    """
    HTMLから基準年を抜き出す優先ロジック:
     1) metaタグ (複数候補)
     2) 本文中の 年+月(＋日) 形式（例: 2025年7月5日 / 2025-07）
     3) 本文中の年単独（最初に見つかるものではなく「より新しい年」を優先）
     4) なければ現在年
    """

    # meta優先 (contentにISOや YYYY-MM-DD などが入っていることが多い)
    for key in config.META_DATE_KEYS:
        tag = soup.find("meta", attrs=key)
        if tag:
            content = (tag.get("content") or "").strip()
            if not content:
                continue
            # 先頭に年がある（YYYY...）ならそれを採用
            m = re.search(r"(20\d{2})", content)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    pass

    # 本文から "YYYY年M月" や "YYYY/M" や "YYYY-M" などを探す（放送日らしい箇所を優先）
    ymd_pattern = re.compile(r"(20\d{2})\s*[年\-/\.]\s*(0?[1-9]|1[0-2])")
    candidate_years = []
    
    for text in soup.stripped_strings:
        t = text.strip()
        if len(t) > 120:
            continue
        if m := ymd_pattern.search(t):
            candidate_years.append(int(m.group(1)))

    if candidate_years:
        return max(candidate_years)

    # 年単独（ただし長文は除く）
    year_pattern = re.compile(r"\b(20\d{2})\b")
    years = []
    for text in soup.stripped_strings:
        t = text.strip()
        if len(t) > 120:
            continue
        if m := year_pattern.search(t):
            years.append(int(m.group(1)))
    if years:
        return max(years)

    # 最後に現在年
    return datetime.now().year


def extract_base_date_from_html(year: int, soup: BeautifulSoup) -> datetime:
    """HTMLから基準日（放送開始日など）を抽出"""
    # date_pattern = re.compile(r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日")
    datetime_pattern = re.compile(
        r"(?P<month>\d{1,2})[月/](?P<day>\d{1,2})日?(?:\（?.?\）?)?\s*(?P<hour>\d{1,2}):(?P<minute>\d{2})")
    
    for text in soup.stripped_strings:
        match = datetime_pattern.search(text)
        if match:
            # 年月日フル
            year = year
            month = int(match.group("month"))
            day = int(match.group("day"))
            hour = int(match.group("hour"))
            minute = int(match.group("minute"))
            return safe_datetime_with_25h(
                year, month, day, hour, minute)
    return datetime.now()


# 修正前
# def extract_best_datetime_with_context(context: str, year: int, base_date: datetime):
#     """
#     コンテキストから最適な日時を抽出しスコアが最大の日時を返す.
#     例）スコア：最速配信 or 独占 or 地上波同時などの特定のキーワードに設定している優先度

#     Args:
#         context:
#         year:
#         base_date:

#     Returns:
#         candidates: スコアが高い日時 
    
#     """
    
#     # contextから年月日だけ抽出してbase_dateを上書きする
#     md_match = re.search(r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日", context)
#     if md_match:
#         month = int(md_match.group("month"))
#         day = int(md_match.group("day"))
#         base_date = datetime(year, month, day)
    
#     candidates = []

#     for pattern in patterns_with_handlers:
#         for match in pattern["pattern"].finditer(context):
#             try:
#                 dt = call_handler(pattern["handler"], match, year, base_date)
#                 # 優先度が設定されていなければ0を設定
#                 score = 1 + pattern.get("confidence", 0)
#                 # score = 1 + score_context_near_match(context, match.start()) + pattern.get("confidence", 0)
                
#                 # スコア計算改善（出現したら1回だけ加算）
#                 sliced_context = context[max(0, match.start()-50): match.end()+50]
#                 score += sum(v for k, v in config.CONTEXT_KEYWORDS.items() if k in sliced_context)
#                 score += sum(v for k, v in config.FRAME_KEYWORDS.items() if k in sliced_context)
#                 score += sum(v for k, v in config.PLATFORMS.items() if k in sliced_context)

#                 candidates.append((dt, score))
#                 logging.debug(
#                     f"Matched pattern: ID: {pattern['id']}, {pattern['pattern'].pattern},"
#                     f"DateTime: {dt}, Score: {score}, Context: {context[:100]}"
#                 )
#             except Exception as e:
#                 logging.warning(f"[extract error] {e} /ID: {pattern['id']} / pattern={pattern['pattern'].pattern} / handler={pattern['handler']} text={match.group(0)}")
#                 print(f"[ERROR] handler実行中に例外発生: {e}")
#                 print(f"[DEBUG] handler: {pattern['handler']}, pattern: {pattern['pattern'].pattern}")
#                 continue

#     if not candidates:
#         logging.warning(f"No datetime candidates found in context: {context[:100]}")
#         return None

#     # スコアが最大の日時を返す
#     # スコア降順 → base_dateに近い順
#     candidates.sort(
#         key=lambda x: (x[1], -abs((x[0] - base_date).total_seconds())),
#         reverse=True
#     )
#     # candidates.sort(key=lambda x: x[1], reverse=True)
#     # デバッグ用
#     for dt, score in candidates:
#         print(f"datetime={dt}, score={score}")
    
#     return candidates[0][0]


# 修正版
def extract_best_datetime_with_context(context: str, year: int, base_date: datetime):
    """
    コンテキストから最適な日時を抽出し、スコア最大の日時を返す。
    前後行の文脈も参照し、スコアリングを拡張可能にしている。
    """
    lines = context.splitlines()
    candidates = []

    for idx, line in enumerate(lines):
        # 前後行を含むスライス
        start = max(0, idx - 1)
        end = min(len(lines), idx + 2)
        context_slice = "\n".join(lines[start:end])

        # 年月日を含むか判定
        md_match = re.search(r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日", context_slice)
        slice_base_date = base_date
        if md_match:
            month = int(md_match.group("month"))
            day = int(md_match.group("day"))
            slice_base_date = slice_base_date.replace(month=month, day=day)

        # パターンマッチ
        for pattern in patterns_with_handlers:
            for match in pattern["pattern"].finditer(context_slice):
                try:
                    handler = pattern["handler"]
                    dt = handler(match, base_date.year, slice_base_date)
                    # 基本スコア
                    score = 1 + pattern.get("confidence", 0)

                    # キーワードスコア（出現1回のみ）
                    for k, v in config.CONTEXT_KEYWORDS.items():
                        if k in context_slice:
                            score += v
                    # for k, v in config.FRAME_KEYWORDS.items():
                    #     if k in context_slice:
                    #         score += v
                    for k, v in config.PLATFORMS.items():
                        if k in context_slice:
                            score += v

                    candidates.append((dt, score))
                    logging.debug(f"Matched pattern ID={pattern['id']}, datetime={dt}, score={score}, context={context_slice[:100]}")
                except Exception as e:
                    logging.warning(f"[extract error] {e} / pattern ID={pattern['id']} / match={match.group(0)}")
                    continue

    if not candidates:
        logging.warning(f"No datetime candidates found in context: {context[:100]}")
        return None

    logging.info(f"【リスト並べ替え前】：{candidates}")
    # スコア降順 → 
    # candidates.sort(key=lambda x: (x[1], -abs((x[0] - base_date).total_seconds())), reverse=True)


    # ソートルール：
    # 1. 年月日 → 昇順
    # 2. 時分 → 降順
    # 3. スコア → 降順
    candidates.sort(
        key=lambda item: (
            item[0].date(),   # 日付 昇順
            -item[0].hour,    # 時間 降順
            -item[0].minute,  # 分   降順
            -item[1]          # スコア 降順
        )
    )

    # デバッグ出力
    for dt, score in candidates:
        print(f"datetime={dt}, score={score}")

    return candidates[0][0]




def extract_onair_times(soup: BeautifulSoup, year: int, base_date: datetime, radius=5) -> list:
    """
    テキストからプラットフォームと日時を抽出する.

    Args:
        soup: サイトHTMLから取得した放送情報
        year: 基準の年
        base_date: 放送開始日時の基準月日
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
                    # プラットフォームと対応した配信日時を追加
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


def find_earliest_per_platform(matches: list, works) -> list:
    """
    プラットフォームに対応した最速配信情報を返す

    Args:
        matches: 


    Returns:
        list[{str, datetime}]
    """
    
    platform_map = {}
    production, url = works
    for platform, dt in matches:
        if platform not in platform_map or dt < platform_map[platform][0]:
            platform_map[platform] = (dt, production, url)
    
    # 最速日時順にソート
    return sorted(platform_map.items(), key=lambda x: x[1][0])


def parse_broadcast_info(html, title: str, *works: list) -> list:
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
        base_date = extract_base_date_from_html(year, soup)
        logging.info(f"Extracted year: {year}, base_date: {base_date} for title: {title}")

        # 放送情報を抽出
        matches = extract_onair_times(soup, year, base_date)
        earliest_list = find_earliest_per_platform(matches, works)

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
    for title, works in title_url_map.items():
        base_url, production = works[0]
        
        if base_url == "": continue

        try:
            url = base_url.rstrip("/") + "/" + on_air
            res = requests.get(url, headers=headers, timeout=5, allow_redirects=True)

            if res.status_code == 200:
                html = res.content
            
            elif res.status_code == 404:
                # リクエスト成功以外は必ずベースURLを渡す
                for other_on_air in other_on_airs:
                    res = requests.get(base_url + other_on_air, headers=headers, timeout=5, allow_redirects=True)
                    if res.status_code == 200:
                        html = res.content
                        break
                if res.status_code != 200:
                    res_base = requests.get(base_url, headers=headers, timeout=5, allow_redirects=True)
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
                broadcast_info[title] = parse_broadcast_info(html, title, production, base_url)
                
            time.sleep(1)

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
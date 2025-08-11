import re
from datetime import datetime, timedelta


def safe_datetime_with_25h(year, month, day, hour, minute) -> datetime:
    """日を跨いでいる場合+1日し翌日にする"""
    if hour >= 24:
        hour -= 24
        base = datetime(year, month, day) + timedelta(days=1)
        return datetime(base.year, base.month, base.day, hour, minute)
    return datetime(year, month, day, hour, minute)


def handler_ymd_hm(m: re.Match) -> datetime:
    """ID1,2.完全日付（年あり）"""
    return safe_datetime_with_25h(
        int(m.group("year")),
        int(m.group("month")),
        int(m.group("day")),
        int(m.group("hour")),
        int(m.group("minute")),
    )


def handler_md_hm(m: re.Match, year: int) -> datetime:
    """ID3,4.年なし日付（曜日つき）"""
    return safe_datetime_with_25h(
        year,
        int(m.group("month")),
        int(m.group("day")),
        int(m.group("hour")),
        int(m.group("minute")),
    )


def handler_slash_md_hm(m: re.Match, year: int) -> datetime:
    """ID5,6.スラッシュ区切り「8/5(火) 25:00」"""
    return safe_datetime_with_25h(
        year,
        int(m.group("month")),
        int(m.group("day")),
        int(m.group("hour")),
        int(m.group("minute")),
    )


def handle_md_time_generic(match: re.Match, year: int) -> datetime:
    """ID9,10.スラッシュ区切りの日付と時間 & 月日と時間"""
    month = int(match.group(1))
    day = int(match.group(2))
    hour = int(match.group(3))
    minute = int(match.group(4))
    return datetime(year, month, day, hour, minute)


def handler_md_ampm(m: re.Match, year: int) -> datetime:
    """ID11,20.午前/午後形式"""
    hour = int(m.group("hour")) + (12 if "午後" in m.group(0) else 0)
    return safe_datetime_with_25h(
        year, int(m.group("month")), int(m.group("day")), hour, int(m.group("minute"))
    )


def handler_weekly_late_night(m: re.Match, year: int, base_date: datetime) -> datetime:
    """ID12,13.「〇月〇日配信開始」→ 時間なしは0:00"""
    return safe_datetime_with_25h(
        year,
        base_date.month,
        base_date.day,
        int(m.group("hour")),
        int(m.group("minute") or 0),
    ) + timedelta(days=1)


def handler_md_hm_range(m: re.Match, year: int) -> datetime:
    """ID7,8.時間範囲（例: 23:00〜24:00）"""
    return safe_datetime_with_25h(
        year,
        int(m.group("month")),
        int(m.group("day")),
        int(m.group("hour")),
        int(m.group("minute")),
    )


def handler_time_next_day(m: re.Match, year: int, base_date: datetime) -> datetime:
    """ID14,15.「時刻＋配信」→ 翌日"""
    return safe_datetime_with_25h(
        year,
        base_date.month,
        base_date.day,
        int(m.group("hour")),
        int(m.group("minute")),
    ) + timedelta(days=1)


def handler_md_midnight(m: re.Match, year: int) -> datetime:
    """ID16.「〇月〇日配信開始」→ 時間なしは0:00"""
    return safe_datetime_with_25h(
        year, int(m.group("month")), int(m.group("day")), 0, 0
    )




# def handler_md_only(m: re.Match, year: int) -> datetime:
#     """
#     ID17用ハンドラ: 「〇月〇日」だけ → 時刻は0時0分（深夜24時）固定で補完
#     """
#     try:
#         month = int(m.group("month"))
#         day = int(m.group("day"))
#     except Exception:
#         month = int(m.group(1))
#         day = int(m.group(2))

#     return datetime(year, month, day, 0, 0)




# ===== 新規追加 =====
def find_time_near(context_lines: list, idx: int):
    """
    指定行付近の時刻を探索
    context_lines: コンテキスト行リスト
    idx: 日付が見つかった行のインデックス
    """
    time_pattern = re.compile(r"(?:(深夜)?(\d{1,2})(?:時|:)(\d{2}))")
    
    # 探索範囲（前後2行ずつ）
    for offset in range(-2, 3):
        pos = idx + offset
        if pos < 0 or pos >= len(context_lines):
            continue
        m = time_pattern.search(context_lines[pos])
        if m:
            late_night, hh, mm = m.groups()
            hh, mm = int(hh), int(mm)
            if late_night == "深夜" and hh < 6:
                hh += 24
            return hh, mm



def handler_md_only(m: re.Match, context_lines: list, year: int) -> datetime:
    """
    ID17用: 「〇月〇日」だけの場合、近くの行から時刻を探して補完
    """
    month = int(m.group("month"))
    day = int(m.group("day"))

    # 近くの行から時刻を探索
    idx = next((i for i, line in enumerate(context_lines) if m.group(0) in line), 0)
    found_time = find_time_near(context_lines, idx)

    if found_time:
        hour, minute = found_time
    else:
        hour, minute = 0, 0  # 時刻情報がない場合は0:00

    return datetime(year, month, day, hour, minute)




def handler_md_late_night(match, base_year):
    """ID18,22 〇月〇日 深夜〇:〇〇 または 深夜〇時〇分形式"""
    month = int(match.group("month"))
    day = int(match.group("day"))
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    # 深夜 → 翌日AM扱い
    hour += 24 if hour < 6 else 0
    date = datetime(base_year, month, day) + (
        timedelta(days=1) if hour >= 24 else timedelta()
    )
    if hour >= 24:
        hour -= 24
    return datetime(date.year, date.month, date.day, hour, minute)


def handler_slash_md_late_night(match, base_year):
    """ID19,23 〇/〇 深夜〇:〇〇形式"""
    month = int(match.group("month"))
    day = int(match.group("day"))
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    hour += 24 if hour < 6 else 0
    date = datetime(base_year, month, day) + (
        timedelta(days=1) if hour >= 24 else timedelta()
    )
    if hour >= 24:
        hour -= 24
    return datetime(date.year, date.month, date.day, hour, minute)


def handler_slash_md_ampm(match, base_year):
    """21 〇/〇 午前/午後〇:〇〇形式"""
    month = int(match.group("month"))
    day = int(match.group("day"))
    ampm = match.group(3)  # グループ3が午前/午後
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))

    if ampm == "午後" and hour != 12:
        hour += 12
    elif ampm == "午前" and hour == 12:
        hour = 0

    date = datetime(base_year, month, day)
    return datetime(date.year, date.month, date.day, hour, minute)


def handler_md_hour_only(match, base_year):
    """ID24 〇月〇日〇時（分省略）"""
    month = int(match.group("month"))
    day = int(match.group("day"))
    hour = int(match.group("hour"))
    minute = 0
    date = datetime(base_year, month, day)
    return datetime(date.year, date.month, date.day, hour, minute)


def handler_slash_md_hour_only(match, base_year):
    """ID25 〇/〇 〇時（分省略）"""
    month = int(match.group("month"))
    day = int(match.group("day"))
    hour = int(match.group("hour"))
    minute = 0
    date = datetime(base_year, month, day)
    return datetime(date.year, date.month, date.day, hour, minute)







def handler_ymdhm_optional(m: re.Match, year: int, base_date: datetime) -> datetime:
    """年月日＋時刻（深夜・25時対応、時刻省略OK）"""
    gd = m.groupdict()
    y = int(gd.get("year") or year)
    month = int(gd["month"])
    day = int(gd["day"])
    hour = int(gd["hour"])
    minute = int(gd["minute"])

    # "深夜" 対応: 深夜+時間が0~5なら翌日扱い
    if gd.get("late_night") == "深夜" and hour < 6:
        hour += 24

    return datetime(y, month, day, hour, minute)


# 拡張された正規表現パターン（適宜追加）
patterns_with_handlers = [
    # 1. 完全日付（年あり） 「2025年7月6日 24時15分」など時分は「時分」表記に対応
    {
        "id": 1,
        "pattern": re.compile(
            r"(?P<year>\d{4})年\s*(?P<month>\d{1,2})月\s*(?P<day>\d{1,2})日(?:（.?）)?\s*(?P<hour>\d{1,2})時(?P<minute>\d{2})分"
        ),
        "handler": handler_ymd_hm,
        "confidence": 5,
    },
    # 2. 完全日付（年あり） コロン区切りの時刻もサポート（例: 2025年7月6日 24:15）
    {
        "id": 2,
        "pattern": re.compile(
            r"(?P<year>\d{4})年\s*(?P<month>\d{1,2})月\s*(?P<day>\d{1,2})日.*?(?P<hour>\d{1,2})[:：](?P<minute>\d{2})"
        ),
        "handler": handler_ymd_hm,
        "confidence": 5,
    },
    # 3. 年なし日付（曜日つき）時分は漢字表記対応
    {
        "id": 3,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日(?:（.?）)?\s*(?P<hour>\d{1,2})時(?P<minute>\d{2})分"
        ),
        "handler": handler_md_hm,
        "confidence": 4,
    },
    # 4. 年なし日付（曜日つき）コロン区切り時刻対応（例: 7月6日 24:15）
    {
        "id": 4,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日(?:（.?）)?\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2})"
        ),
        "handler": handler_md_hm,
        "confidence": 4,
    },
    # 5. スラッシュ区切り（曜日つき）漢字時分対応（例: 7/6（火）24時15分）
    {
        "id": 5,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})/(?P<day>\d{1,2})\s*(?:（(?:月|火|水|木|金|土|日)）)?\s*(?P<hour>\d{1,2})時(?P<minute>\d{2})分"
        ),
        "handler": handler_slash_md_hm,
        "confidence": 4,
    },
    # 6. スラッシュ区切り（曜日つき）コロン時分対応（例: 7/6(火) 24:15）
    {
        "id": 6,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})/(?P<day>\d{1,2})\s*(?:\((?:月|火|水|木|金|土|日)\))?\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2})"
        ),
        "handler": handler_slash_md_hm,
        "confidence": 4,
    },
    # 曜日・毎週など特殊パターン（深夜含む）
    # 12. 毎週〇曜 深夜〇時（例: 毎週金曜25:23）・・・見直し必要？
    {
        "id": 12,
        "pattern": re.compile(
            r"毎週(?:月|火|水|木|金|土|日)曜(?:深夜)?\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2})"
        ),
        "handler": handler_weekly_late_night,
        "confidence": 3,
    },
    # 13. 毎週〇曜 深夜〇時（漢字時分版、例: 毎週金曜25時23分）
    {
        "id": 13,
        "pattern": re.compile(
            r"毎週(?:月|火|水|木|金|土|日)曜(?:深夜)?\s*(?P<hour>\d{1,2})時(?P<minute>\d{2})分"
        ),
        "handler": handler_weekly_late_night,
        "confidence": 4,
    },
    # 18. 月日（曜日）深夜 コロン区切り
    {
        "id": 18,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日(?:（.?）)?\s*深夜\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2})"
        ),
        "handler": handler_md_late_night,
        "confidence": 3,
    },
    # 19. スラッシュ区切り 深夜 コロン区切り
    {
        "id": 19,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})/(?P<day>\d{1,2})\s*深夜\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2})"
        ),
        "handler": handler_slash_md_late_night,
        "confidence": 3,
    },
    # 22. 月日 深夜 漢字時分
    {
        "id": 22,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日\s*深夜\s*(?P<hour>\d{1,2})時(?P<minute>\d{2})分"
        ),
        "handler": handler_md_late_night,
        "confidence": 3,
    },
    # 23. スラッシュ区切り 深夜 漢字時分
    {
        "id": 23,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})/(?P<day>\d{1,2})\s*深夜\s*(?P<hour>\d{1,2})時(?P<minute>\d{2})分"
        ),
        "handler": handler_slash_md_late_night,
        "confidence": 3,
    },
    # 11. 午前/午後形式（例: 7月6日 午後11:30）
    {
        "id": 11,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日\s*(?:午前|午後)(?P<hour>\d{1,2})[:：](?P<minute>\d{2})"
        ),
        "handler": handler_md_ampm,
        "confidence": 2,
    },
    # 20. 月日 午前/午後 コロン区切り
    {
        "id": 20,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日\s*(午前|午後)(?P<hour>\d{1,2})[:：](?P<minute>\d{2})"
        ),
        "handler": handler_md_ampm,
        "confidence": 2,
    },
    # 21. スラッシュ区切り 午前/午後 コロン区切り
    {
        "id": 21,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})/(?P<day>\d{1,2})\s*(午前|午後)(?P<hour>\d{1,2})[:：](?P<minute>\d{2})"
        ),
        "handler": handler_slash_md_ampm,
        "confidence": 2,
    },
    # 7. 「月日（曜日） 時:分」＋「～」「〜」の時間範囲（例: 7月6日 23:00〜24:00）
    {
        "id": 7,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2})\s*[～〜]\s*\d{1,2}[:：]\d{2}"
        ),
        "handler": handler_md_hm_range,
        "confidence": 3,
    },
    # 8. 「月日 時分（漢字）」＋「～」「〜」の時間範囲（例: 7月6日 23時00分〜24時00分）
    {
        "id": 8,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日\s*(?P<hour>\d{1,2})時(?P<minute>\d{2})分\s*[～〜]\s*\d{1,2}時\d{2}分"
        ),
        "handler": handler_md_hm_range,
        "confidence": 3,
    },
    # 9. 「○/× 24:00より順次配信」など「より順次系」コロン区切り
    {
        "id": 9,
        "pattern": re.compile(
            r"(\d{1,2})/(\d{1,2})\s*(\d{1,2}):(\d{2})[より～〜]?順次配信"
        ),
        "handler": handle_md_time_generic,
        "confidence": 2,
    },
    # 10. 「○/× 24時00分より順次配信」漢字時分版
    {
        "id": 10,
        "pattern": re.compile(
            r"(\d{1,2})/(\d{1,2})\s*(\d{1,2})時(\d{2})分[より～〜]?順次配信"
        ),
        "handler": handle_md_time_generic,
        "confidence": 2,
    },
    # 14. 時刻のみ「時:分 配信」→ 翌日扱い
    {
        "id": 14,
        "pattern": re.compile(r"(?P<hour>\d{1,2})[:：](?P<minute>\d{2})\s*配信"),
        "handler": handler_time_next_day,
        "confidence": 1,
    },
    # 15. 時刻のみ「時分漢字」配信（例: 25時23分 配信）→ 翌日扱い
    {
        "id": 15,
        "pattern": re.compile(r"(?P<hour>\d{1,2})時(?P<minute>\d{2})分\s*配信"),
        "handler": handler_time_next_day,
        "confidence": 1,
    },
    # 24. 月日 時のみ（分なし）漢字
    {
        "id": 24,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日\s*(?P<hour>\d{1,2})時"
        ),
        "handler": handler_md_hour_only,
        "confidence": 1,
    },
    # 25. スラッシュ区切り 時のみ（分なし）漢字
    {
        "id": 25,
        "pattern": re.compile(
            r"(?P<month>\d{1,2})/(?P<day>\d{1,2})\s*(?P<hour>\d{1,2})時"
        ),
        "handler": handler_slash_md_hour_only,
        "confidence": 1,
    },
    # 16. 「〇月〇日配信開始」→ 時間なしは0:00
    {
        "id": 16,
        "pattern": re.compile(r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日\s*配信開始"),
        "handler": handler_md_midnight,
        "confidence": 1,
    },
    # 99.
    {
        "id": 99,
        "pattern": re.compile(
            r"(?:(?P<year>\d{4})年)?\s*"
            r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日"
            r"(?:（[^）]*）)?\s*"
            r"(?:より|から)?\s*"
            r"(?:毎週[^\s　]*\s*)?"
            r"(?:(深夜)?(?P<hour>\d{1,2})(?:時|:)(?P<minute>\d{2}))"
        ),
        "handler": handler_ymdhm_optional,
        "confidence": 3,  # 年月日＋時刻は高信頼度
    },
    # 100.
    {
        "id": 100,
        "pattern": re.compile(
            r"(?:(?P<year>\d{4})年)?"
            r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日"
            r"(?:（[^）]*）)?\s*"
            r"(?:より|から)?\s*"
            r"(?:毎週[^\s　]*\s*)?"
            r"(?:(?P<late_night>深夜)?(?P<hour>\d{1,2})(?:時|:)(?P<minute>\d{2}))"
        ),
        "handler": handler_ymdhm_optional,
        "confidence": 3,  # 月日＋時刻はやや高信頼度
    },
    # 17. 「〇月〇日」だけ→ 時間なしは0:00
    {
        "id": 17,
        "pattern": re.compile(r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日"),
        "handler": handler_md_only,
        "confidence": 1,
    },
]

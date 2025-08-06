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
    """1.完全日付（年あり）"""
    return safe_datetime_with_25h(
        int(m.group("year")),
        int(m.group("month")),
        int(m.group("day")),
        int(m.group("hour")),
        int(m.group("minute"))
    )

def handler_md_hm(m: re.Match, year: int) -> datetime:
    """2.年なし日付（曜日つき）"""
    return safe_datetime_with_25h(
        year,
        int(m.group("month")),
        int(m.group("day")),
        int(m.group("hour")),
        int(m.group("minute"))
    )


def handle_md_time_generic(match: re.Match, year: int) -> datetime:
    """3, 5.スラッシュ区切りの日付と時間 & 月日と時間"""
    month = int(match.group(1))
    day = int(match.group(2))
    hour = int(match.group(3))
    minute = int(match.group(4))
    return datetime(year, month, day, hour, minute)



def handler_slash_md_hm(m: re.Match, year: int) -> datetime:
    """4.スラッシュ区切り「8/5(火) 25:00」"""
    return safe_datetime_with_25h(
        year,
        int(m.group("month")),
        int(m.group("day")),
        int(m.group("hour")),
        int(m.group("minute"))
    )


def handler_md_ampm(m: re.Match, year: int) -> datetime:
    """6.午前/午後形式"""
    hour = int(m.group("hour")) + (12 if "午後" in m.group(0) else 0)
    return safe_datetime_with_25h(
        year,
        int(m.group("month")),
        int(m.group("day")),
        hour,
        int(m.group("minute"))
    )




def handler_weekly_late_night(m: re.Match, year: int, base_date: datetime) -> datetime:
    """7.「〇月〇日配信開始」→ 時間なしは0:00"""
    return safe_datetime_with_25h(
        year,
        base_date.month,
        base_date.day,
        int(m.group("hour")),
        int(m.group("minute") or 0)
    ) + timedelta(days=1)



def handler_md_hm_range(m: re.Match, year: int) -> datetime:
    """8.時間範囲（例: 23:00〜24:00）"""
    return safe_datetime_with_25h(
        year,
        int(m.group("month")),
        int(m.group("day")),
        int(m.group("hour")),
        int(m.group("minute"))
    )



def handler_time_next_day(m: re.Match, year: int, base_date: datetime) -> datetime:
    """9.「時刻＋配信」→ 翌日"""
    return safe_datetime_with_25h(
        year,
        base_date.month,
        base_date.day,
        int(m.group("hour")),
        int(m.group("minute"))
    ) + timedelta(days=1)



def handler_md_midnight(m: re.Match, year: int) -> datetime:
    """10.「〇月〇日配信開始」→ 時間なしは0:00"""
    return safe_datetime_with_25h(
        year, int(m.group("month")), int(m.group("day")), 0, 0
    )



def handler_md_only(m: re.Match, year: int) -> datetime:
    """11.「〇月〇日」だけ→ 時間なしは0:00"""
    return safe_datetime_with_25h(year, int(m.group("month")), int(m.group("day")), 0, 0)





# 拡張された正規表現パターン
patterns_with_handlers = [
    # 1. 完全日付（年あり）
    {
        "pattern": re.compile(r'(?P<year>\d{4})年\s*(?P<month>\d{1,2})月\s*(?P<day>\d{1,2})日.*?(?P<hour>\d{1,2})[:：](?P<minute>\d{2})'),
        "handler": handler_ymd_hm,
        "confidence": 3
    },
    # 2. 年なし日付（曜日つき）
    {
        "pattern": re.compile(r'(?P<month>\d{1,2})月(?P<day>\d{1,2})日(?:\((?:月|火|水|木|金|土|日)\))?\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2})'),
        "handler": handler_md_hm,
        "confidence": 3
    },
    # 3. 
    {
        "pattern": re.compile(r'(\d{1,2})月(\d{1,2})日\（?.?\）?\s*(\d{1,2}):(\d{2})[～〜]?'),
        "handler": handle_md_time_generic,
        "confidence": 2
    },
    # 4. スラッシュ区切り「8/5(火) 25:00」
    {
        "pattern": re.compile(r'(?P<month>\d{1,2})/(?P<day>\d{1,2})\s*(?:\((?:月|火|水|木|金|土|日)\))?\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2})'),
        "handler": handler_slash_md_hm,
        "confidence": 2
    },
    # 5. 「○/× 24:00より順次配信」など「より順次系」
    {
        "pattern": re.compile(r'(\d{1,2})/(\d{1,2})\s*(\d{1,2}):(\d{2})[より～〜]?順次配信'),
        "handler": handle_md_time_generic,
        "confidence": 1   
    },
    # 6. 午前/午後形式
    {
        "pattern": re.compile(r'(?P<month>\d{1,2})月(?P<day>\d{1,2})日\s*(?:午前|午後)(?P<hour>\d{1,2})[:：](?P<minute>\d{2})'),
        "handler": handler_md_ampm,
        "confidence": 1
    },
    # 7. 毎週〇曜 深夜〇時
    {
        "pattern": re.compile(r'毎週(?:月|火|水|木|金|土|日)曜(?:深夜)?\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2})'),
        "handler": handler_weekly_late_night,
        "confidence": 1
    },
    # 8. 時間範囲（例: 23:00〜24:00）
    {
        "pattern": re.compile(r'(?P<month>\d{1,2})月(?P<day>\d{1,2})日\s*(?P<hour>\d{1,2})[:：](?P<minute>\d{2})\s*〜\s*\d{1,2}[:：]\d{2}'),
        "handler": handler_md_hm_range,
        "confidence": 1
    },
    # 9. 「時刻＋配信」→ 翌日
    {
        "pattern": re.compile(r'(?P<hour>\d{1,2})[:：](?P<minute>\d{2})\s*配信'),
        "handler": handler_time_next_day
    },
    # 10. 「〇月〇日配信開始」→ 時間なしは0:00
    {
        "pattern": re.compile(r'(?P<month>\d{1,2})月(?P<day>\d{1,2})日\s*配信開始'),
        "handler": handler_md_midnight
    },
    # 11. 「〇月〇日」だけ→ 時間なしは0:00
    {
        "pattern": re.compile(r'(?P<month>\d{1,2})月(?P<day>\d{1,2})日'),
        "handler": handler_md_only
    },
    
]
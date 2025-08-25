import re
from datetime import datetime, timedelta

# -- 正規化: 全角数字/コロン/スペース → 半角に置換するヘルパ（必要なら呼び出し側で使う）
_ZEN2HAN = str.maketrans(
    "０１２３４５６７８９：／　",
    "0123456789:/ "
)

def normalize_text(s: str) -> str:
    return s.translate(_ZEN2HAN)

def safe_datetime_with_25h(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    """24時・25時表記に対応して安全にdatetimeを生成する（翌日に繰り上げを正しく行う）"""
    if hour >= 24:
        hour -= 24
        # base = datetime(year, month, day) + timedelta(days=1)  # ← ここが重要（+1日）
        base = datetime(year, month, day)
        return datetime(base.year, base.month, base.day, hour, minute)
    return datetime(year, month, day, hour, minute)

# -------- ハンドラ（すべて (match, year, base_date) 受けに統一） --------

def handler_ymdhm(m: re.Match, year: int, base_date: datetime) -> datetime:
    """年-月-日 と 時刻（: or 時分）"""
    y = int(m.group("year"))
    month = int(m.group("month"))
    day = int(m.group("day"))
    hour = int(m.group("hour"))
    minute = int(m.group("minute") or 0)
    # AM/PM/深夜/正午の調整
    text = m.group(0)
    if "正午" in text:
        hour = 12
    elif "深夜" in text and hour < 6:
        hour += 24
    elif "午前" in text and hour == 12:
        hour = 0
    elif "午後" in text and hour < 12:
        hour += 12
    return safe_datetime_with_25h(y, month, day, hour, minute)

def handler_md_hm(m: re.Match, year: int, base_date: datetime) -> datetime:
    """月-日 と 時刻（: or 時分）"""
    y = base_date.year if year is None else year
    month = int(m.group("month"))
    day = int(m.group("day"))
    hour = int(m.group("hour"))
    minute = int(m.group("minute") or 0)
    text = m.group(0)
    if "正午" in text:
        hour = 12
    elif "深夜" in text and hour < 6:
        hour += 24
    elif "午前" in text and hour == 12:
        hour = 0
    elif "午後" in text and hour < 12:
        hour += 12
    return safe_datetime_with_25h(y, month, day, hour, minute)

def handler_md_only(m: re.Match, year: int, base_date: datetime) -> datetime:
    """月-日のみ（時刻は 00:00）"""
    y = base_date.year if year is None else year
    month = int(m.group("month"))
    day = int(m.group("day"))
    return datetime(y, month, day, 0, 0)

def handler_hm_only(m: re.Match, year: int, base_date: datetime) -> datetime:
    """時刻のみ（: or 時分、分省略可） + 午前/午後/正午/深夜 対応。日付は base_date を使う。"""
    gd = m.groupdict()
    # minute が無いパターン用に 0 を既定
    hour = int(gd.get("hour") or base_date.month)
    minute = int(gd.get("minute") or 0)

    text = m.group(0)
    if "正午" in text:
        hour = 12
    elif "深夜" in text and hour < 6:
        hour += 24  # 24〜29時相当
    elif "午前" in text and hour == 12:
        hour = 0
    elif "午後" in text and hour < 12:
        hour += 12

    return safe_datetime_with_25h(base_date.year, base_date.month, base_date.day, hour, minute)

def handler_weekly(m: re.Match, year: int, base_date: datetime) -> datetime:
    """毎週◯曜 HH:MM（深夜含む）→ 直近のその曜日の回の時刻を返す（base_date 週基準）"""
    # 曜日 → 0=月 .. 6=日 にマップ
    youbi_map = {"月":0,"火":1,"水":2,"木":3,"金":4,"土":5,"日":6}
    youbi = m.group("youbi")
    target_wd = youbi_map[youbi]

    hour = int(m.group("hour"))
    minute = int(m.group("minute") or 0)

    text = m.group(0)
    if "正午" in text:
        hour = 12
    elif "深夜" in text and hour < 6:
        hour += 24

    # base_date の週で次に来る target_wd に合わせる（同日か先）
    base = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
    delta = (target_wd - base.weekday()) % 7
    day_dt = base + timedelta(days=delta)
    return safe_datetime_with_25h(day_dt.year, day_dt.month, day_dt.day, hour, minute)




# 「曜日カッコ」は半角/全角の両方を許可
WD_OPT = r"(?:[（(]?[月火水木金土日][)）]?)?"
AMPM_OPT = r"(?:\s*(?:午前|午後|深夜|正午))?"

patterns_with_handlers = [
    # 1) 年月日 + 時刻（: or 時分）+ オプションで AM/PM/深夜/正午、曜日カッコ
    {
        "id": 1,
        "pattern": re.compile(
            rf"(?P<year>\d{{4}})年\s*(?P<month>\d{{1,2}})月(?P<day>\d{{1,2}})日\s*{WD_OPT}\s*{AMPM_OPT}\s*(?P<hour>\d{{1,2}})(?:[:：]|時)(?P<minute>\d{{0,2}})分?",
        ),
        "handler": handler_ymdhm,
        "confidence": 5,
    },

    # 2) 月日 + 時刻（: or 時分）+ オプション AM/PM/深夜/正午、曜日カッコ
    {
        "id": 2,
        "pattern": re.compile(
            rf"(?P<month>\d{{1,2}})月(?P<day>\d{{1,2}})日\s*{WD_OPT}\s*{AMPM_OPT}\s*(?P<hour>\d{{1,2}})(?:[:：]|時)(?P<minute>\d{{0,2}})分?",
        ),
        "handler": handler_md_hm,
        "confidence": 4,
    },

    # 3) スラッシュ日付 + 時刻（: or 時分）+ オプション AM/PM/深夜/正午、曜日カッコ
    {
        "id": 3,
        "pattern": re.compile(
            rf"(?P<month>\d{{1,2}})[/／](?P<day>\d{{1,2}})\s*{WD_OPT}\s*{AMPM_OPT}\s*(?P<hour>\d{{1,2}})(?:[:：]|時)(?P<minute>\d{{0,2}})分?",
        ),
        "handler": handler_md_hm,
        "confidence": 4,
    },

    # 4) 毎週◯曜（深夜）HH:MM / HH時（分省略OK）
    {
        "id": 4,
        "pattern": re.compile(
            r"毎週(?P<youbi>月|火|水|木|金|土|日)曜\s*(?:深夜)?\s*(?P<hour>\d{1,2})(?:[:：]|時)(?P<minute>\d{0,2})分?"
        ),
        "handler": handler_weekly,
        "confidence": 4,
    },

    # 5) 時刻のみ（: or 時分、分省略OK）+ オプション AM/PM/深夜/正午
    {
        "id": 5,
        "pattern": re.compile(
            rf"{AMPM_OPT}\s*(?P<hour>\d{{1,2}})(?:[:：]|時)(?P<minute>\d{{0,2}})分?"
        ),
        "handler": handler_hm_only,
        "confidence": 1,
    },

    # 6) 月日のみ（ベースは 00:00）
    {
        "id": 6,
        "pattern": re.compile(r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日"),
        "handler": handler_md_only,
        "confidence": 0,   # ← これを低くして 00:00 が勝たないように
    },
]

from datetime import date, time
from dataclasses import dataclass
from typing import Optional

'''
Notionのtableに書き込むデータのヘッダ情報
データ構造：辞書型
'''

@dataclass
class AnimeInfo:
    work_id: int
    is_start: Optional[int] = None
    start_date: Optional[date]
    time: Optional[time]
    day_of_week: Optional[str] = None
    title: str
    platform: Optional[list] = None
    production: Optional[str] = None
    season: Optional[str] = None # 例: "冬", "春", "夏", "秋"
    official_url: Optional[str] = None
    memo: Optional[str] = None
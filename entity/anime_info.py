from datetime import date, time
from dataclasses import dataclass
from typing import Optional

'''
Notionのtableに書き込むデータのプロパティ情報
データ構造：辞書型
'''

@dataclass
class AnimeInfo:
    work_id: int
    is_start: Optional[int] = None
    start_date: Optional[date] = None
    time_: Optional[time] = None
    day_of_week: Optional[str] = None
    title: Optional[str] = None
    platform: Optional[list] = None
    production: Optional[str] = None
    official_url: Optional[str] = None
    memo: Optional[str] = None
from datetime import date, time
from dataclasses import dataclass
from typing import Optional

'''
Notionのtableに書き込むデータのヘッダ情報
データ構造：辞書型
'''

@dataclass
class AnimeInfo:
    id: int
    start_date: Optional[date]
    time: Optional[time]
    dddd: Optional[str] = None
    title: str
    subsc_name: Optional[list] = None
    production: Optional[str] = None
    year: Optional[str] = None
    month: Optional[str] = None
    season: Optional[str] = None # 例: "春", "夏", "秋", "冬"
    official_url: Optional[str] = None
    memo: Optional[str] = None
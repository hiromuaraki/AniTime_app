from datetime import datetime
import csv

# 年月日を取得
def sysdate() -> tuple:
    date = datetime.now()
    return date.year, date.month, date.day

def get_season(month: int) -> str:
    """月（1〜12)に応じて季節を判定して返す関数"""
    if month in (1, 2, 3):
        return 'winter'
    elif month in (4, 5, 6):
        return 'spring'
    elif month in (7, 8 ,9):
        return 'summer'
    else:
        return 'autumn'

def csv_read(fname: str, data: dict):
    with open(fname, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["アニメタイトル", "配信サービス", "配信開始日時"])
        
        for title, services in data.items():
            for service, dt in services:
                writer.writerow([title, service, dt.strftime("%Y-%m-%d %H:%M:%S")])



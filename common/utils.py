from datetime import datetime
import csv


def sysdate() -> tuple:
    """現在の年月日を取得"""
    date = datetime.now()
    return date.year, date.month, date.day

def get_season(month: int) -> str:
    """
    月（1〜12)に応じて季節を判定して返す関数.
    クール開始-1ヶ月前にAPIを取得できるように+1ヶ月調整
    
    <API取得&スクレイピング時期>
        初回 | 更新
    冬  12月 | 1月
    春  3月  | 4月
    夏  6月  | 7月
    秋  9月  | 10月
    """
    if month in (2, 3, 4):
        return 'spring'
    elif month in (5, 6, 7):
        return 'summer'
    elif month in (8, 9 ,10):
        return 'autumn'
    else:
        return 'winter'

def write_csv(fname: str, data: dict) -> None:
    """最速の配信日時情報をCSVへ保存する"""
    with open(fname, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["アニメタイトル", "配信サービス", "配信開始日時"])
        
        for title, services in data.items():
            for service, dt in services:
                writer.writerow([title, service, dt.strftime("%Y-%m-%d %H:%M:%S")])



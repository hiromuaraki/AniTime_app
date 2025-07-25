from datetime import datetime

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

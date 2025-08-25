from datetime import datetime
import csv, os


def get_sysdate() -> list:
    """現在の年月日を取得"""
    date = datetime.now()
    return [date.year, date.month, date.day]



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
    if month in (4, 5, 6):
        return 'spring'
    elif month in (7, 8, 9):
        return 'summer'
    elif month in (10, 11 ,12):
        return 'autumn'
    else:
        return 'winter'


def exists_file_path(file_path: str) -> bool:
    return os.path.exists(file_path)
    


def convert_str_ymd(date: str) -> tuple:
    year, month, day = map(int, date[:10].split("-"))
    return (year, month, day)



def write_csv(fname: str, data: dict):
    """最速の配信日時情報をCSVへ保存する"""
    with open(fname, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["タイトル", "プラットフォーム", "配信開始日時", "制作会社", "URL"])
        
        for title, service in data.items():
            for platform, data in service:
                dt, production, url = data
                writer.writerow([title, platform, dt.strftime("%Y-%m-%d %H:%M"), production, url])




def read_csv(file_path: str, mode=1) -> dict:
    """
    ローカルのCSVフィアイルを読み込む.
    重複タイトルは追記でまとめる
    
    Args:
        file_path: ローカル上のCSV相対パス
        mode: 読み込みファイルの切り替え制御変数（1: works 2: scrap）
    Returns:

    """
    result = {}
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # ヘッダを飛ばす
        
        for row in reader:
            works = ()
            # worksのcsv
            if mode == 1:
                title, url, production = row[1:]
                works = (url, production)
                
            # anime_scheduleのcsv
            else:
                title, platform, dt, production, url = row
                works = (platform, dt, production, url)

            if title not in result:
                result[title] = []
            result[title].append(works)
        
        return result


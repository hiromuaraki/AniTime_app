# 共通関数をまとめる
import datetime

# 年月日を取得
def get_sysdate() -> str:
    date = datetime.datetime.today()
    return date.strftime('%Y %m %d')

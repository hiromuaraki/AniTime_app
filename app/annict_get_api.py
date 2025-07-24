import requests, json


# AnnictAPIを実行し放送予定情報を取得する
# 1回目のAPI実行時のみページ数1
def get_annict_api(url: str, page=1):
    return requests.get(url)



# AnnictAPIでアニメのアニメ情報を取得し
# {タイトル、値：公式URL}の一覧情報を返す
def programs_data(target_url: str, programs={}) -> dict:
    # 1回目のAnnictAPIを実行
    response = get_annict_api(target_url)
    print(response.text)
    # 次のページ件数が≠'null'の間 apiを実行しページ情報を取得し続ける
    
    while response['programs']['next_page'] != 'null':
        for data in response['programs']['works']:
            title, url = data['title'], data['official_site_url']
            # "programs": "work"をキーとしタイトル・URLをprogramsへセット 
            programs[title] = url
            
            # page+1→ページ件数の更新を見直し

            pass

    return programs
import requests
from model.config import typing


def get_annict_api(url: str, page=1) -> typing.Any:
    """AnnictAPIを実行し現在のシーズンのアニメ情報を取得する（初回だけ1ページ目を取得）"""
    
    try:
        response = requests.get(f'{url}&page={page}')
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        print(f'APIのアクセスに失敗しました。：{e.errno}')
    except requests.exceptions.RequestException as e:
        print(f'その他のリクエストエラー：{e.errno}')
    


def get_title_url_map(target_url: str, page=1) -> dict:
    """
    Annict APIを実行し{タイトル : URL}の対応表を返す関数

    Args:
        target_url（str）:作品情報を取得する為のAPIのURL
        page: API実行時指定するページ数（ページが切り替わる度に更新）

    Returns:
        dict[str, str]: タイトルとURLの対応表

    """
    works_url = {}
    # 1回目のAnnictAPIを実行
    response = get_annict_api(target_url)
    
    total_count = 0
    # ページネーションの制御
    # 次のページが存在する間APIを実行しページ情報を取得し続ける
    while response['total_count'] != total_count:
        
        for work in response['works']:
            title, url = work['title'], work['official_site_url']
            works_url[title] = url
            total_count += 1
        # ページ数を更新し次のページを取得
        page += 1
        response = get_annict_api(target_url, page)

    return works_url
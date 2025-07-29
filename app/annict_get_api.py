import requests
import model.config as config
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
    



def get_staffs(works_info: dict):
    """
    Annict APIを実行し 作品に紐づいた制作会社を取得し作品情報に追加する関数

    Args:


    Returns:

    """

    # 作品IDごとに紐づいた制作会社をapiで取得
    for title, work in works_info.items():
        work_id, _ = work[0]
        params = f'access_token={config.ANNICT_TOKEN}&filter_work_id={work_id}'
        target_url = config.ANNICT_STAFFS_URL + params
        response = get_annict_api(target_url)

        for staff in response['staffs']:
            if 'organization' not in staff:
                continue
            if staff['role_text'] == 'アニメーション制作':
                works_info[title].append(staff['organization']['name'])
                break


def get_title_url_map(work_url: str,  page=1) -> tuple:
    """
    Annict APIを実行し{タイトル : URL}の対応表を返す関数

    Args:
        target_url（str）:作品情報を取得する為のAPIのURL
        page: API実行時指定するページ数（ページが切り替わる度に更新）

    Returns:
        dict[str, str]: タイトルとURLの対応表
        dic[str, [str]]: タイトルごとの作品情報

    """
    works_url, works_info = {}, {}
    # 1回目のAnnictAPIを実行
    response = get_annict_api(work_url)
    
    total_count = 0
    # ページネーションの制御
    # 次のページが存在する間APIを実行しページ情報を取得し続ける
    while response['total_count'] != total_count:
        
        for work in response['works']:
            # TV,Web,otherのみ許可
            total_count += 1
            if work['media'] not in ('tv', 'web', 'other'): continue

            work_id, title, url = work['id'], work['title'], work['official_site_url']
            works_url[title] = url
            
            works_info[title] = []
            works_info[title].append((work_id, url))
        
        # ページ数を更新し次のページを取得
        page += 1
        response = get_annict_api(work_url, page)

    # 作品に紐づいた制作会社を取得
    return works_url, works_info
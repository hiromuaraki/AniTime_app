import requests, typing
import model.config as config


def get_annict_api(url: str, page=1) -> typing.Any:
    """AnnictAPIを実行し現在のシーズンのアニメ情報を取得する（初回だけ1ページ目を取得）"""
    
    try:
        response = requests.get(f'{url}&page={page}')
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        print(f'APIのアクセスに失敗しました。：{e.errno}')
    except requests.exceptions.RequestException as e:
        print(f'その他のリクエストエラー：{e.errno}')
    



def get_staffs(target_url: str, works: dict):
    """
    Annict APIを実行し 作品に紐づいた制作会社を作品情報に追加する関数

    Args:
        target_url（str）:スタッフ情報を取得する為のAPIのURL
        works: 作品IDに紐づいた制作会社を追加するための辞書

    Returns:
        None
    """

    
    page = 1
    # 作品IDごとに紐づいた制作会社をapiで取得し作品情報に追加
    for title, work in works.items():
        work_id, _ = work[0]
        
        response = get_annict_api(target_url.format(work_id), page)
        total_count = 0
        # ページネーションの制御
        while response['total_count'] != total_count:
            is_production = False
            
            for staff in response['staffs']:
                total_count += 1
                # role_otherの場合も取得できるように条件に追加
                if 'organization' in staff:
                    if staff['role_text'] == 'アニメーション制作' or staff['role_other'] == '制作':
                        production = staff['organization']['name']
                        works[title][0].append(production)
                        is_production = True
                        break
            
            # 制作会社が１ページ目にない場合に対応する為のロジック
            # 基本的に{タイトル：プロダクション}のペアで対応させる
            if not is_production and response['next_page'] is not None:
                page += 1
                response = get_annict_api(target_url.format(work_id), page)
            else:
                page = 1
                break
            


def get_works(target_url: str, page=1) -> dict:
    """
    Annict APIを実行し{タイトル : 作品ID、url}の作品情報を返す関数

    Args:
        target_url（str）:作品情報を取得する為のAPIのURL
        page: API実行時指定するページ数（ページが切り替わる度に更新）

    Returns:
        dic[str, [str]]: タイトルごとの作品情報

    """
    works = {}
    # 1回目のAnnictAPIを実行
    response = get_annict_api(target_url)
    
    total_count = 0
    # ページネーションの制御
    # 次のページが存在する間APIを実行しページ情報を取得し続ける
    while response['total_count'] != total_count:
        
        for work in response['works']:

            total_count += 1
            # TV,Web,のみ許可
            if work['media'] not in ('tv', 'web'): continue
        
            work_id, title, url = work['id'], work['title'], work['official_site_url']
            works[title] = []
            works[title].append([work_id, url])

        
        # ページ数を更新し次のページを取得
        page += 1
        response = get_annict_api(target_url, page)

    return works
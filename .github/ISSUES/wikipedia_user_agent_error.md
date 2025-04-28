# Wikipediaからの画像取得失敗：User-Agent制限の問題

## 概要
画像生成バッチ処理実行時、Wikipediaからの参照画像取得において、多数の`403 Forbidden`エラーが発生しています。スクリプト実行結果によると、57名の学者のうち、30名（約53%）の画像取得に失敗しています。これは主にWikipediaのUser-Agent制限に関連する問題です。

```
Error downloading reference image: 403 Client Error: Forbidden. Please comply with the User-Agent policy: https://meta.wikimedia.org/wiki/User-Agent_policy for url: https://upload.wikimedia.org/wikipedia/commons/...
```

## 影響
このエラーにより、多くの学者のアバター画像が自動生成できず、手動での参照画像追加が必要になっています。結果として、コンテンツ作成効率が大幅に低下しています。

## 再現手順
1. Wikipediaの画像URLに対して通常の`requests.get()`メソッドを使用
2. User-Agentヘッダーを設定せずにリクエスト
3. 403 Forbiddenエラーを受信

## 原因
Wikipediaでは、正規のUser-Agentを含まないリクエストをブロックするセキュリティポリシーが実施されています。現在のコードではHTTPリクエスト時にUser-Agentヘッダーを設定していないため、403エラーが発生しています。

[Wikimediaの公式User-Agentポリシー](https://meta.wikimedia.org/wiki/User-Agent_policy)には、アプリケーション名、バージョン、および連絡先情報を含む適切なUser-Agentヘッダーが必要と記載されています。

## 提案する解決策
`scripts/gen_avatar_from_photo.py`内の`extract_image_from_webpage`および`download_reference_image`関数にUser-Agentヘッダーを追加します。

```python
def download_reference_image(url):
    """URLから画像をダウンロードする"""
    try:
        headers = {
            'User-Agent': 'Epi-Gacha/1.0 (https://github.com/username/epi-gacha; email@example.com) Python/3.x requests/2.x'
        }
        response = requests.get(url, stream=True, timeout=10, headers=headers)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        print(f"Reference image downloaded: {img.format} {img.size}")
        return img
    except Exception as e:
        print(f"Error downloading reference image: {e}")
        return None
```

同様に`extract_image_from_webpage`関数内のrequests.getにもヘッダーを追加します。

## 追加の改善点
1. GIF形式の画像をJPEGに変換する機能の追加
2. より堅牢なエラーハンドリング
3. 取得失敗時の代替URL探索ロジックの実装

## 優先度
高：この問題により半数以上の学者画像生成が自動化できていないため、早急な対応が望ましい

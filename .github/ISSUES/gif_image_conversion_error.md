# GIF形式参照画像の変換エラー

## 概要
画像生成バッチ処理実行時、GIF形式の参照画像を処理する際にエラーが発生しています。スクリプト実行結果によると、GIF画像をJPEG形式で保存しようとした際に以下のエラーが発生しています。

```
エラー発生: cannot write mode P as JPEG
```

このエラーにより、トーマス・ベイズやエドモンド・ハレーなど、GIF形式の参照画像を持つ学者のアバター生成が失敗しています。

## 影響
GIF形式の参照画像を持つ学者のアバター生成が完全に失敗し、自動生成プロセスが中断されます。その結果、手動での画像変換作業が必要となり、効率が低下しています。

## 再現手順
1. GIF形式の参照画像（例：Thomas_Bayes.gif）をダウンロード
2. PIL/Pillowライブラリを使用して画像を開く
3. JPEG形式で保存しようとする
4. `cannot write mode P as JPEG`エラーが発生

## 原因
GIF画像はパレットモード（mode='P'）で保存されることが多く、このモードはインデックスカラーを使用します。一方、JPEGはRGBまたはCMYKモードのみをサポートしています。現在のコードでは、画像形式の変換処理が行われておらず、GIF画像をそのままJPEG形式で保存しようとしているため、エラーが発生しています。

## 提案する解決策
`download_reference_image`関数内でGIF画像を適切に変換するコードを追加します。

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
        
        # GIF画像をRGBに変換（パレットモードの処理）
        if img.format == 'GIF' or img.mode == 'P':
            img = img.convert('RGB')
            
        print(f"Reference image downloaded: {img.format} {img.size}")
        return img
    except Exception as e:
        print(f"Error downloading reference image: {e}")
        return None
```

また、`debug_generate_from_photo`関数内の画像保存部分も修正が必要です。

```python
# 保存前に画像形式を確認し変換
if img.mode != 'RGB':
    img = img.convert('RGB')
img.save(temp_img_path)
```

## 追加の改善点
1. 画像形式の自動判別と適切な変換処理の実装
2. WEBP, PNG, BMPなど他の形式も適切に処理
3. エラーメッセージの改善（より具体的な問題と解決策を示す）

## 優先度
中：User-Agent問題ほど発生頻度は高くないものの、著名な学者（ベイズなど）の画像生成に影響するため、優先的に対応すべき課題

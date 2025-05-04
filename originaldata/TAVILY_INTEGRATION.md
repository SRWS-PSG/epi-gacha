# Tavily API 連携ガイド

Epi-Gachaプロジェクトにおける学者データの充実化のために、Tavily APIとの連携を実装しました。このドキュメントでは、連携の概要と使用方法について説明します。

## 1. 概要

Tavily APIは高性能な検索エンジンを提供するAPIサービスで、以下の機能があります：

- **検索機能**: 特定のクエリで関連性の高いウェブコンテンツを検索
- **抽出機能**: 特定のURLからコンテンツを抽出
- **AI要約**: 検索結果のAI要約を生成

このプロジェクトでは、上記の機能を利用して学者データの貢献情報や豆知識を自動的に充実させることが可能になります。

## 2. ファイル構成

Tavily API連携のための主要ファイル：

| ファイル | 説明 |
|---------|------|
| `tavily_api.py` | Tavily APIとの直接連携用モジュール |
| `use_mcp_tool.py` | MCPツールインターフェース（モック/実際のAPI切り替え機能付き） |
| `update_scholars_tavily.py` | 学者データ更新スクリプト |
| `test_tavily_api.py` | APIテスト用スクリプト |
| `.env.sample` | 環境変数設定サンプル |

## 3. セットアップ

### 1. Tavily APIキーの取得

1. [Tavily API公式サイト](https://tavily.com/)にアクセスし、APIキーを取得
2. 取得したAPIキーを環境変数またはconfigファイルに設定

### 2. 環境変数の設定

`.env.sample`ファイルを`.env`にコピーし、必要な情報を入力：

```
# Tavily API設定
TAVILY_API_KEY=your_api_key_here

# モック設定（本番環境では削除または'false'に設定）
# USE_MOCK_TAVILY=true

# OpenAI API設定（データ抽出用）
OPENAI_API_KEY=your_openai_api_key_here
```

## 4. 基本的な使い方

### APIテスト

APIの接続をテストするには、以下のコマンドを実行します：

```bash
# テスト実行（直接API＋MCPインターフェースの両方）
python test_tavily_api.py

# モードを指定してテスト
python test_tavily_api.py --mode direct  # 直接APIのみ
python test_tavily_api.py --mode mcp     # MCPインターフェースのみ

# サンプル環境変数ファイルを保存
python test_tavily_api.py --save-env
```

### 学者データの更新

```bash
# 空データを持つ学者情報の更新
python update_empty_scholar_data.py

# 単一の学者データをテスト更新
python update_single_scholar.py
```

## 5. モックモードと実際のAPI

Tavily APIキーがない場合や、開発中のテストには、モックモードを使用できます：

### モックモードの有効化

次のいずれかの方法でモックモードを有効化：

1. 環境変数で設定：
```
USE_MOCK_TAVILY=true
```

2. スクリプト内で環境変数を設定：
```python
import os
os.environ["USE_MOCK_TAVILY"] = "true"
```

### APIキーを使用した実際のAPI呼び出し

実際のAPIを使用するには：

1. 環境変数にAPIキーを設定：
```
TAVILY_API_KEY=your_api_key_here
```

2. モックモード環境変数が設定されていないことを確認
3. `python update_empty_scholar_data.py`などのスクリプトを実行

## 6. 注意点とベストプラクティス

1. **APIキーの管理**: APIキーを公開リポジトリにコミットしないよう注意
2. **レート制限**: Tavily APIにはレート制限があります。`tavily_api.py`には自動リトライ機能がありますが、大量のリクエストは避けてください
3. **データの検証**: API経由で取得したデータは、`card_browser.html`などを使用して人間による確認を行うことをおすすめします
4. **モックモードの活用**: 開発時はモックモードを使用することで、APIコストを抑えることができます

## 7. トラブルシューティング

### APIキー関連のエラー

```
警告: TAVILY_API_KEYが設定されていません。
```

対処法: `.env`ファイルに正しいAPIキーを設定してください。

### モジュールインポートエラー

```
エラー: tavily_apiモジュールをインポートできません。
```

対処法: `tavily_api.py`が正しいパスにあることを確認してください。

### リクエスト関連のエラー

```
Tavily API エラー: 429 - {"error":"rate_limit_exceeded"}
```

対処法: リクエストの頻度を下げるか、しばらく待ってから再試行してください。

## 8. 将来の拡張

1. **データスキーマ検証**: 取得したデータの形式を検証する機能の追加
2. **並列処理**: 大量のデータ処理のための並列処理機能
3. **キャッシュ機能**: 同一リクエストのキャッシュによるAPI呼び出し回数の削減

---

このドキュメントは、Tavily API連携の基本的な使用方法と設定方法を説明しています。詳細な情報やカスタム実装については、コードを直接参照するか、プロジェクト管理者にお問い合わせください。

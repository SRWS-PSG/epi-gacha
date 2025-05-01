# Epi-Gacha プロジェクト開発計画と進捗状況

このドキュメントは、統計・公衆衛生学者ガチャプロジェクトの開発計画と進捗管理を行うためのものです。

## プロジェクト概要

「Epi-Gacha」は、統計学者・公衆衛生学者の情報をガチャ形式で提供するウェブアプリケーションです。ユーザーは「ガチャ」ボタンをクリックして、ランダムに選ばれた学者の情報カードを閲覧できます。シンプルなインターフェースと静的ファイル構成により、運用コストをほぼゼロに抑えています。

## システム構成

```mermaid
flowchart TD
    subgraph GitHub["GitHub Repository"]
        JSON[("scholars.json<br>学者データ")]
        IMG[("avatars/*.png<br>画像")]
        HTML["index.html<br>フロントエンド"]
        CSS["style.css"]
        JS["gacha.js"]
    end
    
    subgraph Manual["手動メンテナンス"]
        Data["学者データ追加"]
        Scripts["画像生成スクリプト<br>実行（必要時）"]
        Custom["カスタム画像<br>（オプション）"]
    end
    
    subgraph Pages["GitHub Pages"]
        Static["静的サイト"]
    end
    
    Data --> JSON
    Scripts --> IMG
    Custom --> IMG
    JSON --> Static
    IMG --> Static
    HTML --> Static
    CSS --> Static
    JS --> Static
    
    subgraph User["ユーザー"]
        Browser["ブラウザ"]
    end
    
    Static --> Browser
```

## 開発フェーズ

### フェーズ1：基本構造整備（完了）

- [x] GitHub リポジトリ作成
- [x] 基本ディレクトリ構造設定
- [x] scholars.json スキーマ設計と初期データ
- [x] README.md 作成

### フェーズ2：画像生成システム（強化済み）

- [x] OpenAI API利用の画像生成スクリプト作成
- [x] Google Gemini API利用の参照画像ベース画像生成スクリプト実装
- [x] 画像生成状態管理システム（missing/manual_added/generated）
- [x] Wikipediaからの参照画像自動取得機能
- [x] バッチ処理による一括画像生成の仕組み
- [x] 手動実行用GitHub Actionsワークフロー設定
- [x] 画像保存・管理の仕組み実装

### フェーズ3：フロントエンド（完了）

- [x] HTML/CSS基本構造
- [x] シンプルなガチャ機能JavaScriptの実装（1連ガチャのみ）
- [x] カード表示コンポーネント（レスポンシブデザイン）
- [x] レアリティ表示（N, R, SR, SSR）とアニメーション効果
- [x] フィルター機能の実装（専門分野別）
- [x] SSR演出エフェクト
- [x] カード表示の強化（貢献・豆知識セクション分割）
- [x] レアリティ表示の強化（フレーム、エフェクト、華やかな演出）
- [x] SR用の専用エフェクト追加

### フェーズ4：コンテンツ拡充（進行中）

- [x] データ構造の拡張（貢献情報と出典の追加）
- [ ] 追加学者データの収集と登録
- [ ] タグ・カテゴリーの整備
- [ ] トリビア情報の充実
- [x] 参考文献・出典の拡充

### フェーズ5：機能拡張（計画中）

- [ ] フィルター機能の強化（複数条件の組み合わせなど）
- [ ] 「お気に入り」保存機能（localStorage活用）
- [ ] 履歴表示機能
- [ ] モバイルUIのさらなる最適化
- [ ] PWA対応（オフライン利用）

## データ拡張計画

目標学者数：
- 初期リリース：10〜20名
- 第2弾：50名
- 最終：100名以上

優先収集カテゴリ：
1. 統計学の基礎を築いた人物
2. 疫学の主要研究者
3. 現代の公衆衛生学に影響を与えた人物
4. 日本の著名な統計・疫学者

## 画像生成システム

### 自動画像生成フロー

```mermaid
flowchart TD
    subgraph Input["入力"]
        J[("scholars_enhanced.json<br>学者データ")]
        RF[("reference_photos/<br>参照画像（オプション）")]
    end
    
    subgraph Process["処理"]
        B["バッチ処理スクリプト<br>gen_avatars_batch_gemini.py"]
        Check["参照画像の確認"]
        W["Wikipediaから<br>参照画像取得"]
        G["Gemini APIで<br>イラスト生成"]
        CSV["処理状態管理<br>missing_photos.csv"]
    end
    
    subgraph Output["出力"]
        A[("avatars/<br>生成画像")]
        JU[("更新された<br>scholars_enhanced.json")]
    end
    
    J --> B
    RF --> Check
    B --> Check
    Check -- "手動参照画像あり" --> G
    Check -- "参照画像なし" --> W
    W -- "取得成功" --> G
    W -- "取得失敗" --> CSV
    G -- "生成成功" --> A
    G -- "状態記録" --> CSV
    A --> JU
    
    style J fill:#f9f,stroke:#333,stroke-width:2px
    style RF fill:#bbf,stroke:#333,stroke-width:2px
    style A fill:#bfb,stroke:#333,stroke-width:2px
    style JU fill:#fbf,stroke:#333,stroke-width:2px
    style CSV fill:#fbb,stroke:#333,stroke-width:2px
```

### 画像生成状態管理

画像生成プロセスは以下の状態を管理します：

- **missing**: 参照画像が見つからず、手動での追加が必要
- **manual_added**: 手動で参照画像が追加済み
- **generated**: アバター生成に成功

これらの状態はmissing_photos.csvに記録され、バッチ処理時に参照されます。

### アバター生成統計

#### 2025年4月29日実行（Wikipediaからの画像取得）
- 総学者数: 57名
- アバター生成成功: 24名
- 画像取得失敗: 30名
- 処理エラー: 2名
- スキップ（既存画像）: 1名

#### 2025年5月1日実行（既存参照画像からの生成）
- 処理対象: 27名（参照画像はあるが生成画像がなかった学者）
- アバター生成成功: 27名（100%成功率）
- 処理エラー: 0名
- GIF形式の参照画像も正常に処理

### メンテナンスワークフロー（更新版）

```mermaid
sequenceDiagram
    participant M as メンテナー
    participant J as scholars_enhanced.json
    participant C as missing_photos.csv
    participant R as reference_photos/
    participant S as バッチ処理スクリプト
    participant A as avatars/
    participant G as GitHub
    
    M->>J: 1. 新規学者データ追加
    Note over M,C: 自動処理ルート
    M->>+S: 2. バッチ処理スクリプト実行
    S->>R: 3a. 参照画像の確認
    S->>A: 3b. アバター画像生成
    S->>C: 3c. 処理状態記録
    S->>-J: 4. avatarフィールド更新
    
    Note over M,R: 手動処理ルート
    M->>C: 5a. missing状態の学者を確認
    M->>R: 5b. 手動で参照画像追加
    M->>S: 5c. バッチ処理で再実行
    
    M->>G: 6. コミット & プッシュ
    G-->>G: 7. GitHub Pages自動デプロイ
```

代替フロー（手動画像追加）:
1. 学者データをscholars_enhanced.jsonに追加
2. 画像を別途用意し、avatars/{id}.png として保存
3. scholars_enhanced.jsonのavatarフィールドを手動更新
4. コミット & プッシュ

## コスト見積もり

| 項目 | 単価 | 想定回数 | 予算 |
|------|------|----------|------|
| 画像生成 API | $0.04/枚 | 初期:20枚<br>追加:10枚/月 | 初期:$0.8<br>月次:$0.4 |
| GitHub Pages | 無料 | - | $0 |
| ドメイン（オプション） | $10-15/年 | 年1回 | $10-15/年 |

## 担当者

- コンテンツ管理：
- 技術開発：
- デザイン：

## 実装済みの機能

- **ガチャ機能**: 「ガチャ」ボタンを押すとランダムに学者が1名表示される
- **カード表示**: 学者の情報（名前、所属、専門分野、貢献、豆知識など）をカード形式で表示
  - **貢献・豆知識の分離表示**: 名前の後に統計学や公衆衛生学への貢献と豆知識を2段構成で表示
  - **出典表示**: 各セクションに個別の出典リンクを表示
- **レアリティ表示**: N, R, SR, SSRの4段階のレアリティ表示とビジュアル効果
  - **カラーフレーム**: レア度に応じた色付きフレーム（SSRは金、SRは銀など）
  - **華やかな演出**: レア度に応じたエフェクト（SSRはキラキラパーティクル、「SSR GET!!」テキスト表示など）
  - **背景エフェクト**: 高レア度カードの背景効果
- **フィルター機能**: 専門分野でフィルタリングするオプション
- **アニメーション**: カードのスライドイン、SSR/SR時の特別エフェクト
- **レスポンシブデザイン**: モバイル端末を含む様々な画面サイズに対応

## 次のアクション項目

1. 画像生成システムの改善点
   - Wikipediaの画像取得時にUser-Agent制限回避のヘッダー設定追加
   - [x] GIF形式の参照画像の処理対応 → `gen_missing_avatars_from_existing_references.py`で実装済み
   - 画像取得失敗率の低減施策実装

2. 追加データとコンテンツ拡充
   - [x] 参照画像はあるが生成画像がない学者のアバター生成 → 27名全て処理完了
   - [x] 残りの画像がないスカラー（missing状態）への参照画像の手動追加
   - 学者データの追加収集と登録
   - タグ・カテゴリーの整備と統一

3. ウェブサイトと機能強化
   - GitHub Pagesでの公開設定
   - フィルター機能の強化（専門分野、時代、国別など）
   - ユーザーフィードバック収集と改善

4. その他の拡張
   - 音声効果の検討（レア度に応じたサウンド効果）
   - 「お気に入り」保存機能（localStorage活用）
   - PWA対応の検討（オフライン利用）

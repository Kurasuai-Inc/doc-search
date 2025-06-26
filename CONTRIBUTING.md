# doc-search 貢献ガイド

## 開発環境のセットアップ

### 1. リポジトリのクローン
```bash
git clone https://github.com/Kurasuai-Inc/doc-search.git
cd doc-search
```

### 2. 依存関係のインストール
```bash
# 基本インストール
uv pip install -e .

# 開発用ツールもインストール
uv pip install -e ".[dev]"

# セマンティック検索を使用する場合
uv pip install -e ".[semantic]"
```

### 3. 環境変数の設定
```bash
cp .env.example .env
# .envを編集して必要な設定を行う
```

### 4. 動作確認
```bash
# バージョン確認
python -m doc_search.cli --version

# 基本的な検索
python -m doc_search.cli

# インデックス構築
python -m doc_search.cli --index
```

## テストの実行

```bash
# すべてのテストを実行
pytest

# カバレッジ付きで実行
pytest --cov=doc_search
```

## コミットメッセージの規約

- feat: 新機能
- fix: バグ修正
- docs: ドキュメント変更
- test: テスト追加・修正
- refactor: リファクタリング

## 問題報告

GitHubのIssuesで報告してください。
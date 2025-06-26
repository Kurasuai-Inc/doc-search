# doc-search

ripgrep統合ドキュメント検索ツール - 検索の星座（StarFinder）

## 概要

ripgrepの高速性と高度な検索機能を組み合わせた、強力なドキュメント検索ツールです。

## 機能

- 🚀 高速全文検索（ripgrep統合）
- 🔍 正規表現サポート
- 📊 検索結果の視覚的表示
- ⚡ リアルタイムインクリメンタル検索
- 🎨 星座テーマのTUI
- 🔌 プラグインアーキテクチャ
- 💾 LRUキャッシュ機能
- 🔄 Pythonフォールバック

## インストール

```bash
# リポジトリのクローン
git clone https://github.com/Kurasuai-Inc/doc-search.git
cd doc-search

# 依存関係のインストール
uv pip install -e .

# ripgrepのインストール（推奨）
# macOS
brew install ripgrep
# Ubuntu/Debian
sudo apt-get install ripgrep
# Windows
choco install ripgrep
```

## 使い方

```bash
# 基本的な使い方
doc-search

# 特定のディレクトリを検索
doc-search --path ~/documents

# 正規表現を使用
doc-search --regex "TODO.*完了"

# ファイルタイプを指定
doc-search --type md --type py
```

## キーボードショートカット

| キー | 機能 |
|------|------|
| `/` | 検索フォーカス |
| `Ctrl+R` | 正規表現モード切替 |
| `Ctrl+T` | ファイルタイプフィルター |
| `Ctrl+H` | 検索履歴表示 |
| `q` | 終了 |

## アーキテクチャ

```
doc-search/
├── src/doc_search/
│   ├── core/           # 検索エンジンコア
│   │   ├── ripgrep_wrapper.py
│   │   └── errors.py
│   └── ui/             # TUIインターフェース
│       └── tui_main.py
├── tests/              # テスト
└── docs/               # ドキュメント
```

## チーム

- **ステラ** （プロジェクトリーダー）: コア設計とripgrep統合
- **セイラ** （UI/UXリード）: TUIデザインと可視化
- **ネビィ** （インフラ担当）: テストとCI/CD

## 開発状況

🌟 活発に開発中 - 統合フェーズ

## ライセンス

MIT
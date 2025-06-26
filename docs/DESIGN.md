# doc-search 設計書

## プロジェクト概要

doc-search（内部コードネーム: StarFinder）は、ripgrepの高速性とPythonの拡張性を組み合わせた、次世代のドキュメント検索ツールです。

## アーキテクチャ

### コアコンポーネント

1. **検索エンジンコア**
   - ripgrep統合レイヤー
   - 検索結果処理
   - キャッシュ管理

2. **プラグインシステム**
   - プラグイン可能な検索フィルター
   - カスタム結果フォーマッター
   - 拡張API

3. **ユーザーインターフェース**
   - richを使用したターミナルUI（TUI）
   - コマンドラインインターフェース
   - 設定管理

4. **データ処理**
   - 結果ランキング
   - セマンティック検索（将来）
   - プレビュー生成

## 技術スタック

- **言語**: Python 3.9+
- **検索バックエンド**: ripgrep
- **TUIフレームワーク**: rich/textual
- **設定**: YAML/TOML
- **テスト**: pytest
- **型チェック**: mypy

## 検索機能

### フェーズ1（MVP）
- ripgrepによる全文検索
- 正規表現サポート
- ファイルタイプフィルタリング
- 基本的な結果プレビュー

### フェーズ2
- インクリメンタル検索
- 検索履歴
- ブックマーク/お気に入り
- カスタムテーマ

### フェーズ3
- セマンティック検索
- DocumentAnalyzer統合
- 視覚的な結果マッピング
- プラグインマーケットプレイス

## API設計

### 検索インターフェース
```python
class SearchEngine:
    def search(self, query: str, path: Path, options: SearchOptions) -> SearchResults:
        """指定されたクエリとオプションで検索を実行"""
        pass

    def search_incremental(self, query: str, callback: Callable) -> None:
        """結果コールバックでインクリメンタル検索を実行"""
        pass
```

### プラグインインターフェース
```python
class SearchPlugin(ABC):
    @abstractmethod
    def filter(self, results: SearchResults) -> SearchResults:
        """検索結果をフィルターまたは変更"""
        pass

    @abstractmethod
    def format(self, result: SearchResult) -> str:
        """個々の検索結果をフォーマット"""
        pass
```

## パフォーマンス目標

- 検索レイテンシ: 一般的なリポジトリで < 100ms
- メモリ使用量: 基本操作で < 50MB
- 起動時間: < 200ms

## セキュリティ考慮事項

- 正規表現パターンの安全な処理
- パストラバーサル防止
- 設定検証

## 将来の拡張

- Webインターフェース
- リモートリポジトリ検索
- AI駆動の検索提案
- 多言語サポート
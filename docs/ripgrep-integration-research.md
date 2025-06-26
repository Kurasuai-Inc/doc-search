# ripgrep Python統合調査

## 調査概要

ripgrepをPythonから利用する方法について調査した結果をまとめます。

## 統合方法の選択肢

### 1. subprocess経由での実行（推奨）

```python
import subprocess
import json

def search_with_ripgrep(query: str, path: str):
    cmd = ['rg', '--json', query, path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    for line in result.stdout.splitlines():
        data = json.loads(line)
        if data['type'] == 'match':
            yield data
```

**メリット：**
- ripgrepの全機能が利用可能
- 最新バージョンの機能をすぐに使える
- メモリ効率が良い（ripgrepは別プロセス）

**デメリット：**
- ripgrepのインストールが必要
- プロセス起動のオーバーヘッド

### 2. Python-ripgrep バインディング

現在メンテナンスされているPythonバインディングは見つかりませんでした。

### 3. 代替案：pygrep

Pure Pythonの実装ですが、ripgrepほどの性能は期待できません。

## 推奨実装方針

1. **subprocess + JSON出力**を採用
2. ripgrepの存在チェック機能を実装
3. 非同期実行でパフォーマンス向上

## ripgrepの主要オプション

```bash
# JSON形式で出力（パース用）
rg --json "pattern" 

# ファイルタイプ指定
rg -t py "pattern"

# 正規表現無効化（リテラル検索）
rg -F "pattern"

# 大文字小文字無視
rg -i "pattern"

# コンテキスト行数指定
rg -C 3 "pattern"

# ファイル名のみ出力
rg -l "pattern"
```

## エラーハンドリング

```python
def check_ripgrep_installed():
    try:
        subprocess.run(['rg', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
```

## パフォーマンス考慮事項

1. 大規模リポジトリでは`--max-count`で結果数を制限
2. インクリメンタル検索では`--line-buffered`を使用
3. `.gitignore`の自動認識を活用

## 次のステップ

1. 基本的なripgrepラッパークラスの実装
2. 非同期実行のサポート
3. 結果のキャッシング機構
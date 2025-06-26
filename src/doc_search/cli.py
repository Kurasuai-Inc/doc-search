"""
doc-search コマンドラインインターフェース
"""
import click
import asyncio
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv

from .ui.tui_main import DocSearchApp
from .core.ripgrep_wrapper import RipgrepWrapper


# .envファイルを読み込み
load_dotenv()


@click.command()
@click.option('--path', '-p', type=click.Path(exists=True), help='検索対象のパス')
@click.option('--regex', '-r', is_flag=True, help='正規表現モードを有効化')
@click.option('--type', '-t', multiple=True, help='ファイルタイプ指定（例: py, md）')
@click.option('--index', is_flag=True, help='セマンティック検索用のインデックスを構築')
@click.option('--version', '-v', is_flag=True, help='バージョンを表示')
def main(path: Optional[str], regex: bool, type: tuple, index: bool, version: bool):
    """doc-search - 高速ドキュメント検索ツール"""
    if version:
        from . import __version__
        click.echo(f"doc-search version {__version__}")
        return
    
    # 検索パスの設定
    search_path = Path(path) if path else Path.cwd()
    
    # インデックス構築モード
    if index:
        click.echo("🌟 セマンティック検索用のインデックスを構築します...")
        from .core.semantic_search import SemanticSearchEngine
        
        # OpenAI使用判定
        use_openai = os.getenv("USE_OPENAI_EMBEDDINGS", "false").lower() == "true"
        
        engine = SemanticSearchEngine(use_openai=use_openai)
        
        # ドキュメントを収集
        documents = []
        for pattern in ['**/*.md', '**/*.py', '**/*.txt']:
            for file_path in search_path.glob(pattern):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    documents.append((str(file_path), content))
                except Exception:
                    pass
        
        click.echo(f"📄 {len(documents)}個のドキュメントを発見")
        
        # インデックス構築
        engine.build_index(documents)
        click.echo("✅ インデックス構築完了！")
        return
    
    # TUIアプリケーションの起動
    app = DocSearchApp(
        search_path=search_path,
        use_regex=regex,
        file_types=list(type) if type else None
    )
    app.run()


if __name__ == '__main__':
    main()
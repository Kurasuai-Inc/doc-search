"""
doc-search コマンドラインインターフェース
"""
import click
import asyncio
from pathlib import Path
from typing import Optional

from .ui.tui_main import DocSearchApp
from .core.ripgrep_wrapper import RipgrepWrapper


@click.command()
@click.option('--path', '-p', type=click.Path(exists=True), help='検索対象のパス')
@click.option('--regex', '-r', is_flag=True, help='正規表現モードを有効化')
@click.option('--type', '-t', multiple=True, help='ファイルタイプ指定（例: py, md）')
@click.option('--version', '-v', is_flag=True, help='バージョンを表示')
def main(path: Optional[str], regex: bool, type: tuple, version: bool):
    """doc-search - 高速ドキュメント検索ツール"""
    if version:
        from . import __version__
        click.echo(f"doc-search version {__version__}")
        return
    
    # 検索パスの設定
    search_path = Path(path) if path else Path.cwd()
    
    # TUIアプリケーションの起動
    app = DocSearchApp(
        search_path=search_path,
        use_regex=regex,
        file_types=list(type) if type else None
    )
    app.run()


if __name__ == '__main__':
    main()
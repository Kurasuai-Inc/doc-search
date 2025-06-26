"""
TUIとripgrep統合モジュール
"""
from pathlib import Path
from typing import List, Optional
import asyncio

from ..core.ripgrep_wrapper import RipgrepWrapper, SearchOptions, SearchResult
from .tui_main import SearchResult as UISearchResult, SearchResultsContainer


class SearchIntegration:
    """検索エンジンとUIの統合"""
    
    def __init__(self, search_path: Path = None):
        self.search_path = search_path or Path.cwd()
        self.ripgrep = RipgrepWrapper(fallback_to_python=True)
        
    async def perform_search(
        self, 
        query: str, 
        use_regex: bool = True,
        file_types: Optional[List[str]] = None,
        max_results: int = 100
    ) -> List[UISearchResult]:
        """非同期で検索を実行してUI用の結果を返す"""
        if not query:
            return []
            
        # 検索オプションの設定
        options = SearchOptions(
            use_regex=use_regex,
            file_types=file_types,
            max_results=max_results,
            case_sensitive=False,  # デフォルトは大文字小文字無視
            context_lines=2  # 前後2行のコンテキスト
        )
        
        # 検索実行（別スレッドで）
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            self._search_sync,
            query,
            self.search_path,
            options
        )
        
        # UI用の結果に変換
        ui_results = []
        for result in results:
            # スコアを計算（仮実装）
            score = self._calculate_score(result, query)
            
            ui_result = UISearchResult(
                file_path=result.file_path,
                line_number=result.line_number,
                content=result.line_content,
                score=score
            )
            ui_results.append(ui_result)
            
        return ui_results
        
    def _search_sync(self, query: str, path: Path, options: SearchOptions) -> List[SearchResult]:
        """同期的に検索を実行"""
        results = []
        try:
            for result in self.ripgrep.search(query, path, options):
                results.append(result)
        except Exception as e:
            # エラーハンドリング
            from ..core.errors import ErrorHandler
            error_msg = ErrorHandler.handle_search_error(e)
            # TODO: エラーメッセージをUIに表示
            
        return results
        
    def _calculate_score(self, result: SearchResult, query: str) -> int:
        """検索結果のスコアを計算（1-5の星）"""
        # 簡易的なスコア計算
        line_lower = result.line_content.lower()
        query_lower = query.lower()
        
        # 完全一致
        if query_lower in line_lower:
            # ファイル名も考慮
            if 'readme' in result.file_path.lower():
                return 5
            elif any(ext in result.file_path for ext in ['.md', '.rst', '.txt']):
                return 4
            else:
                return 3
        else:
            # 部分一致
            return 2
            
    def update_search_path(self, path: Path):
        """検索パスを更新"""
        self.search_path = path
"""
TUIとripgrep統合モジュール
"""
from pathlib import Path
from typing import List, Optional
import asyncio

from ..core.ripgrep_wrapper import RipgrepWrapper, SearchOptions, SearchResult
from ..core.semantic_search import SemanticSearchEngine, SemanticSearchResult
from .tui_main import SearchResult as UISearchResult, SearchResultsContainer


class SearchIntegration:
    """検索エンジンとUIの統合"""
    
    def __init__(self, search_path: Path = None, enable_semantic: bool = True):
        self.search_path = search_path or Path.cwd()
        self.ripgrep = RipgrepWrapper(fallback_to_python=True)
        self.enable_semantic = enable_semantic
        
        # セマンティック検索エンジン（遅延初期化）
        self._semantic_engine: Optional[SemanticSearchEngine] = None
        self._semantic_available = self._check_semantic_available()
        
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
            # スコアを計算
            score = self._calculate_score(result, query)
            
            ui_result = UISearchResult(
                file_path=result.file_path,
                line_number=result.line_number,
                content=result.line_content,
                score=score
            )
            ui_results.append(ui_result)
            
        # セマンティック検索が有効な場合
        if self.enable_semantic and self._semantic_available:
            semantic_results = await self._perform_semantic_search(query)
            ui_results.extend(semantic_results)
            
        # スコアでソート
        ui_results.sort(key=lambda x: x.score, reverse=True)
            
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
        
    def _check_semantic_available(self) -> bool:
        """セマンティック検索が利用可能かチェック"""
        try:
            import sentence_transformers
            return True
        except ImportError:
            import logging
            logging.warning("sentence-transformersが見つかりません。セマンティック検索は無効です。")
            return False
            
    async def _perform_semantic_search(self, query: str) -> List[UISearchResult]:
        """セマンティック検索を実行"""
        if self._semantic_engine is None:
            self._semantic_engine = SemanticSearchEngine()
            # インデックス構築（初回のみ）
            await self._build_semantic_index()
            
        # セマンティック検索実行
        semantic_results = self._semantic_engine.search(query, top_k=5)
        
        # UI用に変換
        ui_results = []
        for result in semantic_results:
            ui_result = UISearchResult(
                file_path=result.file_path,
                line_number=0,  # セマンティック検索では行番号なし
                content=f"[Semantic] {result.content[:100]}...",
                score=int(result.similarity_score * 5)  # 0-1を1-5に変換
            )
            ui_results.append(ui_result)
            
        return ui_results
        
    async def _build_semantic_index(self):
        """セマンティック検索用のインデックスを構築"""
        documents = []
        
        # MarkdownとPythonファイルを収集
        for pattern in ['**/*.md', '**/*.py', '**/*.txt']:
            for file_path in self.search_path.glob(pattern):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    documents.append((str(file_path), content))
                except Exception:
                    pass
                    
        # インデックス構築（非同期実行）
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._semantic_engine.build_index,
            documents
        )
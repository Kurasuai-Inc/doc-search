"""
ripgrep ラッパー - 高速検索エンジンとの統合
"""
import json
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Iterator, Union
from dataclasses import dataclass
from functools import lru_cache
import re
import logging

from .errors import SearchError, RipgrepNotFoundError, retry

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """検索結果を表すデータクラス"""
    file_path: str
    line_number: int
    line_content: str
    match_start: int
    match_end: int
    
    
@dataclass
class SearchOptions:
    """検索オプション"""
    case_sensitive: bool = True
    use_regex: bool = True
    file_types: Optional[List[str]] = None
    max_results: Optional[int] = None
    context_lines: int = 0


class RipgrepWrapper:
    """ripgrepの機能をラップするクラス"""
    
    def __init__(self, fallback_to_python: bool = True):
        """
        Args:
            fallback_to_python: ripgrepが利用できない場合にPythonフォールバックを使用
        """
        self.fallback_to_python = fallback_to_python
        self._ripgrep_available = self._check_ripgrep()
        
    @staticmethod
    @lru_cache(maxsize=1)
    def _check_ripgrep() -> bool:
        """ripgrepがインストールされているか確認"""
        return shutil.which('rg') is not None
        
    def search(
        self, 
        query: str, 
        path: Union[str, Path], 
        options: Optional[SearchOptions] = None
    ) -> Iterator[SearchResult]:
        """
        指定されたパスで検索を実行
        
        Args:
            query: 検索クエリ
            path: 検索対象のパス
            options: 検索オプション
            
        Yields:
            SearchResult: 検索結果
        """
        if options is None:
            options = SearchOptions()
            
        path = Path(path)
        
        if self._ripgrep_available:
            yield from self._search_with_ripgrep(query, path, options)
        elif self.fallback_to_python:
            logger.warning("ripgrepが見つかりません。Pythonフォールバックを使用します。")
            yield from self._search_with_python(query, path, options)
        else:
            raise RuntimeError("ripgrepが利用できません")
            
    @retry(max_attempts=3, delay=0.5, exceptions=(subprocess.SubprocessError,))
    def _search_with_ripgrep(
        self, 
        query: str, 
        path: Path, 
        options: SearchOptions
    ) -> Iterator[SearchResult]:
        """ripgrepを使用して検索（リトライ機能付き）"""
        cmd = ['rg', '--json']
        
        # オプションの設定
        if not options.case_sensitive:
            cmd.append('-i')
        if not options.use_regex:
            cmd.append('-F')
        if options.max_results:
            cmd.extend(['--max-count', str(options.max_results)])
        if options.context_lines > 0:
            cmd.extend(['-C', str(options.context_lines)])
        if options.file_types:
            for file_type in options.file_types:
                cmd.extend(['-t', file_type])
                
        cmd.extend([query, str(path)])
        
        try:
            # ripgrepを実行
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # 結果を1行ずつ処理
            for line in process.stdout:
                try:
                    data = json.loads(line.strip())
                    if data.get('type') == 'match':
                        match_data = data['data']
                        for submatch in match_data.get('submatches', []):
                            yield SearchResult(
                                file_path=match_data['path']['text'],
                                line_number=match_data['line_number'],
                                line_content=match_data['lines']['text'].rstrip('\n'),
                                match_start=submatch['start'],
                                match_end=submatch['end']
                            )
                except json.JSONDecodeError:
                    logger.warning(f"JSONパースエラー: {line}")
                    
            process.wait()
            
        except subprocess.SubprocessError as e:
            logger.error(f"ripgrep実行エラー: {e}")
            if self.fallback_to_python:
                yield from self._search_with_python(query, path, options)
            else:
                raise
                
    def _search_with_python(
        self, 
        query: str, 
        path: Path, 
        options: SearchOptions
    ) -> Iterator[SearchResult]:
        """Pythonのみを使用したフォールバック検索"""
        # 正規表現パターンの準備
        if options.use_regex:
            flags = 0 if options.case_sensitive else re.IGNORECASE
            pattern = re.compile(query, flags)
        else:
            # リテラル検索の場合
            query_lower = query if options.case_sensitive else query.lower()
        
        # ファイルパターンの準備
        file_patterns = ['*.md', '*.py', '*.txt'] if not options.file_types else [
            f'*.{ft}' for ft in options.file_types
        ]
        
        result_count = 0
        
        # ファイルを再帰的に検索
        for pattern in file_patterns:
            for file_path in path.rglob(pattern):
                if result_count >= (options.max_results or float('inf')):
                    return
                    
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if options.use_regex:
                                matches = list(pattern.finditer(line))
                                for match in matches:
                                    yield SearchResult(
                                        file_path=str(file_path),
                                        line_number=line_num,
                                        line_content=line.rstrip('\n'),
                                        match_start=match.start(),
                                        match_end=match.end()
                                    )
                                    result_count += 1
                            else:
                                # リテラル検索
                                search_line = line if options.case_sensitive else line.lower()
                                start = 0
                                while True:
                                    pos = search_line.find(query_lower, start)
                                    if pos == -1:
                                        break
                                    yield SearchResult(
                                        file_path=str(file_path),
                                        line_number=line_num,
                                        line_content=line.rstrip('\n'),
                                        match_start=pos,
                                        match_end=pos + len(query)
                                    )
                                    result_count += 1
                                    start = pos + 1
                                    
                except (IOError, OSError) as e:
                    logger.warning(f"ファイル読み込みエラー: {file_path} - {e}")
                    
    def is_available(self) -> bool:
        """ripgrepが利用可能かどうか"""
        return self._ripgrep_available
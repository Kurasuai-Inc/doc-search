"""
基本的な動作テスト
"""
import pytest
from pathlib import Path

from doc_search.core.ripgrep_wrapper import RipgrepWrapper, SearchOptions


def test_ripgrep_wrapper_initialization():
    """RipgrepWrapperの初期化テスト"""
    wrapper = RipgrepWrapper()
    assert wrapper is not None
    assert wrapper.fallback_to_python is True


def test_search_options_defaults():
    """SearchOptionsのデフォルト値テスト"""
    options = SearchOptions()
    assert options.case_sensitive is True
    assert options.use_regex is True
    assert options.file_types is None
    assert options.max_results is None
    assert options.context_lines == 0


def test_python_fallback_search(tmp_path):
    """Pythonフォールバック検索のテスト"""
    # テストファイルを作成
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test Document\nThis is a test file.\nSearch for keywords here.")
    
    wrapper = RipgrepWrapper(fallback_to_python=True)
    options = SearchOptions(use_regex=False, case_sensitive=False)
    
    results = list(wrapper._search_with_python("test", tmp_path, options))
    
    assert len(results) > 0
    assert any("test" in r.line_content.lower() for r in results)
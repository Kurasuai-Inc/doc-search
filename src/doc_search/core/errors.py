"""
エラーハンドリングとリトライ機構
"""
import time
import logging
from typing import Callable, TypeVar, Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SearchError(Exception):
    """検索関連の基本エラー"""
    pass


class RipgrepNotFoundError(SearchError):
    """ripgrepが見つからない場合のエラー"""
    pass


class SearchTimeoutError(SearchError):
    """検索タイムアウトエラー"""
    pass


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    リトライデコレータ
    
    Args:
        max_attempts: 最大試行回数
        delay: 初回リトライまでの待機時間（秒）
        backoff: リトライごとの待機時間倍率
        exceptions: リトライ対象の例外タプル
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__}が{max_attempts}回失敗しました: {e}")
                        raise
                    
                    logger.warning(
                        f"{func.__name__}が失敗しました（試行{attempt}/{max_attempts}）: {e}"
                        f" {current_delay}秒後にリトライします..."
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
                    
            # ここには到達しないはず
            raise RuntimeError("予期しないエラー: リトライループを抜けました")
            
        return wrapper
    return decorator


class ErrorHandler:
    """エラーハンドリングのユーティリティクラス"""
    
    @staticmethod
    def handle_search_error(error: Exception, fallback_message: str = "") -> str:
        """
        検索エラーをユーザーフレンドリーなメッセージに変換
        
        Args:
            error: 発生したエラー
            fallback_message: デフォルトメッセージ
            
        Returns:
            ユーザー向けエラーメッセージ
        """
        if isinstance(error, RipgrepNotFoundError):
            return "⚠️ ripgrepが見つかりません。Pythonフォールバックモードで検索します。"
        elif isinstance(error, SearchTimeoutError):
            return "⏱️ 検索がタイムアウトしました。検索範囲を絞って再試行してください。"
        elif isinstance(error, PermissionError):
            return "🔒 一部のファイルにアクセス権限がありません。アクセス可能な範囲で検索します。"
        elif isinstance(error, OSError):
            return f"💾 システムエラーが発生しました: {str(error)}"
        else:
            return fallback_message or f"❌ エラーが発生しました: {str(error)}"
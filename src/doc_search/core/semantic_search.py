"""
セマンティック検索エンジン
"""
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pickle
import hashlib
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SemanticSearchResult:
    """セマンティック検索結果"""
    file_path: str
    content: str
    similarity_score: float
    chunk_index: int


class SemanticSearchEngine:
    """セマンティック検索を実行するエンジン"""
    
    def __init__(self, cache_dir: Optional[Path] = None, use_openai: bool = False):
        """
        Args:
            cache_dir: 埋め込みベクトルのキャッシュディレクトリ
            use_openai: OpenAI Embeddingsを使用するか
        """
        self.cache_dir = cache_dir or Path(".doc_search_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.use_openai = use_openai
        
        # 埋め込みモデル（遅延初期化）
        self._model = None
        self._openai_client = None
        self._embeddings_cache: Dict[str, np.ndarray] = {}
        
        # 環境変数から設定読み込み
        import os
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        
    @property
    def model(self):
        """埋め込みモデルの遅延初期化"""
        if self.use_openai and self.openai_api_key:
            if self._openai_client is None:
                try:
                    import openai
                    self._openai_client = openai.OpenAI(api_key=self.openai_api_key)
                    logger.info(f"OpenAI Embeddings ({self.embedding_model}) を使用します")
                except ImportError:
                    logger.error("openaiがインストールされていません")
                    raise ImportError(
                        "OpenAI Embeddingsを使用するには openai をインストールしてください: "
                        "uv pip install openai"
                    )
            return self._openai_client
        else:
            if self._model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    # 日本語対応の軽量モデル
                    self._model = SentenceTransformer('all-MiniLM-L6-v2')
                    logger.info("ローカルセマンティック検索モデルを読み込みました")
                except ImportError:
                    logger.error("sentence-transformersがインストールされていません")
                    raise ImportError(
                        "セマンティック検索を使用するには sentence-transformers をインストールしてください: "
                        "uv pip install sentence-transformers"
                    )
            return self._model
        
    def build_index(self, documents: List[Tuple[str, str]]) -> None:
        """
        ドキュメントのインデックスを構築
        
        Args:
            documents: (file_path, content) のタプルのリスト
        """
        logger.info(f"{len(documents)}個のドキュメントをインデックス化します")
        
        for file_path, content in documents:
            # ドキュメントをチャンクに分割
            chunks = self._split_into_chunks(content)
            
            # 各チャンクの埋め込みを生成
            for i, chunk in enumerate(chunks):
                cache_key = self._get_cache_key(file_path, i, chunk)
                
                # キャッシュチェック
                cached_embedding = self._load_cached_embedding(cache_key)
                if cached_embedding is not None:
                    self._embeddings_cache[cache_key] = cached_embedding
                else:
                    # 新規生成
                    embedding = self._generate_embedding(chunk)
                    self._embeddings_cache[cache_key] = embedding
                    self._save_cached_embedding(cache_key, embedding)
                    
    def search(
        self, 
        query: str, 
        top_k: int = 10,
        similarity_threshold: float = 0.5
    ) -> List[SemanticSearchResult]:
        """
        セマンティック検索を実行
        
        Args:
            query: 検索クエリ
            top_k: 返す結果の最大数
            similarity_threshold: 類似度の閾値
            
        Returns:
            検索結果のリスト
        """
        if not self._embeddings_cache:
            logger.warning("インデックスが構築されていません")
            return []
            
        # クエリの埋め込みを生成
        query_embedding = self._generate_embedding(query)
        
        # 全ての埋め込みとの類似度を計算
        similarities = []
        for cache_key, doc_embedding in self._embeddings_cache.items():
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            if similarity >= similarity_threshold:
                similarities.append((cache_key, similarity))
                
        # スコアでソート
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 結果を構築
        results = []
        for cache_key, similarity in similarities[:top_k]:
            # cache_keyから情報を復元
            file_path, chunk_index, content = self._parse_cache_key(cache_key)
            results.append(SemanticSearchResult(
                file_path=file_path,
                content=content,
                similarity_score=similarity,
                chunk_index=chunk_index
            ))
            
        return results
        
    def _split_into_chunks(self, content: str, chunk_size: int = 500) -> List[str]:
        """テキストをチャンクに分割"""
        # 簡易的な実装：改行で分割してから結合
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line)
            if current_size + line_size > chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
                
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
            
        return chunks
        
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """コサイン類似度を計算"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
        
    def _get_cache_key(self, file_path: str, chunk_index: int, content: str) -> str:
        """キャッシュキーを生成"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{file_path}:{chunk_index}:{content_hash}"
        
    def _parse_cache_key(self, cache_key: str) -> Tuple[str, int, str]:
        """キャッシュキーから情報を復元（簡易実装）"""
        parts = cache_key.split(':')
        file_path = parts[0]
        chunk_index = int(parts[1])
        # contentは実際のファイルから取得する必要がある
        content = f"[Chunk {chunk_index} from {file_path}]"
        return file_path, chunk_index, content
        
    def _load_cached_embedding(self, cache_key: str) -> Optional[np.ndarray]:
        """キャッシュから埋め込みを読み込み"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"キャッシュ読み込みエラー: {e}")
        return None
        
    def _save_cached_embedding(self, cache_key: str, embedding: np.ndarray) -> None:
        """埋め込みをキャッシュに保存"""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            # キャッシュディレクトリが存在しない場合は作成
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            logger.warning(f"キャッシュ保存エラー: {e}")
            
    def _generate_embedding(self, text: str) -> np.ndarray:
        """テキストの埋め込みベクトルを生成"""
        if self.use_openai and self.openai_api_key:
            # OpenAI Embeddings
            try:
                response = self.model.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )
                embedding = np.array(response.data[0].embedding)
                return embedding
            except Exception as e:
                logger.error(f"OpenAI Embeddings エラー: {e}")
                # フォールバックとしてローカルモデルを使用
                if not hasattr(self, '_fallback_model'):
                    from sentence_transformers import SentenceTransformer
                    self._fallback_model = SentenceTransformer('all-MiniLM-L6-v2')
                return self._fallback_model.encode(text)
        else:
            # ローカルモデル
            return self.model.encode(text)
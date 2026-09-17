"""向量数据库封装（第 26 节，复刻 zhiqida-rag/core/vectorstores.py 并增强稳定性）。

基于 ChromaDB PersistentClient（数据持久化到本地磁盘，HNSW + cosine 距离）。
与 zhiqida-rag 的两点差异：
1. ID 生成改用 **md5(content)** 稳定哈希 —— zhiqida 用内置 hash()，其字符串哈希
   每次进程启动随机加盐，重启后相同内容会生成不同 ID，导致重复入库/无法幂等重建；
2. 数据目录（persist_dir）由上层 store.py 显式传入，不依赖 zhiqida 的 settings。
"""
import hashlib
import os
from typing import List, Optional, Tuple

from rag.embeddings import Embeddings
from rag.loaders import Document


class ChromaVectorStore:
    """ChromaDB 向量库实现：add_documents / similarity_search / delete / count。"""

    def __init__(self, embeddings: Embeddings, persist_dir: str,
                 collection_name: str = "rag_collection"):
        self.embeddings = embeddings
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    def _lazy_init(self):
        """延迟初始化 ChromaDB 客户端与集合（cosine 距离）。"""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings as ChromaSettings
            except ImportError as exc:  # pragma: no cover - 依赖缺失场景
                raise ImportError("chromadb 未安装，请执行: pip install chromadb") from exc
            os.makedirs(self.persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    def _doc_id(self, content: str) -> str:
        """稳定 ID：对文本内容做 md5（跨进程一致，天然去重 + 支持幂等重建）。"""
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def add_documents(self, documents: List[Document],
                      embeddings: Optional[List[List[float]]] = None) -> List[str]:
        """添加文档：生成稳定 ID → 自动嵌入 → 过滤已存在 → 批量 upsert。

        :return: 实际新增的 doc id 列表
        """
        self._lazy_init()
        if embeddings is None:
            embeddings = self.embeddings.embed_documents([d.page_content for d in documents])

        ids, texts, metadatas = [], [], []
        for i, doc in enumerate(documents):
            ids.append(self._doc_id(doc.page_content))
            texts.append(doc.page_content)
            metadatas.append(doc.metadata)

        # 去重：跳过已存在的 ID（幂等，重复上传不产生垃圾块）
        existing = set(self._collection.get(ids=ids).get("ids", []))
        new_ids, new_emb, new_text, new_meta = [], [], [], []
        for i, doc_id in enumerate(ids):
            if doc_id in existing:
                continue
            new_ids.append(doc_id)
            new_emb.append(embeddings[i])
            new_text.append(texts[i])
            new_meta.append(metadatas[i])
        if new_ids:
            self._collection.upsert(
                ids=new_ids,
                embeddings=new_emb,
                documents=new_text,
                metadatas=new_meta,
            )
        return new_ids

    def similarity_search(self, query_embedding: List[float], k: int = 10,
                          where: Optional[dict] = None) -> List[Tuple[Document, float]]:
        """相似度检索：返回 (Document, similarity) 列表（cosine 距离 → 相似度）。"""
        self._lazy_init()
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        docs = []
        hit_ids = results.get("ids") and results["ids"][0] or []
        for i in range(len(hit_ids)):
            doc = Document(
                page_content=results["documents"][0][i],
                metadata=results["metadatas"][0][i],
            )
            docs.append((doc, 1 - results["distances"][0][i]))
        return docs

    def get_documents(self, where: Optional[dict] = None) -> List[dict]:
        """读取集合内全部记录（含 metadata），供文档列表 / 统计使用。"""
        self._lazy_init()
        if self._collection.count() == 0:
            return []
        result = self._collection.get(where=where, include=["metadatas", "documents"])
        items = []
        ids = result.get("ids") or []
        for i in range(len(ids)):
            items.append({
                "id": ids[i],
                "content": result["documents"][i],
                "metadata": result["metadatas"][i],
            })
        return items

    def delete_by_ids(self, ids: List[str]) -> None:
        """按 doc id 删除记录。"""
        self._lazy_init()
        if ids:
            self._collection.delete(ids=ids)

    def count(self, where: Optional[dict] = None) -> int:
        """集合文档总数（可带 where 过滤）。"""
        self._lazy_init()
        if where:
            return len(self._collection.get(where=where).get("ids", []))
        return self._collection.count()

    def delete_collection(self) -> None:
        """删除整个集合（重建索引时使用）。"""
        self._lazy_init()
        self._client.delete_collection(self.collection_name)
        self._collection = None

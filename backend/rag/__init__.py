"""RAG 知识库封装（第 26 节）。

实现尽可能复用同级课程项目 `zhiqida-rag`（core/loaders、core/chunkers、
core/embeddings、core/vectorstores）的设计与代码，仅做两处适配：
1. 配置读取：从 SmartBrief 自己的 `backend/.env`（EMBEDDING_* 前缀）读取，
   不与 zhiqida-rag 的 `ZHIQIDA_` 前缀耦合；
2. 数据目录：模板/术语/持久化目录收敛到 `backend/data/` 下。
"""
from rag.embeddings import Embeddings, SiliconFlowEmbeddings, create_embeddings
from rag.loaders import Document, DocumentLoader, load_document
from rag.chunkers import BaseChunker, RecursiveChunker
from rag.vectorstores import ChromaVectorStore

__all__ = [
    "Embeddings",
    "SiliconFlowEmbeddings",
    "create_embeddings",
    "Document",
    "DocumentLoader",
    "load_document",
    "BaseChunker",
    "RecursiveChunker",
    "ChromaVectorStore",
]

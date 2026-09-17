"""嵌入模型封装（第 26 节，复刻 zhiqida-rag/core/embeddings.py 并适配 SmartBrief 配置）。

与 zhiqida-rag 的差异只有配置来源：这里从 SmartBrief 自己的 `backend/.env`
读取 `EMBEDDING_BASE_URL / EMBEDDING_API_KEY / EMBEDDING_MODEL`（SiliconFlow
兼容 OpenAI Embeddings 格式），避免依赖 zhiqida-rag 的 `ZHIQIDA_` 前缀配置。

延迟初始化（Lazy Init）：__init__ 只保存配置，首次调用时才创建 HTTP 客户端。
"""
import os
from typing import List, Optional

from dotenv import load_dotenv

# 确保 backend/.env 已加载（重复调用无副作用）
load_dotenv()


class Embeddings:
    """嵌入模型抽象基类：定义 embed_documents / embed_query 统一接口。"""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError


class SiliconFlowEmbeddings(Embeddings):
    """硅基流动 API 嵌入模型实现（兼容 OpenAI Embeddings 接口）。

    支持模型：BAAI/bge-m3（默认，1024 维，中文优化）等。
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 model: Optional[str] = None):
        self.api_key = api_key or os.getenv("EMBEDDING_API_KEY", "")
        self.base_url = base_url or os.getenv(
            "EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1"
        )
        self.model = model or os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
        self._client = None

    def _lazy_init(self):
        """延迟初始化 OpenAI 兼容客户端。"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:  # pragma: no cover - 依赖缺失场景
                raise ImportError("openai 库未安装，请执行: pip install openai") from exc
            if not self.api_key:
                raise RuntimeError("未配置 EMBEDDING_API_KEY，请在 backend/.env 中填写")
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文档文本，按传入顺序返回向量。"""
        self._lazy_init()
        response = self._client.embeddings.create(model=self.model, input=texts)
        # 按原始顺序提取（API 返回顺序不保证与入参一致）
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询文本。"""
        self._lazy_init()
        response = self._client.embeddings.create(model=self.model, input=[text])
        return response.data[0].embedding


def create_embeddings() -> Embeddings:
    """工厂函数：创建嵌入模型实例（预留切换实现的扩展点）。"""
    return SiliconFlowEmbeddings()

"""MCP Server：web_search 工具（基于官方 FastMCP，stdio 传输）。

教学要点：
- 本文件是 MCP 协议的 **Server 端**：负责注册工具并暴露给外界调用。
- 使用 FastMCP：只需把普通函数用 `@mcp.tool()` 装饰，FastMCP 自动完成
  JSON Schema 生成、stdio 传输、initialize / tools/list / tools/call 会话流程。
- 由后端 MCPManager 以子进程方式启动（`backend/mcp_client/mcp_client.py` 的 Client 端）。

搜索实现：
- 优先调用必应（Bing）HTML 搜索接口；网络失败时降级为模拟结果，
  保证课程演示（工具调用闭环）在任何环境下可运行。
- 工具返回 JSON 字符串，由 Client 解析为 dict。
"""
import base64
import html
import json
import re
import urllib.parse
import urllib.request

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

mcp = FastMCP("web-search-server")


# ---------------------------------------------------------------- 搜索实现


def _decode_bing_url(href: str) -> str:
    """解码 Bing 跳转链接（base64 编码的 u 参数），还原真实 URL。"""
    m = re.search(r"[?&]u=a1([0-9A-Za-z_-]+)", href)
    if m:
        encoded = m.group(1)
        pad = "=" * (-len(encoded) % 4)
        try:
            return base64.urlsafe_b64decode(encoded + pad).decode("utf-8", errors="ignore")
        except Exception:
            return href
    return href


def _parse_bing(page: str) -> list:
    """从 Bing HTML 页面中提取 标题/摘要/链接。"""
    results = []
    for match in re.finditer(r'<li class="b_algo".*?</li>', page, re.S):
        block = match.group(0)
        title_match = re.search(
            r'<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.S
        )
        snippet_match = re.search(r'<p[^>]*>(.*?)</p>', block, re.S)
        if not title_match:
            continue
        title = html.unescape(re.sub(r"<[^>]+>", "", title_match.group(2))).strip()
        snippet = ""
        if snippet_match:
            snippet = html.unescape(re.sub(r"<[^>]+>", "", snippet_match.group(1))).strip()
        url = _decode_bing_url(html.unescape(title_match.group(1)))
        results.append({"title": title, "snippet": snippet, "url": url})
        if len(results) >= 5:
            break
    return results


def _web_search(query: str, num_results: int = 5) -> dict:
    """真实搜索（必应），失败时降级为模拟结果。"""
    try:
        url = "https://www.bing.com/search?q=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=8) as resp:
            page = resp.read().decode("utf-8", errors="ignore")
        results = _parse_bing(page)[:num_results]
        if results:
            return {"source": "bing", "query": query, "results": results}
        return _mock_search(query, num_results)
    except Exception:
        return _mock_search(query, num_results)


def _mock_search(query: str, num_results: int = 5) -> dict:
    """降级：返回固定的模拟搜索结果（保证演示闭环）。"""
    results = [
        {
            "title": f"「{query}」模拟搜索结果 {i + 1}",
            "snippet": f"这是关于「{query}」的第 {i + 1} 条模拟摘要，"
                       f"用于课程演示 MCP 工具调用闭环。",
            "url": f"https://example.com/{i + 1}",
        }
        for i in range(num_results)
    ]
    return {"source": "mock", "query": query, "results": results}


# ---------------------------------------------------------------- MCP 工具


@mcp.tool()
def web_search(query: str, num_results: int = 5) -> str:
    """联网搜索互联网，返回标题、摘要与链接列表。

    :param query: 搜索关键词
    :param num_results: 返回结果数量（默认 5，最大 10）

    教学要点：
    - 函数签名（参数名 + 类型 + 默认值 + docstring）就是工具的 JSON Schema 来源，
      FastMCP 会自动生成 `inputSchema` 并注入 LLM 的 tools 列表。
    - 返回值统一用 JSON 字符串（确保中文不转义），Client 端会尝试解析回 dict。
    """
    try:
        num_results = int(num_results)      # 兼容 LLM 有时把整数参数传成字符串
    except (ValueError, TypeError):
        num_results = 5                     # 非法值回退默认数量
    num_results = min(max(num_results, 1), 10)  # 限幅：最少 1 条、最多 10 条
    result = _web_search(query, num_results)
    return json.dumps(result, ensure_ascii=False)


# ---------------------------------------------------------------- 启动入口


if __name__ == "__main__":
    mcp.run(transport="stdio")

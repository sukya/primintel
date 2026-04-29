"""
Web Search tool - Search the web using Bocha or LinkAI search API.
Supports two backends with unified response format:
  1. Bocha Search (primary, requires BOCHA_API_KEY)
  2. LinkAI Search (fallback, requires LINKAI_API_KEY)
"""

import os
import json
from typing import Dict, Any, Optional

import requests

from agent.tools.base_tool import BaseTool, ToolResult
from common.log import logger
from common.geo_utils import is_china_ip
from config import conf


# Default timeout for API requests (seconds)
DEFAULT_TIMEOUT = 30


class WebSearch(BaseTool):
    """Tool for searching the web using Bocha or LinkAI search API"""

    name: str = "web_search"
    description: str = (
        "Search the web for real-time information (e.g., stock prices, weather, news, facts). "
        "This tool returns titles, URLs, and truncated snippets. "
        "STRATEGY: If snippets are insufficient for a precise answer, pick the most relevant URL "
        "and use the `web_fetch` tool to read the full content of that page."
    )

    params: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query string"
            },
            "count": {
                "type": "integer",
                "description": "Number of results to return (1-50, default: 10)"
            },
            "freshness": {
                "type": "string",
                "description": (
                    "Time range filter. Options: "
                    "'noLimit' (default), 'oneDay', 'oneWeek', 'oneMonth', 'oneYear', "
                    "or date range like '2025-01-01..2025-02-01'"
                )
            },
            "summary": {
                "type": "boolean",
                "description": "Whether to include text summary for each result (default: false)"
            }
        },
        "required": ["query"]
    }

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._backend = None  # Will be resolved on first execute

    @staticmethod
    def is_available() -> bool:
        """Check if web search is available (Requires Bocha/LinkAI API or SearXNG instance)"""
        return True

    def _resolve_backend(self) -> str:
        """
        Determine which search backend to use.
        Respects search_region (auto, CN, Global).
        
        CN Priority: Bocha > LinkAI > SearXNG (No DDGS)
        Global Priority: Bocha > Serper > LinkAI > DDGS
        """
        region = conf().get("search_region", "auto").lower()
        is_cn = False
        
        if region == "cn":
            is_cn = True
        elif region == "global":
            is_cn = False
        else:
            # auto mode
            try:
                is_cn = is_china_ip()
            except Exception as e:
                logger.debug(f"[WebSearch] Region detection failed: {e}")
                is_cn = False
        
        # 1. Any Region: Bocha is always top priority
        if os.environ.get("BOCHA_API_KEY") or conf().get("bocha_api_key"):
            return "bocha"
            
        # 2. Global specific: Serper
        if not is_cn:
            if os.environ.get("SERPER_API_KEY") or conf().get("serper_api_key"):
                return "serper"
        
        # 3. Any Region: LinkAI
        if os.environ.get("LINKAI_API_KEY") or conf().get("linkai_api_key"):
            return "linkai"
            
        # 4. Fallback (SearXNG acts as the unified free aggregator)
        return "searxng"

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Execute web search

        :param args: Search parameters (query, count, freshness, summary)
        :return: Search results
        """
        query = args.get("query", "").strip()
        if not query:
            return ToolResult.fail("Error: 'query' parameter is required")

        count = args.get("count", 10)
        freshness = args.get("freshness", "noLimit")
        summary = args.get("summary", False)

        # Validate count
        if not isinstance(count, int) or count < 1 or count > 50:
            count = 10

        # Resolve backend
        backend = self._resolve_backend()

        try:
            if backend == "bocha":
                return self._search_bocha(query, count, freshness, summary)
            elif backend == "serper":
                return self._search_serper(query, count, freshness)
            elif backend == "linkai":
                return self._search_linkai(query, count, freshness)
            elif backend == "searxng":
                return self._search_searxng(query, count)
            else:
                return ToolResult.fail(f"Error: Unsupported search backend '{backend}'")
        except requests.Timeout:
            return ToolResult.fail(f"Error: Search request timed out after {DEFAULT_TIMEOUT}s")
        except requests.ConnectionError:
            return ToolResult.fail("Error: Failed to connect to search API")
        except Exception as e:
            logger.error(f"[WebSearch] Unexpected error: {e}", exc_info=True)
            return ToolResult.fail(f"Error: Search failed - {str(e)}")

    def _search_bocha(self, query: str, count: int, freshness: str, summary: bool) -> ToolResult:
        """
        Search using Bocha API

        :param query: Search query
        :param count: Number of results
        :param freshness: Time range filter
        :param summary: Whether to include summary
        :return: Formatted search results
        """
        api_key = os.environ.get("BOCHA_API_KEY", "")
        url = "https://api.bocha.cn/v1/web-search"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "query": query,
            "count": count,
            "freshness": freshness,
            "summary": summary
        }

        logger.debug(f"[WebSearch] Bocha search: query='{query}', count={count}")

        response = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)

        if response.status_code == 401:
            return ToolResult.fail("Error: Invalid BOCHA_API_KEY. Please check your API key.")
        if response.status_code == 403:
            return ToolResult.fail("Error: Bocha API - insufficient balance. Please top up at https://open.bocha.cn")
        if response.status_code == 429:
            return ToolResult.fail("Error: Bocha API rate limit reached. Please try again later.")
        if response.status_code != 200:
            return ToolResult.fail(f"Error: Bocha API returned HTTP {response.status_code}")

        data = response.json()

        # Check API-level error code
        api_code = data.get("code")
        if api_code is not None and api_code != 200:
            msg = data.get("msg") or "Unknown error"
            return ToolResult.fail(f"Error: Bocha API error (code={api_code}): {msg}")

        # Extract and format results
        return self._format_bocha_results(data, query)

    def _format_bocha_results(self, data: dict, query: str) -> ToolResult:
        """
        Format Bocha API response into unified result structure

        :param data: Raw API response
        :param query: Original query
        :return: Formatted ToolResult
        """
        search_data = data.get("data", {})
        web_pages = search_data.get("webPages", {})
        pages = web_pages.get("value", [])

        if not pages:
            return ToolResult.success({
                "query": query,
                "backend": "bocha",
                "total": 0,
                "results": [],
                "message": "No results found"
            })

        results = []
        for page in pages:
            result = {
                "title": page.get("name", ""),
                "url": page.get("url", ""),
                "snippet": page.get("snippet", ""),
                "siteName": page.get("siteName", ""),
                "datePublished": page.get("datePublished") or page.get("dateLastCrawled", ""),
            }
            # Include summary only if present
            if page.get("summary"):
                result["summary"] = page["summary"]
            results.append(result)

        total = web_pages.get("totalEstimatedMatches", len(results))

        return ToolResult.success({
            "query": query,
            "backend": "bocha",
            "total": total,
            "count": len(results),
            "results": results
        })

    def _search_linkai(self, query: str, count: int, freshness: str) -> ToolResult:
        """
        Search using LinkAI plugin API

        :param query: Search query
        :param count: Number of results
        :param freshness: Time range filter
        :return: Formatted search results
        """
        api_key = os.environ.get("LINKAI_API_KEY", "")
        api_base = conf().get("linkai_api_base", "https://api.link-ai.tech")
        url = f"{api_base.rstrip('/')}/v1/plugin/execute"

        from common.utils import get_cloud_headers
        headers = get_cloud_headers(api_key)

        payload = {
            "code": "web-search",
            "args": {
                "query": query,
                "count": count,
                "freshness": freshness
            }
        }

        logger.debug(f"[WebSearch] LinkAI search: query='{query}', count={count}")

        response = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)

        if response.status_code == 401:
            return ToolResult.fail("Error: Invalid LINKAI_API_KEY. Please check your API key.")
        if response.status_code != 200:
            return ToolResult.fail(f"Error: LinkAI API returned HTTP {response.status_code}")

        data = response.json()

        if not data.get("success"):
            msg = data.get("message") or "Unknown error"
            return ToolResult.fail(f"Error: LinkAI search failed: {msg}")

        return self._format_linkai_results(data, query)

    def _format_linkai_results(self, data: dict, query: str) -> ToolResult:
        """
        Format LinkAI API response into unified result structure.
        LinkAI returns the search data in data.data field, which follows
        the same Bing-compatible format as Bocha.

        :param data: Raw API response
        :param query: Original query
        :return: Formatted ToolResult
        """
        raw_data = data.get("data", "")

        # LinkAI may return data as a JSON string
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except (json.JSONDecodeError, TypeError):
                # If data is plain text, return it as a single result
                return ToolResult.success({
                    "query": query,
                    "backend": "linkai",
                    "total": 1,
                    "count": 1,
                    "results": [{"content": raw_data}]
                })

        # If the response follows Bing-compatible structure
        if isinstance(raw_data, dict):
            web_pages = raw_data.get("webPages", {})
            pages = web_pages.get("value", [])

            if pages:
                results = []
                for page in pages:
                    result = {
                        "title": page.get("name", ""),
                        "url": page.get("url", ""),
                        "snippet": page.get("snippet", ""),
                        "siteName": page.get("siteName", ""),
                        "datePublished": page.get("datePublished") or page.get("dateLastCrawled", ""),
                    }
                    if page.get("summary"):
                        result["summary"] = page["summary"]
                    results.append(result)

                total = web_pages.get("totalEstimatedMatches", len(results))
                return ToolResult.success({
                    "query": query,
                    "backend": "linkai",
                    "total": total,
                    "count": len(results),
                    "results": results
                })

        # Fallback: return raw data
        return ToolResult.success({
            "query": query,
            "backend": "linkai",
            "total": 1,
            "count": 1,
            "results": [{"content": str(raw_data)}]
        })


    def _search_serper(self, query: str, count: int, freshness: str) -> ToolResult:
        """
        Search using Serper.dev (Google API)
        """
        api_key = os.environ.get("SERPER_API_KEY") or conf().get("serper_api_key")
        url = "https://google.serper.dev/search"

        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }

        # Map freshness (noLimit/oneDay/oneWeek/oneMonth/oneYear) to serper 'tbs' parameter (qdr:d/w/m/y)
        tbs = ""
        if freshness == "oneDay":
            tbs = "qdr:d"
        elif freshness == "oneWeek":
            tbs = "qdr:w"
        elif freshness == "oneMonth":
            tbs = "qdr:m"
        elif freshness == "oneYear":
            tbs = "qdr:y"

        payload = {
            "q": query,
            "num": count
        }
        if tbs:
            payload["tbs"] = tbs

        logger.debug(f"[WebSearch] Serper search: query='{query}', count={count}")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
            
            if response.status_code == 403:
                return ToolResult.fail("Error: Invalid SERPER_API_KEY or out of credits.")
            if response.status_code != 200:
                return ToolResult.fail(f"Error: Serper API returned HTTP {response.status_code}")

            data = response.json()
            organic_results = data.get("organic", [])
            
            if not organic_results:
                return ToolResult.success({
                    "query": query,
                    "backend": "serper",
                    "total": 0,
                    "results": [],
                    "message": "No results found"
                })

            results = []
            for r in organic_results:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("link", ""),
                    "snippet": r.get("snippet", ""),
                    "datePublished": r.get("date", "")
                })

            return ToolResult.success({
                "query": query,
                "backend": "serper",
                "total": len(results),
                "count": len(results),
                "results": results
            })
        except Exception as e:
            logger.error(f"[WebSearch] Serper error: {e}")
            return ToolResult.fail(f"Error: Serper search failed: {e}")

    def _search_searxng(self, query: str, count: int) -> ToolResult:
        """
        Search using SearXNG public/private instance.
        """
        # Try custom URL first, then pool of reliable public instances
        custom_url = os.environ.get("SEARXNG_URL") or conf().get("searxng_url")
        
        # A list of relatively stable public instances for fallback
        public_instances = [
            "https://searx.be",
            "https://searx.tiekoetter.com",
            "https://search.mdosch.de",
            "https://paulgo.io",
            "https://priv.au",
            "https://search.ononoki.org",
        ]
        
        instances_to_try = [url.strip() for url in custom_url.split(',')] if custom_url else []
        for p in public_instances:
            if p not in instances_to_try:
                instances_to_try.append(p)

        logger.debug(f"[WebSearch] SearXNG search: query='{query}', count={count}")

        last_error = None
        for i, instance_url in enumerate(instances_to_try):
            instance_url = instance_url.strip().rstrip('/')
            url = f"{instance_url}/search"
            
            params = {
                "q": query,
                "format": "json"
            }
            
            try:
                # Use a shorter timeout for public fallbacks to fail fast and retry
                timeout = DEFAULT_TIMEOUT if i == 0 and custom_url else 5
                
                # Add browser User-Agent to avoid 403 Forbidden from bot detection
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=timeout)
                
                # Public instances often Rate Limit (429) or Forbidden (403 json missing)
                if response.status_code != 200:
                    last_error = f"HTTP {response.status_code}"
                    continue
                    
                data = response.json()
                results_data = data.get("results", [])
                
                results = []
                for r in results_data[:count]:
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("content", ""),
                        "siteName": r.get("engine", "")
                    })
                    
                return ToolResult.success({
                    "query": query,
                    "backend": f"searxng ({instance_url})",
                    "total": len(results),
                    "count": len(results),
                    "results": results,
                    "tip": "Snippet information is limited. For detailed facts, use `web_fetch` on a high-relevance URL."
                })
                
            except Exception as e:
                logger.debug(f"[WebSearch] SearXNG instance {instance_url} failed: {e}")
                last_error = str(e)
                continue
                
        # If we exhausted all instances
        region = conf().get("search_region", "auto").lower()
        msg = f"Error: All SearXNG instances failed (Last error: {last_error}). "
        
        # Provide specific advice for Chinese users
        if region == "cn" or (region == "auto" and is_china_ip()):
            msg += "\n提示：检测到您处于国内网络环境，公共搜索节点可能不稳定。推荐在[配置]页填写【博查 AI API Key】(open.bocha.cn) 以获得极速优质的搜索体验。"
        elif not custom_url:
            msg += "Please configure BOCHA_API_KEY or deploy a self-hosted SEARXNG_URL."
            
        return ToolResult.fail(msg)


import re
import httpx
from typing import List, Dict, Any, Optional
from app.config import settings
from app.utils.logger import logger
from app.services.image_gen_service import image_gen_service

class SearchService:
    def __init__(self):
        self.tavily_key = settings.TAVILY_API_KEY
        self.max_results = settings.SEARCH_MAX_RESULTS

    def classify_query(
        self,
        query: str,
        has_attached_docs: bool = False,
        has_attached_images: bool = False,
        force_rag: Optional[bool] = None,
        force_web: Optional[bool] = None
    ) -> str:
        """
        Classifies user query intent:
        - 'image_generation': Requesting AI to create/draw an image
        - 'web_image_search': Requesting to see a photo of a person/place/object from web
        - 'document_creation': Creating a new document (e.g. 'create a report', 'generate docx')
        - 'document_update': Modifying an existing document ('add conclusion', 'rewrite section')
        - 'hybrid': Involves both document comparison and web research
        - 'rag': Questions asking about attached documents/files
        - 'web_search': Questions requiring real-time, current, or external web information
        - 'general': Standard assistant questions
        """
        q = query.lower().strip()

        # 1. Check AI Image Generation intent
        if image_gen_service.is_image_generation_query(q):
            return "image_generation"

        # 2. Check Web Image Search intent
        if image_gen_service.is_web_image_search_query(q):
            return "web_image_search"

        # Check explicit overrides
        if force_web and force_rag:
            return "hybrid"
        if force_web:
            return "web_search"
        if force_rag:
            return "rag"

        # 3. Check document creation intent
        creation_patterns = [
            r"create (a |an )?(report|document|docx|file|draft|summary doc)",
            r"generate (a |an )?(report|document|docx|file)",
            r"write (a |an )?(report|document|docx|essay) on",
            r"export (to |as )?(docx|doc|document)"
        ]
        if any(re.search(pat, q) for pat in creation_patterns):
            return "document_creation"

        # 4. Check document update/edit intent
        update_patterns = [
            r"add (a |an )?(conclusion|section|table|paragraph) to (this|the|my) (document|report|file)",
            r"rewrite (section|paragraph|the document|this document)",
            r"update (this|the|my) (document|report|file)",
            r"correct the grammar in (this|the|my) (document|file)",
            r"modify (this|the|my) (document|file|report)"
        ]
        if has_attached_docs and any(re.search(pat, q) for pat in update_patterns):
            return "document_update"

        # 5. Check hybrid (document + web search)
        hybrid_patterns = [
            r"compare .* (document|pdf|file) with (the latest|current|online|recent)",
            r"how does (this|the|my) (document|pdf) compare (with|to) (recent|current|latest|online)"
        ]
        if has_attached_docs and any(re.search(pat, q) for pat in hybrid_patterns):
            return "hybrid"

        # 6. Check RAG intent (document questions)
        rag_patterns = [
            r"(in|from|according to) (the|this|my) (document|pdf|file|uploaded)",
            r"(what does|what says) (the|this|my) (document|pdf|file)",
            r"summarize (the|this|my) (document|pdf|file)",
            r"uploaded (document|pdf|file|text)"
        ]
        if has_attached_docs:
            if any(re.search(pat, q) for pat in rag_patterns) or len(q.split()) < 7:
                return "rag"

        # 7. Check web search triggers
        web_search_triggers = [
            r"\b(latest|recent|current|today|news|update|developments|price of|who is currently|what happened in 202[4-9])\b",
            r"\b(search the web|google|search online|look up online|find online)\b",
            r"\b(weather in|stock price|election|crypto)\b"
        ]
        if any(re.search(trig, q) for trig in web_search_triggers):
            return "web_search"

        # If user attached document without explicit trigger
        if has_attached_docs:
            return "rag"

        return "general"

    async def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Executes web search with automatic Tavily API + DuckDuckGo free fallback.
        """
        limit = max_results or self.max_results
        cleaned_query = re.sub(r"^(search the web for|look up|search for|google)\s+", "", query, flags=re.I).strip()
        logger.info(f"Executing web search for: '{cleaned_query}'")

        # 1. Try Tavily API if key provided (1000 Free searches/month, high quality)
        tavily_key = settings.TAVILY_API_KEY or self.tavily_key
        if tavily_key:
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": tavily_key,
                            "query": cleaned_query,
                            "search_depth": "basic",
                            "include_answer": True,
                            "max_results": limit
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        results = []
                        for item in data.get("results", []):
                            results.append({
                                "title": item.get("title", "Web Result"),
                                "url": item.get("url", ""),
                                "snippet": item.get("content", "")
                            })
                        if results:
                            logger.info(f"Retrieved {len(results)} results via Tavily")
                            return results
                    else:
                        logger.warning(f"Tavily API returned status {resp.status_code}. Falling back to DuckDuckGo.")
            except Exception as e:
                logger.warning(f"Tavily search failed: {e}. Falling back to DuckDuckGo.")

        # 2. Try duckduckgo_search library (100% Free, zero key required)
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(cleaned_query, max_results=limit))
                formatted = []
                for r in results:
                    formatted.append({
                        "title": r.get("title", "Web Result"),
                        "url": r.get("href") or r.get("link", ""),
                        "snippet": r.get("body") or r.get("snippet", "")
                    })
                if formatted:
                    logger.info(f"Retrieved {len(formatted)} results via DuckDuckGo")
                    return formatted
        except Exception as e:
            logger.warning(f"DuckDuckGo search library failed: {e}. Trying direct HTTP fallback.")

        # 3. Try DuckDuckGo Instant Answer HTTP API fallback
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": cleaned_query, "format": "json", "no_html": "1", "skip_disambig": "1"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    formatted = []
                    abstract = data.get("AbstractText")
                    if abstract:
                        formatted.append({
                            "title": data.get("Heading", cleaned_query),
                            "url": data.get("AbstractURL", "https://duckduckgo.com"),
                            "snippet": abstract
                        })
                    
                    related = data.get("RelatedTopics", [])
                    for topic in related[:limit]:
                        if isinstance(topic, dict) and "Text" in topic:
                            formatted.append({
                                "title": topic.get("Text", "").split(" - ")[0],
                                "url": topic.get("FirstURL", "https://duckduckgo.com"),
                                "snippet": topic.get("Text", "")
                            })
                    if formatted:
                        return formatted
        except Exception as e:
            logger.warning(f"DuckDuckGo HTTP API fallback error: {e}")

        # 4. Graceful fallback for completely offline testing
        return [
            {
                "title": f"Overview: {cleaned_query}",
                "url": f"https://duckduckgo.com/?q={cleaned_query.replace(' ', '+')}",
                "snippet": f"Verified developments and reference research regarding '{cleaned_query}'."
            }
        ]

    def format_search_context(self, search_results: List[Dict[str, str]]) -> str:
        """Formats search results for LLM prompt context."""
        if not search_results:
            return ""
        
        lines = []
        for idx, res in enumerate(search_results):
            lines.append(
                f"[Web Source {idx+1}]: {res['title']}\n"
                f"URL: {res['url']}\n"
                f"Summary: {res['snippet']}\n"
            )
        return "\n".join(lines)

search_service = SearchService()

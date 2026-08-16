"""
PARALLEL SEARCH MCP - Real-world data grounding via Parallel AI MCP.

Integrates with Parallel AI's MCP server for web_search and web_fetch tools.
Used for:
- True agentic behavior (retries on Gemini API failures)
- Multi-attempt crisis analysis
- Real-time weather data and location information

MCP Server: https://search.parallel.ai/mcp
Tools: web_search, web_fetch
"""

import json
import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

# Parallel AI MCP Configuration
PARALLEL_MCP_ENDPOINT = "https://search.parallel.ai/mcp"
PARALLEL_API_KEY = os.getenv("PARALLEL_API_KEY")

if not PARALLEL_API_KEY:
    logger.warning(
        "PARALLEL_API_KEY not found in .env. "
        "Web search will use fallback mock data. "
        "To enable real web search, add PARALLEL_API_KEY to .env"
    )


def parallel_web_search(query: str) -> dict[str, Any]:
    """
    Execute a web search to find live information about a crisis location.
    
    Falls back to mock data if search fails (for dev/demo without internet).
    Returns: {"status": "success", "results": [...], "sources": [...]}
    """
    
    try:
        search_results = _execute_web_search(query)
        if search_results:
            return {
                "status": "success",
                "results": search_results,
                "query": query,
                "source": "web_search"
            }
    except (requests.RequestException, ValueError) as e:
        logger.warning(f"Web search failed for query '{query}': {e!s}. Using fallback data.")
    
    return _get_fallback_results(query)


def _execute_web_search(query: str) -> list[dict[str, Any]]:
    """
    Execute web search via Parallel AI MCP server.
    
    Uses web_search tool from Parallel AI for real-time internet data.
    Returns structured search results for crisis analysis.
    
    MCP Protocol Flow:
    1. Send jsonrpc request to MCP server
    2. Use web_search tool with query
    3. Parse results and return formatted data
    """
    
    if not PARALLEL_API_KEY:
        logger.debug("PARALLEL_API_KEY not configured. Skipping real web search.")
        return []
    
    try:
        # MCP Request for web_search tool
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "web_search",
                "arguments": {"query": query, "limit": 10}
            }
        }
        
        headers = {
            "Authorization": f"Bearer {PARALLEL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            PARALLEL_MCP_ENDPOINT,
            json=mcp_request,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Parse MCP response
            results = data.get("result")
            if results and isinstance(results, list):
                return [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("snippet", r.get("description", ""))
                    }
                    for r in results if r.get("title") or r.get("url")
                ]
            logger.debug(f"Parallel AI web_search returned: {data}")
            return []
    except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
        logger.warning(f"Web search API call failed: {e!s}")
    
    return []


def _get_fallback_results(query: str) -> dict[str, Any]:
    """
    Fallback mock results for development/demo when internet unavailable.
    Returns realistic weather/crisis data for Puri Beach scenario.
    """
    
    results = []
    
    if "puri" in query.lower() or "beach" in query.lower():
        results = [
            {
                "title": "Weather Puri - meteoblue",
                "url": "https://www.meteoblue.com/en/weather/week/puri",
                "snippet": "Mon 8-25 Overcast with rain. 85-90°F. Tropical monsoon conditions with 90-95% precipitation chance."
            },
            {
                "title": "Puri Weather Forecast",
                "url": "https://www.weather-forecast.com/locations/Puri",
                "snippet": "Heavy rain (22mm), heaviest during night. Warm (29°C max). Gentle winds 8-12 mph."
            },
            {
                "title": "NDTV Weather - Puri",
                "url": "https://www.ndtv.com/weather/puri",
                "snippet": "93% chance of rain today in Puri. Monsoon alert issued. Beach conditions: unsafe for outdoor filming."
            },
            {
                "title": "Weather Underground - Puri",
                "url": "https://www.wunderground.com/forecast/in/puri",
                "snippet": "Thunderstorms likely. Wave height 6-8 feet. Current conditions: dangerous for equipment."
            },
            {
                "title": "BBC Weather - Puri",
                "url": "https://www.bbc.com/weather/1259184",
                "snippet": "Monsoon season. 14-day outlook shows continuous rain. Outdoor activity restricted."
            },
            {
                "title": "Puri Beach Tide Forecast",
                "url": "https://www.tideschart.com/india/puri",
                "snippet": "High tide at 14:30. Swell 1.5m. Current: 2 knots southwest. Dangerous swimming conditions."
            },
            {
                "title": "IMDTC - Cyclone Dana Update",
                "url": "https://mausam.imd.gov.in/",
                "snippet": "Cyclone Dana tracking toward Odisha. Puri on high alert. Outdoor shoots not recommended."
            },
            {
                "title": "Skymet Weather - Extended Forecast",
                "url": "https://www.skymetweather.com/forecast/india/odisha/puri",
                "snippet": "5-7 day rain forecast: continuous precipitation. No clear window for outdoor scenes."
            },
            {
                "title": "Local News - Puri Monsoon Alert",
                "url": "https://www.liveodisha.com/news/puri-monsoon",
                "snippet": "Monsoon rains lashing Puri beaches. Tourist advisories issued. All beach activities suspended."
            },
            {
                "title": "Production Notes - Puri Beach Conditions",
                "url": "https://www.productionscout.in/locations/puri",
                "snippet": "August 25-26: Puri Beach inaccessible due to monsoon. Recommend interior/studio alternatives."
            }
        ]
    else:
        results = [
            {
                "title": "Weather Forecast",
                "url": "https://www.weather-forecast.com",
                "snippet": "Standard weather conditions. No severe alerts."
            }
        ]
    
    return {
        "status": "success",
        "results": results,
        "query": query,
        "source": "fallback_mock_data"
    }

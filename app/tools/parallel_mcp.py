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
    Returns realistic data for Puri Beach scenario with DIFFERENT info per category.
    """
    
    results = []
    query_lower = query.lower()
    
    # LOCATION_ACCESS queries
    if "accessibility" in query_lower or "road closures" in query_lower or "travel disruptions" in query_lower:
        results = [
            {"title": "NH5 Highway - Traffic Alert", "url": "https://traffic.imdtc.gov.in/", "snippet": "NH5 blocked near Puri due to waterlogging. 2-hour delays reported. Alternate route via coastal highway advised."},
            {"title": "Puri District - Access Report", "url": "https://puri.gov.in/alerts", "snippet": "All major roads open except beach access restricted. Local transport operating normally."},
            {"title": "NHAI Updates - Odisha", "url": "https://nhai.gov.in/en/live-traffic", "snippet": "Road condition: WET. Visibility: POOR. Speed limit reduced to 40 km/h. Heavy vehicle advisory in effect."},
            {"title": "Local Transport - Puri", "url": "https://puri-transport.com", "snippet": "Bus services suspended to Arambol Beach. Alternative: Taxi/auto available. Cost: +30% surge pricing."},
            {"title": "Railway Updates - Odisha", "url": "https://indianrailways.gov.in/odisha", "snippet": "Trains running on schedule. No cancellations reported. Puri station operational."},
            {"title": "Flight Status - Bhubaneswar", "url": "https://bbs-airport.com/status", "snippet": "Flights operating normally. Visibility acceptable. No diversions."},
            {"title": "Port Authority - Puri", "url": "https://puri-port.gov.in", "snippet": "Sea route closed. High waves 6-8 feet. No water transport available."},
            {"title": "Emergency Services - Odisha Police", "url": "https://odisha-police.gov.in", "snippet": "Patrolling intensified. All access points monitored. No incidents reported."},
            {"title": "Permit Office - Puri Coastal Zone", "url": "https://puri-permits.gov.in", "snippet": "Beach access permits suspended until Sept 2. Administrative office open 9am-5pm."},
            {"title": "Local Guide - Arambol Beach Access", "url": "https://arambol-guide.com", "snippet": "North beach gate closed. South gate operational 6am-4pm only. Water level high."}
        ]
    
    # VENUE_STATUS queries
    elif "facility operational status" in query_lower or "venue status" in query_lower or "closed shutdowns" in query_lower:
        results = [
            {"title": "Kalinga Studios - Status Update", "url": "https://kalinga-studios.com/status", "snippet": "All soundstages operational. Power backup active. AC functioning normally. Ready for production."},
            {"title": "Puri Beach Resort - Facilities", "url": "https://puri-resort.com/facilities", "snippet": "Closed until Sept 3 due to monsoon. Staff on standby. Emergency protocols activated."},
            {"title": "Local Hotels - Operational Status", "url": "https://puri-hotels.com", "snippet": "All hotels operational. Some water damage in ground floor rooms. Water supply normal."},
            {"title": "Studio Rental - Nashik", "url": "https://nashik-studios.com", "snippet": "3 stages available. Full technical support. AC, power, water all operational."},
            {"title": "Police Station - Nashik", "url": "https://nashik-police.gov.in", "snippet": "Operational 24/7. Full staff on duty. No closures or maintenance scheduled."},
            {"title": "Municipal Water Supply - Puri", "url": "https://puri-water.gov.in", "snippet": "Supply normal. No disruptions. Quality tests passed. 24-hour availability."},
            {"title": "Electricity Distribution - Odisha", "url": "https://orppdcl.gov.in", "snippet": "All grids operational. No load shedding planned. Emergency power available."},
            {"title": "Telecom Towers - Puri District", "url": "https://bsnl-odisha.gov.in", "snippet": "All towers operational. 4G/5G coverage normal. No network issues reported."},
            {"title": "Medical Facilities - Puri Hospital", "url": "https://puri-hospital.gov.in", "snippet": "Emergency ward fully staffed. ICU beds available. Ambulance services active."},
            {"title": "Security Services - Puri", "url": "https://puri-security.gov.in", "snippet": "24-hour patrols. Armed guards available for hire. CCTV monitoring active."}
        ]
    
    # LOCAL_EVENTS queries
    elif "events" in query_lower or "festivals" in query_lower or "closures demonstrations" in query_lower:
        results = [
            {"title": "Puri Calendar - Sept 2026", "url": "https://puri-events.gov.in", "snippet": "No major festivals scheduled Sept 1-15. Monsoon season considered quiet period for events."},
            {"title": "Jagannath Temple - Events", "url": "https://jagannath-temple.org", "snippet": "Daily pujas continuing. No special events until Sept 10. Tourism restricted."},
            {"title": "Cultural Programs - Odisha", "url": "https://odisha-culture.gov.in", "snippet": "All outdoor cultural programs postponed until Oct 1. Indoor performances continuing."},
            {"title": "Sports Events - Puri", "url": "https://puri-sports.gov.in", "snippet": "Beach volleyball tournament cancelled. Indoor badminton league continues."},
            {"title": "Business Conventions - Puri", "url": "https://puri-convention.com", "snippet": "No conferences booked Sept 1-10. Next booking: Sept 15 (hotel conference)."},
            {"title": "Film Festival - Odisha", "url": "https://odisha-filmfest.gov.in", "snippet": "Annual film festival rescheduled from Sept to Oct due to monsoon."},
            {"title": "Public Demonstrations - Puri", "url": "https://puri-public-order.gov.in", "snippet": "No demonstrations or protests scheduled. Monsoon weather discourages public gatherings."},
            {"title": "Market Fairs - Local News", "url": "https://puri-markets.gov.in", "snippet": "Weekly markets operating normally. Weekend bazaar continues as scheduled."},
            {"title": "School Holidays - Odisha", "url": "https://odisha-education.gov.in", "snippet": "Schools closed Sept 1-5 (monsoon break). Reopening Sept 6."},
            {"title": "Holiday Calendar - India", "url": "https://india-holidays.gov.in", "snippet": "No national holidays in Sept. Next holiday: Oct 2 (Gandhi Jayanti)."}
        ]
    
    # PUBLIC_ALERTS queries
    elif "announcements alerts" in query_lower or "government warnings" in query_lower or "public alerts" in query_lower:
        results = [
            {"title": "IMD Alert - Cyclone Dana", "url": "https://mausam.imd.gov.in/alerts", "snippet": "CYCLONE DANA WARNING: Expected to intensify. Wind speed 60-80 km/h. Odisha HIGH ALERT issued."},
            {"title": "NDMA Alert - Monsoon Season", "url": "https://ndma.gov.in/alerts", "snippet": "NATIONAL DISASTER ALERT: Heavy rainfall expected. Landslide risk in hilly areas. Avoid outdoor activities."},
            {"title": "Ministry of Home Affairs - Weather Alert", "url": "https://mha.gov.in/weather", "snippet": "ORANGE ALERT for Odisha. Prepare for flooding. Stock food/water. Emergency helpline: 1234-5678."},
            {"title": "Coast Guard - Beach Safety", "url": "https://indiancoastguard.gov.in", "snippet": "BEACH CLOSURE ADVISORY: All beaches in Odisha closed for swimming. Rescue operations on standby."},
            {"title": "Air Quality Alert - Puri", "url": "https://airquality.gov.in/puri", "snippet": "Air quality: MODERATE. Visibility: POOR. Respiratory patients advised to stay indoors."},
            {"title": "Health Department - Disease Alert", "url": "https://odisha-health.gov.in", "snippet": "Monsoon disease warning: Dengue/Malaria cases increasing. Medical supplies deployed."},
            {"title": "Financial Alert - Insurance", "url": "https://insurance-alert.gov.in", "snippet": "Monsoon damage insurance activated. Claims processing expedited. Hotline: 1800-INSURE."},
            {"title": "Travel Advisory - Ministry of External Affairs", "url": "https://mea.gov.in/travel", "snippet": "TRAVEL WARNING: Avoid Odisha coast Sept 1-5. Defer non-essential travel."},
            {"title": "Utility Alert - Power/Water", "url": "https://odisha-utilities.gov.in", "snippet": "UTILITY ALERT: Possible power cuts 6pm-10pm due to monsoon. Water pressure may reduce."},
            {"title": "Police Advisory - Safety", "url": "https://odisha-police.gov.in/alerts", "snippet": "SAFETY ADVISORY: Avoid night travel. Stay home after 8pm. Helpline: 100."}
        ]
    
    # INFRASTRUCTURE queries
    elif "infrastructure" in query_lower or "utilities" in query_lower or "power water status" in query_lower:
        results = [
            {"title": "Power Grid Status - Odisha", "url": "https://orppdcl.gov.in/grid-status", "snippet": "Grid Frequency: 49.8 Hz (Normal). Load: 85% of capacity. Backup generators online."},
            {"title": "Water Treatment - Puri Municipal", "url": "https://puri-water.gov.in/treatment", "snippet": "Treatment capacity: 50 MLD. Current usage: 35 MLD. Reserve storage: 2 days supply."},
            {"title": "Sewage System - Puri", "url": "https://puri-sewage.gov.in", "snippet": "Drainage pumping stations operational. Overflow risk: MODERATE. Monsoon capacity: 80%."},
            {"title": "Telecom Infrastructure - Odisha", "url": "https://bsnl-odisha.gov.in/infra", "snippet": "Fiber optic network: 99% operational. Backup power: 12 hours per tower. 5G rollout: 70%."},
            {"title": "Gas Pipeline - Odisha Network", "url": "https://odisha-gas.gov.in", "snippet": "Pipeline pressure: Normal. No leaks reported. Distribution: Uninterrupted. Supply: 48 hours."},
            {"title": "Waste Management - Puri", "url": "https://puri-waste.gov.in", "snippet": "Collection rate: 95%. Disposal: Daily. Landfill capacity: 60% full. No issues."},
            {"title": "Road Infrastructure - NH Dept", "url": "https://nh-odisha.gov.in", "snippet": "Potholes: 12 reported. Repairs scheduled. Bridge inspections: All clear. Drainage: Adequate."},
            {"title": "Harbor Infrastructure - Port Authority", "url": "https://puri-port.gov.in/infra", "snippet": "Jetty condition: OPERATIONAL. Docking capacity: 4 ships. Fuel storage: 70% full."},
            {"title": "Railway Infrastructure - Indian Railways", "url": "https://indianrailways.gov.in/infra", "snippet": "Track condition: EXCELLENT. Switches: All functional. Signals: 99% operational. Maintenance: Scheduled."},
            {"title": "Airport Infrastructure - Bhubaneswar", "url": "https://bbs-airport.com/infra", "snippet": "Runway: Operational. Lighting: 100% functional. Radar: Clear. Backup systems: Active."}
        ]
    
    # WEATHER (default or explicit weather query)
    else:
        results = [
            {"title": "Weather Puri - meteoblue", "url": "https://www.meteoblue.com/en/weather/week/puri", "snippet": "Mon 8-25 Overcast with rain. 85-90°F. Tropical monsoon conditions with 90-95% precipitation chance."},
            {"title": "Puri Weather Forecast", "url": "https://www.weather-forecast.com/locations/Puri", "snippet": "Heavy rain (22mm), heaviest during night. Warm (29°C max). Gentle winds 8-12 mph."},
            {"title": "NDTV Weather - Puri", "url": "https://www.ndtv.com/weather/puri", "snippet": "93% chance of rain today in Puri. Monsoon alert issued. Beach conditions: unsafe for outdoor filming."},
            {"title": "Weather Underground - Puri", "url": "https://www.wunderground.com/forecast/in/puri", "snippet": "Thunderstorms likely. Wave height 6-8 feet. Current conditions: dangerous for equipment."},
            {"title": "BBC Weather - Puri", "url": "https://www.bbc.com/weather/1259184", "snippet": "Monsoon season. 14-day outlook shows continuous rain. Outdoor activity restricted."},
            {"title": "Puri Beach Tide Forecast", "url": "https://www.tideschart.com/india/puri", "snippet": "High tide at 14:30. Swell 1.5m. Current: 2 knots southwest. Dangerous swimming conditions."},
            {"title": "IMDTC - Cyclone Dana Update", "url": "https://mausam.imd.gov.in/", "snippet": "Cyclone Dana tracking toward Odisha. Puri on high alert. Outdoor shoots not recommended."},
            {"title": "Skymet Weather - Extended Forecast", "url": "https://www.skymetweather.com/forecast/india/odisha/puri", "snippet": "5-7 day rain forecast: continuous precipitation. No clear window for outdoor scenes."},
            {"title": "Local News - Puri Monsoon Alert", "url": "https://www.liveodisha.com/news/puri-monsoon", "snippet": "Monsoon rains lashing Puri beaches. Tourist advisories issued. All beach activities suspended."},
            {"title": "Production Notes - Puri Beach Conditions", "url": "https://www.productionscout.in/locations/puri", "snippet": "August 25-26: Puri Beach inaccessible due to monsoon. Recommend interior/studio alternatives."}
        ]
    
    return {
        "status": "success",
        "results": results,
        "query": query,
        "source": "fallback_mock_data"
    }

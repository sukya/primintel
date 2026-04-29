# encoding:utf-8
import requests
import re
from common.log import logger

# Cache to prevent repeated IP queries during the same session
_cached_is_china = None

def is_china_ip() -> bool:
    """
    Detect if the current environment is running with a Chinese IP.
    Uses international APIs first, with domestic fallbacks.
    Returns True if in China, False otherwise.
    """
    global _cached_is_china
    
    if _cached_is_china is not None:
        return _cached_is_china
        
    # 1. Try ip-api.com (International)
    try:
        response = requests.get('http://ip-api.com/json/?fields=countryCode', timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get('countryCode') == 'CN':
                _cached_is_china = True
                logger.debug("[GeoUtils] Detected CN ip (via ip-api).")
                return True
    except Exception:
        pass

    # 2. Try domestic fallback: pv.sohu.com (More reliable for CN-based servers)
    try:
        # This service returns a JS snippet like: var returnCitySN = {"cip": "x.x.x.x", "cid": "xxxxxx", "cname": "CHINA"};
        response = requests.get('http://pv.sohu.com/cityjson?ie=utf-8', timeout=3)
        if response.status_code == 200:
            # We use regex to extract the JSON part to avoid encoding issues with the full JS snippet
            match = re.search(r'\{.*\}', response.text)
            if match:
                data_str = match.group()
                # If cname contains China related info (often in Chinese/English)
                if "中国" in response.text or "CHINA" in response.text.upper():
                    _cached_is_china = True
                    logger.debug("[GeoUtils] Detected CN ip (via sohu fallback).")
                    return True
    except Exception:
        pass
        
    # Default to False (Global) if all detection fails or returns non-CN
    _cached_is_china = False
    return False

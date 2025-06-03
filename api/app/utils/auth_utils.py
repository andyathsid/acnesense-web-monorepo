import time
from google.auth import default
from google.auth.transport.requests import Request
from flask import current_app

# Cache for the token to avoid repeated authentication
_token_cache = {
    "token": None,
    "expiry": 0
}

def get_access_token():
    """Get a Google Cloud access token using application default credentials"""
    
    # Check if we have a cached token that's still valid
    now = time.time()
    if _token_cache["token"] and _token_cache["expiry"] > now + 300:
        return _token_cache["token"]
    
    try:
        # Use Google Cloud's client library for authentication
        credentials, _ = default()
        
        # Refresh credentials if they're expired
        if not credentials.valid:
            credentials.refresh(Request())
            
        # Cache the token with a slightly earlier expiry for safety
        _token_cache["token"] = credentials.token
        _token_cache["expiry"] = credentials.expiry.timestamp() if credentials.expiry else (now + 3500)
        
        return credentials.token
        
    except Exception as e:
        current_app.logger.error(f"Error obtaining access token: {str(e)}")
        raise Exception(f"Failed to obtain valid access token: {str(e)}")
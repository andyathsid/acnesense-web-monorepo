import time
import requests
from flask import current_app
from google.auth import default
import google.auth.transport.requests

def initialize_token_cache(app):
    """Initialize token cache in the application context when app starts"""
    if not hasattr(app, 'token_cache'):
        app.token_cache = {
            'token': None,
            'expiry': 0,
            'credentials': None
        }

def get_access_token():
    """Get a valid access token for GCP services using application context cache"""
    # Ensure we have a token cache in the app context
    if not hasattr(current_app, 'token_cache'):
        initialize_token_cache(current_app)
    
    # Check if we have a cached token that's still valid
    now = time.time()
    if (current_app.token_cache['token'] and 
        current_app.token_cache['expiry'] > now + 60):
        return current_app.token_cache['token']

    try:
        # Fallback to default credentials with improved error handling
        token = _get_token_from_default_credentials()
        if token:
            return token
        
        # If both methods fail, raise a specific error
        raise Exception("Failed to obtain access token.")
        
    except Exception as e:
        current_app.logger.error(f"Error getting access token: {str(e)}")
        raise Exception(f"Authentication failed: {str(e)}")


def _get_token_from_default_credentials():
    """Get token using default credentials with app context caching"""
    try:
        # Get credentials using default authentication
        credentials, project = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        
        # Force refresh if credentials are not valid
        if not credentials.valid:
            request = google.auth.transport.requests.Request()
            credentials.refresh(request)
        
        # Check again after refresh
        if not credentials.valid:
            current_app.logger.error("Credentials are still invalid after refresh")
            return None
        
        if credentials.token:
            # Cache the credentials and token in app context
            current_app.token_cache['credentials'] = credentials
            current_app.token_cache['token'] = credentials.token
            
            # Handle case where expiry might be None
            if hasattr(credentials, 'expiry') and credentials.expiry:
                current_app.token_cache['expiry'] = credentials.expiry.timestamp() - 60  # 60 seconds buffer
            else:
                # Set expiry to 1 hour from now if not available
                current_app.token_cache['expiry'] = time.time() + 3600 - 60
            
            current_app.logger.info("Successfully obtained token from default credentials")
            return credentials.token
        else:
            current_app.logger.error("Default credentials returned no token")
            
    except Exception as e:
        current_app.logger.error(f"Could not get token from default credentials: {str(e)}")
        
    return None
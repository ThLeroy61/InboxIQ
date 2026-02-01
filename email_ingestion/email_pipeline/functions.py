# functions.py
from msal import PublicClientApplication
import os

CLIENT_ID = os.environ.get("CLIENT_ID")
TENANT_ID = os.environ.get("TENANT_ID")

AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["https://graph.microsoft.com/Mail.ReadWrite"]  # lecture/écriture mails[web:62]

# Chemin pour stocker le cache de token
TOKEN_CACHE_FILE = "/opt/email_ingestion/email_pipeline/token_cache.json"

def get_token():
    import json
    from pathlib import Path
    
    token_file = Path(__file__).parent / "token.json"
    
    with open(token_file, "r") as f:
        token_data = json.load(f)
    
    app = PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY
    )
    
    result = app.acquire_token_by_refresh_token(
        token_data["refresh_token"], 
        scopes=SCOPES
    )
    
    if "access_token" in result:
        return result["access_token"]
    
    raise Exception("Token refresh failed")


def get_headers():
    token = get_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
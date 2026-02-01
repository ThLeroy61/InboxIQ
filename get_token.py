from msal import PublicClientApplication
import json
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

CLIENT_ID = os.environ.get("CLIENT_ID")
AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["https://graph.microsoft.com/Mail.ReadWrite"]

app = PublicClientApplication(client_id=CLIENT_ID, authority=AUTHORITY)

# Ouvre un navigateur pour l'authentification
result = app.acquire_token_interactive(scopes=SCOPES)

if "access_token" in result:
    with open("token.json", "w") as f:
        json.dump(result, f)
    print("Token sauvegardé dans token.json")
else:
    print(f"Erreur: {result}")
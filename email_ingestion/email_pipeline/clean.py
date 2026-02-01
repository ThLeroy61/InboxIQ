import pymongo
from .check_mongo import get_clean, get_raw
import re
import string
import emoji

clean = get_clean()
raw = get_raw()

def clean_text(text):
    text = text.lower()
    text = emoji.replace_emoji(text, "")
    text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

print("Nettoyage des données en cours...")
count = 0

for doc in raw.find():
    clean_doc = {}
    for id, value in enumerate(doc):
        if value in ["_id", "received", "from", "labelled"]:
            clean_doc[value] = doc[value]
        else:
            clean_doc[value] = clean_text(doc[value])
    
    count += 1
    
    try :
        clean.insert_one(clean_doc)
    except pymongo.errors.DuplicateKeyError:
            continue
        
    if count % 50 == 0:
        print(f"{count} emails nettoyés et importés")

print(f"Fin du batch - Nettoyage de {count} données")    
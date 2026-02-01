# functions.py
from msal import PublicClientApplication
import requests
import pymongo

from .check_mongo import get_clean, get_raw
from .functions import get_headers

FOLDERS = {
    "Administratif": "AQMkADAwATY0MDABLWRiZDgtMDVmMy0wMAItMDAKAC4AAAMffFOp6s1-QYisQci0REv8AQB9r9o6MED6To2z1cMkWvcXAAmc_0nOAAAA",
    "Apprentissage & Veille": "AQMkADAwATY0MDABLWRiZDgtMDVmMy0wMAItMDAKAC4AAAMffFOp6s1-QYisQci0REv8AQB9r9o6MED6To2z1cMkWvcXAAmc_0nSAAAA",
    "Finances & Assurances": "AQMkADAwATY0MDABLWRiZDgtMDVmMy0wMAItMDAKAC4AAAMffFOp6s1-QYisQci0REv8AQB9r9o6MED6To2z1cMkWvcXAAmc_0nPAAAA",
    "Logement": "AQMkADAwATY0MDABLWRiZDgtMDVmMy0wMAItMDAKAC4AAAMffFOp6s1-QYisQci0REv8AQB9r9o6MED6To2z1cMkWvcXAAmc_0nQAAAA",
    "Loisirs": "AQMkADAwATY0MDABLWRiZDgtMDVmMy0wMAItMDAKAC4AAAMffFOp6s1-QYisQci0REv8AQB9r9o6MED6To2z1cMkWvcXAAmc_0nTAAAA",
    "Personnel": "AQMkADAwATY0MDABLWRiZDgtMDVmMy0wMAItMDAKAC4AAAMffFOp6s1-QYisQci0REv8AQB9r9o6MED6To2z1cMkWvcXAAmc_0nUAAAA",
    "Professionnel": "AQMkADAwATY0MDABLWRiZDgtMDVmMy0wMAItMDAKAC4AAAMffFOp6s1-QYisQci0REv8AQB9r9o6MED6To2z1cMkWvcXAAmc_0nRAAAA",
    "Booking": "AQMkADAwATY0MDABLWRiZDgtMDVmMy0wMAItMDAKAC4AAAMffFOp6s1-QYisQci0REv8AQB9r9o6MED6To2z1cMkWvcXAAewMnCiAAAA",
    "Archive": "AQMkADAwATY0MDABLWRiZDgtMDVmMy0wMAItMDAKAC4AAAMffFOp6s1-QYisQci0REv8AQB9r9o6MED6To2z1cMkWvcXAAS6qyQnAAAA",
    "Emploi": "AQMkADAwATY0MDABLWRiZDgtMDVmMy0wMAItMDAKAC4AAAMffFOp6s1-QYisQci0REv8AQB9r9o6MED6To2z1cMkWvcXAAmhYTOVAAAA",
    "Handball": "AQMkADAwATY0MDABLWRiZDgtMDVmMy0wMAItMDAKAC4AAAMffFOp6s1-QYisQci0REv8AQB9r9o6MED6To2z1cMkWvcXAAmhYTOaAAAA",
    "Supprimé": "AQMkADAwATY0MDABLWRiZDgtMDVmMy0wMAItMDAKAC4AAAMffFOp6s1-QYisQci0REv8AQB9r9o6MED6To2z1cMkWvcXAAmhYTOXAAAA"
}

FOLDER_BY_ID = {v: k for k, v in FOLDERS.items()}

def list_inbox_messages(top = 50, all_messages = False):
    headers = get_headers()

    #On récupère uniquement les premiers mails si all_messages est False
    if not all_messages:
        url = f"https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages?$top={top}"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        mails = resp.json()["value"]
        
    #Sinon, on boucle tant qu'on trouve un @odata.nextlink, qui fait office de pagination
    else:
        page_size = top
        url = f"https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages?$top={page_size}"
        mails = []
        nb_mails = 50

        while url:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            mails.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
            print(f"{nb_mails} mails traités...")
            nb_mails += 50

    return mails

def register_mail():
    collection = get_raw()
    
    print("Importation des emails...")
    emails = list_inbox_messages(top=50, all_messages=True)
    number_mail_batch = 0
    
    for email in emails:
        try:
            infos_mail = {
                "_id": email['id'],
                "from": email['from']['emailAddress']['address'],
                "subject": email['subject'],
                "received": email['receivedDateTime'],
                "content": email.get('bodyPreview', ""),
                "labelled": False,
                "label_ml": ""
            }
            collection.insert_one(infos_mail)
            print(f"Mail {email['id']} ajouté")
            number_mail_batch += 1
        except pymongo.errors.DuplicateKeyError:
            continue
    
    print(f"Batch traité : {number_mail_batch} mails importés")

def move_message(message_id, destination_folder_id):
    collection = get_clean()
    folder_name = FOLDER_BY_ID.get(destination_folder_id)

    collection.update_one(
        {"_id": message_id},
        {
            "$set": {
                "labelled": True,
                "label_ml": folder_name
            }
        }
    )

    #Se connecter à Mongo, met labelled à true puis ajouter le label : le choix dans la liste
    headers = get_headers()
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/move"
    data = {"destinationId": destination_folder_id}

    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code in [200, 201]:
        moved = resp.json()
        print("Mail déplacé avec succès !")
        print("Nouveau parentFolderId:", moved["parentFolderId"])
        return moved
    else:
        print("Erreur déplacement:", resp.status_code, resp.text)
        resp.raise_for_status()

def delete_message(message_id):
    collection = get_clean()

    collection.update_one(
        {"_id": message_id},
        {
            "$set": {
                "labelled": True,
                "label_ml": "Supprimé"
            }
        }
    )

    headers = get_headers()
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/move"
    data = {"destinationId": "AQMkADAwATY0MDABLWRiZDgtMDVmMy0wMAItMDAKAC4AAAMffFOp6s1-QYisQci0REv8AQB9r9o6MED6To2z1cMkWvcXAAmhYTOXAAAA"}

    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code in [200, 201]:
        moved = resp.json()
        print("Mail supprimé avec succès !")
        return moved
    else:
        print("Erreur déplacement:", resp.status_code, resp.text)
        resp.raise_for_status()
    

##### Si besoin de lister les dossiers dans la boîte de réception #####


# def get_inbox_child_folders():
#     headers = get_headers()
#     url = "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/childFolders"  # childFolders Inbox[web:43]
#     resp = requests.get(url, headers=headers)
#     resp.raise_for_status()
#     folders = resp.json()["value"]

#     print("\n=== Sous-dossiers de Inbox ===")
#     for f in folders:
#         print(f"- {f['displayName']} (ID: {f['id']})")

#     return folders

# print(get_inbox_child_folders())
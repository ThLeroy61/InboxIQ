import streamlit as st
from datetime import date
from train_ml.data import get_sample_mongo
from train_ml.model import train_and_save_model, predict_folder
from email_ingestion.email_pipeline import mail
import math

train_and_save_model()

st.set_page_config(layout="wide")
st.title("Tri email Outlook")

if "toast" in st.session_state:
    msg, icon = st.session_state["toast"]
    st.toast(msg, icon=icon)          # s'affiche après le rerun [web:67][web:72]
    del st.session_state["toast"]

if "batch_emails" not in st.session_state:
    st.session_state["batch_emails"] = get_sample_mongo(50)

THRESHOLD_AUTO_MOVE = 0.4

# 1) auto-move d'abord
auto_moved_ids = []
batch_emails = st.session_state["batch_emails"]

for email in list(batch_emails):
    pred, proba = predict_folder(email["from"], email["subject"], email["content"])
    if proba >= THRESHOLD_AUTO_MOVE:
        destination_id = mail.FOLDERS[pred]
        mail.move_message(email["_id"], destination_id)
        auto_moved_ids.append(email["_id"])

if auto_moved_ids:
    st.session_state["batch_emails"] = [
        e for e in batch_emails if e["_id"] not in auto_moved_ids
    ]
    st.session_state["toast"] = (
        f"{len(auto_moved_ids)} emails déplacés automatiquement ✅",
        "✅",
    )
    st.rerun()

for i, email in enumerate(batch_emails):
    pred, proba = predict_folder(email["from"], email["subject"], email["content"])
    
    col_left, col_center, col_right = st.columns([7, 2, 1])
    
    with col_left:
        st.write("From", email['from'])
        st.write("Sujet", email['subject'])
        st.write("Contenu", email['content'])
        "---"
    
    with col_center:
        st.write("Proposition modèle : ", pred, " (", math.floor(proba * 100), "%)")

    with col_right:
        key_name = f"folder_{i}"
        
        if key_name not in st.session_state:
            st.session_state[key_name] = list(mail.FOLDERS.keys())[0]  # valeur par défaut
            
        choix = st.selectbox("Dossier",
                            list(mail.FOLDERS.keys()),
                            key=key_name)
        
        if st.button('Valider', key=f"validate_{i}"):
            destination_id = mail.FOLDERS[st.session_state[key_name]]
            mail.move_message(email["_id"], destination_id)
            st.session_state["toast"] = ("Email déplacé !", "✅")  # Toast natif [web:60]
            st.session_state["batch_emails"] = [
                e for e in st.session_state["batch_emails"]
                if e["_id"] != email["_id"]
            ]
            st.rerun()
        
        if st.button("Supprimer", key=f"ignore_{i}"):
            mail.delete_message(email["_id"])
            st.toast("🗑️ Email supprimé !", icon="🗑️")  # Toast natif [web:60]
            st.session_state["batch_emails"] = [
                e for e in st.session_state["batch_emails"]
                if e["_id"] != email["_id"]
            ]
            st.session_state["toast"] = ("Email supprimé !", "🗑️")
            st.rerun()
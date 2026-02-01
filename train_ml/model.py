import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from .data import get_labelised_mails
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pandas as pd
from nltk.corpus import stopwords
import joblib
from email_ingestion.email_pipeline.check_mongo import count_labelled_mails, get_ml_infos
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

stop_fr = stopwords.words('french')
MODEL_PATH = "email_model.pkl"

def train_and_save_model():
    ml_database = get_ml_infos()
    nb_mails = count_labelled_mails()
    if nb_mails % 50 != 0:
        return False
    
    if ml_database.find_one({"nb_mails": nb_mails}):
        return False
    
    df = pd.DataFrame(get_labelised_mails())
    
    for col in ['from', 'subject', 'content', 'label_ml']:
        df[col] = df[col].fillna('')
    
    df['text'] = df['from'] + " " + df['subject'] + " " + df['content']

    texts = df['text']
    labels = df['label_ml']
    
    # split + reset_index pour avoir des index propres et alignés
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    X_train = X_train.reset_index(drop=True)
    X_test = X_test.reset_index(drop=True)
    y_train = y_train.reset_index(drop=True)
    y_test = y_test.reset_index(drop=True)

    vectorizer = TfidfVectorizer(
        max_features=5000,
        stop_words=stop_fr,
        token_pattern=r'(?u)\b[^\d\W]\w+\b'
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    modele = LogisticRegression(
        multi_class='multinomial',
        class_weight='balanced',
        max_iter=200
    )
    modele.fit(X_train_vec, y_train)
    
    y_pred = modele.predict(X_test_vec)
    f1 = f1_score(y_test, y_pred, average="macro")
    print("F1 global:", f1)

    # F1 par dossier sur le test
    folder_f1_scores = {}
    for folder_name in y_test.unique():
        mask = (y_test == folder_name)
        support = int(mask.sum())
        if support < 7:
            continue

        y_true_folder = y_test[mask]           # OK, mêmes index
        y_pred_folder = y_pred[mask.to_numpy()]  # mask transformé en array pour indexer y_pred

        f1_folder = f1_score(y_true_folder, y_pred_folder, average="macro")
        folder_f1_scores[folder_name] = {"folder": f1_folder, "support": support}

    
    ml_database.insert_one({
        "nb_mails": nb_mails,
        "f1_score": f1,
        "f1_folder": folder_f1_scores,
    })
    
    joblib.dump({"vectorizer": vectorizer, "model": modele}, MODEL_PATH)
    return True

def load_model():
    data = joblib.load(MODEL_PATH)
    return data["vectorizer"], data["model"]

def predict_folder(from_field, subject, content):
    vectorizer, modele = load_model()
    
    text = f"{from_field} {subject} {content}"
    
    X = vectorizer.transform([text])
    
    pred = modele.predict(X)[0]
    proba = modele.predict_proba(X).max()
    
    return pred, proba

def get_ml_data():
    collection_ml = get_ml_infos()
    return pd.DataFrame(list(collection_ml.find({})))
from dotenv import load_dotenv, find_dotenv
import os
import pymongo

load_dotenv(find_dotenv())

MONGO_URI = os.environ.get("MONGO_URI")
MONGO_RAW = os.environ.get("MONGO_RAW_DATA")
MONGO_CLEAN = os.environ.get("MONGO_CLEAN_DATA")
MONGO_DB = os.environ.get("MONGO_DB")
MONGO_ML = os.environ.get("MONGO_ML_TRAIN")

def get_mongo():
    mongo_client = pymongo.MongoClient(MONGO_URI)
    return mongo_client[MONGO_DB]

def get_raw():
    db = get_mongo()
    return db[MONGO_RAW]

def get_clean():
    db = get_mongo()
    return db[MONGO_CLEAN]

def count_labelled_mails():
    data = get_clean()
    return data.count_documents({"labelled": True})

def get_ml_infos():
    db = get_mongo()
    return db[MONGO_ML]
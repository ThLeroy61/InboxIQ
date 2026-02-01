from email_ingestion.email_pipeline.check_mongo import get_clean, get_ml_infos

collection_clean = get_clean()
collection_ml = get_ml_infos()

def get_sample_mongo(nb):
    
    pipeline = [
        {"$match": {"labelled": False}},
        {"$sample": {"size": nb}}
    ]
    
    return list(collection_clean.aggregate(pipeline))

def get_labelised_mails():
        
    pipeline = [
        {"$match": {"labelled": True}}
    ]
    
    return list(collection_clean.aggregate(pipeline))

def get_ml_infos():
    return list(collection_ml.find())
from pymongo import MongoClient
from utils import config


def insert_reference(publication):
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client.publications
    collection = db.references
    publication['_class'] = config.get('DEFAULT', 'CLASS_PATH')
    return collection.insert_one(publication).inserted_id


def insert_all(references):
    for reference in references:
        reference['_class'] = config.get('DEFAULT', 'CLASS_PATH')
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client.publications
    collection = db.references
    return collection.insert_many(references)


def get_impc_papers():
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client.publications
    collection = db.references
    return collection.find({'consortiumPaper': True})


def exist(pmid):
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client.publications
    collection = db.references
    return collection.find_one({'pmid': str(pmid)}) is not None


def get_existing_pmids():
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client.publications
    collection = db.references
    return [result['pmid'] for result in collection.find({}, {'pmid': 1})]


def get_by_pmid(pmid):
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client.publications
    collection = db.references
    return collection.find_one({'pmid': pmid})


def delete_by_pmid(pmid):
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client.publications
    collection = db.references
    return collection.delete_one({'pmid': pmid})
from pymongo import MongoClient, TEXT
from utils import config
import datetime


def insert_reference(publication):
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    collection = db[config.get('DEFAULT', 'MONGO_REFERENCES_COLLECTION')]
    publication['_class'] = config.get('DEFAULT', 'CLASS_PATH')
    return collection.insert_one(publication).inserted_id


def insert_all(references, collection=None, class_path=None):
    class_path = config.get('DEFAULT', 'CLASS_PATH') if class_path is None else class_path
    for reference in references:
        reference['_class'] = class_path
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    collection = config.get('DEFAULT',
                            'MONGO_REFERENCES_COLLECTION') if collection is None else collection
    collection = db[collection]
    return collection.insert_many(references)


def get_impc_papers():
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    collection = db[config.get('DEFAULT', 'MONGO_REFERENCES_COLLECTION')]
    return collection.find({'consortiumPaper': True})


def exist(pmid):
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    collection = db[config.get('DEFAULT', 'MONGO_REFERENCES_COLLECTION')]
    return collection.find_one({'pmid': str(pmid)}) is not None


def get_existing_pmids():
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    collection = db[config.get('DEFAULT', 'MONGO_REFERENCES_COLLECTION')]
    return [result['pmid'] for result in collection.find({}, {'pmid': 1})]


def get_all():
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    collection = db[config.get('DEFAULT', 'MONGO_REFERENCES_COLLECTION')]
    return [result for result in collection.find({})]


def get_by_pmid(pmid):
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    collection = db[config.get('DEFAULT', 'MONGO_REFERENCES_COLLECTION')]
    return collection.find_one({'pmid': str(pmid)})


def update_by_pmid(pmid, changes):
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    collection = db[config.get('DEFAULT', 'MONGO_REFERENCES_COLLECTION')]
    collection.update_one({'pmid': pmid}, {'$set': changes})


def delete_by_pmid(pmid):
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    collection = db[config.get('DEFAULT', 'MONGO_REFERENCES_COLLECTION')]
    return collection.delete_one({'pmid': pmid})


def create_text_index(field, name):
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    collection = db[config.get('DEFAULT', 'MONGO_ALLELES_COLLECTION')]
    collection.create_index([(field, TEXT)], name=name,
                            default_language='english')


def drop_collection(collection_name):
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    db.drop_collection(collection_name)


def get_by_allele_symbol(allele_symbol):
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    collection = db[config.get('DEFAULT', 'MONGO_ALLELES_COLLECTION')]
    allele = collection.find_one({'alleleSymbol': allele_symbol})
    if allele is None:
        allele = {'alleleSymbol': allele_symbol, 'alleleName': '', 'acc': '', 'gacc': '',
                  'geneSymbol': '', 'project': ''}
    else:
        allele.pop('_id')
    return allele


def get_by_date_before():
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    collection = db[config.get('DEFAULT', 'MONGO_REFERENCES_COLLECTION')]
    return [result for result in collection.find({"status": "reviewed", "firstPublicationDate": {
        "$lte": datetime.datetime.strptime("2018-10-10", "%Y-%m-%d")}})]


def get_by_date_after():
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    collection = db[config.get('DEFAULT', 'MONGO_REFERENCES_COLLECTION')]
    return [result for result in collection.find({"status": "reviewed", "firstPublicationDate": {
        "$gt": datetime.datetime.strptime("2018-10-10T00:00:00.000+0000", "%Y-%m-%dT%H:%M:%S%z")}})]


def affiliation_exists(pmid):
    client = MongoClient(config.get('DEFAULT', 'MONGO_DATASOURCE_URL'))
    db = client[config.get('DEFAULT', 'MONGO_DATABASE')]
    collection = db[config.get('DEFAULT', 'MONGO_AFFILIATIONS_COLLECTION')]
    return collection.find_one({'pmid': str(pmid)}) is not None
from typing import List, Dict
from utils import solr_access, mongo_access, config

import csv


def get_alleles_from_file(file_path) -> Dict:
    alleles = {}
    with open(file_path) as f:
        for row in csv.DictReader(f, skipinitialspace=True):
            allele = {k: v for k, v in row.items()}
            alleles[allele["alleleSymbol"]] = allele
    return alleles


def get_alleles_from_solr() -> Dict:
    return solr_access.get_all_alleles()


def load_alleles(allele_list: List[Dict]):
    mongo_access.insert_all(
        allele_list,
        config.get("DEFAULT", "MONGO_ALLELES_COLLECTION"),
        "org.impc.publications.models.Allele",
    )
    return True


def create_allele_index():
    mongo_access.create_text_index("alleleSymbol", "allele_search")


def drop_alleles_collection():
    mongo_access.drop_collection("alleles")


def load_all():
    # solr_alleles = get_alleles_from_solr()
    # print(len(solr_alleles))
    emma_alleles = get_alleles_from_file(config.get("DEFAULT", "LOAD_ALLELE_FILE"))
    # for emma_allele in emma_alleles.values():
    #     if emma_allele['alleleSymbol'] not in solr_alleles:
    #         solr_alleles[emma_allele['alleleSymbol']] = emma_allele

    alleles = emma_alleles.values()
    # print(len(alleles))
    drop_alleles_collection()
    load_alleles(alleles)
    create_allele_index()

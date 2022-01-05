import csv

from utils.mongo_access import get_by_pmid, update_by_pmid
from utils.solr_access import resolve_allele


def add_alleles_from_file(allele_publication_file: str):
    with open(allele_publication_file) as f:
        allele_publication_list = [
            {k: str(v) for k, v in row.items()}
            for row in csv.DictReader(f, skipinitialspace=True)
        ]
    allele_x_publication = {}

    for allele in allele_publication_list:
        pmid = allele["PMID"].replace("PMID: ", "")
        if pmid not in allele_x_publication:
            allele_x_publication[pmid] = []
        allele_x_publication[pmid].append(allele["Allele_symbol"])

    for pmid, allele_list in allele_x_publication.items():
        print(f"Processing {pmid}")
        reference = get_by_pmid(pmid)
        current_alleles = (
            [a["alleleSymbol"] for a in reference["alleles"]]
            if reference["alleles"] is not None
            else []
        )
        for allele_symbol in allele_list:
            if allele_symbol not in current_alleles:
                allele_ref = resolve_allele(allele_symbol)
                reference["alleles"].append(allele_ref)
        update_by_pmid(pmid, reference)
        print(f"Finished {pmid}, {len(allele_list)} added")
    return


if __name__ == "__main__":
    add_alleles_from_file("docs/impc_pub_allele_list.csv")

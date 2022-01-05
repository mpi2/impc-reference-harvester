import pysolr
from utils import config
from solrq import Q

solr = pysolr.Solr(config.get("DEFAULT", "ALLELE2_SOLR"))


def resolve_allele(allele_symbol):
    results = []
    if allele_symbol != "":
        query = Q(allele_symbol=allele_symbol)
        results = solr.search(query, rows=1)
    allele = dict()
    allele["alleleSymbol"] = allele_symbol
    allele["geneSymbol"] = ""
    allele["project"] = ""
    allele["alleleName"] = ""
    allele["acc"] = ""
    allele["gacc"] = ""
    allele["orderId"] = ""
    allele["emmaId"] = ""
    allele["_class"] = "org.impc.publications.models.Allele"
    if len(results) > 0 and allele_symbol != "":
        solr_allele = results.docs[0]
        result = _map_solr_allele(solr_allele)
        for key, value in result.items():
            if value is not None:
                allele[key] = value
    return allele


def get_all_alleles():
    query = Q(type="Allele")
    results = solr.search(query, rows=2147483647)
    alleles = {}
    for solr_allele in results.docs:
        allele = _map_solr_allele(solr_allele)
        allele["orderId"] = ""
        allele["emmaId"] = ""
        alleles[allele["alleleSymbol"]] = allele
    return alleles


def _map_solr_allele(solr_allele):
    return dict(
        _class="org.impc.publications.models.Allele",
        acc=solr_allele["allele_mgi_accession_id"]
        if "allele_mgi_accession_id" in solr_allele
        else None,
        gacc=solr_allele["mgi_accession_id"]
        if "mgi_accession_id" in solr_allele
        else None,
        geneSymbol=solr_allele["marker_symbol"]
        if "marker_symbol" in solr_allele
        else None,
        alleleSymbol=solr_allele["allele_symbol"]
        if "allele_symbol" in solr_allele
        else None,
        alleleName=solr_allele["allele_name"] if "allele_name" in solr_allele else None,
        project=solr_allele["allele_design_project"]
        if "allele_design_project" in solr_allele
        else None,
    )

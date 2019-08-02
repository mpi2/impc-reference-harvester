import pysolr
from utils import config
from solrq import Q

solr = pysolr.Solr(config.get('DEFAULT', 'ALLELE2_SOLR'))


def resolve_allele(allele_symbol):
    query = Q(allele_symbol=allele_symbol)
    results = solr.search(query, rows=1)
    allele = dict()
    allele['alleleSymbol'] = allele_symbol
    allele['geneSymbol'] = allele_symbol.split('<')[0]
    allele['project'] = allele_symbol.split('(')[1].split(')')[0]
    allele['alleleName'] = allele_symbol.split('<')[1].split('>')[0]
    allele['acc'] = ''
    allele['gacc'] = ''
    if len(results) > 0:
        result = results.docs[0]
        allele['acc'] = result[
            'allele_mgi_accession_id'] if 'allele_mgi_accession_id' in result else ''
        allele['gacc'] = result['mgi_accession_id'] if 'mgi_accession_id' in result else ''
    return allele


def get_all_alleles():
    query = Q(type='Allele')
    results = solr.search(query, rows=2147483647)
    alleles = {}
    for solr_allele in results.docs:
        allele = dict(acc=solr_allele[
            'allele_mgi_accession_id'] if 'allele_mgi_accession_id' in solr_allele else None,
                      gacc=solr_allele[
                          'mgi_accession_id'] if 'mgi_accession_id' in solr_allele else None,
                      geneSymbol=solr_allele[
                          'marker_symbol'] if 'marker_symbol' in solr_allele else None,
                      alleleSymbol=solr_allele[
                          'allele_symbol'] if 'allele_symbol' in solr_allele else None,
                      alleleName=solr_allele[
                          'allele_name'] if 'allele_name' in solr_allele else None,
                      project=solr_allele[
                          'allele_design_project'] if 'allele_design_project' in solr_allele else None)
        alleles[allele['alleleSymbol']] = allele
    return alleles

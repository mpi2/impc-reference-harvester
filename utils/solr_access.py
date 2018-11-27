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
        allele['acc'] = result['allele_mgi_accession_id'] if 'allele_mgi_accession_id' in result else ''
        allele['gacc'] = result['mgi_accession_id'] if 'mgi_accession_id' in result else ''
    return allele

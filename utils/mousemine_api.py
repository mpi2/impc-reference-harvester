from utils import config, logger
from intermine.webservice import Service
from bs4 import BeautifulSoup
from tqdm import tqdm


def get_mousemine_references_from_webservice():
    service_name = config.get('DEFAULT', 'MOUSE_MINER_URL')
    service = Service(service_name)
    query = service.new_query(config.get('DEFAULT', 'MOUSEMINE_SERVICE'))

    query_soup = BeautifulSoup(open(config.get('DEFAULT', 'MOUSEMINE_QUERY_PATH')), 'lxml')
    query_element = query_soup.find('query')
    query.add_view(query_element['view'])
    for constraint_element in query_element.find_all('constraint'):
        constraint_name = constraint_element['path'].replace(service_name + '.', '')
        query.add_constraint(constraint_name, constraint_element['op'],
                             constraint_element['value'],
                             code=constraint_element['code'])
    query.set_logic(query_element['constraintlogic'])
    alleles = []
    for row in tqdm(query.rows()):
        result = parse_result_row(row)
        alleles.append(result)
    return alleles


def parse_result_row(result):
    result_dict = dict()
    result_dict['pmid'] = result['publications.pubMedId']
    result_dict['acc'] = result['primaryIdentifier']
    result_dict['gacc'] = result['feature.primaryIdentifier']
    result_dict['gene_symbol'] = result['feature.symbol']
    result_dict['project'] = result['projectCollection']
    result_dict['allele_name'] = result['name']
    result_dict['allele_symbol'] = result['symbol']
    result_dict['source'] = 'mousemine'
    return result_dict


def get_pmid2alleles_map(alleles):
    pmid2alleles_map = dict()
    for allele in tqdm(alleles):
        pmid = allele.pop('pmid')
        allele_symbol = allele.pop('allele_symbol')
        allele['alleleSymbol'] = allele_symbol
        if pmid not in pmid2alleles_map:
            pmid2alleles_map[pmid] = []
        pmid2alleles_map[pmid].append(allele)
    return pmid2alleles_map


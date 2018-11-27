import requests
from utils import config, logger
import json
import urllib.parse
from datetime import datetime


def get_papers_by_keyword(keyword):
    europmc_url = config.get('DEFAULT', 'EUROPE_PMC_SERVICE_URL')
    europmc_query = config.get('DEFAULT', 'EUROPE_PMC_KEYWORDS_QUERY').format(keyword=keyword)
    europmc_rq_url = europmc_url + urllib.parse.quote_plus(europmc_query)
    europmc_results = execute_query_all(europmc_rq_url)
    europmc_results = [{'keyword': keyword, 'source': 'europmc', **parse_result(r)} for r in europmc_results]
    return europmc_results


def get_citing_papers(pmid):
    europmc_url = config.get('DEFAULT', 'EUROPE_PMC_SERVICE_URL')
    europmc_query = config.get('DEFAULT', 'EUROPE_PMC_CITES_QUERY').format(pmid=pmid)
    europmc_rq_url = europmc_url + urllib.parse.quote_plus(europmc_query)
    europmc_results = execute_query_all(europmc_rq_url)
    europmc_results = [{'cites': [pmid], 'source': 'europmc', **parse_result(r)} for r in europmc_results]
    return europmc_results


def get_paper_by_pmid(pmid):
    europmc_url = config.get('DEFAULT', 'EUROPE_PMC_SERVICE_URL')
    europmc_query = config.get('DEFAULT', 'EUROPE_PMC_PMID_QUERY').format(pmid=pmid)
    europmc_rq_url = europmc_url + urllib.parse.quote_plus(europmc_query)
    results = execute_query(europmc_rq_url)['resultList']['result']
    paper = results[0] if len(results) > 0 else {}
    return parse_result(paper)


def execute_query(query, cursor_mark='%2A'):
    europmc_results = None
    europmc_opts = config.get('DEFAULT', 'EUROPE_PMC_QUERY_OPTS').format(cursor=cursor_mark)
    rq_url = query + europmc_opts
    try:
        logger.info("EuroPMC query started: " + rq_url)
        europmc_results_json = requests.get(rq_url).text
        europmc_results = json.loads(europmc_results_json)
        logger.info("EuroPMC query finished")
    except Exception:
        logger.error("EuroPMC query failed: " + rq_url)
    return europmc_results


def execute_query_all(rq_url):
    cursor_mark = '%2A'
    done = False
    results = []
    while not done:
        page_result = execute_query(rq_url, cursor_mark)
        results.extend(page_result['resultList']['result'])
        done = cursor_mark == page_result['nextCursorMark']
        cursor_mark = page_result['nextCursorMark']
    return results


def parse_result(reference):
    author_list = reference.pop('authorList') if 'authorList' in reference else []
    reference['authorList'] = author_list['author'] if not type(author_list) == list else author_list
    grant_list = reference.pop('grantsList') if 'grantsList' in reference else []
    reference['grantsList'] = grant_list['grant'] if 'grant' in grant_list else grant_list
    full_text_url_list = reference.pop('fullTextUrlList') if 'fullTextUrlList' in reference else []
    reference['fullTextUrlList'] = full_text_url_list['fullTextUrl'] if 'fullTextUrl' in full_text_url_list else full_text_url_list
    mesh_heading_list = reference.pop('meshHeadingList') if 'meshHeadingList' in reference else []
    mesh_heading_list = mesh_heading_list['meshHeading'] if 'meshHeading' in mesh_heading_list else mesh_heading_list
    mesh_heading_list = [mesh_term['descriptorName'] for mesh_term in mesh_heading_list]
    reference['meshHeadingList'] = mesh_heading_list
    reference['firstPublicationDate'] = datetime.strptime(reference['firstPublicationDate'], '%Y-%m-%d')
    return reference

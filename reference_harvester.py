import click
from docs.impc_header import header
from utils import mousemine_api, europe_pmc_api, mongo_access, config, nlp
import tqdm
from joblib import Parallel, delayed


@click.command()
def harvest():
    """Command line application to harvest publications that cite or contain IMPC data resources"""
    existing_pmids = mongo_access.get_existing_pmids()
    click.secho(header, fg='yellow', bold=True)
    click.secho("Execute Mousemine query", fg='blue')
    alleles = mousemine_api.get_mousemine_references_from_webservice()
    click.secho("Group results by PMID", fg='blue')
    grouped_alleles = mousemine_api.get_pmid2alleles_map(alleles)
    mousemine_references = []
    for pmid, alleles in grouped_alleles.items():
        if pmid in existing_pmids:
            continue
        bibliographic_data = europe_pmc_api.get_paper_by_pmid(pmid)
        mousemine_reference = {'alleles': alleles, 'reviewed': True, 'falsePositive': False,
                               'datasource': 'mousemine', 'consortiumPaper': False, 'citations': [],
                               'cites': [], 'alleleCandidates': [], 'citedBy': [], **bibliographic_data}
        mousemine_references.append(mousemine_reference)
        existing_pmids.append(pmid)

    citing_consortium_papers_index = {}
    consortium_papers = mongo_access.get_impc_papers()
    for paper in consortium_papers:
        for citing_paper in europe_pmc_api.get_citing_papers(paper['pmid']):
            if citing_paper['pmid'] in existing_pmids:
                continue
            if citing_paper['pmid'] not in citing_consortium_papers_index:
                citing_consortium_papers_index[citing_paper['pmid']] = {'reviewed': False, 'alleles': [],
                                                                        'falsePositive': False,
                                                                        'datasource': 'europepmc',
                                                                        'consortiumPaper': False,
                                                                        'citations': [],
                                                                        'citedBy': [],
                                                                        'alleleCandidates': [], **citing_paper}
            else:
                citing_consortium_papers_index[citing_paper['pmid']]['cites'].append(paper['pmid'])
            existing_pmids.append(citing_paper['pmid'])
    citing_consortium_papers = [paper for paper in citing_consortium_papers_index.values()]

    search_results = []
    europe_pmc_papers = []
    for keyword in config.get('DEFAULT', 'TARGET_KEYWORDS').split(','):
        search_results.extend(europe_pmc_api.get_papers_by_keyword(keyword))
    for index, paper in enumerate(search_results):
        if paper['pmid'] in existing_pmids:
            continue
        europe_pmc_papers.append({'reviewed': False, 'alleles': [], 'falsePositive': False,
                                  'datasource': 'europepmc', 'consortiumPaper': False,
                                  'citations': [], 'cites': [], 'citedBy': [], 'alleleCandidates': [], **paper})
        existing_pmids.append(paper['pmid'])

    click.secho("Found {} new references in Mousemine".format(len(mousemine_references)), fg='green', bold=True)
    click.secho("Found {} new references in EuroPMC".format(len(europe_pmc_papers)), fg='green', bold=True)
    click.secho("Found {} new references in EuroPMC citing Consortium papers".format(len(citing_consortium_papers)), fg='green', bold=True)
    for reference in mousemine_references + europe_pmc_papers + citing_consortium_papers:
        existing_reference = mongo_access.get_by_pmid(reference['pmid'])
        if existing_reference:
            if existing_reference['datasource'] == 'manual' and reference['datasource'] == 'mousemine':
                mongo_access.delete_by_pmid(existing_reference['pmid'])

    all_references = mousemine_references + europe_pmc_papers + citing_consortium_papers
    click.secho("NLP Processing", fg='blue')
    all_references_processed = Parallel(n_jobs=8)(delayed(nlp.get_fragments)(reference) for reference in all_references)
    if len(all_references_processed) > 0:
        mongo_access.insert_all(all_references_processed)
    click.secho("Finished", fg='blue')


if __name__ == '__main__':
    harvest()

import click
from docs.impc_header import header
from utils import mousemine_api, europe_pmc_api, mongo_access, config, nlp, allele_importer
from joblib import Parallel, delayed
from itertools import chain
from tqdm import tqdm
import csv


@click.command()
@click.option('--use-mousemine', '-m', is_flag=True, help="Use mousemine.")
@click.option('--use-alleles', '-a', is_flag=True, help="Use alleles file.")
@click.option('--use-consortium-citations', '-c', is_flag=True, help="Use alleles file.")
@click.option('--add_order_id', '-o', is_flag=True, help="Import order ids.")
@click.option('--load-reviewed-pmids', '-p', is_flag=True, help="Load pmids from file.")
@click.option('--import-alleles', '-i', is_flag=True, help="Import load alleles file.")
def harvest(use_mousemine, use_alleles, use_consortium_citations, add_order_id, load_reviewed_pmids,
            import_alleles):
    """Command line application to harvest publications that cite or contain IMPC data resources"""
    existing_pmids = mongo_access.get_existing_pmids()
    click.secho(header, fg='yellow', bold=True)
    update_exisiting_papers = True
    reviewed_references = []
    mousemine_references = []
    update_papers = []
    update_pmids = []

    if import_alleles:
        allele_importer.load_all()

    if load_reviewed_pmids:
        with open(config.get('DEFAULT', 'LOAD_PMIDS_FILE')) as f:
            content = f.readlines()
            for line in content:
                pmid = line.strip()
                if update_exisiting_papers and pmid in existing_pmids:
                    if pmid not in update_pmids:
                        paper = mongo_access.get_by_pmid(pmid)
                        update_papers.append(paper)
                        update_pmids.append(pmid)
                    continue
                bibliographic_data = europe_pmc_api.get_paper_by_pmid(pmid)
                reviewed_reference = dict(
                    chain({'alleles': [], 'reviewed': True, 'falsePositive': False,
                           'datasource': 'manual', 'consortiumPaper': False, 'citations': [],
                           'cites': [], 'alleleCandidates': [], 'citedBy': [],
                           'pendingEmailConfirmation': False, 'orderId': None}.items(),
                          bibliographic_data.items()))
                reviewed_references.append(reviewed_reference)

    if use_mousemine:
        click.secho("Execute Mousemine query", fg='blue')
        alleles = mousemine_api.get_mousemine_references_from_webservice()
        click.secho("Group results by PMID", fg='blue')
        grouped_alleles = mousemine_api.get_pmid2alleles_map(alleles)

        for pmid, alleles in grouped_alleles.items():
            if update_exisiting_papers and pmid in existing_pmids:
                if pmid not in update_pmids:
                    paper = mongo_access.get_by_pmid(pmid)
                    update_papers.append(paper)
                    update_pmids.append(pmid)
                continue
            bibliographic_data = europe_pmc_api.get_paper_by_pmid(pmid)
            mousemine_reference = dict(
                chain({'alleles': alleles, 'reviewed': True, 'falsePositive': False,
                       'datasource': 'mousemine', 'consortiumPaper': False, 'citations': [],
                       'cites': [], 'alleleCandidates': [], 'citedBy': [],
                       'pendingEmailConfirmation': False, 'orderId': None}.items(),
                      bibliographic_data.items()))
            mousemine_references.append(mousemine_reference)

    citing_consortium_papers_index = {}
    citing_consortium_papers = []

    if use_consortium_citations:
        consortium_papers = mongo_access.get_impc_papers()
        for paper in consortium_papers:
            for citing_paper in europe_pmc_api.get_citing_papers(paper['pmid']):
                if update_exisiting_papers and citing_paper['pmid'] in existing_pmids:
                    if citing_paper['pmid'] not in update_pmids:
                        citing_paper = mongo_access.get_by_pmid(citing_paper['pmid'])
                        update_papers.append(citing_paper)
                        update_pmids.append(citing_paper['pmid'])
                    continue
                if citing_paper['pmid'] not in citing_consortium_papers_index:
                    citing_consortium_papers_index[citing_paper['pmid']] = dict(
                        chain({'reviewed': False, 'alleles': [],
                               'falsePositive': False,
                               'datasource': 'europepmc',
                               'consortiumPaper': False,
                               'pendingEmailConfirmation': False,
                               'citations': [],
                               'citedBy': [],
                               'alleleCandidates': [], 'orderId': None}.items(),
                              citing_paper.items()))
                else:
                    citing_consortium_papers_index[citing_paper['pmid']]['cites'].append(
                        paper['pmid'])
        citing_consortium_papers = [paper for paper in citing_consortium_papers_index.values()]

    search_results = []
    europe_pmc_papers = []
    alleles = None
    for keyword in config.get('DEFAULT', 'TARGET_KEYWORDS').split(','):
        search_results.extend(europe_pmc_api.get_papers_by_keyword(keyword))
    if use_alleles:
        with open(config.get('DEFAULT', 'TARGET_ALLELE_FILE')) as f:
            alleles = f.read().splitlines()
        for keyword in alleles:
            search_results.extend(europe_pmc_api.get_papers_by_keyword(keyword))

    for index, paper in enumerate(search_results):
        if update_exisiting_papers and paper['pmid'] in existing_pmids:
            if paper['pmid'] not in update_pmids:
                paper = mongo_access.get_by_pmid(paper['pmid'])
                update_papers.append(paper)
                update_pmids.append(paper['pmid'])
            continue
        else:
            europe_pmc_papers.append(dict(
                chain({'reviewed': False, 'alleles': [], 'falsePositive': False,
                       'datasource': 'europepmc', 'consortiumPaper': False,
                       'pendingEmailConfirmation': False,
                       'citations': [], 'cites': [], 'citedBy': [],
                       'alleleCandidates': [], 'orderId': None}.items(), paper.items())))

    click.secho("Found {} new references in Mousemine".format(len(mousemine_references)),
                fg='green', bold=True)
    click.secho("Found {} new references in EuroPMC".format(len(europe_pmc_papers)), fg='green',
                bold=True)
    click.secho("Found {} new references in EuroPMC citing Consortium papers".format(
        len(citing_consortium_papers)), fg='green', bold=True)
    all_raw_references = reviewed_references + mousemine_references + europe_pmc_papers
    all_raw_references += citing_consortium_papers
    for reference in all_raw_references:
        existing_reference = mongo_access.get_by_pmid(reference['pmid'])
        if existing_reference:
            if existing_reference['datasource'] in ['manual', 'europepmc'] and \
                    reference['datasource'] == 'mousemine':
                mongo_access.update_by_pmid(existing_reference['pmid'],
                                            {'alleles': reference['alleles'],
                                             'datasource': 'mousemine'})
    if add_order_id:
        with open(config.get('DEFAULT', 'ORDER_ID_FILE'), encoding='utf-8-sig') as f:
            csv_orders = [{k: v for k, v in row.items()}
                 for row in csv.DictReader(f, skipinitialspace=True)]
            pmid_order = {c['pubmed_id']: c['request_id'] for c in csv_orders}
        for ref in all_raw_references:
            ref['orderId'] = pmid_order[ref['pmid']] if ref['pmid'] in pmid_order else None

    all_references = reviewed_references + mousemine_references + europe_pmc_papers + citing_consortium_papers
    click.secho("NLP Processing", fg='blue')
    all_references_processed = Parallel(n_jobs=8)(
        delayed(nlp.get_fragments)(reference, alleles) for reference in tqdm(all_references))
    if len(all_references_processed) > 0:
        mongo_access.insert_all(all_references_processed)
    click.secho("Update NLP Processing for existing papers", fg='blue')
    update_references_processed = Parallel(n_jobs=8)(
        delayed(nlp.get_fragments)(reference, alleles) for reference in tqdm(update_papers))

    click.secho("Update existing papers in Mongodb", fg='blue')
    for reference in tqdm(update_references_processed):
        mongo_access.update_by_pmid(reference['pmid'],
                                    {'fragments': reference['fragments'],
                                     'citations': reference[
                                         'citations'] if 'citations' in reference else [],
                                     'alleleCandidates': reference['alleleCandidates'],
                                     'correspondence': reference[
                                         'correspondence'] if 'correspondence' in reference else []
                                     })
    click.secho("Update existing papers in Mongodb", fg='blue')
    click.secho("Finished", fg='blue')


if __name__ == '__main__':
    harvest()
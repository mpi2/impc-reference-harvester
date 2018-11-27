from utils import config, logger, komp2_api, europe_pmc_api as ea, mongo_access, nlp


def migrate_reviewed():
    reviewed_publications = komp2_api.get_reviewed()
    for publication in reviewed_publications:
        bibliographic_data = ea.get_paper_by_pmid(publication['pmid'])
        reference = {'reviewed': True, 'consortiumPaper': False, 'falsePositive': False,
                     'alleles': publication['alleles'], 'datasource': publication['datasource'],
                     'alleleCandidates': [], 'citedBy': [],
                     **bibliographic_data}
        reference = nlp.get_fragments(reference)
        mongo_access.insert_reference(reference)
    return True


def migrate_impc():
    impc_publications = komp2_api.get_impc_papers()
    for publication in impc_publications:
        bibliographic_data = ea.get_paper_by_pmid(publication['pmid'])
        reference = {'reviewed': True, 'alleles': publication['alleles'], 'falsePositive': False,
                     'datasource': publication['datasource'], 'consortiumPaper': True,
                     'alleleCandidates': [],
                     **bibliographic_data}
        reference = nlp.get_fragments(reference)
        reference['citedBy'] = [dict(url=citing['fullTextUrlList'][0]['url'],
                                     title=citing['title'],
                                     publicationDate=citing['firstPublicationDate'])
                                for citing in ea.get_citing_papers(publication['pmid'])]
        mongo_access.insert_reference(reference)
    return True


def migrate_falsepositive():
    impc_publications = komp2_api.get_falsepositive()
    for publication in impc_publications:
        bibliographic_data = ea.get_paper_by_pmid(publication['pmid'])
        reference = {'reviewed': True, 'alleles': publication['alleles'], 'falsePositive': True,
                     'datasource': publication['datasource'], 'consortiumPaper': False,
                     'alleleCandidates': [], 'citedBy': [],
                     **bibliographic_data}
        reference = nlp.get_fragments(reference)
        mongo_access.insert_reference(reference)
    return True


migrate_impc()
migrate_reviewed()
migrate_falsepositive()

from utils import config
from utils.models import Allele, Publication
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from tqdm import tqdm

engine = create_engine(config.get('DEFAULT', 'KOMP2_DATASOURCE'))
Session = sessionmaker(bind=engine)


def get_allele2gene_map():
    session = Session()
    allele_list = session.query(Allele).all().distinct()
    allele_gen_map = dict()
    for allele in tqdm(allele_list):
        allele_gen_map[allele.acc] = allele.gf_acc
    session.close()
    return allele_gen_map


def get_impc_papers():
    session = Session()
    publication_list = session.query(Publication)\
        .filter(Publication.consortium_paper == 'yes')\
        .filter(Publication.falsepositive == 'no').distinct()
    pmids = []
    pmid_index = []
    for publication in tqdm(publication_list):
        if publication.pmid in pmid_index:
            continue
        pmid_index.append(publication.pmid)
        alleles = get_alleles(publication)
        pmids.append(dict(pmid=publication.pmid, alleles=alleles, datasource=publication.datasource))
    session.close()
    return pmids


def get_reviewed():
    session = Session()
    publication_list = session.query(Publication).filter(Publication.reviewed == 'yes')\
        .filter(Publication.falsepositive == 'no') \
        .filter(Publication.consortium_paper == 'no') \
        .filter(Publication.datasource != 'mousemine').distinct()
    pmids = []
    pmid_index = []
    for publication in tqdm(publication_list):
        if publication.pmid in pmid_index:
            continue
        pmid_index.append(publication.pmid)
        alleles = get_alleles(publication)
        pmids.append(dict(pmid=publication.pmid, alleles=alleles, datasource=publication.datasource))
    session.close()
    return pmids


def get_falsepositive():
    session = Session()
    publication_list = session.query(Publication).filter(Publication.falsepositive == 'yes').distinct()
    pmids = []
    pmid_index = []
    for publication in tqdm(publication_list):
        if publication.pmid in pmid_index:
            continue
        pmid_index.append(publication.pmid)
        alleles = get_alleles(publication)
        pmids.append(dict(pmid=publication.pmid, alleles=alleles, datasource=publication.datasource))
    session.close()
    return pmids


def get_alleles(publication):
    alleles = []
    if publication.symbol != 'Not available' and publication.symbol != '' and publication.symbol != 'N/A':
        for index, symbol in enumerate(publication.symbol.split('|||')):
            allele = dict()
            allele['acc'] = publication.acc.split('|||')[index] if publication.acc else ''
            allele['gacc'] = publication.gacc.split('|||')[index] if publication.gacc else ''
            allele['geneSymbol'] = publication.symbol.split('<')[0]
            allele['project'] = publication.symbol.split('(')[1].split(')')[0]
            allele['alleleName'] = publication.name.split('|||')[index] if publication.name else ''
            allele['alleleSymbol'] = symbol
            allele['candidate'] = False
            alleles.append(allele)
    return alleles

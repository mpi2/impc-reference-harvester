from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.mysql import VARCHAR, TIMESTAMP

Base = declarative_base()


class Allele(Base):
    __tablename__ = 'allele'
    acc = Column(VARCHAR(30), primary_key=True)
    db_id = Column(Integer)
    gf_acc = Column(VARCHAR(20))
    gf_db_id = Column(Integer)
    biotype_acc = Column(VARCHAR(20))
    biotype_db_id = Column(Integer)
    symbol = Column(VARCHAR(100))
    name = Column(VARCHAR(200))

    def __repr__(self):
        return "<Allele(acc='%s', db_id='%s', gf_acc='%s')>" % (
            self.acc, self.db_id, self.gf_acc)


class Publication(Base):
    __tablename__ = 'allele_ref'
    dbid = Column(Integer, primary_key=True)
    gacc = Column(VARCHAR(200))
    acc = Column(VARCHAR(200))
    symbol = Column(VARCHAR(200))
    name = Column(VARCHAR(200))
    pmid = Column(Integer)
    date_of_publication = Column(VARCHAR(30))
    reviewed = Column(VARCHAR(3))
    grant_id = Column(VARCHAR(200))
    agency = Column(VARCHAR(200))
    acronym = Column(VARCHAR(200))
    title = Column(VARCHAR(200))
    journal = Column(VARCHAR(200))
    paper_url = Column(VARCHAR(200))
    datasource = Column(VARCHAR(200))
    timestamp = Column(TIMESTAMP(200))
    falsepositive = Column(VARCHAR(3))
    mesh = Column(VARCHAR(200))
    meshtree = Column(VARCHAR(200))
    author = Column(VARCHAR(200))
    consortium_paper = Column(VARCHAR(3))
    abstract = Column(VARCHAR(1000))
    cited_by = Column(VARCHAR(200))
    cites_consortium_paper = Column(VARCHAR(3))

    def __repr__(self):
        return "<Publication(pmid='%s', db_d='%s', symbol='%s')>" % (
            self.pmid, self.dbid, self.symbol)


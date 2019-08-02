from unittest import mock
from utils.komp2_api import get_allele2gene_map
from utils.models import Allele
import pytest
from sqlalchemy.exc import SQLAlchemyError


@mock.patch('utils.komp2_api.Session')
def test_get_allele2gene_map_one_allele(mock_session):
    test_allele = Allele()
    test_allele.acc = "MGI:4244706"
    test_allele.gf_acc = "MGI:1915571"
    mock_session.return_value.query(Allele).all.return_value = [test_allele]
    allele_gene_map = get_allele2gene_map()
    assert(allele_gene_map["MGI:4244706"] == "MGI:1915571")


@mock.patch('utils.komp2_api.Session')
def test_get_allele2gene_map_no_alleles(mock_session):
    mock_session.return_value.query(Allele).all.return_value = []
    allele_gene_map = get_allele2gene_map()
    assert(allele_gene_map == {})


@mock.patch('utils.komp2_api.Session')
def test_raises(mock_session):
    mock_session.return_value.query(Allele).all.side_effect = lambda: exec('raise(SQLAlchemyError("some info"))')
    with pytest.raises(Exception) as excinfo:
        get_allele2gene_map()
    assert str(excinfo.value) == 'some info'

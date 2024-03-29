import csv
from itertools import chain

import click
from joblib import Parallel, delayed
from tqdm import tqdm

from docs.impc_header import header
from utils import (
    mousemine_api,
    europe_pmc_api,
    mongo_access,
    config,
    nlp,
    allele_importer,
)
from utils.solr_access import resolve_allele


@click.command()
@click.option("--use-mousemine", "-m", is_flag=True, help="Use mousemine.")
@click.option("--use-alleles", "-a", is_flag=True, help="Use alleles file.")
@click.option(
    "--use-consortium-citations", "-c", is_flag=True, help="Use consortium citations."
)
@click.option("--add-order-id", "-o", is_flag=True, help="Import order ids.")
@click.option("--load-reviewed-pmids", "-p", is_flag=True, help="Load pmids from file.")
@click.option("--import-alleles", "-i", is_flag=True, help="Import load alleles file.")
@click.option("--use-infrafrontier-nlp", "-n", is_flag=True, help="Use Infrafrontier specific NLP.")
def harvest(
        use_mousemine,
        use_alleles,
        use_consortium_citations,
        add_order_id,
        load_reviewed_pmids,
        import_alleles,
        use_infrafrontier_nlp
):
    """Command line application to harvest publications that cite or contain IMPC data resources"""
    existing_pmids = mongo_access.get_existing_pmids()
    click.secho(header, fg="yellow", bold=True)
    update_exisiting_papers = True
    update_papers = []
    update_pmids = []
    harvested_references = {}
    keyword_harvest_count = 0
    citation_harvest_count = 0
    mousemine_harvest_count = 0

    if import_alleles:
        allele_importer.load_all()

    if load_reviewed_pmids:
        with open(config.get("DEFAULT", "LOAD_PMIDS_FILE")) as f:
            csv_orders = [
                {k: v for k, v in row.items()}
                for row in csv.DictReader(f, skipinitialspace=True)
            ]
            for line in csv_orders:
                pmid = line["PubMed ID"]
                if update_exisiting_papers and pmid in existing_pmids:
                    if pmid not in update_pmids:
                        paper = mongo_access.get_by_pmid(pmid)
                        paper["comment"] = line["comment"]
                        update_papers.append(paper)
                        update_pmids.append(pmid)
                    continue
                elif pmid in harvested_references:
                    continue
                bibliographic_data = europe_pmc_api.get_paper_by_pmid(pmid)
                reviewed_reference = dict(
                    chain(
                        {
                            "alleles": [],
                            "status": "reviewed",
                            "datasource": "manual",
                            "consortiumPaper": False,
                            "citations": [],
                            "cites": [],
                            "alleleCandidates": [],
                            "citedBy": [],
                            "comment": line["comment"],
                            "tags": [],
                        }.items(),
                        bibliographic_data.items(),
                    )
                )
                harvested_references[pmid] = reviewed_reference

    if use_mousemine:
        click.secho("Execute Mousemine query", fg="blue")
        alleles = mousemine_api.get_mousemine_references_from_webservice()
        click.secho("Group results by PMID", fg="blue")
        grouped_alleles = mousemine_api.get_pmid2alleles_map(alleles)

        for pmid, alleles in grouped_alleles.items():
            if update_exisiting_papers and pmid in existing_pmids:
                if pmid not in update_pmids:
                    paper = mongo_access.get_by_pmid(pmid)
                    update_papers.append(paper)
                    update_pmids.append(pmid)
                continue
            elif pmid in harvested_references:
                continue
            bibliographic_data = europe_pmc_api.get_paper_by_pmid(pmid)
            mousemine_reference = dict(
                chain(
                    {
                        "alleles": alleles,
                        "status": "reviewed",
                        "datasource": "mousemine",
                        "consortiumPaper": False,
                        "citations": [],
                        "cites": [],
                        "alleleCandidates": [],
                        "citedBy": [],
                        "comment": "",
                        "tags": [],
                    }.items(),
                    bibliographic_data.items(),
                )
            )
            harvested_references[pmid] = mousemine_reference
            mousemine_harvest_count += 1

    if use_consortium_citations:
        consortium_papers = mongo_access.get_impc_papers()
        for paper in consortium_papers:
            for citing_paper in europe_pmc_api.get_citing_papers(paper["pmid"]):
                if update_exisiting_papers and citing_paper["pmid"] in existing_pmids:
                    if citing_paper["pmid"] not in update_pmids:
                        citing_paper = mongo_access.get_by_pmid(citing_paper["pmid"])
                        update_papers.append(citing_paper)
                        update_pmids.append(citing_paper["pmid"])
                    continue
                if citing_paper["pmid"] not in harvested_references:
                    harvested_references[citing_paper["pmid"]] = dict(
                        chain(
                            {
                                "alleles": [],
                                "status": "pending",
                                "datasource": "europepmc",
                                "consortiumPaper": False,
                                "citations": [],
                                "citedBy": [],
                                "alleleCandidates": [],
                                "comment": "",
                                "tags": [],
                            }.items(),
                            citing_paper.items(),
                        )
                    )
                else:
                    harvested_references[citing_paper["pmid"]]["cites"].append(
                        paper["pmid"]
                    )
                    citation_harvest_count += 1

    search_results = []
    alleles = None
    for keyword in config.get("DEFAULT", "TARGET_KEYWORDS").split(","):
        search_results.extend(europe_pmc_api.get_papers_by_keyword(keyword))
    if use_alleles:
        with open(config.get("DEFAULT", "TARGET_ALLELE_FILE")) as f:
            alleles = f.read().splitlines()
        click.secho(
            "Found {} alleles to use".format(len(alleles)),
            fg="green",
            bold=True,
        )

#        for keyword in alleles:
#            try:
#                search_results.extend(europe_pmc_api.get_papers_by_keyword(keyword))
#            except Exception as e:
#                print('[ERROR] Encountered exception: {}'.format(e.__class__))

    for index, paper in enumerate(search_results):
        if update_exisiting_papers and paper["pmid"] in existing_pmids:
            if paper["pmid"] not in update_pmids:
                paper = mongo_access.get_by_pmid(paper["pmid"])
                update_papers.append(paper)
                update_pmids.append(paper["pmid"])
            continue
        elif paper["pmid"] in harvested_references:
            continue
        else:
            harvested_references[paper["pmid"]] = dict(
                chain(
                    {
                        "alleles": [],
                        "datasource": "europepmc",
                        "status": "pending",
                        "citations": [],
                        "cites": [],
                        "citedBy": [],
                        "alleleCandidates": [],
                        "comment": "",
                        "tags": [],
                    }.items(),
                    paper.items(),
                )
            )
            keyword_harvest_count += 1

    click.secho(
        "Found {} new references in Mousemine".format(mousemine_harvest_count),
        fg="green",
        bold=True,
    )
    click.secho(
        "Found {} new references in EuroPMC".format(keyword_harvest_count),
        fg="green",
        bold=True,
    )
    click.secho(
        "Found {} new references in EuroPMC citing Consortium papers".format(
            citation_harvest_count
        ),
        fg="green",
        bold=True,
    )
    all_raw_references = harvested_references.values()

    for reference in all_raw_references:
        existing_reference = mongo_access.get_by_pmid(reference["pmid"])
        if existing_reference:
            if (
                    existing_reference["datasource"] in ["manual", "europepmc"]
                    and reference["datasource"] == "mousemine"
            ):
                try:
                    mongo_access.update_by_pmid(
                        existing_reference["pmid"],
                        {"alleles": reference["alleles"], "datasource": "mousemine"},
                    )
                except Exception as e:
                    print('[ERROR] Encountered exception: {}'.format(e.__class__))
    if add_order_id:
        click.secho("Updating allele info using provided order ids file", fg="blue")
        with open(config.get("DEFAULT", "ORDER_ID_FILE"), encoding="utf-8-sig") as f:
            csv_orders = [
                {k: v for k, v in row.items()}
                for row in csv.DictReader(f, skipinitialspace=True)
            ]
            pmid_vs_alleles = dict()
            for c in csv_orders:
                allele = (
                    resolve_allele(c["allele"]) if "allele" in c else resolve_allele("")
                )
                allele["_class"] = "org.impc.publications.models.AlleleRef"
                allele["orderId"] = c["order ID"]
                if c["PubMed ID"] not in pmid_vs_alleles:
                    pmid_vs_alleles[c["PubMed ID"]] = []
                pmid_vs_alleles[c["PubMed ID"]].append(allele)
        for ref in all_raw_references:
            ref["alleles"] = (
                pmid_vs_alleles[ref["pmid"]] if ref["pmid"] in pmid_vs_alleles else []
            )
        for ref in update_papers:
            ref["alleles"] = (
                pmid_vs_alleles[ref["pmid"]]
                if ref["pmid"] in pmid_vs_alleles and len(ref["alleles"]) == 0
                else ref["alleles"]
            )
        all_papers = mongo_access.get_all()
        for ref in [paper for paper in all_papers if paper["pmid"] not in update_pmids]:
            ref["alleles"] = (
                pmid_vs_alleles[ref["pmid"]]
                if ref["pmid"] in pmid_vs_alleles and len(ref["alleles"]) == 0
                else ref["alleles"]
            )
            update_papers.append(ref)
            update_pmids.append(ref["pmid"])

    click.secho("NLP Processing", fg="blue")
    if use_infrafrontier_nlp:
        long_alleles = [allele_name for allele_name in alleles if len(allele_name) > 7]
        all_references_processed = Parallel(n_jobs=8)(
            delayed(nlp.get_fragments)(reference, long_alleles)
            for reference in tqdm(all_raw_references)
        )
    else:
        all_references_processed = Parallel(n_jobs=8)(
            delayed(nlp.get_fragments)(reference, alleles)
            for reference in tqdm(all_raw_references)
        )
    if len(all_references_processed) > 0:
        mongo_access.insert_all(all_references_processed)

    if use_infrafrontier_nlp:
        click.secho("Skipping NLP Processing for existing papers", fg="blue")
        return

    click.secho("Update NLP Processing for existing papers", fg="blue")
    if len(update_papers) == 0:
        click.secho("    Updating all", fg="blue")
        update_papers = mongo_access.get_all()
    else:
        for paper in mongo_access.get_all():
            if paper["pmid"] not in update_pmids:
                update_papers.append(paper)
                update_pmids.append(paper["pmid"])
    update_references_processed = Parallel(n_jobs=8)(
        delayed(nlp.get_fragments)(reference, alleles)
        for reference in tqdm(update_papers)
    )

    click.secho(
        f"Update existing papers in Mongodb: {len(update_references_processed)}",
        fg="blue",
    )
    for reference in tqdm(update_references_processed):
        try:
            mongo_access.update_by_pmid(
                reference["pmid"],
                {
                    "fragments": reference["fragments"],
                    "comment": reference["comment"]
                    if "comment" in reference and reference["comment"] is not None
                    else "",
                    "tags": reference["tags"]
                    if "tags" in reference and reference["tags"] is not None
                    else [],
                    "citations": reference["citations"] if "citations" in reference else [],
                    "alleleCandidates": reference["alleleCandidates"],
                    "alleles": reference["alleles"] if "alleles" in reference else [],
                    "correspondence": reference["correspondence"]
                    if "correspondence" in reference
                    else [],
                },
            )
        except Exception as e:
            print('[ERROR] Encountered exception: {}'.format(e.__class__))
    click.secho("Update existing papers in Mongodb", fg="blue")
    click.secho("Finished", fg="blue")


if __name__ == "__main__":
    harvest()

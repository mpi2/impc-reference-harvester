from urllib import request
import tarfile
import requests
import time
import json
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO, BytesIO
from bs4 import BeautifulSoup
from bs4.element import Comment
import os.path

from requests.adapters import HTTPAdapter
from urllib3 import Retry

from utils import config, logger
from urllib import parse


session = requests.session()
retries = Retry(total=5, backoff_factor=1)
session.mount("http://", HTTPAdapter(max_retries=retries))
session.mount("https://", HTTPAdapter(max_retries=retries))


def download_fulltext(reference):
    url_list = reference["fullTextUrlList"]
    urls_by_type = {url["documentStyle"]: url["url"] for url in url_list}
    nxml_file_name = (
        config.get("DEFAULT", "XML_DIR") + "/" + reference["pmid"] + ".nxml"
    )
    txt_file_name = config.get("DEFAULT", "TXT_DIR") + "/" + reference["pmid"] + ".txt"

    if os.path.isfile(nxml_file_name) or get_xml(reference):
        with open(nxml_file_name, "r") as xml_file:
            cites_pmids = reference["cites"] if "cites" in reference else []
            text, citations, correspondence = process_xml(xml_file.read(), cites_pmids)
            if len(cites_pmids) > 0 and len(citations) > 0:
                reference["citations"].extend(citations)
            if len(correspondence) > 0:
                reference["correspondence"] = correspondence
    elif os.path.isfile(txt_file_name):
        with open(txt_file_name, "r") as txt_file:
            text = txt_file.read()
    elif "html" in urls_by_type:
        text = process_html(urls_by_type["html"])
    elif "pdf" in urls_by_type:
        text = process_pdf(urls_by_type["pdf"])
    elif "doi" in urls_by_type:
        text = process_doi(urls_by_type["doi"])
    else:
        text = ""
    if not os.path.isfile(txt_file_name) and len(text) > 0:
        with open(txt_file_name, "w") as txt_file:
            txt_file.write(text)
    return text


def process_html(url):
    response = process_url(url)
    if response is None:
        return ""
    body = (
        response.text.replace("\n", " ")
        .replace("<sup>", "&lt;")
        .replace("</sup>", "&gt;")
    )
    soup = BeautifulSoup(body, "html.parser")
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return " ".join(t.strip() for t in visible_texts)


def process_xml(xml_text, cites_pmids):
    if not xml_text:
        return ""
    xml_text = (
        xml_text.replace("\n", " ")
        .replace("<sup>", "&lt;")
        .replace("</sup>", "&gt;")
        .replace("<italic>", "")
        .replace("</italic>", "")
    )
    soup = BeautifulSoup(xml_text, "xml")
    text = ""
    sections = ["ack", "funding-group", "abstract", "article-title", "body"]
    for section in sections:
        section_content = soup.find_all(section)
        text += " ".join(t.text.strip() for t in section_content)

    citations = []
    for cites_pmid in cites_pmids:
        ref_list_elem = soup.find("ref-list")
        if ref_list_elem:
            pub_id_elem = ref_list_elem.find(
                "pub-id", {"pub-id-type": "pmid"}, text=cites_pmid
            )
            if pub_id_elem:
                citation_elem = pub_id_elem.parent
                if citation_elem:
                    ref_elem = citation_elem.parent
                    if ref_elem.has_attr("id"):
                        ref_id = ref_elem["id"]
                        citations_elems = soup.findAll("xref", {"rid": ref_id})
                        pmid_citations = []
                        for citation in citations_elems:
                            if citation.findParent("p"):
                                citation_text = citation.findParent("p").text.replace(
                                    citation.text, "[{}]".format(cites_pmid)
                                )
                                citation_text = citation_text.replace(
                                    "[" + citation.text + "]", "[{}]".format(cites_pmid)
                                )
                                citation_text = citation_text.replace(
                                    citation.text + ",", "[{}]".format(cites_pmid)
                                )
                                pmid_citations.append(citation_text)
                        citations.append(
                            {"pmid": cites_pmid, "references": pmid_citations}
                        )
    return text, citations, get_corresponding_authors(soup)


def process_pdf(url):
    response = process_url(url)
    if not response:
        return ""
    pdf_content = response.content
    pdf_content = BytesIO(pdf_content)
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = "utf-8"
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()

    for page in PDFPage.get_pages(
        pdf_content,
        pagenos,
        maxpages=maxpages,
        password=password,
        caching=caching,
        check_extractable=True,
    ):
        interpreter.process_page(page)

    text = retstr.getvalue()
    device.close()
    retstr.close()
    return text


def process_doi(url):
    url = resolve_doi(url)
    return process_html(url)


def process_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36 Edge/12.0"
    }
    try:
        response = session.get(url, headers=headers)
    except Exception as e:
        logger.info("Failed to get: {} time".format(url))
        return None
    return response


def resolve_doi(doi_url):
    doi = doi_url.replace("https://doi.org/", "")
    doi_resolver_request = config.get("DEFAULT", "DOI_RESOLVER_URL").format(
        doi=parse.quote(doi)
    )
    response = session.get(doi_resolver_request)
    response = json.loads(response.content.decode("utf-8"))
    if "values" in response and response["values"]:
        return response["values"][0]["data"]["value"]
    else:
        return doi_url


def get_xml(reference):
    if "pmcid" not in reference:
        return False
    if "isOpenAccess" in reference and reference["isOpenAccess"] != "Y":
        return False
    rq_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/PMC{reference['pmcid']}/fullTextXML"
    try:
        # logger.info("PMC OA query started: " + rq_url)
        # pmc_xml_record = session.get(rq_url).text
        # pmc_xml_soup = BeautifulSoup(pmc_xml_record, "xml")
        # if pmc_xml_soup.find("error"):
        #     logger.error("File not found in PMC-OA: " + rq_url)
        #     return False
        # link_element = pmc_xml_soup.find("link")
        # href_value = link_element["href"]
        # if href_value:
        #     extract_tgz(
        #         href_value, config.get("DEFAULT", "XML_DIR") + "/", reference["pmid"]
        #     )
        #     return True
        logger.info("EuropePMC query started: " + rq_url)
        r = session.get(rq_url)
        file = open(
            config.get("DEFAULT", "XML_DIR") + "/" + reference["pmid"] + ".nxml", "w"
        )
        file.write(r.text)
        file.close()
    except Exception as e:
        logger.error("PMC OA query failed " + rq_url + ": " + str(e))
        return False


def extract_tgz(ftp_url, out_path, pmcid):
    tmpfile = BytesIO()
    ftpstream = request.urlopen(ftp_url)
    while True:
        s = ftpstream.read(16384)
        if not s:
            break
        tmpfile.write(s)
    ftpstream.close()
    tmpfile.seek(0)
    tar = tarfile.open(fileobj=tmpfile, mode="r:gz")
    for member in tar.getmembers():
        if member.isreg() and member.name.endswith(".nxml"):
            member.name = pmcid + ".nxml"
            tar.extract(member, out_path + "/")  # extract
    tar.close()
    tmpfile.close()


def tag_visible(element):
    if element.parent.name in [
        "style",
        "script",
        "head",
        "title",
        "meta",
        "[document]",
    ]:
        return False
    if isinstance(element, Comment):
        return False
    return True


def get_corresponding_authors(soup):
    corresponding_refs = soup.find_all("xref", {"ref-type": "corresp"})
    correspondence_info = {}
    for corresponding_ref in corresponding_refs:
        if corresponding_ref["rid"] not in correspondence_info:
            correspondence_info[corresponding_ref["rid"]] = {
                "authors": [],
                "emails": [],
            }
            corresp = soup.find(attrs={"id": corresponding_ref["rid"]})
            if corresp is None:
                print(
                    "NO CORRESP: "
                    + soup.find("article-id", {"pub-id-type": "pmid"}).text
                )
                emails = []
            else:
                emails = [email.text for email in corresp.find_all("email")]
            correspondence_info[corresponding_ref["rid"]]["emails"] = emails
        if corresponding_ref.parent.find("given-names") is None:
            print(
                "NO GIVEN NAMES: "
                + soup.find("article-id", {"pub-id-type": "pmid"}).text
            )
            author_given_names = ""
            if corresponding_ref.parent.find("collab") is not None:
                author_given_names = corresponding_ref.parent.find("collab").text
        else:
            author_given_names = corresponding_ref.parent.find("given-names").text
        if corresponding_ref.parent.find("surname") is None:
            print(
                "NO SURNAME: " + soup.find("article-id", {"pub-id-type": "pmid"}).text
            )
            author_surname = ""
        else:
            author_surname = corresponding_ref.parent.find("surname").text
        author_name = author_given_names + " " + author_surname
        correspondence_info[corresponding_ref["rid"]]["authors"].append(author_name)
    return list(correspondence_info.values())

import nltk
import re
from utils.fulltext_downloader import *
from utils.solr_access import resolve_allele


def get_fragments(reference):
    text = download_fulltext(reference)
    reference['fragments'], reference['alleleCandidates'] = get_fragments_from_text(text)
    return reference


def get_fragments_from_text(text):
    fragments = {
        'EUCOMM': [],
        'KOMP': [],
        'IKMC': [],
        'International Knockout Mouse Consortium': [],
        'IMPC': [],
        'International Mouse Phenotyping Consortium': [],
    }
    allele_name_candidates = [match.group().replace(' ', '') for match in re.finditer('(([a-z]|[0-9])*?(\s*)<(\s*)tm([A-Z]|[a-z]|[0-9]|\.)*?\((eucomm|komp)\)([a-z]|[0-9])*?\s*>)', text, re.IGNORECASE)]
    allele_name_candidates = [allele_symbol.replace('eucomm', 'EUCOMM').replace('komp', 'KOMP').replace(' ', '') for
                         allele_symbol in allele_name_candidates]
    allele_name_candidates = list(set(allele_name_candidates))
    allele_candidates = [resolve_allele(candidate_name) for candidate_name in allele_name_candidates]

    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    sentences = tokenizer.tokenize(text)
    for i, sentence in enumerate(sentences):
        for key in fragments:
            if re.search(key, sentence, re.IGNORECASE):
                mention_context = sentences[i - 1] if i - 1 >= 0 else ''
                mention_context += sentence
                mention_context += sentences[i + 1] if i + 1 < len(sentences) else ''
                fragments[key].append(mention_context)
    return fragments, allele_candidates

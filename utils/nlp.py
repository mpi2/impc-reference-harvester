import nltk
import re
from utils.fulltext_downloader import *
from utils.mongo_access import get_by_allele_symbol


def get_fragments(reference, alleles=None):
    text = download_fulltext(reference)
    reference['fragments'], reference['alleleCandidates'] = get_fragments_from_text(text, alleles)
    return reference


def get_fragments_from_text(text, alleles=None):
    if alleles is None:
        allele_name_candidates = [match.group().replace(' ', '') for match in re.finditer(config.get('DEFAULT', 'ALLELE_REGEX'), text, re.IGNORECASE)]
        allele_name_candidates = [allele_symbol.replace('eucomm', 'EUCOMM').replace('komp', 'KOMP').replace('impc', 'IMPC').replace(' ', '') for
                             allele_symbol in allele_name_candidates]
        allele_name_candidates = list(set(allele_name_candidates))
    else:
        allele_name_candidates = alleles

    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    sentences = tokenizer.tokenize(text)

    keywords = config.get('DEFAULT', 'TEXT_KEYWORDS').split(',')
    if alleles is not None:
        keywords.extend(alleles)
    else:
        keywords.extend(allele_name_candidates)
    fragments = {}
    allele_candidates = []
    for i, sentence in enumerate(sentences):
        for key in keywords:
            if re.search(re.escape(key), sentence, re.IGNORECASE):
                mention_context = sentences[i - 1] if i - 1 >= 0 else ''
                mention_context += ' ' + sentence
                mention_context += ' ' + sentences[i + 1] if i + 1 < len(sentences) else ''
                if key not in fragments:
                    fragments[key] = []
                fragments[key].append(mention_context)
                if key in allele_name_candidates and key not in allele_candidates:
                    allele_candidates.append(key)
    allele_candidates = [get_by_allele_symbol(candidate_name) for candidate_name in
                         allele_candidates]
    return [{'keyword': key, 'mentions': mentions} for key, mentions in fragments.items()], allele_candidates
